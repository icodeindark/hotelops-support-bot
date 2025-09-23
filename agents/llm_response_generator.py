"""
LLM Response Generator - The Brain of the System
Makes the assistant respond naturally like ChatGPT by using LLM for all responses
"""

from typing import Dict, Any, List, Optional
from llm_utils import ask_gemini
from logger_config import log_action, log_error
from .state_schema import ChatState, ConversationState, IntentType


class LLMResponseGenerator:
    """Uses LLM as the primary brain for generating natural, contextual responses"""
    
    def __init__(self):
        self.system_persona = """
You are a helpful, friendly AI assistant for HotelOpsAI - a hotel management system. 

PERSONALITY:
- Conversational and natural (like ChatGPT)
- Professional but approachable 
- Use emojis sparingly but appropriately
- Match the user's tone (casual/formal)
- Be concise but helpful

CAPABILITIES:
- User Management: Create, update, list, delete users
- Service Management: Add and manage services
- Knowledge Base: Answer questions about HotelOpsAI
- Troubleshooting: Help with common issues

IMPORTANT:
- Always acknowledge what you've done/understood
- Provide clear next steps
- Be proactive in asking for missing information
- Celebrate successes naturally
- Handle errors gracefully
"""

    def generate_response(self, 
                         intent: Optional[str], 
                         state: ChatState, 
                         current_message: str,
                         action_result: Optional[Dict] = None,
                         context: Optional[str] = None) -> str:
        """
        Generate natural response using LLM as the brain
        
        Args:
            intent: The detected intent (user_create, greeting, etc.)
            state: Current conversation state
            current_message: User's current message
            action_result: Result of any action performed (user created, etc.)
            context: Additional context information
        """
        
        try:
            # Build conversation context
            conversation_history = self._build_conversation_context(state)
            
            # Build context-aware prompt based on intent
            prompt = self._build_intent_specific_prompt(intent, state, current_message, 
                                                       conversation_history, action_result, context)

            response = ask_gemini(prompt)
            
            log_action("LLM_RESPONSE_GENERATED", 
                      f"Generated natural response for intent: {intent}", 
                      session_id=state.get("session_id", "unknown"))
            
            return response.strip()
            
        except Exception as e:
            error_msg = str(e)
            session_id = state.get("session_id", "unknown")
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                log_action("API_QUOTA_FALLBACK", f"Using fallback due to quota exceeded for intent: {intent}", session_id=session_id)
            else:
                log_error("LLM_RESPONSE_ERROR", f"Failed to generate LLM response: {error_msg}", session_id=session_id)
            
            # Enhanced fallback response
            return self._get_smart_fallback_response(intent, current_message, state)
    
    def _build_intent_specific_prompt(self, intent: Optional[str], state: ChatState, 
                                     current_message: str, conversation_history: str,
                                     action_result: Optional[Dict], context: Optional[str]) -> str:
        """Build intent-specific prompts for better responses"""
        
        base_prompt = f"""
{self.system_persona}

CONVERSATION HISTORY:
{conversation_history}

USER'S CURRENT MESSAGE: "{current_message}"
"""

        if intent == "general_help":
            # Handle general help after operations
            user_op = state.get("user_operation")
            recent_actions = "No recent actions" if not action_result else f"Recent action: {action_result}"
            
            return f"""{base_prompt}

CONTEXT: The user just completed an operation or needs general assistance with user management.
{recent_actions}

Generate a natural, helpful response that:
1. If a user was just created, celebrate the success naturally
2. Ask what else they'd like to do
3. Be conversational and friendly
4. Don't use bullet points or rigid lists
5. Sound like a helpful colleague

Response:"""

        elif intent == "user_create":
            user_op = state.get("user_operation", {})
            missing_fields = user_op.get("missing_fields", [])
            
            if missing_fields:
                collected = {k: v for k, v in user_op.items() 
                           if k not in missing_fields and v is not None and k not in ['operation_type', 'required_fields', 'collected_fields', 'missing_fields']}
                
                return f"""{base_prompt}

CONTEXT: User wants to create a new user account.
Missing information: {', '.join(missing_fields)}
Information already collected: {collected}

Generate a natural response that:
1. Acknowledges what information they've provided
2. Asks for missing information conversationally
3. Provides examples if helpful
4. Be encouraging and friendly

Response:"""
            else:
                return f"""{base_prompt}

CONTEXT: All user information collected, showing confirmation.
User data: {user_op}

Generate a natural confirmation message that:
1. Shows the collected information clearly
2. Asks for final confirmation
3. Be enthusiastic about creating the user
4. Sound natural and conversational

Response:"""

        else:
            # Default prompt for other intents
            context_info = f"Additional context: {context}" if context else ""
            
            return f"""{base_prompt}

{context_info}

Generate a natural, helpful response that:
1. Acknowledges what the user said/did
2. Provides relevant information or next steps
3. Maintains conversation flow
4. Sounds like a real person, not a robot

Response:"""

    def _build_conversation_context(self, state: ChatState) -> str:
        """Build conversation history for context"""
        
        messages = state.get("messages", [])
        if not messages:
            return "This is the start of our conversation."
        
        # Get last 5 messages for context
        recent_messages = messages[-5:]
        context_lines = []
        
        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                context_lines.append(f"User: {content}")
            else:
                context_lines.append(f"Assistant: {content}")
        
        return "\n".join(context_lines)
    
    def _build_system_context(self, 
                             intent: Optional[str], 
                             state: ChatState, 
                             action_result: Optional[Dict],
                             context: Optional[str]) -> str:
        """Build system context for the LLM"""
        
        context_parts = []
        
        # Current intent and state
        if intent:
            context_parts.append(f"Intent: {intent}")
        
        conversation_state = state.get("conversation_state", "idle")
        context_parts.append(f"Conversation State: {conversation_state}")
        
        # Active operation
        user_operation = state.get("user_operation")
        if user_operation:
            op_type = user_operation.get("operation_type", "unknown")
            context_parts.append(f"Current Operation: {op_type}")
            
            # Add operation details if available
            if op_type == "create":
                missing_fields = user_operation.get("missing_fields", [])
                collected_fields = user_operation.get("collected_fields", [])
                
                if collected_fields:
                    context_parts.append(f"Collected Data: {', '.join(collected_fields)}")
                if missing_fields:
                    context_parts.append(f"Still Missing: {', '.join(missing_fields)}")
        
        # Action results
        if action_result:
            if action_result.get("success"):
                context_parts.append(f"✅ Action Completed: {action_result.get('message', 'Success')}")
            else:
                context_parts.append(f"❌ Action Failed: {action_result.get('error', 'Unknown error')}")
        
        # Additional context
        if context:
            context_parts.append(f"Additional Context: {context}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, intent: Optional[str], message: str) -> str:
        """Simple fallback if LLM fails"""
        
        if intent == "greeting":
            return "Hello! I'm your HotelOpsAI assistant. How can I help you today? 😊"
        elif intent == "user_create":
            return "I'd be happy to help you create a new user! Could you tell me their details?"
        elif intent == "unclear":
            return f"I'm not sure I understand '{message}'. Could you please clarify what you'd like to do?"
        else:
            return "I'm here to help! What would you like to do today?"
    
    def _get_smart_fallback_response(self, intent: Optional[str], message: str, state: ChatState) -> str:
        """Enhanced fallback with context awareness for quota/error situations"""
        # Check if we have user data in progress
        user_operation = state.get("user_operation", {})
        extracted_data = state.get("extracted_data", {})
        conversation_state = state.get("conversation_state", "idle")
        
        # Context-aware fallback responses
        if intent == "user_create" and conversation_state == "collecting_user_data":
            missing_fields = user_operation.get("missing_fields", [])
            if missing_fields:
                missing_str = ", ".join(missing_fields)
                return f"I'm ready to create the user account. I still need: {missing_str}. Please provide these details."
            else:
                return "I have all the information needed. Would you like me to create this user account now?"
        
        elif intent in ["user_create", "fast_routed"] and ("name" in message.lower() or "manager" in message.lower()):
            # User is providing data
            return "Thank you for providing that information! I'm processing the user creation. Do you have any additional details like email address?"
        
        elif "create" in message.lower() and "user" in message.lower():
            return "I'll help you create a new user account. Please provide the user's full name, role/position, and email address."
        
        elif intent == "knowledge_query":
            return "I can help you find information from our knowledge base. What specific topic do you need help with?"
        
        elif intent == "service_management" or "service" in message.lower():
            return "I can assist with service management. What would you like to do - create, update, list, or manage services?"
        
        elif intent == "troubleshooting" or "help" in message.lower():
            return "I'm here to help with troubleshooting. What specific issue are you experiencing?"
        
        # Default fallback
        return self._get_fallback_response(intent, message)

    def generate_confirmation_response(self, user_data: Dict, state: ChatState) -> str:
        """Generate natural confirmation message for user creation"""
        
        try:
            conversation_history = self._build_conversation_context(state)
            
            prompt = f"""
{self.system_persona}

SITUATION: The user wants to create a new user account and I've collected their information. 
I need to show them the details and ask for confirmation in a natural, friendly way.

CONVERSATION HISTORY:
{conversation_history}

USER DATA COLLECTED:
- Name: {user_data.get('first_name', '')} {user_data.get('last_name', '')}
- Email: {user_data.get('email', 'Not provided')}
- Phone: {user_data.get('phone', 'Not provided')}
- Role: {user_data.get('role', 'Not provided')}
- Department: {user_data.get('department', 'Not provided')}

Generate a natural confirmation message that:
1. Shows the collected information clearly
2. Asks for confirmation in a friendly way
3. Sounds conversational, not robotic

Response:"""

            response = ask_gemini(prompt)
            
            log_action("LLM_CONFIRMATION_GENERATED", 
                      f"Generated confirmation for user: {user_data.get('first_name', '')} {user_data.get('last_name', '')}", 
                      session_id=state.get("session_id", "unknown"))
            
            return response.strip()
            
        except Exception as e:
            log_error("LLM_CONFIRMATION_ERROR", f"Failed to generate confirmation: {str(e)}", 
                     session_id=state.get("session_id", "unknown"))
            
            # Fallback
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            return f"Perfect! I have the details for {name}. Should I create this user account? (yes/no)"

    def generate_success_response(self, action: str, result: Dict, state: ChatState) -> str:
        """Generate natural success message"""
        
        try:
            conversation_history = self._build_conversation_context(state)
            
            prompt = f"""
{self.system_persona}

SITUATION: I just successfully completed an action for the user and need to celebrate the success naturally.

CONVERSATION HISTORY:
{conversation_history}

ACTION COMPLETED: {action}
RESULT: {result}

Generate a natural success message that:
1. Celebrates the completion
2. Provides relevant details
3. Asks what they'd like to do next
4. Sounds genuinely helpful and conversational

Response:"""

            response = ask_gemini(prompt)
            
            log_action("LLM_SUCCESS_GENERATED", 
                      f"Generated success response for: {action}", 
                      session_id=state.get("session_id", "unknown"))
            
            return response.strip()
            
        except Exception as e:
            log_error("LLM_SUCCESS_ERROR", f"Failed to generate success response: {str(e)}", 
                     session_id=state.get("session_id", "unknown"))
            
            # Fallback
            return f"Great! I successfully completed the {action}. What would you like to do next?"


# Global instance
llm_response_generator = LLMResponseGenerator()
