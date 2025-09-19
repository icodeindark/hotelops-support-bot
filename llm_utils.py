import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GEN_API_KEY"))

def ask_gemini(prompt: str):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            return "⚠️ **API Quota Exceeded** - I've reached my daily request limit. Please try again later or contact support for assistance with your request."
        else:
            return f"⚠️ **Service Temporarily Unavailable** - I encountered an error: {error_msg[:100]}... Please try again in a moment."
