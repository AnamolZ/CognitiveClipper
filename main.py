import requests
import time
import os
from dotenv import load_dotenv
from rich import print
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from numpy import dot
from numpy.linalg import norm

class AudioTranscription:
    def __init__(self, apiKey):
        self.apiKey = apiKey

    def transcribeAudio(self, audioPath):
        if not os.path.exists(audioPath):
            raise FileNotFoundError(f"Audio file {audioPath} not found.")
        uploadUrl = self.uploadAudio(audioPath)
        transcriptionId = self.requestTranscription(uploadUrl)
        return self.pollForTranscription(transcriptionId)

    def uploadAudio(self, audioPath):
        endpoint = 'https://api.assemblyai.com/v2/upload'
        with open(audioPath, 'rb') as file:
            response = requests.post(endpoint, headers={'authorization': self.apiKey}, files={'file': file})
        response.raise_forStatus()
        return response.json()['upload_url']

    def requestTranscription(self, uploadUrl):
        endpoint = 'https://api.assemblyai.com/v2/transcript'
        payload = {'audio_url': uploadUrl}
        response = requests.post(endpoint, json=payload, headers={'authorization': self.apiKey})
        response.raise_forStatus()
        return response.json()['id']

    def pollForTranscription(self, transcriptionId):
        endpoint = f'https://api.assemblyai.com/v2/transcript/{transcriptionId}'
        maxWaitTime = 600
        startTime = time.time()
        while time.time() - startTime < maxWaitTime:
            response = requests.get(endpoint, headers={'authorization': self.apiKey})
            responseData = response.json()
            if responseData['status'] == 'completed':
                return responseData['text']
            if responseData['status'] == 'error':
                raise Exception(f"Transcription failed: {responseData.get('error', 'Unknown error')}")
            time.sleep(5)
        raise TimeoutError('Transcription timed out')

class QABot:
    def __init__(self, model):
        self.model = model

    def generateAnswer(self, query, relevantData):
        if not relevantData:
            return "No relevant data found."
        scores = [score for score, _ in relevantData]
        maxScore = max(scores) if scores else 1
        normalizedScores = [score / maxScore for score in scores]
        return "\n\n".join(f"**Passage {i + 1} (Score: {normalizedScores[i]:.2f}):** {text}" 
                           for i, (_, text) in enumerate(relevantData))

    def answerQuery(self, query, localData):
        relevantData = self.fetchRelevantData(query, localData)
        return self.generateAnswer(query, relevantData)

    def fetchRelevantData(self, query, localData, topK=5):
        queryEmbedding = self.model.encode(query, convert_to_tensor=True).tolist()
        scoresAndTexts = []
        for text in localData:
            textEmbedding = self.model.encode(text, convert_to_tensor=True).tolist()
            score = self.computeSimilarity(queryEmbedding, textEmbedding)
            scoresAndTexts.append((score, text))
        sortedScoresAndTexts = sorted(scoresAndTexts, key=lambda x: x[0], reverse=True)
        return sortedScoresAndTexts[:topK]

    def computeSimilarity(self, queryEmbedding, textEmbedding):
        return dot(queryEmbedding, textEmbedding) / (norm(queryEmbedding) * norm(textEmbedding))

class GenaiQA:
    def __init__(self, modelName, genaiApiKey):
        self.model = SentenceTransformer(modelName)
        genai.configure(api_key=genaiApiKey)
        self.genaiModel = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def interactiveQA(self, audioPath, transcriptionText):
        if not transcriptionText:
            videoId = "FZieYYj0ImE"
            transcriptionText = self.getTranscript(videoId)
            if transcriptionText.startswith("Error:"):
                print("Unsupported right now.")
                return

        inputUser = (f"This document contains a transcription of the video's audio. Please just provide a professionally crafted summary based on the transcript paragraph. Transcription: {transcriptionText}")
        response = self.genaiModel.generate_content(inputUser)
        print(response.text)

        localData = [transcriptionText]
        qaBot = QABot(self.model)
        while True:
            query = input("Ask: ").strip()
            if query.lower() == 'exit':
                break
            answer = qaBot.answerQuery(query, localData)
            inputUser = f"For this question, I'm seeking the perfect answer. Please provide the answer directly. {query}\n\n{answer}"
            response = self.genaiModel.generate_content(inputUser)
            print(response.text)

    def getTranscript(self, videoId):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(videoId)
            return " ".join(item['text'] for item in transcript)
        except Exception as e:
            return f"Error: {e}"

def main():
    load_dotenv()
    assemblyaiApiKey = os.getenv("ASSEMBLYAI_API_KEY")
    genaiApiKey = os.getenv("GENAI_API_KEY")
    audioPath = 'audio.mp3'
    modelName = "multi-qa-mpnet-base-dot-v1"

    audioTranscription = AudioTranscription(assemblyaiApiKey)
    transcriptionText = None
    if audioPath:
        try:
            transcriptionText = audioTranscription.transcribeAudio(audioPath)
        except Exception as e:
            print(f"Audio transcription error: {e}")

    genaiQA = GenaiQA(modelName, genaiApiKey)
    genaiQA.interactiveQA(audioPath, transcriptionText)

if __name__ == "__main__":
    main()
