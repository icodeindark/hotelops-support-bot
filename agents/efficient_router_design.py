"""
HotelOpsAI Efficient Multi-Agent Router Architecture
Maximum Efficiency Design with Clean State Management

DESIGN PRINCIPLES:
1. Simple, explicit routing rules
2. Clear state transitions  
3. Fast intent classification
4. Fail-safe fallbacks
5. No sticky agent behavior
"""

from enum import Enum
from typing import Dict, Optional, List, Tuple
import re

class AgentType(Enum):
    ROUTER = "router"
    CONVERSATION = "conversation_manager"
    USER_MGMT = "user_management"
    SERVICE_MGMT = "service_management"
    KNOWLEDGE = "knowledge_base"
    TROUBLESHOOT = "troubleshoot"

class ConversationState(Enum):
    IDLE = "idle"
    USER_CREATION = "user_creation"
    SERVICE_CREATION = "service_creation"
    QUESTION_ANSWERING = "question_answering"
    TROUBLESHOOTING = "troubleshooting"

class EfficientRouter:
    """
    Lightning-fast router with simple, reliable classification
    """
    
    def __init__(self):
        # Simple keyword-based routing (much faster than complex regex)
        self.routing_rules = {
            # USER MANAGEMENT - Clear keywords
            AgentType.USER_MGMT: [
                "user", "create user", "add user", "new user", "list users", 
                "delete user", "update user", "manage user", "user management"
            ],
            
            # SERVICE MANAGEMENT - Clear keywords  
            AgentType.SERVICE_MGMT: [
                "service", "add service", "create service", "new service",
                "service management", "service manager", "manage service"
            ],
            
            # KNOWLEDGE BASE - Question patterns
            AgentType.KNOWLEDGE: [
                "how to", "what is", "how do", "explain", "help with",
                "guide", "tutorial", "instructions", "about", "information"
            ],
            
            # TROUBLESHOOTING - Problem patterns
            AgentType.TROUBLESHOOT: [
                "problem", "issue", "error", "not working", "broken", 
                "fix", "trouble", "help", "can't", "won't", "doesn't work"
            ]
        }
        
        # Explicit agent switching patterns (highest priority)
        self.agent_switch_patterns = {
            "conversation manager": AgentType.CONVERSATION,
            "service manager": AgentType.SERVICE_MGMT,
            "user management": AgentType.USER_MGMT,
            "knowledge base": AgentType.KNOWLEDGE,
            "troubleshoot": AgentType.TROUBLESHOOT,
            "go to": "EXTRACT_AGENT",  # "go to service manager"
            "switch to": "EXTRACT_AGENT",  # "switch to user management"
        }
    
    def classify_intent(self, message: str, current_state: dict) -> Tuple[AgentType, float]:
        """
        Fast, reliable intent classification
        Returns: (target_agent, confidence)
        """
        message_lower = message.lower().strip()
        
        # 1. HIGHEST PRIORITY: Explicit agent switching
        for pattern, target in self.agent_switch_patterns.items():
            if pattern in message_lower:
                if target == "EXTRACT_AGENT":
                    # Extract agent name from "go to X" or "switch to X"
                    extracted_agent = self._extract_agent_from_message(message_lower)
                    if extracted_agent:
                        return extracted_agent, 1.0
                else:
                    return target, 1.0
        
        # 2. MEDIUM PRIORITY: Current conversation context
        current_agent = current_state.get("active_agent")
        conversation_state = current_state.get("conversation_state", "idle")
        
        # If we're in the middle of an operation, continue with same agent
        if conversation_state != "idle":
            if conversation_state == "user_creation" and current_agent == "user_management":
                return AgentType.USER_MGMT, 0.9
            elif conversation_state == "service_creation" and current_agent == "service_management":
                return AgentType.SERVICE_MGMT, 0.9
            # etc.
        
        # 3. LOWEST PRIORITY: Keyword-based routing
        best_agent = AgentType.CONVERSATION
        max_score = 0.0
        
        for agent, keywords in self.routing_rules.items():
            score = self._calculate_keyword_score(message_lower, keywords)
            if score > max_score:
                max_score = score
                best_agent = agent
        
        # Minimum confidence threshold
        confidence = max_score if max_score > 0.3 else 0.5
        
        return best_agent, confidence
    
    def _extract_agent_from_message(self, message: str) -> Optional[AgentType]:
        """Extract target agent from 'go to X' patterns"""
        
        patterns = {
            "service": AgentType.SERVICE_MGMT,
            "user": AgentType.USER_MGMT,
            "knowledge": AgentType.KNOWLEDGE,
            "conversation": AgentType.CONVERSATION,
            "troubleshoot": AgentType.TROUBLESHOOT
        }
        
        for keyword, agent in patterns.items():
            if keyword in message:
                return agent
        
        return None
    
    def _calculate_keyword_score(self, message: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword in message:
                matches += 1
        
        return matches / total_keywords if total_keywords > 0 else 0.0

class StateManager:
    """
    Clean state management with clear transitions
    """
    
    @staticmethod
    def should_route_to_new_agent(current_state: dict, message: str) -> bool:
        """
        Decide if we should route to a new agent or continue with current
        """
        
        conversation_state = current_state.get("conversation_state", "idle")
        
        # Always route if idle
        if conversation_state == "idle":
            return True
        
        # Check for explicit agent switching requests
        message_lower = message.lower()
        switch_indicators = [
            "go to", "switch to", "conversation manager", 
            "service manager", "user management", "knowledge base"
        ]
        
        if any(indicator in message_lower for indicator in switch_indicators):
            return True
        
        # Check for clear topic switches
        topic_switches = {
            "user_creation": ["service", "question", "problem", "how to"],
            "service_creation": ["user", "question", "problem", "how to"],
            "question_answering": ["user", "service", "problem"],
            "troubleshooting": ["user", "service", "question"]
        }
        
        current_topics = topic_switches.get(conversation_state, [])
        if any(topic in message_lower for topic in current_topics):
            return True
        
        return False
    
    @staticmethod
    def determine_conversation_state(agent: AgentType, message: str) -> str:
        """Determine the new conversation state based on agent and message"""
        
        message_lower = message.lower()
        
        if agent == AgentType.USER_MGMT:
            if any(word in message_lower for word in ["create", "add", "new"]):
                return "user_creation"
            else:
                return "idle"
        
        elif agent == AgentType.SERVICE_MGMT:
            if any(word in message_lower for word in ["create", "add", "new"]):
                return "service_creation"
            else:
                return "idle"
        
        elif agent == AgentType.KNOWLEDGE:
            return "question_answering"
        
        elif agent == AgentType.TROUBLESHOOT:
            return "troubleshooting"
        
        else:
            return "idle"

# USAGE EXAMPLE:
"""
# In your multi_agent_system.py:

def _router_node(self, state: ChatState) -> ChatState:
    message = state.get("query", "")
    
    # Fast routing decision
    target_agent, confidence = self.efficient_router.classify_intent(message, state)
    
    # State management
    should_route = StateManager.should_route_to_new_agent(state, message)
    
    if should_route:
        # Route to new agent
        state["active_agent"] = target_agent.value
        state["conversation_state"] = StateManager.determine_conversation_state(target_agent, message)
        state["confidence"] = confidence
    
    # Continue with existing agent
    return state
"""
