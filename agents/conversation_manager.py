"""
HotelOpsAI Conversation Manager - State Transitions & Flow Control
Senior AI Engineer Implementation

The Conversation Manager handles:
1. General conversation management
2. State transitions and flow control  
3. Context preservation across turns
4. Fallback responses and error recovery
5. Session management and cleanup
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .state_schema import (
    ChatState, IntentType, ConversationState, AgentType,
    add_message_to_state, transition_conversation_state,
    update_state_timestamp
)
from .llm_response_generator import llm_response_generator
from database.memory_db import db_adapter
from logger_config import agent_logger, log_action, log_error
from llm_utils import ask_gemini

class ConversationManager:
    """
    Manages conversation flow, state transitions, and provides fallback responses
    """
    
    def __init__(self):
        self.conversation_stats = {
            "total_conversations": 0,
            "successful_handoffs": 0,
            "fallback_responses": 0,
            "context_preservations": 0
        }
        
        # Response templates for different scenarios
        self.response_templates = {
            "greeting": self._get_greeting_response,
            "unclear": self._get_unclear_response,
            "error_recovery": self._get_error_recovery_response,
            "handoff_request": self._get_handoff_response,
            "general_help": self._get_general_help_response
        }
        
        agent_logger.info("Conversation Manager initialized")
    
    def handle_conversation(self, state: ChatState, message: str) -> ChatState:
        """
        Main entry point for conversation management
        
        Handles:
        - Intent-based responses  
        - State transitions
        - Context preservation
        - Error recovery
        """
        
        intent_str = state.get("current_intent")
        conversation_state_str = state.get("conversation_state", "idle")
        
        log_action("CONVERSATION_MANAGER", 
                  f"Handling conversation - Intent: {intent_str}, State: {conversation_state_str}", 
                  session_id=state["session_id"])
        
        try:
            # Convert string intent back to enum if needed
            intent = self._parse_intent(intent_str)
            
            # Determine response based on intent and state
            response = self._generate_contextual_response(state, message, intent)
            
            # Add response to state
            updated_state = add_message_to_state(
                state, response, "assistant",
                agent_id="conversation_manager",
                metadata={
                    "intent": intent_str,
                    "response_type": self._get_response_type(intent)
                }
            )
            
            # Update conversation state
            new_conv_state = self._determine_next_state(intent, conversation_state_str)
            updated_state = transition_conversation_state(
                updated_state, new_conv_state,
                reason=f"Conversation manager handled {intent_str}"
            )
            
            # Track statistics
            self.conversation_stats["total_conversations"] += 1
            if intent == IntentType.HANDOFF_REQUEST:
                self.conversation_stats["successful_handoffs"] += 1
            elif intent == IntentType.UNCLEAR:
                self.conversation_stats["fallback_responses"] += 1
            
            return update_state_timestamp(updated_state)
            
        except Exception as e:
            import traceback
            error_msg = f"Conversation management failed: {str(e)}"
            full_traceback = traceback.format_exc()
            
            log_error("CONVERSATION_ERROR", error_msg, session_id=state["session_id"])
            agent_logger.error(f"Full conversation manager error traceback:\n{full_traceback}")
            
            # Debug: Log the exact state that caused the error
            agent_logger.error(f"Error in conversation manager with intent_str: {intent_str} (type: {type(intent_str)})")
            agent_logger.error(f"Conversation state str: {conversation_state_str} (type: {type(conversation_state_str)})")
            agent_logger.error(f"State keys: {list(state.keys())}")
            
            # Provide error recovery response
            return self._handle_conversation_error(state, error_msg)
    
    def _parse_intent(self, intent_str: Optional[str]) -> Optional[IntentType]:
        """Convert string intent back to enum"""
        
        if not intent_str:
            return None
            
        for intent_enum in IntentType:
            if intent_enum.value == intent_str:
                return intent_enum
        
        return IntentType.UNCLEAR
    
    def _generate_contextual_response(self, state: ChatState, message: str, intent: Optional[IntentType]) -> str:
        """Generate appropriate response based on context - OPTIMIZED with templates"""
        
        # OPTIMIZATION: Use templates for common intents instead of LLM
        if intent == IntentType.GREETING:
            return self._get_greeting_response(state, message)
        elif intent == IntentType.UNCLEAR:
            return self._get_unclear_response(state, message)
        elif intent == IntentType.HANDOFF_REQUEST:
            return self._get_handoff_response(state)
        elif intent == IntentType.KNOWLEDGE_QUERY:
            return self._handle_knowledge_query(state, message)
        else:
            # Only use LLM for complex cases
            conversation_history = self._get_conversation_context(state)
            return llm_response_generator.generate_response(
                intent=intent.value if intent else None,
                state=state,
                current_message=message,
                context=f"Conversation flow - handling {intent.value if intent else 'unknown'} intent"
            )
    
    def _get_greeting_response(self, state: ChatState, original_message: str = "") -> str:
        """Generate natural, context-aware greeting response"""
        
        # Check if user has interacted before
        user_id = state.get("user_id")
        session_history = self._get_user_session_history(user_id)
        
        # Detect the style of greeting to respond appropriately
        message_lower = original_message.lower() if original_message else ""
        
        # Casual/informal greetings
        if any(word in message_lower for word in ["dude", "hey", "sup", "yo", "what's up"]):
            if len(session_history) > 1:
                base_greeting = "Hey! Good to see you back! 😊"
            else:
                base_greeting = "Hey there! I'm your HotelOpsAI assistant. 😊"
        
        # "How are you" type greetings  
        elif any(phrase in message_lower for phrase in ["how are you", "how r u", "how ya doing"]):
            if len(session_history) > 1:
                base_greeting = "I'm doing great, thanks for asking! How can I help you today? 😊"
            else:
                base_greeting = "I'm doing great! Nice to meet you! I'm your HotelOpsAI assistant. 😊"
        
        # Formal greetings
        elif any(word in message_lower for word in ["hello", "hi", "good morning", "good afternoon"]):
            if len(session_history) > 1:
                base_greeting = "👋 Hello again! Welcome back!"
            else:
                base_greeting = "👋 Hello! I'm your HotelOpsAI assistant."
        
        # Default for unclear greetings
        else:
            if len(session_history) > 1:
                base_greeting = "👋 Welcome back!"
            else:
                base_greeting = "👋 Hello! I'm your HotelOpsAI assistant."
        
        # Add capabilities in a natural way
        return f"""{base_greeting}

