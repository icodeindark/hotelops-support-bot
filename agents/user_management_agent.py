"""
HotelOpsAI User Management Agent - Complete User Operations
Senior AI Engineer Implementation

Handles all user-related operations with interactive workflows:
- User creation with validation
- User updates and modifications
- User deletion with confirmations
- User search and listing
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

from .state_schema import (
    ChatState, IntentType, ConversationState, UserOperationData,
    transition_conversation_state, add_message_to_state, 
    update_state_timestamp, log_error_to_state
)
from .data_extraction_agent import data_extraction_agent
from .llm_response_generator import llm_response_generator
from database.memory_db import db_adapter
from logger_config import agent_logger, log_action, log_error, log_user_mgmt
from llm_utils import ask_gemini

class UserManagementAgent:
    """
    Specialized agent for user management operations
    with comprehensive workflows and validation
    """
    
    def __init__(self):
        self.required_fields = {
            "create": ["first_name", "last_name", "email"],
            "update": ["user_id"],  # Need to identify user first
            "delete": ["user_id"]
        }
        
        self.optional_fields = [
            "phone", "role", "department", "property", "status"
        ]
        
        # Performance tracking
        self.operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operation_types": {}
        }
        
        agent_logger.info("User Management Agent initialized")
    
    def process_user_request(self, state: ChatState, message: str) -> ChatState:
        """
        Main entry point for user management requests
        
        Routes to appropriate sub-workflow based on intent and conversation state
        """
        
        intent_str = state.get("current_intent")
        conversation_state = state.get("conversation_state")
        
        # Convert string intent to enum
        intent = None
        if intent_str:
            for intent_enum in IntentType:
                if intent_enum.value == intent_str:
                    intent = intent_enum
                    break
        
        log_action("USER_MGMT_REQUEST", 
                  f"Intent: {intent_str}, "
                  f"State: {conversation_state}, "
                  f"Message: {message[:100]}",
                  session_id=state["session_id"])
        
        try:
            # First, check if we're in an ongoing conversation state
            if conversation_state == ConversationState.CONFIRMATION_PENDING.value:
                # Handle confirmation responses regardless of intent
                return self._handle_confirmation_response(state, message)
            elif conversation_state == ConversationState.DATA_COLLECTION.value:
                # Handle data collection regardless of intent
                return self._handle_data_collection_response(state, message)
            elif conversation_state == ConversationState.COLLECTING_USER_DATA.value:
                # Handle natural data collection regardless of intent
                return self._handle_natural_data_collection(state, message)
            
            # Route based on intent for new operations
            elif intent == IntentType.USER_CREATE:
                return self._handle_user_creation_natural(state, message)
            elif intent == IntentType.USER_UPDATE:
                return self._handle_user_update(state, message)
            elif intent == IntentType.USER_DELETE:
                return self._handle_user_deletion(state, message)
            elif intent == IntentType.USER_LIST:
                return self._handle_user_listing(state, message)
            elif intent == IntentType.USER_SEARCH:
                return self._handle_user_search(state, message)
            else:
                # Handle ongoing conversations based on state or fallback
                return self._handle_conversation_state(state, message)
                
        except Exception as e:
            error_msg = f"User management processing failed: {str(e)}"
            log_error("USER_MGMT_ERROR", error_msg, session_id=state["session_id"])
            
            self.operation_stats["failed_operations"] += 1
            
            return log_error_to_state(
                state, error_msg, "user_management_error",
                agent_id="user_management", recoverable=True
            )
    
    def _handle_user_creation(self, state: ChatState, message: str) -> ChatState:
        """Handle user creation workflow"""
        
        conversation_state = state.get("conversation_state")
        
        # Debug logging
        log_action("DEBUG_USER_CREATE", 
                  f"conversation_state='{conversation_state}' (type: {type(conversation_state)}), "
                  f"DATA_COLLECTION.value='{ConversationState.DATA_COLLECTION.value}', "
                  f"comparison: {conversation_state == ConversationState.DATA_COLLECTION.value}",
                  session_id=state["session_id"])
        
        if conversation_state == ConversationState.DATA_COLLECTION.value:
            return self._collect_user_data(state, message)
        elif conversation_state == ConversationState.CONFIRMATION_PENDING.value:
            return self._confirm_user_creation(state, message)
        else:
            # Start new user creation workflow
            return self._start_user_creation(state, message)
    
    def _start_user_creation(self, state: ChatState, message: str) -> ChatState:
        """Initialize user creation workflow"""
        
        log_action("USER_CREATE_START", "Starting user creation workflow", 
                  session_id=state["session_id"])
        
        # Initialize user operation data if not exists
        if not state.get("user_operation"):
            state["user_operation"] = UserOperationData(
                operation_type="create",
                user_id=None,
                first_name=None,
                last_name=None,
                email=None,
                phone=None,
                role=None,
                department=None,
                property=None,
                status="active",
                required_fields=self.required_fields["create"],
                collected_fields=[],
                missing_fields=self.required_fields["create"]
            )
        
        # Extract data from initial message
        updated_state = data_extraction_agent.extract_entities(
            message, "user_create", state
        )
        
        # Get the user operation data (it might have been updated by data extraction agent)
        user_op = updated_state["user_operation"]
        
        log_action("EXTRACTED_ENTITIES", f"Found {len(updated_state.get('extracted_entities', []))} entities", 
                  session_id=state["session_id"])
        
        # The data extraction agent should have already populated user_operation
        # Let's manually ensure the data gets copied from extracted_entities to user_operation
        collected_data = {}
        
        # Get data from extracted entities
        for entity in updated_state.get("extracted_entities", []):
            if entity.get("is_valid", False):
                field_name = entity["entity_type"]
                log_action("ENTITY_FOUND", f"Found {field_name}: {entity['value']}", 
                          session_id=state["session_id"])
                
                if field_name in ["first_name", "last_name", "email", "phone", "role", "department"]:
                    collected_data[field_name] = entity["value"]
                    if field_name not in user_op.get("collected_fields", []):
                        user_op["collected_fields"].append(field_name)
        
        # Handle full name extraction
        full_name_entities = [e for e in updated_state.get("extracted_entities", []) if e["entity_type"] == "full_name"]
        if full_name_entities:
            full_name_entity = full_name_entities[0]
            if full_name_entity.get("is_valid", False):
                name_parts = full_name_entity["value"].split()
                if len(name_parts) >= 2:
                    collected_data["first_name"] = name_parts[0]
                    collected_data["last_name"] = " ".join(name_parts[1:])
                    for field in ["first_name", "last_name"]:
                        if field not in user_op.get("collected_fields", []):
                            user_op["collected_fields"].append(field)
        
        # Update user operation with collected data
        for field, value in collected_data.items():
            user_op[field] = value
            
        log_action("DATA_APPLIED", f"Applied data to user_op: {collected_data}", 
                  session_id=state["session_id"])
        
        # Update missing fields
        user_op["missing_fields"] = [
            field for field in user_op["required_fields"] 
            if field not in user_op["collected_fields"] or not user_op.get(field)
        ]
        
        # Validate collected data
        validation_errors = self._validate_user_data(collected_data)
        if validation_errors:
            updated_state["validation_errors"] = validation_errors
            
            error_msg = "Data validation failed: " + "; ".join(validation_errors)
            updated_state = add_message_to_state(
                updated_state, error_msg, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.DATA_COLLECTION,
                reason="Validation errors need to be resolved"
            )
        
        # Check if we have all required data
        if not user_op["missing_fields"]:
            # We have all required data, move to confirmation
            confirmation_message = llm_response_generator.generate_confirmation_response(user_op, updated_state)
            
            updated_state = add_message_to_state(
                updated_state, confirmation_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.CONFIRMATION_PENDING,
                reason="All required data collected, awaiting confirmation"
            )
        else:
            # Request missing data
            request_message = self._generate_data_request_message(user_op["missing_fields"])
            
            updated_state = add_message_to_state(
                updated_state, request_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.DATA_COLLECTION,
                reason="Missing required fields"
            )
    
    def _collect_user_data(self, state: ChatState, message: str) -> ChatState:
        """Collect missing user data - DEPRECATED: Use _handle_data_collection_response instead"""
        
        log_action("DEPRECATED_COLLECT_USER_DATA", f"Using deprecated method, redirecting to new handler", 
                  session_id=state["session_id"])
        
        # Redirect to the new proper handler
        return self._handle_data_collection_response(state, message)
    
    def _confirm_user_creation(self, state: ChatState, message: str) -> ChatState:
        """Handle user creation confirmation"""
        
        message_lower = message.lower().strip()
        
        if message_lower in ["yes", "y", "confirm", "create", "ok", "proceed"]:
            # Proceed with user creation
            return self._execute_user_creation(state)
        elif message_lower in ["no", "n", "cancel", "abort", "stop"]:
            # Cancel user creation
            updated_state = add_message_to_state(
                state, "User creation cancelled. How can I help you?", "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User cancelled creation"
            )
        else:
            # Ask for clarification
            clarification_message = (
                "Please confirm if you want to create this user account:\n"
                "- Type 'yes' to create the user\n"
                "- Type 'no' to cancel"
            )
            
            updated_state = add_message_to_state(
                state, clarification_message, "assistant",
                agent_id="user_management"
            )
            
            return updated_state
    
    def _execute_user_creation(self, state: ChatState) -> ChatState:
        """Execute the actual user creation"""
        
        log_action("USER_CREATE_EXECUTE", "Starting user creation execution", 
                  session_id=state["session_id"])
        
        user_op = state.get("user_operation")
        if not user_op:
            error_message = "❌ **Error**: No user data found for creation."
            updated_state = add_message_to_state(
                state, error_message, "assistant", agent_id="user_management"
            )
            return transition_conversation_state(
                updated_state, ConversationState.IDLE, reason="No user data"
            )
        
        log_action("USER_CREATE_USERDATA", f"User operation data: {user_op}", 
                  session_id=state["session_id"])
        
        try:
            # Check if we have required data first
            first_name = user_op.get("first_name")
            last_name = user_op.get("last_name")
            email = user_op.get("email")
            
            log_action("USER_CREATE_FIELDS", f"Fields - First: {first_name}, Last: {last_name}, Email: {email}", 
                      session_id=state["session_id"])
            
            if not first_name or not last_name or not email:
                error_message = (
                    "❌ **Cannot create user**: Missing required information.\n\n"
                    f"Current data:\n"
                    f"• First Name: {first_name or 'Missing'}\n"
                    f"• Last Name: {last_name or 'Missing'}\n"
                    f"• Email: {email or 'Missing'}\n\n"
                    "Please provide complete information like: `John, Doe, john@email.com`"
                )
                
                log_action("USER_CREATE_MISSING", f"Missing fields detected", 
                          session_id=state["session_id"])
                
                updated_state = add_message_to_state(
                    state, error_message, "assistant",
                    agent_id="user_management"
                )
                
                return transition_conversation_state(
                    updated_state, ConversationState.IDLE,
                    reason="Missing required user data"
                )
            
            # Prepare user data for database
            user_data = {
                "first_name": user_op["first_name"],
                "last_name": user_op["last_name"],
                "email": user_op["email"],
                "phone": user_op.get("phone"),
                "role": user_op.get("role", "staff"),
                "department": user_op.get("department", "general"),
                "property": user_op.get("property"),
                "status": "active"
            }
            
            log_action("USER_CREATE_DATA", f"Prepared user data: {user_data}", 
                      session_id=state["session_id"])
            
            # Create user in database (includes duplicate check)
            log_action("USER_CREATE_DB", "Creating user in database", 
                      session_id=state["session_id"])
            
            try:
                created_user = db_adapter.create_user(user_data)
            except ValueError as e:
                # Handle duplicate email error
                error_message = f"❌ **Error**: {str(e)}"
                updated_state = add_message_to_state(
                    state, error_message, "assistant",
                    agent_id="user_management"
                )
                return transition_conversation_state(
                    updated_state, ConversationState.IDLE,
                    reason="Duplicate email error"
                )
            
            log_action("USER_CREATE_SUCCESS", f"User created with ID: {created_user.get('user_id', 'unknown')}", 
                      session_id=state["session_id"])
            
            # Log the creation
            log_user_mgmt("CREATE_USER", user_data, session_id=state["session_id"])
            
            # Generate natural success message using LLM
            action_result = {
                "success": True,
                "user_id": created_user['user_id'],
                "user_data": created_user
            }
            success_message = llm_response_generator.generate_success_response(
                action="user creation",
                result=action_result,
                state=state
            )
            
            updated_state = add_message_to_state(
                state, success_message, "assistant",
                agent_id="user_management"
            )
            
            # Clear user operation data
            updated_state["user_operation"] = None
            
            self.operation_stats["total_operations"] += 1
            self.operation_stats["successful_operations"] += 1
            self.operation_stats["operation_types"]["create"] = \
                self.operation_stats["operation_types"].get("create", 0) + 1
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User creation completed successfully"
            )
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to create user: {str(e)}"
            full_traceback = traceback.format_exc()
            
            log_error("USER_CREATE_ERROR", error_msg, session_id=state["session_id"])
            log_action("USER_CREATE_TRACEBACK", f"Full error: {full_traceback}", 
                      session_id=state["session_id"])
            
            error_message = f"❌ **Error**: Failed to create user account. {error_msg}"
            
            updated_state = add_message_to_state(
                state, error_message, "assistant",
                agent_id="user_management"
            )
            
            self.operation_stats["failed_operations"] += 1
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User creation failed"
            )
    
    def _handle_user_listing(self, state: ChatState, message: str) -> ChatState:
        """Handle user listing requests"""
        
        try:
            # Get users from database
            users = db_adapter.list_users(limit=50)
            
            if not users:
                response_message = "No users found in the system."
            else:
                # Format user list
                response_parts = [f"📋 **User List** ({len(users)} users):\n"]
                
                for i, user in enumerate(users, 1):
                    status_emoji = "✅" if user.get("status") == "active" else "❌"
                    response_parts.append(
                        f"{i}. {status_emoji} **{user['first_name']} {user['last_name']}**\n"
                        f"   • Email: {user['email']}\n"
                        f"   • Role: {user.get('role', 'N/A')}\n"
                        f"   • Department: {user.get('department', 'N/A')}\n"
                        f"   • ID: {user['user_id']}\n"
                    )
                
                response_message = "\n".join(response_parts)
            
            updated_state = add_message_to_state(
                state, response_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User listing completed"
            )
            
        except Exception as e:
            error_msg = f"Failed to list users: {str(e)}"
            log_error("USER_LIST_ERROR", error_msg, session_id=state["session_id"])
            
            error_message = f"❌ **Error**: Failed to retrieve user list. {error_msg}"
            
            updated_state = add_message_to_state(
                state, error_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User listing failed"
            )
    
    def _handle_user_search(self, state: ChatState, message: str) -> ChatState:
        """Handle user search requests"""
        
        # Extract search query from message
        search_query = message.replace("search", "").replace("find", "").replace("user", "").strip()
        
        if not search_query:
            request_message = "What would you like to search for? Please provide a name, email, or role."
            
            updated_state = add_message_to_state(
                state, request_message, "assistant",
                agent_id="user_management"
            )
            
            return updated_state
        
        try:
            # Search users in database
            users = db_adapter.search_users(search_query, limit=20)
            
            if not users:
                response_message = f"No users found matching '{search_query}'."
            else:
                response_parts = [f"🔍 **Search Results for '{search_query}'** ({len(users)} found):\n"]
                
                for i, user in enumerate(users, 1):
                    status_emoji = "✅" if user.get("status") == "active" else "❌"
                    response_parts.append(
                        f"{i}. {status_emoji} **{user['first_name']} {user['last_name']}**\n"
                        f"   • Email: {user['email']}\n"
                        f"   • Role: {user.get('role', 'N/A')}\n"
                        f"   • Department: {user.get('department', 'N/A')}\n"
                        f"   • ID: {user['user_id']}\n"
                    )
                
                response_message = "\n".join(response_parts)
            
            updated_state = add_message_to_state(
                state, response_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User search completed"
            )
            
        except Exception as e:
            error_msg = f"Failed to search users: {str(e)}"
            log_error("USER_SEARCH_ERROR", error_msg, session_id=state["session_id"])
            
            error_message = f"❌ **Error**: Failed to search users. {error_msg}"
            
            updated_state = add_message_to_state(
                state, error_message, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User search failed"
            )
    
    def _handle_confirmation_response(self, state: ChatState, message: str) -> ChatState:
        """Handle user confirmation responses (yes/no)"""
        
        log_action("CONFIRMATION_RESPONSE", f"Handling confirmation: '{message}'", 
                  session_id=state["session_id"])
        
        response_lower = message.lower().strip()
        
        # Check if this looks like new user data instead of confirmation
        if self._looks_like_user_data(message):
            log_action("CONFIRMATION_NEW_DATA", f"Detected new user data in confirmation: {message[:50]}...", 
                      session_id=state["session_id"])
            
            # Extract data from the new message
            updated_state = data_extraction_agent.extract_entities(
                message, "user_create", state
            )
            
            # Update the user operation with newly extracted data
            return self._update_user_operation_from_entities(updated_state, message)
        
        # Handle positive confirmations
        elif any(word in response_lower for word in ['yes', 'y', 'confirm', 'create', 'proceed', 'ok', 'okay']):
            # Before executing, check if we actually have valid data
            user_op = state.get("user_operation", {})
            if not user_op or not user_op.get("first_name") or not user_op.get("last_name") or not user_op.get("email"):
                # Missing required data - should not be in confirmation state
                log_action("CONFIRMATION_INVALID", "User confirmed but missing required data", 
                          session_id=state["session_id"])
                
                missing_fields = []
                if not user_op.get("first_name"):
                    missing_fields.append("First Name")
                if not user_op.get("last_name"):
                    missing_fields.append("Last Name")
                if not user_op.get("email"):
                    missing_fields.append("Email")
                
                response = (
                    f"I need the following information first:\n"
                    + "\n".join([f"• **{field}**" for field in missing_fields]) +
                    f"\n\nCould you please provide them? For example: *\"John Smith, john@email.com\"*"
                )
                
                updated_state = add_message_to_state(
                    state, response, "assistant",
                    agent_id="user_management"
                )
                
                return transition_conversation_state(
                    updated_state, ConversationState.DATA_COLLECTION,
                    reason="Missing required data, back to collection"
                )
            
            # Execute user creation only if we have valid data
            return self._execute_user_creation(state)
        
        # Handle negative confirmations  
        elif any(word in response_lower for word in ['no', 'n', 'cancel', 'stop', 'abort']):
            updated_state = add_message_to_state(
                state, "User creation cancelled. How can I help you?", "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User cancelled operation"
            )
        
        # If unclear, ask for clarification
        else:
            clarification_msg = (
                "Please confirm if you want to create this user:\n"
                "• Type 'yes' to create the user\n"
                "• Type 'no' to cancel"
            )
            
            updated_state = add_message_to_state(
                state, clarification_msg, "assistant",
                agent_id="user_management"
            )
            
            # Stay in confirmation pending state
            return state
    
    def _looks_like_user_data(self, message: str) -> bool:
        """Check if message contains any user data"""
        
        # Specific patterns for user data - avoid false positives
        patterns = [
            r'name\s*[:=]\s*\w+',  # name: John
            r'email\s*[:=]\s*\S+@\S+',  # email: john@mail.com
            r'phone\s*[:=]\s*[\d\s\-\(\)]+',  # phone: 123-456-7890
            r'\S+@\S+\.\S+',  # email pattern
            r'[\d\s\-\(\)]{10,}',  # phone pattern (10+ digits)
            r'role\s*[:=]\s*\w+',  # role: manager
            r'department\s*[:=]\s*\w+',  # department: FO
            r'first\s*name\s*[:=]\s*\w+',  # first name: John
            r'last\s*name\s*[:=]\s*\w+',  # last name: Doe
        ]
        
        message_lower = message.lower()
        
        # Check for any pattern - be more liberal
        for pattern in patterns:
            if re.search(pattern, message_lower):
                log_action("USER_DATA_DETECTED", f"Pattern matched: {pattern} in '{message}'", 
                          session_id="unknown")
                return True
        
        # Check for basic comma-separated values that could be names/emails
        # But exclude common command patterns
        if ',' in message and len(message.split(',')) >= 2:
            # Exclude messages that are clearly commands
            command_words = {'create', 'add', 'make', 'new', 'please', 'can', 'could', 'want', 'need', 'help'}
            if any(word in message_lower for word in command_words):
                return False
                
            parts = [part.strip() for part in message.split(',')]
            # If any part looks like an email or valid name, consider it user data
            for part in parts:
                if '@' in part and '.' in part:  # More specific email check
                    log_action("USER_DATA_DETECTED", f"Email detected in comma-separated data: '{message}'", 
                              session_id="unknown")
                    return True
                elif (len(part.split()) <= 2 and part.replace(' ', '').isalpha() and 
                      len(part.strip()) >= 2 and part.lower() not in command_words):
                    log_action("USER_DATA_DETECTED", f"Name detected in comma-separated data: '{message}'", 
                              session_id="unknown")
                    return True
        
        return False
    
    def _update_user_operation_from_entities(self, state: ChatState, original_message: str) -> ChatState:
        """Update user operation from extracted entities and show confirmation"""
        
        log_action("UPDATE_USER_OP", f"Updating user_operation from entities for message: '{original_message}'", 
                  session_id=state["session_id"])
        
        # Get or initialize user_operation
        user_op = state.get("user_operation", {})
        if not user_op:
            user_op = {
                "operation_type": "create",
                "user_id": None,
                "first_name": None,
                "last_name": None,
                "email": None,
                "phone": None,
                "role": None,
                "department": None,
                "property": None,
                "status": "active",
                "required_fields": ["first_name", "last_name", "email"],
                "collected_fields": [],
                "missing_fields": ["first_name", "last_name", "email"]
            }
        
        # Apply extracted entities to user_operation
        for entity in state.get("extracted_entities", []):
            if entity.get("is_valid", False):
                field_name = entity["entity_type"]
                log_action("UPDATE_ENTITY", f"Processing entity {field_name}: {entity['value']}", 
                          session_id=state["session_id"])
                
                if field_name == "full_name":
                    name_parts = entity["value"].split()
                    if len(name_parts) >= 2:
                        user_op["first_name"] = name_parts[0]
                        user_op["last_name"] = " ".join(name_parts[1:])
                        for field in ["first_name", "last_name"]:
                            if field not in user_op.get("collected_fields", []):
                                user_op["collected_fields"].append(field)
                elif field_name in ["first_name", "last_name", "email", "phone", "role", "department"]:
                    user_op[field_name] = entity["value"]
                    if field_name not in user_op.get("collected_fields", []):
                        user_op["collected_fields"].append(field_name)
        
        # Update missing fields
        required_fields = ["first_name", "last_name", "email"]
        missing_fields = [field for field in required_fields if not user_op.get(field)]
        user_op["missing_fields"] = missing_fields
        
        # Update state with modified user_operation
        updated_state = state.copy()
        updated_state["user_operation"] = user_op
        
        log_action("UPDATE_USER_OP_COMPLETE", f"Updated user_op: {user_op}", 
                  session_id=state["session_id"])
        
        # Generate appropriate response
        if missing_fields:
            response = f"I still need: {', '.join(missing_fields)}. Please provide them."
            updated_state = transition_conversation_state(
                updated_state, ConversationState.DATA_COLLECTION,
                reason="Still missing required fields"
            )
        else:
            response = llm_response_generator.generate_confirmation_response(user_op, updated_state)
            updated_state = transition_conversation_state(
                updated_state, ConversationState.CONFIRMATION_PENDING,
                reason="All data collected, awaiting final confirmation"
            )
        
        return add_message_to_state(
            updated_state, response, "assistant",
            agent_id="user_management"
        )

    def _handle_data_collection_response(self, state: ChatState, message: str) -> ChatState:
        """Handle responses during data collection phase"""
        
        log_action("DATA_COLLECTION_RESPONSE", f"Collecting data: '{message}'", 
                  session_id=state["session_id"])
        
        # Handle special commands
        if message.lower().strip() in ["cancel", "quit", "exit", "stop"]:
            updated_state = add_message_to_state(
                state, "User creation cancelled. How can I help you?", "assistant",
                agent_id="user_management"
            )
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="User cancelled operation"
            )
        
        # Try to extract entities from the message
        updated_state = data_extraction_agent.extract_entities(
            message, "user_create", state
        )
        
        # Get or initialize user_operation
        user_op = updated_state.get("user_operation", {})
        if not user_op:
            user_op = {
                "operation_type": "create",
                "user_id": None,
                "first_name": None,
                "last_name": None,
                "email": None,
                "phone": None,
                "role": None,
                "department": None,
                "property": None,
                "status": "active",
                "required_fields": ["first_name", "last_name", "email"],
                "collected_fields": [],
                "missing_fields": ["first_name", "last_name", "email"]
            }
            updated_state["user_operation"] = user_op
        
        # Apply extracted entities to user_operation
        collected_data = {}
        for entity in updated_state.get("extracted_entities", []):
            if entity.get("is_valid", False):
                field_name = entity["entity_type"]
                log_action("DATA_COLLECTION_ENTITY", f"Found {field_name}: {entity['value']}", 
                          session_id=state["session_id"])
                
                if field_name == "full_name":
                    name_parts = entity["value"].split()
                    if len(name_parts) >= 2:
                        collected_data["first_name"] = name_parts[0]
                        collected_data["last_name"] = " ".join(name_parts[1:])
                        user_op["first_name"] = name_parts[0]
                        user_op["last_name"] = " ".join(name_parts[1:])
                        for field in ["first_name", "last_name"]:
                            if field not in user_op.get("collected_fields", []):
                                user_op["collected_fields"].append(field)
                elif field_name in ["first_name", "last_name", "email", "phone", "role", "department"]:
                    collected_data[field_name] = entity["value"]
                    user_op[field_name] = entity["value"]
                    if field_name not in user_op.get("collected_fields", []):
                        user_op["collected_fields"].append(field_name)
        
        # Update missing fields
        required_fields = ["first_name", "last_name", "email"]
        missing_fields = [field for field in required_fields if not user_op.get(field)]
        user_op["missing_fields"] = missing_fields
        
        log_action("DATA_COLLECTION_STATUS", f"Collected: {collected_data}, Missing: {missing_fields}", 
                  session_id=state["session_id"])
        
        # Generate appropriate response
        if missing_fields:
            # Still missing data - ask for what's missing
            if len(missing_fields) == len(required_fields):
                # No data collected yet, provide friendly guidance
                response = (
                    "I'd be happy to help you create a new user! 😊\n\n"
                    "Could you tell me:\n"
                    "• **What's their name?** (first and last)\n"
                    "• **Email address?**\n"
                    "• **Phone number?** (optional)\n"
                    "• **Role/position?** (optional)\n\n"
                    "Just tell me naturally - for example: *\"John Smith, john@company.com, manager\"*"
                )
            else:
                # Some data collected, ask for the rest
                missing_list = [field.replace('_', ' ').title() for field in missing_fields]
                if collected_data:
                    collected_items = []
                    if collected_data.get("first_name") and collected_data.get("last_name"):
                        collected_items.append(f"**Name**: {collected_data['first_name']} {collected_data['last_name']}")
                    elif collected_data.get("first_name"):
                        collected_items.append(f"**First Name**: {collected_data['first_name']}")
                    elif collected_data.get("last_name"):
                        collected_items.append(f"**Last Name**: {collected_data['last_name']}")
                    if collected_data.get("email"):
                        collected_items.append(f"**Email**: {collected_data['email']}")
                    
                    if collected_items:
                        response = "Great! I have:\n" + "\n".join([f"✅ {item}" for item in collected_items])
                        response += f"\n\nI still need: {', '.join(missing_list)}"
                    else:
                        response = f"I need: {', '.join(missing_list)}"
                else:
                    response = f"I need: {', '.join(missing_list)}"
            
            # Stay in data collection state
            updated_state = transition_conversation_state(
                updated_state, ConversationState.DATA_COLLECTION,
                reason="Still collecting required user data"
            )
        else:
            # Have all required data - show confirmation
            response = llm_response_generator.generate_confirmation_response(user_op, updated_state)
            updated_state = transition_conversation_state(
                updated_state, ConversationState.CONFIRMATION_PENDING,
                reason="All required data collected, awaiting confirmation"
            )
        
        return add_message_to_state(
            updated_state, response, "assistant",
            agent_id="user_management"
        )
    
    def _handle_natural_data_collection(self, state: ChatState, message: str) -> ChatState:
        """Handle natural conversation for data collection with deduplication"""
        
        log_action("NATURAL_DATA_COLLECTION", f"Processing natural input: '{message}'", 
                  session_id=state["session_id"])
        
        # OPTIMIZATION: Check if we've already processed this exact message
        if state.get("last_processed_message") == message:
            log_action("DUPLICATE_MESSAGE", "Skipping duplicate message processing", 
                      session_id=state["session_id"])
            return state
        
        # Mark message as processed
        state["last_processed_message"] = message
        
        # Only extract data if we haven't done so recently
        if not state.get("extraction_done", False):
            updated_state = data_extraction_agent.extract_entities(
                message, "user_create", state
            )
            updated_state["extraction_done"] = True
        else:
            updated_state = state
        
        # Process and update user operation with extracted data
        user_op = updated_state.get("user_operation", {})
        collected_data = {}
        
        # Get data from extracted entities
        for entity in updated_state.get("extracted_entities", []):
            if entity.get("is_valid", False):
                field_name = entity["entity_type"]
                log_action("NATURAL_ENTITY_FOUND", f"Found {field_name}: {entity['value']}", 
                          session_id=state["session_id"])
                
                if field_name in ["first_name", "last_name", "email", "phone", "role", "department"]:
                    collected_data[field_name] = entity["value"]
                    user_op[field_name] = entity["value"]
                    if field_name not in user_op.get("collected_fields", []):
                        user_op.get("collected_fields", []).append(field_name)
        
        # Handle full name extraction
        full_name_entities = [e for e in updated_state.get("extracted_entities", []) if e["entity_type"] == "full_name"]
        if full_name_entities:
            full_name_entity = full_name_entities[0]
            if full_name_entity.get("is_valid", False):
                name_parts = full_name_entity["value"].split()
                if len(name_parts) >= 2:
                    collected_data["first_name"] = name_parts[0]
                    collected_data["last_name"] = " ".join(name_parts[1:])
                    user_op["first_name"] = name_parts[0]
                    user_op["last_name"] = " ".join(name_parts[1:])
                    
                    for field in ["first_name", "last_name"]:
                        if field not in user_op.get("collected_fields", []):
                            user_op.get("collected_fields", []).append(field)
        
        # Update missing fields
        required_fields = ["first_name", "last_name", "email"]
        missing_fields = [field for field in required_fields if not user_op.get(field)]
        user_op["missing_fields"] = missing_fields
        
        log_action("NATURAL_COLLECTED", f"Collected: {collected_data}, Missing: {missing_fields}", 
                  session_id=state["session_id"])
        
        # OPTIMIZATION: Use template responses instead of LLM for common cases
        if missing_fields:
            # Still missing data - ask naturally for what's missing
            response = self._generate_natural_request(missing_fields, collected_data)
        else:
            # Have all data - show confirmation
            response = self._generate_natural_confirmation(user_op)
            updated_state = transition_conversation_state(
                updated_state, ConversationState.CONFIRMATION_PENDING,
                reason="All required data collected, awaiting confirmation"
            )
        
        return add_message_to_state(
            updated_state, response, "assistant",
            agent_id="user_management"
        )
    
    def _handle_user_creation_natural(self, state: ChatState, message: str) -> ChatState:
        """Handle user creation with optimized flow and reduced LLM calls"""
        
        log_action("USER_CREATE_NATURAL", f"Starting natural user creation: '{message}'", 
                  session_id=state["session_id"])
        
        # Initialize user operation data if not exists
        if not state.get("user_operation"):
            state["user_operation"] = UserOperationData(
                operation_type="create",
                user_id=None,
                first_name=None,
                last_name=None,
                email=None,
                phone=None,
                role=None,
                department=None,
                property=None,
                status="active",
                required_fields=["first_name", "last_name", "email"],
                collected_fields=[],
                missing_fields=["first_name", "last_name", "email"]
            )
        
        # OPTIMIZATION: Only extract data if we haven't done so recently
        if not state.get("extraction_done", False):
            updated_state = data_extraction_agent.extract_entities(
                message, "user_create", state
            )
            updated_state["extraction_done"] = True
        else:
            updated_state = state
        
        # Process any extracted entities
        extracted_entities = updated_state.get("extracted_entities", [])
        user_op = updated_state.get("user_operation", {})
        
        # Apply extracted data to user operation
        data_found = False
        for entity in extracted_entities:
            if entity.get("is_valid", False):
                field_name = entity["entity_type"]
                if field_name in ["first_name", "last_name", "email", "phone", "role", "department"]:
                    user_op[field_name] = entity["value"]
                    if field_name not in user_op.get("collected_fields", []):
                        user_op["collected_fields"].append(field_name)
                    data_found = True
                    log_action("NATURAL_DATA_EXTRACTED", f"Found {field_name}: {entity['value']}", 
                              session_id=state["session_id"])
        
        # Update missing fields
        required_fields = ["first_name", "last_name", "email"]
        missing_fields = [field for field in required_fields if not user_op.get(field)]
        user_op["missing_fields"] = missing_fields
        
        updated_state["user_operation"] = user_op
        
        if data_found and not missing_fields:
            # We have all required data - show confirmation using template
            response = self._generate_natural_confirmation(user_op)
            updated_state = add_message_to_state(
                updated_state, response, "assistant",
                agent_id="user_management"
            )
            return transition_conversation_state(
                updated_state, ConversationState.CONFIRMATION_PENDING,
                reason="All required data collected, awaiting confirmation"
            )
        elif data_found:
            # Some data collected, use template response
            response = self._generate_natural_request(missing_fields, user_op)
            
            updated_state = add_message_to_state(
                updated_state, response, "assistant",
                agent_id="user_management"
            )
            return transition_conversation_state(
                updated_state, ConversationState.COLLECTING_USER_DATA,
                reason="Collecting remaining required data"
            )
        else:
            # No data found - use template guidance
            response = (
                "I'd be happy to help you create a new user! 😊\n\n"
                "Could you tell me:\n"
                "• **What's their name?** (first and last)\n"
                "• **Email address?**\n"
                "• **Phone number?** (optional)\n"
                "• **Role/position?** (optional)\n\n"
                "Just tell me naturally - for example: *\"John Smith, john@company.com, manager\"*"
            )
            
            updated_state = add_message_to_state(
                updated_state, response, "assistant",
                agent_id="user_management"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.COLLECTING_USER_DATA,
                reason="Starting natural data collection"
            )
    
    def _handle_conversation_state(self, state: ChatState, message: str) -> ChatState:
        """Handle ongoing conversation states"""
        
        conversation_state = state.get("conversation_state")
        
        if conversation_state == ConversationState.DATA_COLLECTION.value:
            return self._collect_user_data(state, message)
        elif conversation_state == ConversationState.CONFIRMATION_PENDING.value:
            return self._confirm_user_creation(state, message)
        else:
            # Default to idle state handling
            return self._handle_general_query(state, message)
    
    def _handle_general_query(self, state: ChatState, message: str) -> ChatState:
        """Handle general user management queries using LLM"""
        
        # Use LLM to generate natural response based on context
        general_response = llm_response_generator.generate_response(
            intent="general_help",
            state=state,
            current_message=message,
            context="User management assistance after operation completion or unclear request"
        )
        
        updated_state = add_message_to_state(
            state, general_response, "assistant",
            agent_id="user_management"
        )
        
        return transition_conversation_state(
            updated_state, ConversationState.IDLE,
            reason="General help provided via LLM"
        )
    
    # Helper methods
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> List[str]:
        """Validate user data and return list of errors"""
        
        errors = []
        
        # Email validation
        if "email" in user_data:
            email = user_data["email"]
            if not email or "@" not in email:
                errors.append("Invalid email format")
            elif db_adapter.email_exists(email):
                errors.append("Email already exists")
        
        # Name validation
        for field in ["first_name", "last_name"]:
            if field in user_data:
                name = user_data[field]
                if not name or len(name.strip()) < 1:
                    errors.append(f"{field.replace('_', ' ').title()} cannot be empty")
        
        return errors
    
    def _validate_single_field(self, field_name: str, value: str) -> bool:
        """Validate a single field value"""
        
        if not value or not value.strip():
            return False
        
        if field_name == "email":
            return "@" in value and "." in value
        elif field_name in ["first_name", "last_name"]:
            return len(value.strip()) >= 1
        elif field_name == "phone":
            # Basic phone validation
            digits = ''.join(filter(str.isdigit, value))
            return len(digits) >= 10
        
        return True
    
    def _generate_confirmation_message(self, user_op: UserOperationData) -> str:
        """Generate confirmation message for user creation"""
        
        return (
            f"📋 **Please confirm the user details:**\n\n"
            f"• **First Name**: {user_op['first_name']}\n"
            f"• **Last Name**: {user_op['last_name']}\n"
            f"• **Email**: {user_op['email']}\n"
            f"• **Phone**: {user_op.get('phone') or 'Not provided'}\n"
            f"• **Role**: {user_op.get('role') or 'staff'}\n"
            f"• **Department**: {user_op.get('department') or 'general'}\n\n"
            f"**Type 'yes' to create this user or 'no' to cancel.**"
        )
    
    def _generate_data_request_message(self, missing_fields: List[str]) -> str:
        """Generate message requesting missing data"""
        
        field_descriptions = {
            "first_name": "First Name",
            "last_name": "Last Name", 
            "email": "Email Address",
            "phone": "Phone Number",
            "role": "Role/Position",
            "department": "Department"
        }
        
        if len(missing_fields) == 1:
            field = missing_fields[0]
            field_name = field_descriptions.get(field, field.replace('_', ' ').title())
            return f"Please provide the user's **{field_name}**:"
        else:
            missing_list = [field_descriptions.get(f, f.replace('_', ' ').title()) for f in missing_fields]
            return (
                f"I need the following information to create the user:\n\n"
                + "\n".join([f"• {field}" for field in missing_list]) +
                f"\n\nPlease provide the **{missing_list[0]}** first:"
            )
    
    def _generate_single_field_request(self, field_name: str) -> str:
        """Generate request for a single field"""
        
        field_prompts = {
            "first_name": "What is the user's **first name**?",
            "last_name": "What is the user's **last name**?",
            "email": "What is the user's **email address**?",
            "phone": "What is the user's **phone number**? (optional)",
            "role": "What is the user's **role or position**? (optional)",
            "department": "What **department** does the user belong to? (optional)"
        }
        
        return field_prompts.get(field_name, f"Please provide the {field_name.replace('_', ' ')}:")
    
    def _generate_natural_request(self, missing_fields: List[str], collected_data: Dict[str, Any]) -> str:
        """Generate natural language request for missing data"""
        
        # Build a natural response acknowledging what we have and asking for what's missing
        response_parts = []
        
        if collected_data:
            # Acknowledge what we've collected
            collected_items = []
            if collected_data.get("first_name") and collected_data.get("last_name"):
                collected_items.append(f"**Name**: {collected_data['first_name']} {collected_data['last_name']}")
            elif collected_data.get("first_name"):
                collected_items.append(f"**First Name**: {collected_data['first_name']}")
            elif collected_data.get("last_name"):
                collected_items.append(f"**Last Name**: {collected_data['last_name']}")
            
            if collected_data.get("email"):
                collected_items.append(f"**Email**: {collected_data['email']}")
            if collected_data.get("phone"):
                collected_items.append(f"**Phone**: {collected_data['phone']}")
            if collected_data.get("role"):
                collected_items.append(f"**Role**: {collected_data['role']}")
            
            if collected_items:
                response_parts.append("Great! I have:\n" + "\n".join([f"✅ {item}" for item in collected_items]))
        
        # Ask for missing data
        if missing_fields:
            missing_requests = []
            for field in missing_fields:
                if field == "first_name":
                    missing_requests.append("**First name**")
                elif field == "last_name":
                    missing_requests.append("**Last name**")
                elif field == "email":
                    missing_requests.append("**Email address**")
            
            if missing_requests:
                response_parts.append(f"\nI still need:\n" + "\n".join([f"❓ {req}" for req in missing_requests]))
                response_parts.append("\nJust tell me naturally! 😊")
        
        return "\n".join(response_parts) if response_parts else "Could you provide the user details?"
    
    def _generate_natural_confirmation(self, user_op: Dict[str, Any]) -> str:
        """Generate natural language confirmation"""
        
        confirmation = "Perfect! Let me confirm the details:\n\n"
        confirmation += f"👤 **Name**: {user_op.get('first_name', '')} {user_op.get('last_name', '')}\n"
        confirmation += f"📧 **Email**: {user_op.get('email', '')}\n"
        
        if user_op.get('phone'):
            confirmation += f"📱 **Phone**: {user_op.get('phone')}\n"
        if user_op.get('role'):
            confirmation += f"💼 **Role**: {user_op.get('role')}\n"
        
        confirmation += "\nShould I create this user account? Just say **yes** to confirm! ✨"
        
        return confirmation
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get user management operation statistics"""
        
        success_rate = 0.0
        if self.operation_stats["total_operations"] > 0:
            success_rate = self.operation_stats["successful_operations"] / self.operation_stats["total_operations"]
        
        return {
            **self.operation_stats,
            "success_rate": success_rate
        }

# Initialize user management agent
user_management_agent = UserManagementAgent()
