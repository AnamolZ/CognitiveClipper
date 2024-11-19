import google.generativeai as genai
from app.services.qa_service import QAService
from sentence_transformers import SentenceTransformer

class GenaiService:
    def __init__(self, model_name, genai_api_key):
        self.model = SentenceTransformer(model_name)
        genai.configure(api_key=genai_api_key)
        self.genai_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def get_summary(self, transcription_text):
        if not transcription_text:
            return "No transcription text provided."
        input_user = (f"This document contains a transcription of the video's audio. Please provide a professionally crafted summary based on the transcript. Transcription: {transcription_text}")
        response = self.genai_model.generate_content(input_user)
        return response.text

    def get_answer(self, query, local_data):
        qa_service = QAService(self.model)
        answer = qa_service.answer_query(query, local_data)
        input_user = f"For this question, provide a direct and accurate answer. {query}\n\n{answer}"
        response = self.genai_model.generate_content(input_user)
        return response.text
