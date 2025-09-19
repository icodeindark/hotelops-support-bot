import os
import google.generativeai as genai
from dotenv import load_dotenv
from logger_config import llm_logger, api_logger, log_api_call, log_error

load_dotenv()
genai.configure(api_key=os.environ.get("GEN_API_KEY"))

def ask_gemini(prompt: str):
    try:
        # Log the API call attempt
        prompt_preview = prompt[:150] + "..." if len(prompt) > 150 else prompt
        llm_logger.info(f"Gemini API call - Prompt: {prompt_preview}")
        
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        
        # Log successful response
        response_preview = response.text[:100] + "..." if len(response.text) > 100 else response.text
        log_api_call("GEMINI", "SUCCESS", f"Response: {response_preview}")
        llm_logger.info(f"Gemini API success - Response length: {len(response.text)} chars")
        
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        
        # Log the error with details
        log_error("API_ERROR", f"Gemini API failed: {error_msg}", function_name="ask_gemini")
        llm_logger.error(f"Gemini API error: {error_msg}")
        
        if "quota" in error_msg.lower() or "429" in error_msg:
            log_api_call("GEMINI", "QUOTA_EXCEEDED", "Daily quota limit reached")
            return "⚠️ **API Quota Exceeded** - I've reached my daily request limit. Please try again later or contact support for assistance with your request."
        else:
            log_api_call("GEMINI", "ERROR", f"Error: {error_msg[:100]}")
            return f"⚠️ **Service Temporarily Unavailable** - I encountered an error: {error_msg[:100]}... Please try again in a moment."
