from typing import Dict, Any, Optional
from enum import Enum

class ConversationState(Enum):
    IDLE = "idle"
    COLLECTING_USER_DATA = "collecting_user_data"
    CONFIRMING_USER_CREATE = "confirming_user_create"
    COLLECTING_USER_UPDATES = "collecting_user_updates"
    CONFIRMING_USER_UPDATE = "confirming_user_update"
    CONFIRMING_USER_DELETE = "confirming_user_delete"
    CONFIRMING_USER_BLOCK = "confirming_user_block"
    COLLECTING_PASSWORD_RESET = "collecting_password_reset"
    COLLECTING_SERVICE_DATA = "collecting_service_data"
    CONFIRMING_SERVICE_CREATE = "confirming_service_create"

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session data"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'state': ConversationState.IDLE,
                'data': {},
                'context': {},
                'last_action': None,
                'pending_confirmation': None
            }
        return self.sessions[session_id]
    
    def set_state(self, session_id: str, state: ConversationState, data: Dict[str, Any] = None):
        """Set conversation state with optional data"""
        session = self.get_session(session_id)
        session['state'] = state
        if data:
            session['data'].update(data)
    
    def update_session_data(self, session_id: str, data: Dict[str, Any]):
        """Update session data without changing state"""
        session = self.get_session(session_id)
        session['data'].update(data)
    
    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.sessions:
            self.sessions[session_id] = {
                'state': ConversationState.IDLE,
                'data': {},
                'context': {},
                'last_action': None,
                'pending_confirmation': None
            }
    
    def is_in_conversation(self, session_id: str) -> bool:
        """Check if session is in an active conversation"""
        session = self.get_session(session_id)
        return session['state'] != ConversationState.IDLE
    
    def get_missing_fields(self, session_id: str, required_fields: list) -> list:
        """Get list of missing required fields"""
        session = self.get_session(session_id)
        data = session.get('data', {})
        missing = []
        for field in required_fields:
            if not data.get(field, '').strip():
                missing.append(field)
        return missing
    
    def format_confirmation_data(self, session_id: str, action: str) -> str:
        """Format data for confirmation display"""
        session = self.get_session(session_id)
        data = session.get('data', {})
        
        if action == 'create_user':
            return f"""
**User Creation Summary:**
- Name: {data.get('first_name', '')} {data.get('last_name', '')}
- Email: {data.get('email', 'Not provided')}
- Phone: {data.get('phone', 'Not provided')}
- Level: {data.get('level', 'Not specified')}
- Department: {data.get('department', 'Not specified')}
- Role: {data.get('role', 'Not specified')}
- Property: {data.get('property', 'Not specified')}
- City: {data.get('city', 'Not specified')}
- State: {data.get('state', 'Not specified')}
- Country: {data.get('country', 'Not specified')}
""".strip()
        
        elif action == 'update_user':
            user_id = data.get('user_id', '')
            updates = data.get('updates', {})
            update_list = '\n'.join([f"- {k}: {v}" for k, v in updates.items() if v])
            return f"""
**User Update Summary (ID: {user_id}):**
{update_list}
""".strip()
        
        elif action == 'delete_user':
            return f"""
**User Deletion Summary:**
- User ID: {data.get('user_id', '')}
- Name: {data.get('user_name', '')}
⚠️ **WARNING: This action cannot be undone!**
""".strip()
        
        return "Confirmation data not available"

# Global session manager
session_manager = SessionManager()
