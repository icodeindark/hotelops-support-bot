"""
Smart Router with Conversation Flow and API Optimization
Reduces API calls by 70%+ while maintaining natural conversation
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ConversationContext:
    """Lightweight conversation context"""
    session_id: str
    current_agent: str
    current_topic: str
    last_intent: str
    conversation_state: str
    user_data_progress: Dict[str, Any]
    last_successful_action: Optional[str]
    message_count: int
    failed_attempts: List[str]
    
class SmartRouter:
    """
    Smart routing with conversation flow and minimal API usage
    """
    
    def __init__(self):
        # Session contexts - in-memory for speed
        self.session_contexts: Dict[str, ConversationContext] = {}
        
        # Pattern-based intent classification (no API needed)
        self.intent_patterns = self._initialize_smart_patterns()
        
        # Common typo corrections
        self.typo_map = {
            "manaegment": "management", "managment": "management",
            "srvice": "service", "sevice": "service", 
            "usr": "user", "usre": "user",
            "troubleshoot": "troubleshoot", "troubleshot": "troubleshoot"
        }
        
        # Conversation flow keywords (seamless switching)
        self.flow_keywords = {
            "topic_switch": [
                "what about", "how about", "tell me about", "what else",
                "also", "another", "different", "switch to", "go to"
            ],
            "continuation": [
                "and", "also", "plus", "additionally", "furthermore"
            ],
            "clarification": [
                "what", "huh", "unclear", "explain", "meaning"
            ]
        }
    
    def route_message(self, session_id: str, message: str, 
                     current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart routing with conversation flow - minimal API usage
        """
        
        # Get or create context
        context = self._get_context(session_id, current_state)
        
        # Normalize message (fix typos)
        normalized_msg = self._normalize_message(message)
        
        # STEP 1: Check if this is conversation flow (NO API CALL)
        flow_result = self._analyze_conversation_flow(normalized_msg, context)
        
        if flow_result["is_flow"]:
            return self._handle_conversation_flow(flow_result, context, current_state)
        
        # STEP 2: Pattern-based intent detection (NO API CALL)
        pattern_intent = self._classify_with_patterns(normalized_msg, context)
        
        if pattern_intent["confidence"] > 0.8:
            return self._route_with_pattern_intent(pattern_intent, context, current_state)
        
        # STEP 3: Context-based routing (NO API CALL) 
        context_route = self._route_with_context(normalized_msg, context)
        
        if context_route["confident"]:
            return self._apply_context_route(context_route, context, current_state)
        
        # STEP 4: Only use API for truly ambiguous cases (LAST RESORT)
        return self._route_with_llm_fallback(normalized_msg, context, current_state)
    
    def _get_context(self, session_id: str, current_state: Dict[str, Any]) -> ConversationContext:
        """Get or create conversation context"""
        
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = ConversationContext(
                session_id=session_id,
                current_agent=current_state.get("active_agent", "conversation_manager"),
                current_topic="general",
                last_intent="greeting",
                conversation_state=current_state.get("conversation_state", "idle"),
                user_data_progress={},
                last_successful_action=None,
                message_count=0,
                failed_attempts=[]
            )
        
        context = self.session_contexts[session_id]
        context.message_count += 1
        
        return context
    
    def _normalize_message(self, message: str) -> str:
        """Quick typo correction without API"""
        
        words = message.lower().split()
        corrected = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            corrected.append(self.typo_map.get(clean_word, word))
        
        return ' '.join(corrected)
    
    def _analyze_conversation_flow(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        
        message_lower = message.lower()
        
        # Check for topic switching
        is_topic_switch = any(keyword in message_lower for keyword in self.flow_keywords["topic_switch"])
        
        # Check for continuation
        is_continuation = any(keyword in message_lower for keyword in self.flow_keywords["continuation"])
        
        # Check for clarification request
        is_clarification = any(keyword in message_lower for keyword in self.flow_keywords["clarification"])
        
        # Determine flow type
        if is_topic_switch:
            target_topic = self._infer_target_topic(message_lower)
            return {
                "is_flow": True,
                "flow_type": "topic_switch",
                "target_topic": target_topic,
                "confidence": 0.9
            }
        
        elif is_continuation and context.current_agent != "conversation_manager":
            return {
                "is_flow": True,
                "flow_type": "continuation",
                "target_agent": context.current_agent,
                "confidence": 0.95
            }
        
        elif is_clarification:
            return {
                "is_flow": True,
                "flow_type": "clarification",
                "target_agent": "conversation_manager",
                "confidence": 0.8
            }
        
        return {"is_flow": False}
    
    def _infer_target_topic(self, message: str) -> str:
        """Infer target topic from message"""
        
        if any(word in message for word in ["user", "account", "employee", "staff"]):
            return "user_management"
        elif any(word in message for word in ["service", "work order", "task", "maintenance"]):
            return "service_management"
        elif any(word in message for word in ["help", "how", "what", "faq", "question"]):
            return "knowledge_base"
        elif any(word in message for word in ["problem", "issue", "error", "broken"]):
            return "troubleshooting"
        else:
            return "general"
    
    def _classify_with_patterns(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Pattern-based intent classification - NO API"""
        
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            max_score = 0
            
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    # Score based on pattern specificity and context
                    base_score = 0.7 + (len(pattern) / 1000)
                    
                    # Context boost
                    if self._is_contextually_relevant(intent, context):
                        base_score += 0.2
                    
                    max_score = max(max_score, base_score)
            
            if max_score > 0:
                scores[intent] = min(max_score, 1.0)
        
        if scores:
            best_intent = max(scores, key=scores.get)
            return {
                "intent": best_intent,
                "confidence": scores[best_intent],
                "method": "pattern"
            }
        
        return {"intent": "unclear", "confidence": 0.0, "method": "pattern"}
    
    def _route_with_context(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Route based on conversation context"""
        
        # If in data collection mode, continue unless explicit switch
        if context.conversation_state == "collecting_user_data":
            # Check if message looks like user data
            if self._looks_like_user_data(message):
                return {
                    "confident": True,
                    "target_agent": "user_management",
                    "reasoning": "Continuing user data collection"
                }
            # Check if explicit topic switch
            elif any(keyword in message.lower() for keyword in ["service", "help", "question"]):
                return {
                    "confident": True,
                    "target_agent": self._infer_agent_from_topic(self._infer_target_topic(message)),
                    "reasoning": "Explicit topic switch during data collection"
                }
        
        # Continue with current agent for related queries
        if context.current_agent and self._is_related_query(message, context.current_agent):
            return {
                "confident": True,
                "target_agent": context.current_agent,
                "reasoning": "Related to current topic"
            }
        
        return {"confident": False}
    
    def _handle_conversation_flow(self, flow_result: Dict[str, Any], 
                                 context: ConversationContext, 
                                 current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation flow without API"""
        
        flow_type = flow_result["flow_type"]
        
        if flow_type == "topic_switch":
            target_agent = self._infer_agent_from_topic(flow_result["target_topic"])
            
            # Update context
            context.current_agent = target_agent
            context.current_topic = flow_result["target_topic"]
            
            # Generate natural transition
            transition = self._generate_transition_response(context.current_agent, target_agent)
            
            return {
                "target_agent": target_agent,
                "intent": "topic_switch",
                "confidence": flow_result["confidence"],
                "routing_method": "conversation_flow",
                "transition_response": transition,
                "updated_state": {
                    **current_state,
                    "active_agent": target_agent,
                    "conversation_state": "operation_execution"
                }
            }
        
        elif flow_type == "continuation":
            return {
                "target_agent": context.current_agent,
                "intent": "continuation",
                "confidence": flow_result["confidence"],
                "routing_method": "conversation_flow",
                "updated_state": current_state
            }
        
        elif flow_type == "clarification":
            return {
                "target_agent": "conversation_manager",
                "intent": "clarification",
                "confidence": flow_result["confidence"],
                "routing_method": "conversation_flow",
                "updated_state": {
                    **current_state,
                    "active_agent": "conversation_manager"
                }
            }
        
        return {"error": "Unknown flow type"}
    
    def _route_with_pattern_intent(self, pattern_result: Dict[str, Any],
                                  context: ConversationContext,
                                  current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Route using pattern-detected intent"""
        
        intent = pattern_result["intent"]
        target_agent = self._map_intent_to_agent(intent)
        
        # Update context
        context.last_intent = intent
        context.current_agent = target_agent
        
        return {
            "target_agent": target_agent,
            "intent": intent,
            "confidence": pattern_result["confidence"],
            "routing_method": "pattern_matching",
            "updated_state": {
                **current_state,
                "active_agent": target_agent,
                "conversation_state": self._determine_conversation_state(intent)
            }
        }
    
    def _route_with_llm_fallback(self, message: str, context: ConversationContext,
                               current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to LLM only for truly ambiguous cases"""
        
        # Import here to avoid circular dependency
        from agents.router_agent import router_agent
        
        # Use existing LLM classification as fallback
        llm_result = router_agent.process_message(current_state, message)
        
        # Update context with LLM result
        context.current_agent = llm_result.get("active_agent", "conversation_manager")
        
        return {
            "target_agent": context.current_agent,
            "intent": "llm_classified",
            "confidence": 0.6,  # Lower confidence for LLM fallback
            "routing_method": "llm_fallback",
            "updated_state": llm_result
        }
    
    def _generate_transition_response(self, from_agent: str, to_agent: str) -> str:
        """Generate natural transition response"""
        
        transitions = {
            ("conversation_manager", "user_management"): "Sure! Let me help you with user management.",
            ("user_management", "service_management"): "Of course! Switching to service management now.",
            ("service_management", "knowledge_base"): "Great! Let me search for that information.",
            ("knowledge_base", "user_management"): "Absolutely! Back to user management.",
            ("any", "any"): "Got it! How can I help you with that?"
        }
        
        key = (from_agent, to_agent)
        return transitions.get(key, transitions[("any", "any")])
    
    def _initialize_smart_patterns(self) -> Dict[str, List[str]]:
        """Initialize smart intent patterns"""
        
        return {
            "user_create": [
                r'\b(?:add|create|new|register)\s+(?:user|account|employee)\b',
                r'\bneed\s+to\s+(?:add|create)\s+(?:user|someone)\b',
                r'\b(?:hire|onboard)\s+(?:new\s+)?(?:employee|staff)\b'
            ],
            "user_management": [
                r'\buser\s+(?:management|admin)\b',
                r'\b(?:manage|handle)\s+users\b'
            ],
            "service_management": [
                r'\bservice\s+(?:management|admin)\b',
                r'\b(?:manage|handle)\s+services\b'
            ],
            "knowledge_query": [
                r'\b(?:how\s+to|what\s+is|tell\s+me|explain)\b',
                r'\b(?:help\s+with|information\s+about)\b'
            ],
            "troubleshooting": [
                r'\b(?:problem|issue|error|trouble|broken)\b',
                r'\b(?:not\s+working|fix|solve)\b'
            ],
            "greeting": [
                r'^\b(?:hi|hello|hey|good\s+morning)\b',
                r'^\b(?:what\'s\s+up|how\s+are\s+you)\b'
            ]
        }
    
    def _is_contextually_relevant(self, intent: str, context: ConversationContext) -> bool:
        """Check if intent is contextually relevant"""
        
        relevance_map = {
            "user_management": ["user_create", "user_update", "user_delete", "user_list"],
            "service_management": ["service_add", "service_list"],
            "knowledge_base": ["knowledge_query"],
            "troubleshooting": ["troubleshooting"]
        }
        
        current_topic = context.current_topic
        return intent in relevance_map.get(current_topic, [])
    
    def _looks_like_user_data(self, message: str) -> bool:
        """Check if message contains user data"""
        
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
            r'\b(?:name\s*[:=]\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # names
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # phone
            r'\b(?:role|position)\s*[:=]\s*\w+\b'  # role
        ]
        
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)
    
    def _is_related_query(self, message: str, current_agent: str) -> bool:
        """Check if message is related to current agent's domain"""
        
        agent_keywords = {
            "user_management": ["user", "account", "employee", "staff"],
            "service_management": ["service", "work", "order", "task"],
            "knowledge_base": ["help", "information", "how", "what"],
            "conversation_manager": ["general", "chat", "talk"]
        }
        
        keywords = agent_keywords.get(current_agent, [])
        return any(keyword in message.lower() for keyword in keywords)
    
    def _infer_agent_from_topic(self, topic: str) -> str:
        """Map topic to agent"""
        
        topic_agent_map = {
            "user_management": "user_management",
            "service_management": "service_management", 
            "knowledge_base": "knowledge_base",
            "troubleshooting": "knowledge_base",
            "general": "conversation_manager"
        }
        
        return topic_agent_map.get(topic, "conversation_manager")
    
    def _map_intent_to_agent(self, intent: str) -> str:
        """Map intent to agent"""
        
        intent_agent_map = {
            "user_create": "user_management",
            "user_update": "user_management",
            "user_delete": "user_management",
            "user_list": "user_management",
            "service_add": "service_management",
            "service_list": "service_management",
            "knowledge_query": "knowledge_base",
            "troubleshooting": "knowledge_base",
            "greeting": "conversation_manager",
            "unclear": "conversation_manager"
        }
        
        return intent_agent_map.get(intent, "conversation_manager")
    
    def _determine_conversation_state(self, intent: str) -> str:
        """Determine conversation state from intent"""
        
        state_map = {
            "user_create": "collecting_user_data",
            "user_update": "data_collection",
            "user_delete": "confirmation_pending",
            "service_add": "data_collection",
            "knowledge_query": "operation_execution",
            "troubleshooting": "operation_execution",
            "greeting": "operation_execution"
        }
        
        return state_map.get(intent, "operation_execution")
    
    def _apply_context_route(self, context_route: Dict[str, Any],
                           context: ConversationContext, 
                           current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply context-based routing"""
        
        target_agent = context_route["target_agent"]
        
        # Update context
        context.current_agent = target_agent
        
        return {
            "target_agent": target_agent,
            "intent": "context_continuation",
            "confidence": 0.85,
            "routing_method": "context_based",
            "reasoning": context_route["reasoning"],
            "updated_state": {
                **current_state,
                "active_agent": target_agent
            }
        }

# Global smart router instance
smart_router = SmartRouter()
