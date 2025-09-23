"""
HotelOpsAI Multi-Agent LangGraph System - Complete Integration
Senior AI Engineer Implementation

This integrates all specialized agents into a cohesive LangGraph workflow
with proper state management and agent coordination.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional
from datetime import datetime
import re

from .state_schema import (
    ChatState, AgentType, IntentType, ConversationState,
    create_initial_state, add_message_to_state, transition_conversation_state,
    set_active_agent, update_state_timestamp
)
from .router_agent import router_agent
from .user_management_agent import user_management_agent
from .data_extraction_agent import data_extraction_agent
from .conversation_manager import conversation_manager
from .knowledge_base_agent import knowledge_base_agent
from database.memory_db import db_adapter
from tools import faq_tools, troubleshooting
from logger_config import agent_logger, log_action, log_error
from llm_utils import ask_gemini

class MultiAgentSystem:
    """
    Orchestrates the multi-agent system with LangGraph state management
    """
    
    def __init__(self):
        self.graph = None
        self.system_stats = {
            "total_conversations": 0,
            "successful_conversations": 0,
            "agent_usage": {},
            "average_response_time": 0.0
        }
        
        agent_logger.info("Multi-Agent System initializing...")
        self._build_graph()
        agent_logger.info("Multi-Agent System ready")
    
    def _build_graph(self):
        """Build the complete LangGraph workflow"""
        
        # Create state graph
        self.graph = StateGraph(ChatState)
        
        # === NODE DEFINITIONS ===
        
        # Entry point - Initialize conversation
        self.graph.add_node("initialize_conversation", self._initialize_conversation)
        
        # Router node - Intent classification and agent routing
        self.graph.add_node("router", self._router_node)
        
        # Specialized agent nodes
        self.graph.add_node("user_management", self._user_management_node)
        self.graph.add_node("service_management", self._service_management_node)
        self.graph.add_node("knowledge_base", self._knowledge_base_node)
        self.graph.add_node("conversation_manager", self._conversation_manager_node)
        
        # Data processing node
        self.graph.add_node("data_extraction", self._data_extraction_node)
        
        # Response generation node
        self.graph.add_node("response_generator", self._response_generator_node)
        
        # Error handling node
        self.graph.add_node("error_handler", self._error_handler_node)
        
        # Session management
        self.graph.add_node("save_session", self._save_session_node)
        
        # === EDGE DEFINITIONS ===
        
        # Set entry point
        self.graph.set_entry_point("initialize_conversation")
        
        # Flow from initialization to router
        self.graph.add_edge("initialize_conversation", "router")
        
        # Conditional edges from router to specialized agents
        self.graph.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "user_management": "user_management",
                "service_management": "service_management", 
                "knowledge_base": "knowledge_base",
                "conversation_manager": "conversation_manager",
                "data_extraction": "data_extraction",
                "error_handler": "error_handler"
            }
        )
        
        # All agents can go to response generator or back to router
        for agent_node in ["user_management", "service_management", "knowledge_base", "conversation_manager"]:
            self.graph.add_conditional_edges(
                agent_node,
                self._determine_next_step,
                {
                    "continue_conversation": "router",
                    "generate_response": "response_generator",
                    "save_and_end": "save_session",
                    "error": "error_handler"
                }
            )
        
        # Data extraction flows
        self.graph.add_edge("data_extraction", "response_generator")
        
        # Response generator flows
        self.graph.add_conditional_edges(
            "response_generator",
            self._after_response,
            {
                "continue": "router",
                "end": "save_session"
            }
        )
        
        # Error handler flows
        self.graph.add_edge("error_handler", "save_session")
        
        # Session save to end
        self.graph.add_edge("save_session", END)
        
        # Compile the graph
        self.graph = self.graph.compile()
    
    # === NODE IMPLEMENTATIONS ===
    
    def _initialize_conversation(self, state: ChatState) -> ChatState:
        """Initialize conversation state and load session data"""
        
        session_id = state.get("session_id", "default")
        user_id = state.get("user_id", "anonymous")
        
        log_action("CONVERSATION_START", f"Initializing conversation for user {user_id}", 
                  session_id=session_id)
        
        # Load existing session if available
        existing_session = db_adapter.get_session(session_id)
        
        if existing_session:
            # Restore session state
            updated_state = state.copy()
            updated_state.update(existing_session)
            agent_logger.info(f"Restored session {session_id}")
        else:
            # Initialize new conversation state
            updated_state = state.copy()
            if not updated_state.get("conversation_id"):
                updated_state = create_initial_state(user_id, session_id)
                updated_state.update(state)  # Preserve original input
            
            agent_logger.info(f"Created new conversation {updated_state['conversation_id']}")
        
        # Update system stats
        self.system_stats["total_conversations"] += 1
        
        return update_state_timestamp(updated_state)
    
    def _check_explicit_agent_switch(self, message: str) -> Optional[str]:
        """Check if message contains explicit agent switching request"""
        
        message_lower = message.lower().strip()
        
        # Direct agent references
        agent_keywords = {
            "conversation manager": "conversation_manager",
            "service manager": "service_management", 
            "service management": "service_management",
            "user management": "user_management",
            "knowledge base": "knowledge_base",
            "troubleshoot": "troubleshoot"
        }
        
        # Check direct mentions
        for keyword, agent in agent_keywords.items():
            if keyword in message_lower:
                return agent
        
        # Check "go to" and "switch to" patterns
        switch_patterns = [
            r"(?:go\s+to|switch\s+to|take\s+me\s+to)\s+(\w+)",
            r"(?:i\s+want\s+to\s+(?:go\s+to|switch\s+to))\s+(\w+)"
        ]
        
        for pattern in switch_patterns:
            match = re.search(pattern, message_lower)
            if match:
                target = match.group(1)
                if "service" in target or "manager" in target:
                    return "service_management"
                elif "user" in target:
                    return "user_management"
                elif "conversation" in target:
                    return "conversation_manager"
                elif "knowledge" in target:
                    return "knowledge_base"
                elif "troubleshoot" in target:
                    return "troubleshoot"
        
        return None
    
    def _indicates_topic_switch(self, message: str, current_agent: str) -> bool:
        """Check if message indicates a topic switch from current agent"""
        
        message_lower = message.lower().strip()
        
        # Topic keywords for different domains - switch when these are mentioned
        topic_keywords = {
            "user_management": ["service", "srvice", "management", "troubleshoot", "problem", "how to", "what is", "about", "information", "faq", "help"], 
            "service_management": ["user", "create", "add", "manage", "new user", "delete user"],
            "knowledge_base": ["user", "service", "create", "add", "manage"],
            "conversation_manager": ["user", "service", "troubleshoot", "problem"]
        }
        
        # General question indicators (should always go to knowledge or conversation)
        question_indicators = [
            "when did", "how old", "what year", "about hotelopsai", 
            "information about", "tell me about", "general information"
        ]
        
        if any(indicator in message_lower for indicator in question_indicators):
            return True
        
        # Check for topic switches based on current agent
        switch_keywords = topic_keywords.get(current_agent, [])
        return any(keyword in message_lower for keyword in switch_keywords)
    
    def _router_node(self, state: ChatState) -> ChatState:
        """Route to appropriate agent based on conversation flow and intent classification"""
        
        start_time = datetime.now()
        
        # Get the current message
        current_message = state.get("query", "")
        if not current_message and state.get("messages"):
            # Get last user message
            user_messages = [msg for msg in state["messages"] if msg["role"] == "user"]
            if user_messages:
                current_message = user_messages[-1]["content"]
        
        if not current_message:
            current_message = "hello"  # Default greeting
        
        # USE SMART ROUTER FIRST (saves 70%+ API calls)
        try:
            from improvements.smart_router import smart_router
            from improvements.conversation_flow import flow_manager
            
            # Try smart routing first
            smart_result = smart_router.route_message(state["session_id"], current_message, state)
            
            if smart_result.get("routing_method") != "llm_fallback":
                # Smart router handled it - no API call needed!
                log_action("SMART_ROUTING", 
                          f"Routed via {smart_result['routing_method']}: {smart_result['target_agent']}", 
                          session_id=state["session_id"])
                
                # Apply the routing
                updated_state = smart_result["updated_state"]
                
                # Track performance
                response_time = (datetime.now() - start_time).total_seconds()
                updated_state["response_times"] = state.get("response_times", {})
                updated_state["response_times"]["router"] = response_time
                
                return updated_state
            
        except ImportError:
            # Fallback to original routing if smart router not available
            pass
        
        # PREVENT DUPLICATE PROCESSING - Critical Fix
        if state.get("_processing_router", False):
            log_action("SKIP_DUPLICATE", "Preventing duplicate router processing", session_id=state["session_id"])
            return state
        
        state["_processing_router"] = True
        
        # Check if we're in the middle of a conversation that should bypass routing
        conversation_state = state.get("conversation_state")
        active_agent = state.get("active_agent")
        
        # MEMORY CONTINUITY FIX - Check if user wants to continue with collected data
        if (conversation_state == ConversationState.COLLECTING_USER_DATA.value and 
            active_agent == AgentType.USER_MANAGEMENT.value):
            
            # Check if user is asking to proceed with previously provided data
            proceed_phrases = ["add that", "create", "finish", "do it", "proceed", "yes", "confirm", "continue", "go ahead"]
            if any(phrase in current_message.lower() for phrase in proceed_phrases):
                log_action("MEMORY_CONTINUITY", f"Continuing with collected data: {current_message[:50]}...", 
                          session_id=state["session_id"])
                state["_processing_router"] = False
                return self._route_to_agent_type(state, AgentType.USER_MANAGEMENT)
        
        # Check if this looks like user data continuation
        def looks_like_user_data(msg):
            # First, check for explicit agent routing requests (with typo tolerance)
            agent_requests = [
                r'\bconversation\s+manager\b',
                r'\bservice\s+management\b', 
                r'\bservice\b.*\bmanagement\b',  # flexible service management
                r'\bsrvice\b',  # common typo
                r'\bmanagement\b',  # standalone management
                r'\bknowledge\s+base\b',
                r'\btroubleshoot\b',
                r'\bfaq\b',
                r'\bhelp\b.*\bwith\b',
                r'\bwhat.*about.*service\b',
                r'\bgo\s+to\b',
                r'\broute\s+to\b',
                r'\bswitch\s+to\b'
            ]
            
            # If this is an explicit agent request, don't treat as user data
            if any(re.search(pattern, msg, re.IGNORECASE) for pattern in agent_requests):
                return False
            
            # More specific patterns for actual user data - avoid false positives
            patterns = [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
                r'name\s*[:=]\s*\w+',  # "name: John" or "name = John"
                r'email\s*[:=]\s*\S+@\S+',  # "email: john@mail.com"
                r'phone\s*[:=]\s*[\d\s\-\(\)]+',  # "phone: 123-456-7890"
                r'role\s*[:=]\s*\w+',  # "role: manager"
                r'department\s*[:=]\s*\w+',  # "department: FO"
                r',.*@.*\.com',  # comma-separated with email
                r'\bname\s+is\b|\bhis\s+name\b|\bher\s+name\b',  # explicit name indicators
            ]
            return any(re.search(pattern, msg, re.IGNORECASE) for pattern in patterns)
        
        # EFFICIENT ROUTING LOGIC
        # 1. Check for explicit agent switching first (highest priority)
        explicit_agent_switch = self._check_explicit_agent_switch(current_message)
        
        if explicit_agent_switch:
            log_action("EXPLICIT_ROUTING", f"Explicit agent switch detected: {explicit_agent_switch}", 
                      session_id=state["session_id"])
            # Force route through router for new agent
            updated_state = router_agent.process_message(state, current_message)
        
        # 2. If we're in critical conversation states, continue ONLY if it's not a topic switch
        elif (conversation_state in [ConversationState.CONFIRMATION_PENDING.value, ConversationState.DATA_COLLECTION.value] or
              (conversation_state == ConversationState.COLLECTING_USER_DATA.value and 
               not self._indicates_topic_switch(current_message, active_agent) and
               looks_like_user_data(current_message))):
            if active_agent == "user_management":
                log_action("DIRECT_ROUTING", f"Continuing user_management (state: {conversation_state})", 
                          session_id=state["session_id"])
                updated_state = user_management_agent.process_user_request(state, current_message)
            else:
                updated_state = router_agent.process_message(state, current_message)
        
        # 3. Check if message indicates topic switch (medium priority)
        elif self._indicates_topic_switch(current_message, active_agent):
            log_action("TOPIC_SWITCH", f"Topic switch detected from {active_agent}: {current_message[:50]}...", 
                      session_id=state["session_id"])
            updated_state = router_agent.process_message(state, current_message)
        
        # 4. If previous agent was user_management and this looks like user data, continue
        elif active_agent == "user_management" and looks_like_user_data(current_message):
            log_action("CONTEXT_ROUTING", f"Continuing user management - user data: {current_message[:50]}...", 
                      session_id=state["session_id"])
            updated_state = user_management_agent.process_user_request(state, current_message)
        
        # 5. Default: Route through router for new conversations
        else:
            updated_state = router_agent.process_message(state, current_message)
        
        # Track router performance
        response_time = (datetime.now() - start_time).total_seconds()
        active_agent = updated_state.get("active_agent")
        
        if active_agent:
            # active_agent is stored as string value, not enum
            agent_name = active_agent if isinstance(active_agent, str) else active_agent.value
            if agent_name not in self.system_stats["agent_usage"]:
                self.system_stats["agent_usage"][agent_name] = 0
            self.system_stats["agent_usage"][agent_name] += 1
        
        # Update response times
        if "response_times" not in updated_state:
            updated_state["response_times"] = {}
        updated_state["response_times"]["router"] = response_time
        
        # Cleanup processing flag
        if "_processing_router" in updated_state:
            del updated_state["_processing_router"]
        
        return updated_state
    
    def _user_management_node(self, state: ChatState) -> ChatState:
        """Handle user management operations"""
        
        start_time = datetime.now()
        
        # Get current message
        current_message = state.get("query", "")
        if not current_message and state.get("messages"):
            user_messages = [msg for msg in state["messages"] if msg["role"] == "user"]
            if user_messages:
                current_message = user_messages[-1]["content"]
        
        # Process through user management agent
        updated_state = user_management_agent.process_user_request(state, current_message)
        
        # Track performance
        response_time = (datetime.now() - start_time).total_seconds()
        updated_state["response_times"]["user_management"] = response_time
        
        return updated_state
    
    def _service_management_node(self, state: ChatState) -> ChatState:
        """Handle service management operations (placeholder for now)"""
        
        # TODO: Implement service management agent
        
        response = (
            "🔧 **Service Management**\n\n"
            "Service management features are coming soon! For now, I can help you with:\n"
            "• User management (create, update, delete users)\n"
            "• FAQ and troubleshooting\n"
            "• General HotelOpsAI guidance\n\n"
            "How else can I assist you?"
        )
        
        updated_state = add_message_to_state(
            state, response, "assistant",
            agent_id="service_management"
        )
        
        return transition_conversation_state(
            updated_state, ConversationState.IDLE,
            reason="Service management placeholder response"
        )
    
    def _knowledge_base_node(self, state: ChatState) -> ChatState:
        """Handle FAQ and knowledge base queries"""
        
        start_time = datetime.now()
        
        # Get query from state
        query = state.get("query", "")
        if not query and state.get("messages"):
            user_messages = [msg for msg in state["messages"] if msg["role"] == "user"]
            if user_messages:
                query = user_messages[-1]["content"]
        
        try:
            # Search FAQ first
            faq_results = faq_tools.search_faq(query, limit=3)
            
            if faq_results:
                # Format FAQ response
                if len(faq_results) == 1 and faq_results[0].get("relevance_score", 0) > 3:
                    # High confidence single result - direct answer
                    faq = faq_results[0]
                    response = f"**{faq['question']}**\n\n{faq['answer']}"
                else:
                    # Multiple results - formatted list
                    response_parts = [f"💡 **Found {len(faq_results)} relevant answer(s):**\n"]
                    
                    for i, faq in enumerate(faq_results[:3], 1):
                        response_parts.append(
                            f"**{i}. {faq['question']}**\n"
                            f"{faq['answer']}\n"
                        )
                    
                    response = "\n".join(response_parts)
            else:
                # No FAQ results - try troubleshooting
                troubleshoot_result = troubleshooting.get_troubleshooting(query)
                
                if troubleshoot_result:
                    response = f"🔧 **Troubleshooting Help:**\n\n{troubleshoot_result}"
                else:
                    # Use AI for general response
                    prompt = f"""
                    As a HotelOpsAI assistant, help with this query: {query}
                    
                    Provide helpful, specific guidance related to hotel operations and management.
                    Keep the response concise and actionable.
                    """
                    
                    response = ask_gemini(prompt)
            
            # Add response to state
            updated_state = add_message_to_state(
                state, response, "assistant",
                agent_id="knowledge_base"
            )
            
            # Track performance
            response_time = (datetime.now() - start_time).total_seconds()
            updated_state["response_times"]["knowledge_base"] = response_time
            
            return transition_conversation_state(
                updated_state, ConversationState.IDLE,
                reason="Knowledge base query completed"
            )
            
        except Exception as e:
            error_msg = f"Knowledge base error: {str(e)}"
            log_error("KB_ERROR", error_msg, session_id=state["session_id"])
            
            error_response = "I encountered an error while searching for information. Please try rephrasing your question."
            
            updated_state = add_message_to_state(
                state, error_response, "assistant",
                agent_id="knowledge_base"
            )
            
            return transition_conversation_state(
                updated_state, ConversationState.ERROR_RECOVERY,
                reason="Knowledge base error"
            )
    
    def _conversation_manager_node(self, state: ChatState) -> ChatState:
        """Handle general conversation management and fallback responses"""
        
        start_time = datetime.now()
        
        # Get current message
        current_message = state.get("query", "")
        if not current_message and state.get("messages"):
            user_messages = [msg for msg in state["messages"] if msg["role"] == "user"]
            if user_messages:
                current_message = user_messages[-1]["content"]
        
        # Use the dedicated conversation manager
        updated_state = conversation_manager.handle_conversation(state, current_message)
        
        # Track performance
        response_time = (datetime.now() - start_time).total_seconds()
        updated_state["response_times"]["conversation_manager"] = response_time
        
        return updated_state
    
    def _data_extraction_node(self, state: ChatState) -> ChatState:
        """Process data extraction requests"""
        
        # This node is typically called by other agents, not directly
        # It's included for completeness and future use
        
        query = state.get("query", "")
        operation_type = state.get("user_operation", {}).get("operation_type", "user_create")
        
        # Extract entities
        updated_state = data_extraction_agent.extract_entities(query, operation_type, state)
        
        return updated_state
    
    def _response_generator_node(self, state: ChatState) -> ChatState:
        """Generate final response and format output"""
        
        # Check if we already have a response from an agent
        if state.get("messages") and state["messages"][-1]["role"] == "assistant":
            # Response already generated by agent
            return state
        
        # Generate a fallback response
        response = "I've processed your request. How else can I help you?"
        
        updated_state = add_message_to_state(
            state, response, "assistant",
            agent_id="response_generator"
        )
        
        return updated_state
    
    def _error_handler_node(self, state: ChatState) -> ChatState:
        """Handle errors and provide recovery options"""
        
        last_error = state.get("last_error", "An unexpected error occurred.")
        retry_count = state.get("retry_count", 0)
        
        if retry_count < state.get("max_retries", 3):
            response = (
                f"⚠️ **I encountered an issue**: {last_error}\n\n"
                "Let me try to help you in a different way. "
                "Could you please rephrase your request or try again?"
            )
        else:
            response = (
                "❌ **I'm having trouble processing your request** after multiple attempts.\n\n"
                "Please try:\n"
                "• Simplifying your request\n"
                "• Asking about something else\n"
                "• Contacting system support if the issue persists\n\n"
                "How else can I assist you?"
            )
        
        updated_state = add_message_to_state(
            state, response, "assistant",
            agent_id="error_handler"
        )
        
        return transition_conversation_state(
            updated_state, ConversationState.IDLE,
            reason="Error handled"
        )
    
    def _save_session_node(self, state: ChatState) -> ChatState:
        """Save session state and conversation data"""
        
        session_id = state.get("session_id")
        
        if session_id:
            # Save session data
            session_data = {
                "session_id": session_id,
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
                "conversation_state": state.get("conversation_state", ConversationState.IDLE.value),
                "active_agent": state.get("active_agent"),
                "user_operation": state.get("user_operation"),
                "service_operation": state.get("service_operation"),
                "extracted_data": state.get("extracted_data", {}),
                "last_updated": datetime.now().isoformat()
            }
            
            db_adapter.save_session(session_id, session_data)
            
            # Save conversation
            if state.get("conversation_id"):
                conversation_data = {
                    "conversation_id": state["conversation_id"],
                    "session_id": session_id,
                    "user_id": state.get("user_id"),
                    "messages": state.get("messages", []),
                    "created_at": state.get("created_at"),
                    "updated_at": datetime.now().isoformat()
                }
                
                db_adapter.save_conversation(state["conversation_id"], conversation_data)
        
        log_action("SESSION_SAVED", f"Session {session_id} saved", session_id=session_id)
        
        return state
    
    # === ROUTING LOGIC ===
    
    def _route_to_agent(self, state: ChatState) -> str:
        """Determine which agent to route to based on state"""
        
        active_agent_str = state.get("active_agent")
        conversation_state = state.get("conversation_state")
        
        # Handle errors
        if state.get("last_error") and state.get("retry_count", 0) >= state.get("max_retries", 3):
            return "error_handler"
        
        # Route based on active agent string value
        if active_agent_str == "user_management":
            return "user_management"
        elif active_agent_str == "service_management":
            return "service_management"
        elif active_agent_str == "knowledge_base":
            return "knowledge_base"
        elif active_agent_str == "data_extraction":
            return "data_extraction"
        elif active_agent_str == "conversation_manager":
            return "conversation_manager"
        else:
            # Default to conversation manager
            return "conversation_manager"
    
    def _determine_next_step(self, state: ChatState) -> str:
        """Determine next step after agent processing"""
        
        conversation_state = state.get("conversation_state")
        
        # Check for errors
        if state.get("last_error"):
            return "error"
        
        # Check if conversation is complete
        if conversation_state == ConversationState.IDLE:
            return "save_and_end"
        
        # Check if we need to continue conversation
        if conversation_state in [
            ConversationState.DATA_COLLECTION,
            ConversationState.CONFIRMATION_PENDING,
            ConversationState.OPERATION_EXECUTION
        ]:
            return "generate_response"
        
        # Default to save and end
        return "save_and_end"
    
    def _after_response(self, state: ChatState) -> str:
        """Determine flow after response generation"""
        
        conversation_state = state.get("conversation_state")
        
        # If still in active conversation, continue
        if conversation_state in [
            ConversationState.DATA_COLLECTION,
            ConversationState.CONFIRMATION_PENDING
        ]:
            return "continue"
        
        # Otherwise end conversation
        return "end"
    
    # === PUBLIC INTERFACE ===
    
    def process_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """
        Main entry point for processing user messages
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message: User message
            
        Returns:
            Processing result with response and metadata
        """
        
        start_time = datetime.now()
        
        try:
            # Create initial state
            initial_state = create_initial_state(user_id, session_id)
            initial_state["query"] = message
            
            # Add user message to state
            initial_state = add_message_to_state(
                initial_state, message, "user"
            )
            
            # Process through the graph
            result_state = self.graph.invoke(initial_state)
            
            # Extract response
            response = "I'm sorry, I couldn't process your request."
            if result_state.get("messages"):
                assistant_messages = [
                    msg for msg in result_state["messages"] 
                    if msg["role"] == "assistant"
                ]
                if assistant_messages:
                    response = assistant_messages[-1]["content"]
            
            # Calculate metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self.system_stats["successful_conversations"] += 1
            
            # Update average response time
            total_convs = self.system_stats["total_conversations"]
            current_avg = self.system_stats["average_response_time"]
            self.system_stats["average_response_time"] = \
                ((current_avg * (total_convs - 1)) + response_time) / total_convs
            
            return {
                "response": response,
                "session_id": session_id,
                "conversation_id": result_state.get("conversation_id"),
                "conversation_state": result_state.get("conversation_state", ConversationState.IDLE.value),
                "active_agent": result_state.get("active_agent"),
                "response_time": response_time,
                "success": True
            }
            
        except Exception as e:
            error_msg = f"Multi-agent processing failed: {str(e)}"
            log_error("MULTI_AGENT_ERROR", error_msg, session_id=session_id)
            
            return {
                "response": "I encountered an error while processing your request. Please try again.",
                "session_id": session_id,
                "conversation_id": None,
                "conversation_state": ConversationState.ERROR_RECOVERY.value,
                "active_agent": None,
                "response_time": (datetime.now() - start_time).total_seconds(),
                "success": False,
                "error": error_msg
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        
        success_rate = 0.0
        if self.system_stats["total_conversations"] > 0:
            success_rate = self.system_stats["successful_conversations"] / self.system_stats["total_conversations"]
        
        return {
            **self.system_stats,
            "success_rate": success_rate
        }
    
    def reset_stats(self):
        """Reset system statistics"""
        
        self.system_stats = {
            "total_conversations": 0,
            "successful_conversations": 0,
            "agent_usage": {},
            "average_response_time": 0.0
        }

# Initialize the multi-agent system
multi_agent_system = MultiAgentSystem()
