"""
HotelOpsAI Router Agent - Intent Classification & Agent Routing
Senior AI Engineer Implementation

The Router Agent is the entry point for all conversations. It:
1. Classifies user intent with confidence scoring
2. Routes to appropriate specialized agents
3. Handles context switching between agents
4. Manages conversation flow control
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from .state_schema import (
    ChatState, AgentType, IntentType, ConversationState,
    set_active_agent, transition_conversation_state, 
    add_message_to_state, log_error_to_state
)
from llm_utils import ask_gemini
from logger_config import agent_logger, log_action, log_error

class RouterAgent:
    """
    Advanced Router Agent with ML-based intent classification
    and sophisticated routing logic
    """
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.confidence_threshold = 0.7
        self.min_confidence_for_routing = 0.5
        
        # Performance tracking
        self.routing_stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "intent_accuracy": {}
        }
        
        agent_logger.info("Router Agent initialized with intent classification capabilities")
    
    def _initialize_intent_patterns(self) -> Dict[IntentType, Dict]:
        """Initialize comprehensive intent classification patterns"""
        
        return {
            # USER MANAGEMENT INTENTS
            IntentType.USER_CREATE: {
                "keywords": [
                    "add user", "create user", "new user", "register user",
                    "add account", "create account", "new account",
                    "add employee", "hire", "onboard", "add staff",
                    "add him", "add her", "add this person", "add contact"
                ],
                "patterns": [
                    r"add\s+(?:a\s+)?(?:new\s+)?user",
                    r"create\s+(?:a\s+)?(?:new\s+)?user",
                    r"i\s+(?:want\s+to\s+|wanna\s+|need\s+to\s+)?add",
                    r"(?:john|jane|[a-z]+)\s*,\s*[\w\.-]+@[\w\.-]+",  # Structured data
                    r"register\s+(?:new\s+)?(?:user|employee|staff)"
                ],
                "context_clues": ["email", "phone", "name", "role", "department"],
                "weight": 1.0
            },
            
            IntentType.USER_UPDATE: {
                "keywords": [
                    "update user", "edit user", "modify user", "change user",
                    "update profile", "edit profile", "change details",
                    "update info", "edit info", "modify details"
                ],
                "patterns": [
                    r"(?:update|edit|modify|change)\s+(?:user|profile|account)",
                    r"change\s+(?:the\s+)?(?:email|phone|role|name)",
                    r"update\s+(?:his|her|their)\s+(?:info|details|profile)"
                ],
                "context_clues": ["user id", "email", "existing", "current"],
                "weight": 0.9
            },
            
            IntentType.USER_DELETE: {
                "keywords": [
                    "delete user", "remove user", "deactivate user",
                    "disable user", "terminate user", "remove account"
                ],
                "patterns": [
                    r"(?:delete|remove|deactivate|disable)\s+(?:user|account)",
                    r"terminate\s+(?:user|employee|access)",
                    r"remove\s+(?:him|her|this\s+user)"
                ],
                "context_clues": ["delete", "remove", "terminate", "disable"],
                "weight": 0.95
            },
            
            IntentType.USER_LIST: {
                "keywords": [
                    "list users", "show users", "all users", "user list",
                    "view users", "see users", "display users"
                ],
                "patterns": [
                    r"(?:list|show|display|view)\s+(?:all\s+)?users",
                    r"(?:see|get)\s+(?:all\s+)?(?:user\s+)?list",
                    r"who\s+are\s+(?:all\s+)?(?:the\s+)?users"
                ],
                "context_clues": ["list", "all", "show", "display"],
                "weight": 0.8
            },
            
            IntentType.USER_SEARCH: {
                "keywords": [
                    "find user", "search user", "look for user",
                    "find person", "search for", "locate user"
                ],
                "patterns": [
                    r"(?:find|search|look\s+for|locate)\s+(?:user|person)",
                    r"where\s+is\s+(?:user|person|employee)",
                    r"search\s+(?:for\s+)?[\w\.-]+@[\w\.-]+"  # Search by email
                ],
                "context_clues": ["find", "search", "where", "locate"],
                "weight": 0.7
            },
            
            # SERVICE MANAGEMENT INTENTS
            IntentType.SERVICE_ADD: {
                "keywords": [
                    "add service", "create service", "new service",
                    "add work order", "create task", "new task",
                    "add request", "create request", "service request"
                ],
                "patterns": [
                    r"(?:add|create|new)\s+(?:service|work\s+order|task|request)",
                    r"(?:need\s+)?(?:to\s+)?(?:add|create)\s+(?:a\s+)?service",
                    r"service\s+(?:for|request)"
                ],
                "context_clues": ["service", "work order", "task", "maintenance"],
                "weight": 0.9
            },
            
            IntentType.SERVICE_LIST: {
                "keywords": [
                    "list services", "show services", "all services",
                    "view services", "service list", "see services"
                ],
                "patterns": [
                    r"(?:list|show|display|view)\s+(?:all\s+)?services",
                    r"(?:see|get)\s+(?:service\s+)?list",
                    r"what\s+services\s+(?:are\s+)?(?:available|there)"
                ],
                "context_clues": ["services", "list", "all", "available"],
                "weight": 0.8
            },
            
            # KNOWLEDGE BASE INTENTS
            IntentType.KNOWLEDGE_QUERY: {
                "keywords": [
                    "how to", "what is", "how do i", "what does",
                    "explain", "tell me about", "help with",
                    "guide", "tutorial", "instructions"
                ],
                "patterns": [
                    r"(?:how\s+(?:to|do\s+i)|what\s+(?:is|does)|explain)",
                    r"(?:tell\s+me\s+about|help\s+with|guide\s+(?:me\s+)?(?:to|on))",
                    r"(?:instructions|tutorial|steps)\s+(?:for|to|on)",
                    r"(?:can\s+you\s+)?(?:explain|show\s+me|help)"
                ],
                "context_clues": ["how", "what", "explain", "help", "guide"],
                "weight": 0.8
            },
            
            IntentType.TROUBLESHOOTING: {
                "keywords": [
                    "problem", "issue", "error", "not working",
                    "broken", "fix", "trouble", "help",
                    "can't", "won't", "doesn't work"
                ],
                "patterns": [
                    r"(?:problem|issue|error|trouble)\s+with",
                    r"(?:not\s+working|broken|doesn't\s+work)",
                    r"(?:can't|won't|unable\s+to)",
                    r"(?:fix|solve|resolve)\s+(?:this|the|my)"
                ],
                "context_clues": ["problem", "error", "broken", "fix", "help"],
                "weight": 0.9
            },
            
            # GENERAL INTENTS
            IntentType.GREETING: {
                "keywords": [
                    "hello", "hi", "hey", "good morning", "good afternoon",
                    "good evening", "greetings", "what's up", "howdy"
                ],
                "patterns": [
                    r"^(?:hello|hi|hey|greetings)(?:\s+there|!|\.|,)?$",
                    r"^good\s+(?:morning|afternoon|evening)",
                    r"^(?:what's\s+up|how\s+are\s+you|howdy)"
                ],
                "context_clues": ["greeting", "hello", "hi"],
                "weight": 0.6
            },
            
            IntentType.HANDOFF_REQUEST: {
                "keywords": [
                    "talk to human", "speak to person", "human support",
                    "escalate", "supervisor", "manager", "agent",
                    "conversation manager", "go to", "switch to", "route to"
                ],
                "patterns": [
                    r"(?:talk\s+to|speak\s+to|connect\s+me\s+to)\s+(?:human|person|agent)",
                    r"(?:human\s+support|live\s+support|real\s+person)",
                    r"(?:escalate|supervisor|manager|representative)",
                    r"(?:go\s+to|switch\s+to|route\s+to)\s+(?:conversation\s+)?manager",
                    r"conversation\s+manager",
                    r"(?:take\s+me\s+to|bring\s+me\s+to)\s+(?:conversation\s+)?manager"
                ],
                "context_clues": ["human", "person", "escalate", "supervisor", "conversation", "manager", "go to", "switch"],
                "weight": 1.0
            }
        }
    
    def process_message(self, state: ChatState, message: str) -> ChatState:
        """
        Main entry point for router agent processing
        
        Flow:
        1. Analyze message for intent
        2. Calculate confidence scores
        3. Route to appropriate agent
        4. Update conversation state
        """
        
        log_action("ROUTER_PROCESS", f"Processing message: {message[:100]}", 
                  session_id=state["session_id"])
        
        try:
            # EFFICIENCY OPTIMIZATION - Skip API for obvious cases
            try:
                from efficiency.simple_optimizations import efficiency_optimizer
                
                # Try lightning-fast routing first
                fast_result = efficiency_optimizer.fast_route(message)
                if fast_result:
                    log_action("FAST_ROUTE", 
                              f"⚡ {fast_result['method']}: {message} → {fast_result['agent']}", 
                              session_id=state["session_id"])
                    
                    # Create optimized state without API call
                    optimized_state = state.copy()
                    optimized_state["active_agent"] = fast_result["agent"]
                    optimized_state["current_intent"] = "fast_routed"
                    optimized_state["intent_confidence"] = fast_result["confidence"]
                    optimized_state["api_saved"] = True
                    
                    return optimized_state
                
                # Check conversation flow optimization
                current_agent = state.get("active_agent", "conversation_manager")
                flow_agent = efficiency_optimizer.optimize_conversation_flow(message, current_agent)
                if flow_agent:
                    log_action("FLOW_OPTIMIZED", 
                              f"🔄 Flow continuation: {message} → {flow_agent}", 
                              session_id=state["session_id"])
                    
                    optimized_state = state.copy()
                    optimized_state["active_agent"] = flow_agent
                    optimized_state["current_intent"] = "flow_continuation"
                    optimized_state["intent_confidence"] = 0.9
                    optimized_state["api_saved"] = True
                    
                    return optimized_state
                    
            except (ImportError, Exception):
                pass  # Efficiency optimization not available, continue with normal routing
            
            # Add user message to state
            updated_state = add_message_to_state(
                state, message, "user", 
                metadata={"router_processing": True}
            )
            
            # Classify intent
            intent_result = self._classify_intent(message, updated_state)
            
            # Update state with intent classification
            intent = intent_result["intent"]
            # Ensure intent is stored as string value for state serialization
            updated_state["current_intent"] = intent.value if intent else None
            updated_state["intent_confidence"] = intent_result["confidence"]
            
            # Route to appropriate agent
            routed_state = self._route_to_agent(updated_state, intent_result)
            
            # Cache this API result for future use
            try:
                from improvements.simple_flow_enhancer import flow_enhancer
                flow_enhancer.cache_api_result(message, routed_state)
            except (ImportError, Exception):
                pass  # Caching not available
            
            # Log routing decision
            intent_name = intent.value if intent else 'None'
            # active_agent is now stored as string value, not enum
            agent_name = routed_state.get('active_agent', 'None')
            log_action("ROUTER_DECISION", 
                      f"Intent: {intent_name}, "
                      f"Confidence: {intent_result['confidence']:.2f}, "
                      f"Agent: {agent_name}",
                      session_id=state["session_id"])
            
            self.routing_stats["total_routes"] += 1
            self.routing_stats["successful_routes"] += 1
            
            return routed_state
            
        except Exception as e:
            import traceback
            error_msg = f"Router processing failed: {str(e)}"
            full_traceback = traceback.format_exc()
            
            log_error("ROUTER_ERROR", error_msg, session_id=state["session_id"])
            agent_logger.error(f"Full router error traceback:\n{full_traceback}")
            
            # Debug: Log the exact state that caused the error
            agent_logger.error(f"Error occurred with state keys: {list(state.keys())}")
            if 'intent_result' in locals():
                agent_logger.error(f"Intent result: {intent_result}")
                agent_logger.error(f"Intent type: {type(intent_result.get('intent'))}")
            agent_logger.error(f"Active agent in state: {state.get('active_agent')} (type: {type(state.get('active_agent'))})")
            
            self.routing_stats["failed_routes"] += 1
            
            # Return state with error logged and fallback agent
            fallback_state = log_error_to_state(
                state, error_msg, "router_error", 
                agent_id="router", recoverable=True
            )
            
            # Ensure we have a fallback agent set as string
            fallback_state["active_agent"] = "conversation_manager"
            fallback_state["conversation_state"] = "error_recovery"
            
            return fallback_state
    
    def _classify_intent(self, message: str, state: ChatState) -> Dict:
        """
        Comprehensive intent classification using multiple methods:
        1. Pattern matching
        2. Keyword analysis
        3. Context awareness
        4. ML-based classification (via LLM)
        """
        
        message_lower = message.lower().strip()
        
        # Method 1: Pattern-based classification
        pattern_results = self._pattern_based_classification(message_lower)
        
        # Method 2: Keyword-based classification
        keyword_results = self._keyword_based_classification(message_lower)
        
        # Method 3: Context-aware classification
        context_results = self._context_aware_classification(message_lower, state)
        
        # Method 4: Structured data detection
        structured_results = self._structured_data_classification(message)
        
        # Combine results with weighted scoring
        combined_scores = self._combine_classification_results(
            pattern_results, keyword_results, context_results, structured_results
        )
        
        # Get best intent
        best_intent, confidence = self._get_best_intent(combined_scores)
        
        # If confidence is low, use LLM for additional classification
        if confidence < self.confidence_threshold:
            llm_result = self._llm_based_classification(message, state)
            if llm_result["confidence"] > confidence:
                best_intent = llm_result["intent"]
                confidence = llm_result["confidence"]
        
        agent_logger.info(f"Intent classification: {best_intent.value if best_intent else 'None'} "
                         f"(confidence: {confidence:.2f})")
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "method": "hybrid",
            "all_scores": combined_scores
        }
    
    def _pattern_based_classification(self, message: str) -> Dict[IntentType, float]:
        """Classify intent using regex patterns"""
        
        scores = {}
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            pattern_matches = 0
            
            for pattern in config.get("patterns", []):
                if re.search(pattern, message, re.IGNORECASE):
                    pattern_matches += 1
                    score += 0.3  # Each pattern match adds to score
            
            if pattern_matches > 0:
                scores[intent] = min(score * config["weight"], 1.0)
        
        return scores
    
    def _keyword_based_classification(self, message: str) -> Dict[IntentType, float]:
        """Classify intent using keyword matching"""
        
        scores = {}
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in config.get("keywords", []):
                if keyword in message:
                    keyword_matches += 1
                    score += 0.2  # Each keyword match adds to score
            
            if keyword_matches > 0:
                scores[intent] = min(score * config["weight"], 1.0)
        
        return scores
    
    def _context_aware_classification(self, message: str, state: ChatState) -> Dict[IntentType, float]:
        """Classify intent based on conversation context"""
        
        scores = {}
        
        # Check for context clues in recent messages
        recent_messages = state["messages"][-3:] if len(state["messages"]) > 3 else state["messages"]
        context_text = " ".join([msg["content"] for msg in recent_messages])
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            
            for clue in config.get("context_clues", []):
                if clue in message or clue in context_text.lower():
                    score += 0.1
            
            # Boost score based on current conversation state
            if state["conversation_state"] == ConversationState.DATA_COLLECTION:
                if intent in [IntentType.USER_CREATE, IntentType.USER_UPDATE, IntentType.SERVICE_ADD]:
                    score += 0.3
            
            if score > 0:
                scores[intent] = min(score * config["weight"], 1.0)
        
        return scores
    
    def _structured_data_classification(self, message: str) -> Dict[IntentType, float]:
        """Detect structured data patterns (like CSV-style input)"""
        
        scores = {}
        
        # Check for email patterns (strong indicator of user data)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        
        has_email = bool(re.search(email_pattern, message))
        has_phone = bool(re.search(phone_pattern, message))
        has_commas = ',' in message
        
        # Structured user data detection
        if has_email and (has_commas or has_phone):
            scores[IntentType.USER_CREATE] = 0.9
        
        # Name patterns
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        if re.search(name_pattern, message) and (has_email or has_phone):
            scores[IntentType.USER_CREATE] = scores.get(IntentType.USER_CREATE, 0) + 0.3
        
        return scores
    
    def _llm_based_classification(self, message: str, state: ChatState) -> Dict:
        """Use LLM for advanced intent classification when other methods are uncertain"""
        
        try:
            # Create classification prompt
            intent_options = [intent.value for intent in IntentType]
            
            prompt = f"""
            You are an expert at understanding user intent in a hotel management system. Classify this message accurately.

            Message: "{message}"

            INTENT CLASSIFICATION RULES:
            
            🔹 **greeting** - Use for: "hi", "hello", "how are you", "hey", "dude", casual greetings, "what's up"
            🔹 **user_create** - Use for: "create user", "add user", "new user", providing user details (names, emails, roles), continuing user creation conversations
            🔹 **user_update** - Use for: "update user", "edit user", "modify user", "change user details"
            🔹 **user_delete** - Use for: "delete user", "remove user", "deactivate user"
            🔹 **user_list** - Use for: "list users", "show users", "all users", "user list"
            🔹 **user_search** - Use for: "find user", "search user", "look for user"
            🔹 **service_add** - Use for: "add service", "create service", "new service"
            🔹 **knowledge_query** - Use for: actual questions about HotelOpsAI features, "how to", technical questions
            🔹 **troubleshooting** - Use for: "problem", "error", "issue", "not working", "help with"
            🔹 **handoff_request** - Use ONLY for explicit requests: "speak to human", "transfer to agent", "need human help"
            🔹 **unclear** - Use for: ambiguous messages that don't fit any category

            CRITICAL RULES: 
            - If someone provides user details (name, email, role), it's **user_create**, NOT handoff_request
            - Context matters: if they were creating a user, continue with user_create
            - "his name is John, email john@mail.com" = **user_create**
            - "he's a manager named John" = **user_create** (providing user details)
            - "ok..he's a manager of engineering named Federic" = **user_create** (user details)
            - Don't classify data as handoff_request just because it mentions "he's", "she's", "manager", or casual language
            - Only use handoff_request for EXPLICIT requests to talk to humans/agents
            - Be intelligent about context - follow the conversation flow
            - Personal pronouns (he, she, his, her) usually indicate user data provision, not handoff requests

            Available intents: {', '.join(intent_options)}

            Recent conversation context:
            {self._get_conversation_context(state)}

            Respond with JSON format:
            {{
                "intent": "most_likely_intent",
                "confidence": 0.85,
                "reasoning": "brief explanation"
            }}
            """
            
            response = ask_gemini(prompt)
            
            # Parse JSON response with better error handling
            try:
                # Clean the response - sometimes LLM adds extra text
                response_clean = response.strip()
                
                # Try to extract JSON if wrapped in markdown
                if "```json" in response_clean:
                    start = response_clean.find("```json") + 7
                    end = response_clean.find("```", start)
                    if end > start:
                        response_clean = response_clean[start:end].strip()
                elif "```" in response_clean:
                    start = response_clean.find("```") + 3
                    end = response_clean.find("```", start)
                    if end > start:
                        response_clean = response_clean[start:end].strip()
                
                # Parse JSON
                result = json.loads(response_clean)
                intent_str = result.get("intent", "unclear")
                confidence = float(result.get("confidence", 0.0))
                
                # Convert string to IntentType
                intent = None
                for intent_enum in IntentType:
                    if intent_enum.value == intent_str:
                        intent = intent_enum
                        break
                
                if not intent:
                    intent = IntentType.UNCLEAR
                    confidence = 0.0
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "reasoning": result.get("reasoning", "")
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                agent_logger.warning(f"Failed to parse LLM classification response: {e}")
                agent_logger.warning(f"Response was: {response[:200]}...")
                
                # Fallback: try to extract intent from text
                response_lower = response.lower()
                
                if "greeting" in response_lower:
                    return {"intent": IntentType.GREETING, "confidence": 0.7}
                elif "user" in response_lower and ("create" in response_lower or "add" in response_lower):
                    return {"intent": IntentType.USER_CREATE, "confidence": 0.6}
                elif "knowledge" in response_lower or "question" in response_lower:
                    return {"intent": IntentType.KNOWLEDGE_QUERY, "confidence": 0.6}
                else:
                    return {"intent": IntentType.UNCLEAR, "confidence": 0.0}
                
        except Exception as e:
            agent_logger.error(f"LLM classification failed: {e}")
            return {"intent": IntentType.UNCLEAR, "confidence": 0.0}
    
    def _combine_classification_results(self, *result_sets) -> Dict[IntentType, float]:
        """Combine multiple classification results with weighted scoring"""
        
        combined_scores = {}
        
        for results in result_sets:
            for intent, score in results.items():
                if intent not in combined_scores:
                    combined_scores[intent] = 0.0
                combined_scores[intent] += score
        
        # Normalize scores
        max_score = max(combined_scores.values()) if combined_scores else 1.0
        if max_score > 0:
            for intent in combined_scores:
                combined_scores[intent] = min(combined_scores[intent] / max_score, 1.0)
        
        return combined_scores
    
    def _get_best_intent(self, scores: Dict[IntentType, float]) -> Tuple[Optional[IntentType], float]:
        """Get the highest scoring intent"""
        
        if not scores:
            return IntentType.UNCLEAR, 0.0
        
        best_intent = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_intent]
        
        # If confidence is too low, classify as unclear
        if confidence < self.min_confidence_for_routing:
            return IntentType.UNCLEAR, confidence
        
        return best_intent, confidence
    
    def _route_to_agent(self, state: ChatState, intent_result: Dict) -> ChatState:
        """Route conversation to appropriate specialized agent"""
        
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # Define agent routing rules - handle both enum and None cases
        agent_routing = {}
        if intent:
            agent_routing = {
                IntentType.USER_CREATE: AgentType.USER_MANAGEMENT,
                IntentType.USER_UPDATE: AgentType.USER_MANAGEMENT,
                IntentType.USER_DELETE: AgentType.USER_MANAGEMENT,
                IntentType.USER_LIST: AgentType.USER_MANAGEMENT,
                IntentType.USER_SEARCH: AgentType.USER_MANAGEMENT,
                
                IntentType.SERVICE_ADD: AgentType.SERVICE_MANAGEMENT,
                IntentType.SERVICE_LIST: AgentType.SERVICE_MANAGEMENT,
                
                IntentType.KNOWLEDGE_QUERY: AgentType.KNOWLEDGE_BASE,
                IntentType.TROUBLESHOOTING: AgentType.KNOWLEDGE_BASE,
                
                IntentType.HANDOFF_REQUEST: AgentType.CONVERSATION_MANAGER,
                IntentType.GREETING: AgentType.CONVERSATION_MANAGER,
                IntentType.UNCLEAR: AgentType.CONVERSATION_MANAGER
            }
        
        target_agent = agent_routing.get(intent, AgentType.CONVERSATION_MANAGER)
        
        # Set active agent with routing context - store as string value
        updated_state = state.copy()
        updated_state["active_agent"] = target_agent.value
        
        # Store routing metadata
        if "routing_history" not in updated_state:
            updated_state["routing_history"] = []
        
        routing_entry = {
            "agent": target_agent.value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "reason": f"Intent: {intent.value if intent else 'unclear'}",
            "previous_agent": state.get("active_agent")
        }
        
        updated_state["routing_history"].append(routing_entry)
        
        # Transition conversation state based on intent
        new_conv_state = self._determine_conversation_state(intent)
        updated_state["conversation_state"] = new_conv_state.value if hasattr(new_conv_state, 'value') else str(new_conv_state)
        
        return updated_state
    
    def _determine_conversation_state(self, intent: Optional[IntentType]) -> ConversationState:
        """Determine appropriate conversation state based on intent"""
        
        # For user creation, let the agent determine the appropriate state based on available data
        if intent == IntentType.USER_CREATE:
            return ConversationState.IDLE  # Let user management agent handle state transition
        elif intent in [IntentType.USER_UPDATE, IntentType.SERVICE_ADD]:
            return ConversationState.DATA_COLLECTION
        elif intent in [IntentType.USER_DELETE]:
            return ConversationState.CONFIRMATION_PENDING
        elif intent in [IntentType.KNOWLEDGE_QUERY, IntentType.TROUBLESHOOTING]:
            return ConversationState.OPERATION_EXECUTION
        elif intent == IntentType.HANDOFF_REQUEST:
            return ConversationState.HUMAN_HANDOFF
        else:
            return ConversationState.OPERATION_EXECUTION
    
    def _get_conversation_context(self, state: ChatState) -> str:
        """Get formatted conversation context for LLM"""
        
        recent_messages = state["messages"][-3:] if len(state["messages"]) > 3 else state["messages"]
        
        context_lines = []
        for msg in recent_messages:
            role = msg["role"].title()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines) if context_lines else "No previous context"
    
    def get_routing_stats(self) -> Dict:
        """Get router performance statistics"""
        
        success_rate = 0.0
        if self.routing_stats["total_routes"] > 0:
            success_rate = self.routing_stats["successful_routes"] / self.routing_stats["total_routes"]
        
        return {
            **self.routing_stats,
            "success_rate": success_rate,
            "confidence_threshold": self.confidence_threshold
        }

# Initialize router agent instance
router_agent = RouterAgent()
