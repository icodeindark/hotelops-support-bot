import os
import hashlib
import time
from functools import lru_cache
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
from logger_config import llm_logger, api_logger, log_api_call, log_error

load_dotenv()
genai.configure(api_key=os.environ.get("GEN_API_KEY"))

class QuotaManager:
    """Manages API quota and request deduplication"""
    
    def __init__(self):
        self.daily_requests = 0
        self.max_requests = 40  # Leave buffer for free tier
        self.last_reset = datetime.now().date()
        self.processed_requests = set()
        self.request_cache = {}
        
    def can_make_request(self):
        """Check if we can make a request without exceeding quota"""
        today = datetime.now().date()
        
        # Reset counter if new day
        if today != self.last_reset:
            self.daily_requests = 0
            self.last_reset = today
            self.processed_requests.clear()
            self.request_cache.clear()
            
        return self.daily_requests < self.max_requests
    
    def record_request(self, prompt_hash: str):
        """Record a request to track quota"""
        self.daily_requests += 1
        self.processed_requests.add(prompt_hash)
    
    def is_duplicate(self, prompt_hash: str):
        """Check if this exact prompt was already processed"""
        return prompt_hash in self.processed_requests
    
    def get_cached_response(self, prompt_hash: str):
        """Get cached response if available"""
        return self.request_cache.get(prompt_hash)
    
    def cache_response(self, prompt_hash: str, response: str):
        """Cache a response"""
        self.request_cache[prompt_hash] = response

# Global quota manager
quota_manager = QuotaManager()

@lru_cache(maxsize=100)
def ask_gemini_cached(prompt_hash: str, prompt: str):
    """Cached version of ask_gemini to avoid duplicate processing"""
    try:
        # Log the API call attempt
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        llm_logger.info(f"Gemini API call - Prompt: {prompt_preview}")
        
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        
        # Log successful response
        response_preview = response.text[:50] + "..." if len(response.text) > 50 else response.text
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

def ask_gemini(prompt: str):
    """Optimized Gemini API call with caching and quota management"""
    
    # Create hash for deduplication
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    
    # Check for duplicates
    if quota_manager.is_duplicate(prompt_hash):
        llm_logger.info(f"Skipping duplicate request: {prompt_hash[:8]}...")
        return "Request already processed"
    
    # Check quota
    if not quota_manager.can_make_request():
        log_api_call("GEMINI", "QUOTA_LIMIT", "Daily quota limit reached")
        return "⚠️ **API Quota Exceeded** - I've reached my daily request limit. Please try again later."
    
    # Check cache first
    cached_response = quota_manager.get_cached_response(prompt_hash)
    if cached_response:
        llm_logger.info(f"Returning cached response for: {prompt_hash[:8]}...")
        return cached_response
    
    # Make API call
    response = ask_gemini_cached(prompt_hash, prompt)
    
    # Record request and cache response
    quota_manager.record_request(prompt_hash)
    quota_manager.cache_response(prompt_hash, response)
    
    return response

def get_quota_status():
    """Get current quota status"""
    return {
        "daily_requests": quota_manager.daily_requests,
        "max_requests": quota_manager.max_requests,
        "remaining": quota_manager.max_requests - quota_manager.daily_requests,
        "can_make_request": quota_manager.can_make_request()
    }
