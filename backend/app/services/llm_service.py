import google.generativeai as genai

from app.config import settings


def get_gemini_client() -> genai.GenerativeModel:
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)
