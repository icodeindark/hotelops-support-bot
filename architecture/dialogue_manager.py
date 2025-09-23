"""
Central Dialogue Manager - The Brain of Our Hotel Management Bot
Orchestrates conversation flow, maintains context, and coordinates agents
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

@dataclass
class ConversationTurn:
    """Single conversation turn with full context"""
    user_input: str
    intent: str
    entities: Dict[str, Any]
    context: Dict[str, Any]
    agent_response: str
    agent_used: str
    timestamp: datetime
    confidence: float

class DialogueManager:
    """
    Central orchestrator for hotel management conversations
    Inspired by enterprise architecture but simplified for our needs
    """
    
    def __init__(self):
        # Conversation memory
        self.active_sessions: Dict[str, List[ConversationTurn]] = {}
        
        # Context tracking
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Agent registry
        self.available_agents = {
            "user_management": None,
            "service_management": None, 
            "knowledge_base": None,
            "conversation_manager": None
        }
        
        # Response templates for consistency
        self.response_templates = {
            "transition": "I understand you want to {action}. Let me help you with that.",
            "clarification": "Could you clarify what you mean by '{term}'?",
            "confirmation": "Just to confirm, you want to {action}. Is that correct?",
            "error": "I had trouble understanding that. Could you rephrase?"
        }
        
        # Conversation policies
        self.policies = {
            "max_clarification_attempts": 2,
            "auto_escalate_after": 5,  # failed attempts
            "context_retention_turns": 10
        }
    
    def process_conversation_turn(self, session_id: str, user_input: str, 
                                current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main conversation processing pipeline
        This replaces the scattered routing logic in multi_agent_system
        """
        
        # Step 1: Initialize or restore conversation context
        context = self._get_conversation_context(session_id, current_state)
        
        # Step 2: Parallel processing - NLU and Context Analysis
        nlu_result = self._process_nlu(user_input, context)
        context_analysis = self._analyze_context(user_input, context)
        
        # Step 3: Dialogue policy - decide what to do
        dialogue_decision = self._apply_dialogue_policy(nlu_result, context_analysis, context)
        
        # Step 4: Agent coordination
        agent_response = self._coordinate_agent(dialogue_decision, context)
        
        # Step 5: Response generation and formatting
        final_response = self._generate_response(agent_response, dialogue_decision, context)
        
        # Step 6: Update conversation memory
        self._update_conversation_memory(session_id, user_input, nlu_result, 
                                       agent_response, dialogue_decision)
        
        return final_response
    
    def _get_conversation_context(self, session_id: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get or create conversation context"""
        
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                "current_topic": "general",
                "current_agent": "conversation_manager",
                "user_preferences": {},
                "collected_data": {},
                "conversation_state": "idle",
                "failed_attempts": 0,
                "last_successful_action": None,
                "turn_count": 0
            }
        
        context = self.session_contexts[session_id].copy()
        context.update(current_state)  # Merge with current state
        context["turn_count"] += 1
        
        return context
    
    def _process_nlu(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Natural Language Understanding with context awareness"""
        
        # Try fast pattern matching first (from our improvements)
        try:
            from improvements.simple_flow_enhancer import flow_enhancer
            pattern_result = flow_enhancer.enhance_routing(
                user_input, 
                context.get("current_agent", "conversation_manager"),
                context
            )
            
            if not pattern_result.get("use_api", True):
                return {
                    "intent": pattern_result.get("intent", "unclear"),
                    "confidence": pattern_result.get("confidence", 0.8),
                    "entities": {},
                    "method": pattern_result.get("method", "pattern"),
                    "requires_api": False
                }
        except ImportError:
            pass
        
        # Fallback to router agent for complex cases
        return {
            "intent": "unclear",
            "confidence": 0.5,
            "entities": {},
            "method": "fallback", 
            "requires_api": True
        }
    
    def _analyze_context(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation context for flow decisions"""
        
        analysis = {
            "is_continuation": False,
            "is_topic_switch": False,
            "is_clarification_needed": False,
            "is_data_collection": False,
            "confidence": 0.0
        }
        
        # Check for continuation patterns
        continuation_words = ["also", "and", "plus", "furthermore"]
        if any(word in user_input.lower() for word in continuation_words):
            analysis["is_continuation"] = True
            analysis["confidence"] = 0.9
        
        # Check for topic switches
        topic_switches = ["what about", "tell me about", "switch to", "go to"]
        if any(phrase in user_input.lower() for phrase in topic_switches):
            analysis["is_topic_switch"] = True
            analysis["confidence"] = 0.85
        
        # Check if we're collecting data
        if context.get("conversation_state") in ["collecting_user_data", "data_collection"]:
            analysis["is_data_collection"] = True
            analysis["confidence"] = 0.95
        
        # Check if clarification is needed
        short_unclear = len(user_input.split()) < 3 and user_input.lower() in ["what", "huh", "unclear"]
        if short_unclear or context.get("failed_attempts", 0) > 0:
            analysis["is_clarification_needed"] = True
            analysis["confidence"] = 0.8
        
        return analysis
    
    def _apply_dialogue_policy(self, nlu_result: Dict[str, Any], 
                              context_analysis: Dict[str, Any],
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply dialogue management policies"""
        
        policy_decision = {
            "action": "route_to_agent",
            "target_agent": "conversation_manager",
            "response_type": "normal",
            "requires_confirmation": False,
            "needs_clarification": False
        }
        
        # Policy 1: Handle clarification needs
        if context_analysis["is_clarification_needed"]:
            policy_decision.update({
                "action": "clarify",
                "target_agent": "conversation_manager",
                "response_type": "clarification"
            })
            return policy_decision
        
        # Policy 2: Continue data collection if active
        if context_analysis["is_data_collection"] and not context_analysis["is_topic_switch"]:
            policy_decision.update({
                "action": "continue_data_collection",
                "target_agent": context.get("current_agent", "user_management"),
                "response_type": "data_collection"
            })
            return policy_decision
        
        # Policy 3: Handle topic switches
        if context_analysis["is_topic_switch"]:
            target_agent = self._infer_agent_from_intent(nlu_result["intent"])
            policy_decision.update({
                "action": "topic_switch",
                "target_agent": target_agent,
                "response_type": "transition"
            })
            return policy_decision
        
        # Policy 4: Continue with current agent if continuation
        if context_analysis["is_continuation"]:
            policy_decision.update({
                "action": "continue_topic",
                "target_agent": context.get("current_agent", "conversation_manager"),
                "response_type": "normal"
            })
            return policy_decision
        
        # Policy 5: Route based on intent
        target_agent = self._infer_agent_from_intent(nlu_result["intent"])
        policy_decision.update({
            "action": "route_to_agent",
            "target_agent": target_agent,
            "response_type": "normal"
        })
        
        return policy_decision
    
    def _coordinate_agent(self, dialogue_decision: Dict[str, Any], 
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate with appropriate agent"""
        
        target_agent = dialogue_decision["target_agent"]
        action = dialogue_decision["action"]
        
        # This would call the actual agent
        # For now, return a placeholder response
        return {
            "agent_used": target_agent,
            "response": f"Agent {target_agent} would handle: {action}",
            "success": True,
            "data": {}
        }
    
    def _generate_response(self, agent_response: Dict[str, Any], 
                          dialogue_decision: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unified, context-aware response"""
        
        response_type = dialogue_decision["response_type"]
        base_response = agent_response.get("response", "")
        
        # Add context-appropriate framing
        if response_type == "transition":
            action = dialogue_decision.get("action", "help you")
            prefix = self.response_templates["transition"].format(action=action)
            final_response = f"{prefix}\n\n{base_response}"
        
        elif response_type == "clarification":
            final_response = self.response_templates["clarification"].format(
                term=context.get("unclear_term", "that")
            )
        
        elif response_type == "data_collection":
            final_response = base_response  # Agent handles data collection flow
        
        else:
            final_response = base_response
        
        return {
            "response": final_response,
            "agent_used": agent_response["agent_used"],
            "success": agent_response["success"],
            "context_updated": True,
            "dialogue_state": dialogue_decision
        }
    
    def _update_conversation_memory(self, session_id: str, user_input: str,
                                   nlu_result: Dict[str, Any], agent_response: Dict[str, Any],
                                   dialogue_decision: Dict[str, Any]):
        """Update conversation memory for context"""
        
        turn = ConversationTurn(
            user_input=user_input,
            intent=nlu_result["intent"],
            entities=nlu_result.get("entities", {}),
            context=self.session_contexts.get(session_id, {}),
            agent_response=agent_response.get("response", ""),
            agent_used=agent_response.get("agent_used", "unknown"),
            timestamp=datetime.now(),
            confidence=nlu_result.get("confidence", 0.0)
        )
        
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = []
        
        self.active_sessions[session_id].append(turn)
        
        # Keep only recent turns to manage memory
        max_turns = self.policies["context_retention_turns"]
        if len(self.active_sessions[session_id]) > max_turns:
            self.active_sessions[session_id] = self.active_sessions[session_id][-max_turns:]
        
        # Update session context
        if session_id in self.session_contexts:
            self.session_contexts[session_id].update({
                "current_agent": agent_response.get("agent_used", "conversation_manager"),
                "last_intent": nlu_result["intent"],
                "last_successful_action": dialogue_decision["action"] if agent_response.get("success") else None
            })
    
    def _infer_agent_from_intent(self, intent: str) -> str:
        """Map intent to appropriate agent"""
        
        intent_agent_map = {
            "user_create": "user_management",
            "user_update": "user_management", 
            "user_list": "user_management",
            "service_add": "service_management",
            "service_list": "service_management",
            "knowledge_query": "knowledge_base",
            "troubleshooting": "knowledge_base",
            "faq": "knowledge_base",
            "greeting": "conversation_manager",
            "unclear": "conversation_manager"
        }
        
        return intent_agent_map.get(intent, "conversation_manager")
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary for debugging/monitoring"""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        turns = self.active_sessions[session_id]
        context = self.session_contexts.get(session_id, {})
        
        return {
            "session_id": session_id,
            "total_turns": len(turns),
            "current_agent": context.get("current_agent"),
            "current_topic": context.get("current_topic"),
            "recent_intents": [turn.intent for turn in turns[-5:]],
            "average_confidence": sum(turn.confidence for turn in turns) / len(turns) if turns else 0,
            "last_activity": turns[-1].timestamp.isoformat() if turns else None
        }

# Global dialogue manager instance
dialogue_manager = DialogueManager()
