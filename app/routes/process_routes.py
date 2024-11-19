from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.transcription_service import YouTubeTranscriber
from app.services.qa_service import QABot
from utils.file_utils import remove_file
import os
import google.generativeai as genai

router = APIRouter()

class ProcessRequest(BaseModel):
    action: str
    input: str

api_key = os.getenv("ASSEMBLYAI_API_KEY")
genaiApiKey = os.getenv("GENAI_API_KEY")
modelName = "multi-qa-mpnet-base-dot-v1"

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

@router.post("/process")
async def process_request(request: ProcessRequest):
    action = request.action
    input_text = request.input

    if os.path.exists('video.m4a'):
        os.remove('video.m4a')

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
