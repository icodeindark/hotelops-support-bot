from typing import Dict, Any, Optional, Tuple
from .user_data_manager import user_manager
from .session_manager import session_manager, ConversationState
from context.role_context import get_contextual_prompt
from logger_config import user_mgmt_logger, session_logger, log_user_mgmt, log_action, log_error

class InteractiveUserManager:
    """Handles interactive user management with multi-turn conversations"""
    
    def __init__(self):
        self.required_fields = ['first_name', 'last_name']
        self.optional_fields = ['level', 'department', 'role', 'property', 'address1', 'address2', 'city', 'state', 'country', 'language']
        
    def process_user_request(self, query: str, session_id: str = "default") -> str:
        """Main entry point for processing user management requests"""
        session = session_manager.get_session(session_id)
        current_state = session['state']
        
        # Handle ongoing conversations
        if current_state != ConversationState.IDLE:
            return self._handle_conversation_state(query, session_id)
        
        # Parse new requests
        query_lower = query.lower()
        
        # Check for user data patterns first (comma-separated data like "John Doe,email,phone,role")
        if self._looks_like_user_data(query):
            return self._start_user_creation(query, session_id)
        elif any(phrase in query_lower for phrase in ['add user', 'create user', 'new user', 'wanna add', 'want to add', 'add a user', 'create a user', 'add him', 'add her', 'add this', 'add to system', 'add contact']):
            return self._start_user_creation(query, session_id)
        elif any(phrase in query_lower for phrase in ['edit user', 'update user', 'modify user']):
            return self._start_user_editing(query, session_id)
        elif any(phrase in query_lower for phrase in ['delete user', 'remove user']):
            return self._start_user_deletion(query, session_id)
        elif any(phrase in query_lower for phrase in ['block user', 'unblock user']):
            return self._start_user_block_unblock(query, session_id)
        elif any(phrase in query_lower for phrase in ['reset password']):
            return self._start_password_reset(query, session_id)
        elif query.lower().strip() in ['reset', 'clear', 'start over', 'cancel']:
            session_manager.clear_session(session_id)
            return "Session cleared. How can I help you with user management?"
        else:
            return self._handle_general_user_query(query, session_id)
    
    def _handle_conversation_state(self, query: str, session_id: str) -> str:
        """Handle responses in ongoing conversations"""
        session = session_manager.get_session(session_id)
        state = session['state']
        
        if state == ConversationState.COLLECTING_USER_DATA:
            return self._collect_user_data(query, session_id)
        elif state == ConversationState.CONFIRMING_USER_CREATE:
            return self._confirm_user_creation(query, session_id)
        elif state == ConversationState.COLLECTING_USER_UPDATES:
            return self._collect_user_updates(query, session_id)
        elif state == ConversationState.CONFIRMING_USER_UPDATE:
            return self._confirm_user_update(query, session_id)
        elif state == ConversationState.CONFIRMING_USER_DELETE:
            return self._confirm_user_deletion(query, session_id)
        elif state == ConversationState.CONFIRMING_USER_BLOCK:
            return self._confirm_user_block_unblock(query, session_id)
        else:
            session_manager.clear_session(session_id)
            return "I'm sorry, something went wrong. Let's start over. How can I help you?"
    
    def _start_user_creation(self, query: str, session_id: str) -> str:
        """Start the user creation process"""
        # Clear any existing session first for fresh start
        session_manager.clear_session(session_id)
        
        # Always try to extract data, but be smart about it
        extracted_data = self._extract_user_info_from_query(query)
        
        session_manager.set_state(session_id, ConversationState.COLLECTING_USER_DATA, {
            'action': 'create_user',
            **extracted_data
        })
        
        return self._request_missing_user_info(session_id)
    
    def _looks_like_user_data(self, query: str) -> bool:
        """Check if query looks like structured user data"""
        # Check for comma-separated data with email pattern
        if "," in query and "@" in query:
            return True
        
        # Check for structured patterns like "Name, email, phone, role"
        parts = query.split(",")
        if len(parts) >= 3:
            # Look for email or phone patterns
            for part in parts:
                part = part.strip()
                if "@" in part or (part.replace("+", "").replace("-", "").replace("(", "").replace(")", "").replace(" ", "").isdigit() and len(part) >= 10):
                    return True
        
        return False
    
    def _extract_user_info_from_query(self, query: str) -> Dict[str, str]:
        """Extract user information from natural language query"""
        data = {}
        query_lower = query.lower()
        
        import re
        
        # Don't extract from casual requests
        casual_phrases = ['i wanna', 'i want to', 'i would like', 'can you', 'please', 'help me']
        if any(phrase in query_lower for phrase in casual_phrases) and 'add' in query_lower:
            return data  # Return empty data for casual requests
        
        # Handle comma-separated data first (like "John Doe,john@mail.com,8374928338,manager-housekeeping")
        if "," in query:
            parts = [part.strip() for part in query.split(",")]
            
            for i, part in enumerate(parts):
                # First part is usually the name
                if i == 0 and " " in part:
                    name_parts = part.split()
                    if len(name_parts) >= 2:
                        data['first_name'] = name_parts[0]
                        data['last_name'] = ' '.join(name_parts[1:])
                
                # Look for email
                elif "@" in part:
                    data['email'] = part
                
                # Look for phone (numbers with 10+ digits)
                elif re.match(r'^[+]?[0-9\s\-\(\)]{10,}$', part):
                    data['phone'] = part
                
                # Look for department/role patterns
                elif any(dept in part.lower() for dept in ['housekeeping', 'front', 'maintenance', 'admin', 'manager', 'staff', 'supervisor']):
                    if 'manager' in part.lower():
                        data['role'] = 'Manager'
                        if 'housekeeping' in part.lower():
                            data['department'] = 'Housekeeping'
                        elif 'front' in part.lower():
                            data['department'] = 'Front Desk'
                        elif 'maintenance' in part.lower():
                            data['department'] = 'Maintenance'
                    elif 'staff' in part.lower():
                        data['role'] = 'Staff'
                        if 'housekeeping' in part.lower():
                            data['department'] = 'Housekeeping'
                    elif 'supervisor' in part.lower():
                        data['role'] = 'Supervisor'
                    else:
                        # Try to extract department
                        if 'housekeeping' in part.lower():
                            data['department'] = 'Housekeeping'
                        elif 'front' in part.lower():
                            data['department'] = 'Front Desk'
                        elif 'maintenance' in part.lower():
                            data['department'] = 'Maintenance'
        
        else:
            # Handle non-comma separated data
            # ONLY extract names if there are clear indicators this is structured data
            # Avoid extracting from casual conversation like "i wanna add a user to the system"
            
            # Only look for names if query contains explicit structured indicators
            has_structured_data = any(indicator in query_lower for indicator in [
                'name:', 'email:', 'phone:', 'department:', 'role:', '@', 
                'first name', 'last name', 'called', 'named'
            ])
            
            if has_structured_data:
                # Look for explicit name patterns like "name John Smith" or "first name John"
                name_pattern1 = re.search(r'(?:name|called|named)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)', query, re.IGNORECASE)
                name_pattern2 = re.search(r'first\s*name\s*:?\s*([A-Z][a-z]+)', query, re.IGNORECASE)
                name_pattern3 = re.search(r'last\s*name\s*:?\s*([A-Z][a-z]+)', query, re.IGNORECASE)
                
                if name_pattern1:
                    data['first_name'] = name_pattern1.group(1)
                    data['last_name'] = name_pattern1.group(2)
                else:
                    if name_pattern2:
                        data['first_name'] = name_pattern2.group(1)
                    if name_pattern3:
                        data['last_name'] = name_pattern3.group(1)
            
            # Email pattern
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', query)
            if email_match:
                data['email'] = email_match.group(1)
            
            # Phone pattern  
            phone_match = re.search(r'(?:phone|mobile|contact)\s*:?\s*([+]?[0-9\s\-\(\)]{10,})', query, re.IGNORECASE)
            if phone_match:
                data['phone'] = phone_match.group(1).strip()
            
            # Department pattern
            dept_match = re.search(r'department\s*:?\s*([A-Za-z\s]+?)(?:\s*[,.]|$)', query, re.IGNORECASE)
            if dept_match:
                data['department'] = dept_match.group(1).strip()
            
            # Role pattern
            role_match = re.search(r'role\s*:?\s*([A-Za-z\s]+?)(?:\s*[,.]|$)', query, re.IGNORECASE)
            if role_match:
                data['role'] = role_match.group(1).strip()
        
        return data
    
    def _request_missing_user_info(self, session_id: str) -> str:
        """Request missing information for user creation"""
        session = session_manager.get_session(session_id)
        data = session['data']
        
        # Check what's missing
        missing_required = []
        for field in self.required_fields:
            if not data.get(field, '').strip():
                missing_required.append(field)
        
        # Check email/phone requirement
        if not data.get('email', '').strip() and not data.get('phone', '').strip():
            missing_required.append('email_or_phone')
        
        if missing_required:
            missing_display = {
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'email_or_phone': 'Email OR Phone Number'
            }
            
            missing_list = [missing_display.get(field, field) for field in missing_required]
            
            current_info = ""
            if any(data.get(field) for field in ['first_name', 'last_name', 'email', 'phone', 'department', 'role']):
                current_info = "\n**Information I have so far:**\n"
                for field, value in data.items():
                    if value and field != 'action':
                        display_name = field.replace('_', ' ').title()
                        current_info += f"- {display_name}: {value}\n"
            
            return f"""I'm helping you create a new user account. {current_info}

**Still needed (Required):**
{chr(10).join(f'- {item}' for item in missing_list)}

**Optional Information:** Level, Department, Role, Property, Address, City, State, Country, Language

Please provide the missing required information, or say 'cancel' to stop."""
        
        else:
            # All required info collected, show summary and ask for confirmation
            session_manager.set_state(session_id, ConversationState.CONFIRMING_USER_CREATE)
            summary = session_manager.format_confirmation_data(session_id, 'create_user')
            
            return f"""{summary}

**Please confirm:** Type 'yes' to create this user, 'no' to cancel, or provide additional information to update the details."""
    
    def _collect_user_data(self, query: str, session_id: str) -> str:
        """Collect user data from user response"""
        if query.lower().strip() == 'cancel':
            session_manager.clear_session(session_id)
            return "User creation cancelled."
        
        # Extract new information from the response
        new_data = self._extract_user_info_from_query(query)
        
        # Manual field extraction for common patterns
        query_lower = query.lower()
        lines = query.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                field_mapping = {
                    'first_name': 'first_name', 'firstname': 'first_name', 'fname': 'first_name',
                    'last_name': 'last_name', 'lastname': 'last_name', 'lname': 'last_name',
                    'email': 'email', 'email_address': 'email',
                    'phone': 'phone', 'phone_number': 'phone', 'mobile': 'phone',
                    'level': 'level', 'privilege_level': 'level',
                    'department': 'department', 'dept': 'department',
                    'role': 'role', 'position': 'role',
                    'property': 'property', 'hotel': 'property',
                    'address': 'address1', 'address1': 'address1',
                    'city': 'city', 'state': 'state', 'country': 'country',
                    'language': 'language', 'lang': 'language'
                }
                
                if key in field_mapping and value:
                    new_data[field_mapping[key]] = value
        
        # Handle simple single-field responses (like "John" when asking for first name)
        if not new_data and query.strip() and not any(char in query for char in [':', '@', ',']):
            session = session_manager.get_session(session_id)
            missing_fields = session_manager.get_missing_fields(session_id, ['first_name', 'last_name', 'email', 'phone'])
            
            # If we're missing first_name and this looks like a name
            if 'first_name' in missing_fields and query.strip().replace(' ', '').isalpha():
                new_data['first_name'] = query.strip().title()
            # If we have first_name but missing last_name and this looks like a name
            elif 'last_name' in missing_fields and 'first_name' not in missing_fields and query.strip().replace(' ', '').isalpha():
                new_data['last_name'] = query.strip().title()
            # If we're missing email and this looks like an email
            elif ('email' in missing_fields or 'phone' in missing_fields) and '@' in query:
                new_data['email'] = query.strip()
        
        # Update session data
        session_manager.update_session_data(session_id, new_data)
        
        # Provide feedback about what was captured
        feedback = ""
        if new_data:
            captured = []
            for key, value in new_data.items():
                display_name = key.replace('_', ' ').title()
                captured.append(f"{display_name}: {value}")
            feedback = f"✓ Captured: {', '.join(captured)}\n\n"
        
        return feedback + self._request_missing_user_info(session_id)
    
    def _confirm_user_creation(self, query: str, session_id: str) -> str:
        """Handle user creation confirmation"""
        response = query.lower().strip()
        
        if response in ['yes', 'y', 'confirm', 'create', 'proceed']:
            session = session_manager.get_session(session_id)
            user_data = {k: v for k, v in session['data'].items() if k != 'action'}
            
            # Attempt to create user
            success, message, user_id = user_manager.add_user(user_data)
            
            session_manager.clear_session(session_id)
            
            if success:
                return f"✅ **Success!** {message}\n**User ID:** {user_id}\n\nThe user can now be invited via WhatsApp, SMS, or Email from the User Management dashboard."
            else:
                return f"❌ **Error:** {message}\n\nPlease try again with corrected information."
        
        elif response in ['no', 'n', 'cancel', 'stop']:
            session_manager.clear_session(session_id)
            return "User creation cancelled."
        
        else:
            # User wants to modify something
            new_data = self._extract_user_info_from_query(query)
            if new_data:
                session = session_manager.get_session(session_id)
                session['data'].update(new_data)
                session_manager.set_state(session_id, ConversationState.COLLECTING_USER_DATA)
                return self._request_missing_user_info(session_id)
            else:
                return "Please type 'yes' to confirm creation, 'no' to cancel, or provide the information you'd like to change."
    
    def _start_user_editing(self, query: str, session_id: str) -> str:
        """Start user editing process"""
        # Try to extract user identifier from query
        user_id, user_data = self._find_user_from_query(query)
        
        if user_id:
            session_manager.set_state(session_id, ConversationState.COLLECTING_USER_UPDATES, {
                'action': 'update_user',
                'user_id': user_id,
                'user_name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
                'updates': {}
            })
            
            current_info = user_manager.get_user_summary(user_id)
            return f"""**Current User Information:**
{current_info}

**What would you like to update?** You can change:
- Name (first_name, last_name)
- Contact (email, phone)
- Role and Department
- Property assignment
- Personal information (address, city, state, country, language)

Please specify what you want to change, or say 'cancel' to stop.

*Example: "Change role to Manager and department to Housekeeping"*"""
        
        else:
            return """I need to identify which user to edit. Please provide:
- User ID (e.g., user_001)
- Email address
- Phone number
- Full name

*Example: "Edit user john@hotel.com" or "Edit user_001"*"""
    
    def _find_user_from_query(self, query: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Find user from query text"""
        # Extract email pattern
        import re
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', query)
        if email_match:
            result = user_manager.find_user(email_match.group(1))
            if result:
                return result
        
        # Extract user_id pattern
        user_id_match = re.search(r'user_(\d+)', query, re.IGNORECASE)
        if user_id_match:
            user_id = f"user_{user_id_match.group(1)}"
            result = user_manager.find_user(user_id)
            if result:
                return result
        
        # Extract phone pattern
        phone_match = re.search(r'([+]?[0-9\s\-\(\)]{10,})', query)
        if phone_match:
            result = user_manager.find_user(phone_match.group(1).strip())
            if result:
                return result
        
        return None, None
    
    def _handle_general_user_query(self, query: str, session_id: str) -> str:
        """Handle general user management queries"""
        query_lower = query.lower()
        
        if any(phrase in query_lower for phrase in ['list users', 'show users', 'all users']):
            users = user_manager.get_all_users()
            if not users:
                return "No users found in the system. Would you like to create a new user?"
            
            user_list = "**Current Users:**\n\n"
            for user_id, user_data in users.items():
                status_icon = "🟢" if user_data.get('status') == 'active' else "🔴"
                user_list += f"{status_icon} **{user_id}**: {user_data.get('first_name', '')} {user_data.get('last_name', '')} - {user_data.get('email', 'N/A')} - {user_data.get('role', 'N/A')}\n"
            
            return user_list + "\n*Type 'edit user [identifier]' to modify, or 'delete user [identifier]' to remove.*"
        
        else:
            context = """The user has a general user management query that doesn't match specific CRUD operations.

Provide helpful guidance about available user management functions:
- Creating users (add user, create user, new user)
- Editing users (edit user, update user, modify user)
- Deleting users (delete user, remove user)
- Blocking/unblocking users
- Listing users (list users, show users)
- Password reset (Company Admin only)

Be professional and guide them to the appropriate action."""
            
            prompt = get_contextual_prompt(query, context)
            
            from llm_utils import ask_gemini
            return ask_gemini(prompt)

# Global instance
interactive_user_manager = InteractiveUserManager()