I can help you with user management, answer questions about HotelOpsAI, troubleshoot issues, or manage services.

What would you like to do?"""
    
    def _get_unclear_response(self, state: ChatState, message: str) -> str:
        """Generate response for unclear intents"""
        
        return f"""🤔 **I'm not sure I understand "{message[:50]}{'...' if len(message) > 50 else ''}"**

I can help you with:

• **User Management**: "add user", "list users", "find user"
• **Questions**: "how to...", "what is...", "help with..."
• **Services**: "add service", "list services"
• **Troubleshooting**: Describe any issues you're experiencing

Could you please clarify what you'd like to do?"""
    
    def _get_handoff_response(self, state: ChatState) -> str:
        """Generate human handoff response"""
        
        return """🤝 **Human Support Request**

I understand you'd like to speak with a human agent. While I don't have direct access to escalate to human support in this prototype, here are your options:

• **Contact your system administrator**
• **Email**: support@hotelopsai.com  
• **Support portal**: Check your HotelOpsAI dashboard for support options
• **Documentation**: Browse our knowledge base for detailed guides

In the meantime, I'm here to help with any questions you might have! Many issues can be resolved quickly through our automated assistance."""
    
    def _get_general_help_response(self, state: ChatState) -> str:
        """Generate general help response"""
        
        return """💡 **I'm here to help with HotelOpsAI!**

Here's what I can assist you with:

**👥 User Management**
- Add new users: "add user [name, email, role]"  
- List existing users: "show all users"
- Find specific users: "find user [name/email]"
- Update user information: "edit user [email]"

**❓ Questions & Support**
- Ask about features: "how to reset password?"
- Get guidance: "what are user roles?"
- Troubleshoot issues: "login problems", "access issues"

**🔧 Services & Work Orders**
- Create services: "add service [description]"
- View services: "list services"

Just tell me what you need help with, and I'll guide you through it step by step!"""
    
    def _handle_knowledge_query(self, state: ChatState, message: str) -> str:
        """Handle knowledge base queries with conversational context"""
        
        try:
            # Use AI to provide helpful response
            prompt = f"""
            As a helpful HotelOpsAI assistant, answer this question: {message}
            
            Provide a clear, helpful response about hotel operations and management.
            Keep it concise and actionable. If you're not sure about specific HotelOpsAI features,
            provide general guidance and suggest they contact support for specific details.
            
            Format your response professionally with clear sections if needed.
            """
            
            response = ask_gemini(prompt)
            
            # Add helpful footer
            footer = "\n\n💡 **Need more specific help?** Feel free to ask about user management, troubleshooting, or other HotelOpsAI features!"
            
            return f"{response}{footer}"
            
        except Exception as e:
            log_error("KNOWLEDGE_QUERY_ERROR", str(e), session_id=state["session_id"])
            
            return """I'd be happy to help answer your question! However, I'm having trouble accessing detailed information right now.

For specific questions about HotelOpsAI features:
• Check the help documentation in your dashboard
• Contact support for detailed guidance
• Ask me about user management or troubleshooting - I can help with those!

What specific aspect of HotelOpsAI would you like to know about?"""
    
    def _get_error_recovery_response(self, state: ChatState) -> str:
        """Generate error recovery response"""
        
        retry_count = state.get("retry_count", 0)
        
        if retry_count == 0:
            return """⚠️ **I encountered a small hiccup while processing your request.**

Let me try to help you in a different way. Could you please:
• Rephrase your question or request
• Be more specific about what you need
• Try a simpler version of your request

What would you like assistance with?"""
        
        elif retry_count < 3:
            return """⚠️ **I'm still having trouble with that request.**

Let's try a different approach:
• Ask about user management: "add user", "list users"
• Get help with features: "how to...", "what is..."  
• Report a problem: "I'm having trouble with..."

What can I help you with instead?"""
        
        else:
            return """❌ **I'm having persistent issues processing that type of request.**

Here's what you can try:
• **Refresh the page** and try again
• **Simplify your request** - ask about one thing at a time
• **Contact support** if the issue continues
• **Ask about basic features** - user management, FAQ, etc.

I apologize for the inconvenience. How else can I assist you?"""
    
    def _determine_next_state(self, intent: Optional[IntentType], current_state: str) -> ConversationState:
        """Determine the next conversation state"""
        
        # Most conversation manager interactions end in IDLE state
        # unless they're starting a new workflow
        
        if intent in [IntentType.USER_CREATE, IntentType.USER_UPDATE]:
            return ConversationState.DATA_COLLECTION
        elif intent == IntentType.USER_DELETE:
            return ConversationState.CONFIRMATION_PENDING
        elif intent == IntentType.HANDOFF_REQUEST:
            return ConversationState.HUMAN_HANDOFF
        else:
            return ConversationState.IDLE
    
    def _get_response_type(self, intent: Optional[IntentType]) -> str:
        """Get response type for metadata"""
        
        if intent == IntentType.GREETING:
            return "greeting"
        elif intent == IntentType.HANDOFF_REQUEST:
            return "handoff"
        elif intent == IntentType.UNCLEAR:
            return "clarification"
        elif intent == IntentType.KNOWLEDGE_QUERY:
            return "knowledge"
        else:
            return "general_help"
    
    def _get_conversation_context(self, state: ChatState) -> str:
        """Get formatted conversation context - OPTIMIZED for smaller context"""
        
        messages = state.get("messages", [])
        # OPTIMIZATION: Reduce from 5 to 2 messages for context
        recent_messages = messages[-2:] if len(messages) > 2 else messages
        
        context_lines = []
        for msg in recent_messages:
            role = msg["role"].title()
            # OPTIMIZATION: Reduce content length from 100 to 50 chars
            content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines) if context_lines else "No previous context"
    
    def _get_user_session_history(self, user_id: str) -> List[Dict]:
        """Get user's session history for personalization"""
        
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    def _handle_conversation_error(self, state: ChatState, error_msg: str) -> ChatState:
        """Handle conversation errors gracefully"""
        
        error_response = self._get_error_recovery_response(state)
        
        updated_state = add_message_to_state(
            state, error_response, "assistant",
            agent_id="conversation_manager",
            metadata={"error_recovery": True, "original_error": error_msg}
        )
        
        return transition_conversation_state(
            updated_state, ConversationState.ERROR_RECOVERY,
            reason="Error recovery mode"
        )
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation management statistics"""
        
        return self.conversation_stats.copy()

# Initialize conversation manager
conversation_manager = ConversationManager()
