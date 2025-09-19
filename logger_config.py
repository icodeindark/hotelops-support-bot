import logging
import os
from datetime import datetime

def setup_logger():
    """Setup comprehensive logging for the HotelOpsAI Support Bot"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"hotelops_bot_{timestamp}.log")
    
    # Configure logging format
    log_format = """%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | Line:%(lineno)-4d | %(message)s"""
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Create specific loggers for different components
    loggers = {
        'main': logging.getLogger('main'),
        'agent': logging.getLogger('agent'),
        'user_mgmt': logging.getLogger('user_mgmt'),
        'session': logging.getLogger('session'),
        'faq': logging.getLogger('faq'),
        'llm': logging.getLogger('llm'),
        'api': logging.getLogger('api'),
        'error': logging.getLogger('error')
    }
    
    # Set specific log levels
    loggers['error'].setLevel(logging.ERROR)
    loggers['api'].setLevel(logging.INFO)
    
    print(f"🔧 Logging initialized. Log file: {log_file}")
    
    return loggers, log_file

# Initialize loggers
loggers, current_log_file = setup_logger()

# Export commonly used loggers
main_logger = loggers['main']
agent_logger = loggers['agent']
user_mgmt_logger = loggers['user_mgmt']
session_logger = loggers['session']
faq_logger = loggers['faq']
llm_logger = loggers['llm']
api_logger = loggers['api']
error_logger = loggers['error']

def log_action(action_type: str, details: str, user_id: str = None, session_id: str = None):
    """Log user actions with context"""
    context = f"Session:{session_id}" if session_id else "No-Session"
    if user_id:
        context += f" | User:{user_id}"
    
    main_logger.info(f"ACTION[{action_type}] | {context} | {details}")

def log_error(error_type: str, error_msg: str, function_name: str = None, session_id: str = None):
    """Log errors with context"""
    context = f"Session:{session_id}" if session_id else "No-Session"
    if function_name:
        context += f" | Function:{function_name}"
    
    error_logger.error(f"ERROR[{error_type}] | {context} | {error_msg}")

def log_api_call(api_name: str, status: str, details: str = None, tokens_used: int = None):
    """Log API calls and token usage"""
    token_info = f" | Tokens:{tokens_used}" if tokens_used else ""
    detail_info = f" | {details}" if details else ""
    
    api_logger.info(f"API[{api_name}] | Status:{status}{token_info}{detail_info}")

def log_user_mgmt(action: str, user_data: dict, session_id: str = None):
    """Log user management actions"""
    user_info = f"Name:{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
    email_info = f"Email:{user_data.get('email', 'N/A')}"
    context = f"Session:{session_id}" if session_id else "No-Session"
    
    user_mgmt_logger.info(f"USER_MGMT[{action}] | {context} | {user_info} | {email_info}")

# Export current log file for display in debug panel
def get_current_log_file():
    return current_log_file
