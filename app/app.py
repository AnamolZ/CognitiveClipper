import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from app.services.youtube_service import YouTubeService
from app.services.genai_service import GenaiService

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Load API keys from .env
api_key = os.getenv("ASSEMBLYAI_API_KEY")
genaiApiKey = os.getenv("GENAI_API_KEY")
modelName = "multi-qa-mpnet-base-dot-v1"

class ProcessRequest(BaseModel):
    action: str
    input: str

@app.post("/process")
async def process_request(request: ProcessRequest):
    action = request.action
    input_text = request.input

    if action == "transcribe":
        yt_service = YouTubeService(api_key, input_text)
        yt_service.download_video()
        transcript_text = yt_service.transcribe_video("video.m4a")
        if not transcript_text:
            raise HTTPException(status_code=500, detail="Transcription failed.")
        
        genai_service = GenaiService(modelName, genaiApiKey)
        summary_text = genai_service.getSummary(transcript_text)
        return JSONResponse(content={"status": "success", "summary": summary_text})

    elif action == "ask":
        genai_service = GenaiService(modelName, genaiApiKey)
        answer_text = genai_service.getAnswer(input_text, [input_text])
        return JSONResponse(content={"status": "success", "answer": answer_text})

    else:
        raise HTTPException(status_code=400, detail="Invalid action.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
