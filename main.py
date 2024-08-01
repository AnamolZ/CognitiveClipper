import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from rich import print
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import yt_dlp
import assemblyai as aai
from numpy import dot
from numpy.linalg import norm

load_dotenv()

class ProcessRequest(BaseModel):
    action: str
    input: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

api_key = os.getenv("ASSEMBLYAI_API_KEY")
genaiApiKey = os.getenv("GENAI_API_KEY")
modelName = "multi-qa-mpnet-base-dot-v1"

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

    def getSummary(self, transcriptionText):
        if not transcriptionText:
            return "No transcription text provided."

        inputUser = (f"This document contains a transcription of the video's audio. Please just provide a professionally crafted summary based on the transcript paragraph. Transcription: {transcriptionText}")
        response = self.genaiModel.generate_content(inputUser)
        return response.text

    def getAnswer(self, query, localData):
        qaBot = QABot(self.model)
        answer = qaBot.answerQuery(query, localData)
        inputUser = f"For this question, I'm seeking the perfect answer. Please provide the answer directly. {query}\n\n{answer}"
        response = self.genaiModel.generate_content(inputUser)
        return response.text

class YouTubeTranscriber:
    def __init__(self, api_key, url):
        self.api_key = api_key
        self.url = url
        self.ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'merge_output_format': None,
        }
        aai.settings.api_key = self.api_key

    def remove_existing_video(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def download_video(self):
        try:
            self.remove_existing_video('video.mp4')
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.url])
            print("Download completed successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")

    def transcribe_video(self, filename):
        if not os.path.exists(filename):
            print(f"File {filename} not found.")
            return ""
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(filename)
        return transcript.text

@app.post("/process")
async def process_request(request: ProcessRequest):
    action = request.action
    input_text = request.input

    if action == "transcribe":
        yt_transcriber = YouTubeTranscriber(api_key, input_text)
        yt_transcriber.download_video()
        transcript_text = yt_transcriber.transcribe_video("video.m4a")
        if not transcript_text:
            raise HTTPException(status_code=500, detail="Transcription failed.")
        
        genaiQA = GenaiQA(modelName, genaiApiKey)
        summary_text = genaiQA.getSummary(transcript_text)
        
        return JSONResponse(content={"status": "success", "summary": summary_text})

    elif action == "ask":
        genaiQA = GenaiQA(modelName, genaiApiKey)
        answer_text = genaiQA.getAnswer(input_text, [input_text])
        
        return JSONResponse(content={"status": "success", "answer": answer_text})

    else:
        raise HTTPException(status_code=400, detail="Invalid action.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)