import requests
import time
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from rich import print
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

GENAI_API = os.getenv("GENAI_API_KEY")

genai.configure(api_key=GENAI_API)

class AudioTranscription:
    def __init__(self, assemblyai_api_key):
        self.assemblyai_api_key = assemblyai_api_key

    def transcribe_audio(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"The audio file {audio_path} does not exist.")
        upload_url = self.upload_audio(audio_path)
        transcription_id = self.request_transcription(upload_url)
        return self.poll_for_transcription(transcription_id)

    def upload_audio(self, audio_path):
        upload_endpoint = 'https://api.assemblyai.com/v2/upload'
        with open(audio_path, 'rb') as f:
            response = requests.post(upload_endpoint, headers={'authorization': self.assemblyai_api_key}, files={'file': f})
        response.raise_for_status()
        return response.json()['upload_url']

    def request_transcription(self, upload_url):
        transcription_endpoint = 'https://api.assemblyai.com/v2/transcript'
        transcription_payload = {'audio_url': upload_url}
        response = requests.post(transcription_endpoint, json=transcription_payload, headers={'authorization': self.assemblyai_api_key})
        response.raise_for_status()
        return response.json()['id']

    def poll_for_transcription(self, transcription_id):
        transcription_endpoint = f'https://api.assemblyai.com/v2/transcript/{transcription_id}'
        max_wait_time = 600
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            response = requests.get(transcription_endpoint, headers={'authorization': self.assemblyai_api_key})
            response_data = response.json()
            if response_data['status'] == 'completed':
                return response_data['text']
            elif response_data['status'] == 'error':
                raise Exception(f"Transcription failed: {response_data.get('error', 'Unknown error')}")
            time.sleep(5)
        raise TimeoutError('Transcription timed out')

class QABot:
    def __init__(self, model, index):
        self.model = model
        self.index = index

    def fetch_relevant_data(self, query, topK=5):
        query_embedding = self.model.encode(query, convert_to_tensor=True).tolist()
        try:
            response = self.index.query(vector=query_embedding, top_k=topK, include_metadata=True)
            relevant_data = [(match["score"], match["metadata"]["text"]) for match in response["matches"]]
        except Exception as e:
            print(f"[red]Error querying Pinecone index: {e}[/red]")
            relevant_data = []
        return relevant_data

    def generate_answer(self, query, relevant_data):
        if not relevant_data:
            return "No relevant data found."

        scores = [score for score, _ in relevant_data]
        max_score = max(scores)
        normalized_scores = [score / max_score for score in scores]

        answer_pieces = [
            f"**Passage {i+1} (Score: {normalized_scores[i]:.2f}):** {text}"
            for i, (_, text) in enumerate(relevant_data)
        ]
        return "\n\n".join(answer_pieces)

    def answer_query(self, query):
        relevant_data = self.fetch_relevant_data(query)
        answer = self.generate_answer(query, relevant_data)
        return answer

def setup_pinecone_and_genai():
    load_dotenv()
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    model_name = "multi-qa-mpnet-base-dot-v1"
    model = SentenceTransformer(model_name)
    
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(index_name)
    
    return model, index

def interactive_qa(audio_path, assemblyai_api_key, model, index):
    audio_transcription = AudioTranscription(assemblyai_api_key)
    try:
        transcription_text = audio_transcription.transcribe_audio(audio_path)
        
        genai_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        input_user = f"This document contains a transcription of the video's audio. Please just provide a professionally crafted summary based on the transcript paragraph. Transcription: {transcription_text}"
        response = genai_model.generate_content(input_user)
        print(response.text)

        qa_bot = QABot(model, index)
        while True:
            query = input("Ask: ").strip()
            if query.lower() == 'exit':
                break

            answer = qa_bot.answer_query(query)
            input_user = f"For this question, I'm seeking the perfect answer. Please provide the answer directly. {query}\n\n{answer}"
            response = genai_model.generate_content(input_user)
            print(response.text)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    assemblyai_api = os.getenv("ASSEMBLYAI_API_KEY")
    assemblyai_api_key = assemblyai_api
    audio_path = 'audio.mp3'
    
    model, index = setup_pinecone_and_genai()
    interactive_qa(audio_path, assemblyai_api_key, model, index)
