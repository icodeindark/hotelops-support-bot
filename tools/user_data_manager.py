import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# File paths for data persistence
USERS_DATA_FILE = os.path.join("context", "users_data.json")
SERVICES_DATA_FILE = os.path.join("context", "services_data.json")

class UserDataManager:
    def __init__(self):
        self.users = self.load_users_data()
        self.services = self.load_services_data()
        self.next_user_id = self._get_next_user_id()
        self.next_service_id = self._get_next_service_id()
    
    def load_users_data(self) -> Dict[str, Any]:
        """Load users from JSON file or create empty dict"""
        try:
            if os.path.exists(USERS_DATA_FILE):
                with open(USERS_DATA_FILE, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception:
            return {}
    
    def save_users_data(self):
        """Save users to JSON file"""
        try:
            os.makedirs(os.path.dirname(USERS_DATA_FILE), exist_ok=True)
            with open(USERS_DATA_FILE, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving users data: {e}")
    
    def load_services_data(self) -> Dict[str, Any]:
        """Load services from JSON file or create empty dict"""
        try:
            if os.path.exists(SERVICES_DATA_FILE):
                with open(SERVICES_DATA_FILE, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception:
            return {}
    
    def save_services_data(self):
        """Save services to JSON file"""
        try:
            os.makedirs(os.path.dirname(SERVICES_DATA_FILE), exist_ok=True)
            with open(SERVICES_DATA_FILE, 'w') as f:
                json.dump(self.services, f, indent=2)
        except Exception as e:
            print(f"Error saving services data: {e}")
    
    def _get_next_user_id(self) -> int:
        """Get next available user ID"""
        if not self.users:
            return 1
        existing_ids = [int(uid.replace('user_', '')) for uid in self.users.keys() if uid.startswith('user_')]
        return max(existing_ids, default=0) + 1
    
    def _get_next_service_id(self) -> int:
        """Get next available service ID"""
        if not self.services:
            return 1
        existing_ids = [int(sid.replace('service_', '')) for sid in self.services.keys() if sid.startswith('service_')]
        return max(existing_ids, default=0) + 1
    
    def user_exists_by_email_or_phone(self, email: str = None, phone: str = None) -> Optional[str]:
        """Check if user exists by email or phone, return user_id if found"""
        for user_id, user_data in self.users.items():
            if email and user_data.get('email', '').lower() == email.lower():
                return user_id
            if phone and user_data.get('phone', '') == phone:
                return user_id
        return None
    
    def find_user(self, identifier: str) -> Optional[tuple]:
        """Find user by email, phone, or user_id. Returns (user_id, user_data) or None"""
        # Direct user_id lookup
        if identifier in self.users:
            return identifier, self.users[identifier]
        
        # Search by email or phone
        for user_id, user_data in self.users.items():
            if (user_data.get('email', '').lower() == identifier.lower() or 
                user_data.get('phone', '') == identifier):
                return user_id, user_data
        
        return None
    
    def create_user_template(self) -> Dict[str, Any]:
        """Create empty user template with all possible fields"""
        return {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "level": "",
            "department": "",
            "role": "",
            "property": "",
            "personal_info": {
                "address1": "",
                "address2": "",
                "city": "",
                "state": "",
                "country": "",
                "language": ""
            },
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def validate_user_data(self, user_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate user data. Returns (is_valid, error_messages)"""
        errors = []
        
        # Required fields
        if not user_data.get('first_name', '').strip():
            errors.append("First Name is required")
        if not user_data.get('last_name', '').strip():
            errors.append("Last Name is required")
        
        # At least email or phone required
        email = user_data.get('email', '').strip()
        phone = user_data.get('phone', '').strip()
        if not email and not phone:
            errors.append("Either Email or Phone Number is required")
        
        # Check for duplicates (when creating new user)
        if email or phone:
            existing_user = self.user_exists_by_email_or_phone(email, phone)
            if existing_user:
                errors.append(f"User with this email/phone already exists (ID: {existing_user})")
        
        return len(errors) == 0, errors
    
    def add_user(self, user_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Add new user. Returns (success, message, user_id)"""
        is_valid, errors = self.validate_user_data(user_data)
        if not is_valid:
            return False, "; ".join(errors), None
        
        user_id = f"user_{self.next_user_id:03d}"
        user_template = self.create_user_template()
        
        # Update template with provided data
        for key, value in user_data.items():
            if key in user_template:
                user_template[key] = value
            elif key in user_template.get('personal_info', {}):
                user_template['personal_info'][key] = value
        
        self.users[user_id] = user_template
        self.next_user_id += 1
        self.save_users_data()
        
        return True, f"User {user_data.get('first_name', '')} {user_data.get('last_name', '')} successfully created", user_id
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> tuple[bool, str]:
        """Update existing user. Returns (success, message)"""
        if user_id not in self.users:
            return False, "User not found"
        
        user_data = self.users[user_id].copy()
        
        # Apply updates
        for key, value in updates.items():
            if key in user_data:
                user_data[key] = value
            elif key in user_data.get('personal_info', {}):
                user_data['personal_info'][key] = value
        
        user_data['last_updated'] = datetime.now().isoformat()
        
        # Validate updated data (skip duplicate check for existing user)
        temp_manager = UserDataManager()
        temp_manager.users = {k: v for k, v in self.users.items() if k != user_id}
        is_valid, errors = temp_manager.validate_user_data(user_data)
        
        if not is_valid:
            return False, "; ".join(errors)
        
        self.users[user_id] = user_data
        self.save_users_data()
        
        return True, f"User {user_data.get('first_name', '')} {user_data.get('last_name', '')} successfully updated"
    
    def delete_user(self, user_id: str) -> tuple[bool, str]:
        """Delete user. Returns (success, message)"""
        if user_id not in self.users:
            return False, "User not found"
        
        user_data = self.users[user_id]
        user_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
        
        del self.users[user_id]
        self.save_users_data()
        
        return True, f"User {user_name} (ID: {user_id}) has been permanently deleted"
    
    def block_unblock_user(self, user_id: str, action: str) -> tuple[bool, str]:
        """Block or unblock user. Returns (success, message)"""
        if user_id not in self.users:
            return False, "User not found"
        
        if action not in ['block', 'unblock']:
            return False, "Invalid action. Use 'block' or 'unblock'"
        
        new_status = 'blocked' if action == 'block' else 'active'
        self.users[user_id]['status'] = new_status
        self.users[user_id]['last_updated'] = datetime.now().isoformat()
        self.save_users_data()
        
        user_name = f"{self.users[user_id].get('first_name', '')} {self.users[user_id].get('last_name', '')}"
        return True, f"User {user_name} has been {action}ed successfully"
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users"""
        return self.users
    
    def get_user_summary(self, user_id: str) -> str:
        """Get formatted user summary"""
        if user_id not in self.users:
            return "User not found"
        
        user = self.users[user_id]
        return f"""
User ID: {user_id}
Name: {user.get('first_name', '')} {user.get('last_name', '')}
Email: {user.get('email', 'N/A')}
Phone: {user.get('phone', 'N/A')}
Role: {user.get('role', 'N/A')}
Department: {user.get('department', 'N/A')}
Level: {user.get('level', 'N/A')}
Property: {user.get('property', 'N/A')}
Status: {user.get('status', 'N/A')}
""".strip()

# Global instance
user_manager = UserDataManager()
