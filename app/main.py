from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.process_routes import router as process_router
from app.routes.home_routes import router as home_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(process_router)
app.include_router(home_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Court Case Scraper API!"}
