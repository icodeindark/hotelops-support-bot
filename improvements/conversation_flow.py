"""
Conversation Flow Manager for Seamless Agent Transitions
Maintains natural conversation without losing context
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class FlowTransition:
    """Represents a conversation flow transition"""
    from_agent: str
    to_agent: str
    trigger_message: str
    transition_type: str  # "natural", "explicit", "clarification"
    confidence: float
    transition_response: str

@dataclass 
class ConversationFlow:
    """Tracks conversation flow and context"""
    session_id: str
    current_agent: str
    previous_agent: str
    topic_history: List[str] = field(default_factory=list)
    agent_history: List[str] = field(default_factory=list)
    transitions: List[FlowTransition] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
class ConversationFlowManager:
    """
    Manages seamless conversation flow between agents
    """
    
    def __init__(self):
        self.active_flows: Dict[str, ConversationFlow] = {}
        
        # Natural transition templates
        self.transition_templates = {
            ("user_management", "service_management"): [
                "Perfect! Now let's talk about services. {question}",
                "Absolutely! Switching to service management. {question}",
                "Sure thing! What would you like to know about services?"
            ],
            ("service_management", "knowledge_base"): [
                "Great question! Let me search our knowledge base for that.",
                "I can help with that! Checking our documentation...",
                "Perfect! Let me find that information for you."
            ],
            ("knowledge_base", "user_management"): [
                "Got it! Now, back to user management - what do you need?",
                "Sure! Let's handle your user management request.",
                "Absolutely! How can I help with user management?"
            ],
            ("any", "conversation_manager"): [
                "I understand you'd like to chat. What's on your mind?",
                "Sure! What would you like to talk about?",
                "Of course! How can I help you today?"
            ]
        }
        
        # Topic continuity phrases
        self.continuity_phrases = {
            "user_management": {
                "follow_up": "Also regarding users, {query}",
                "related": "Another user question: {query}",
                "clarification": "To clarify about users: {query}"
            },
            "service_management": {
                "follow_up": "Also about services, {query}",
                "related": "Another service question: {query}", 
                "clarification": "To clarify about services: {query}"
            },
            "knowledge_base": {
                "follow_up": "Another question: {query}",
                "related": "Related to that: {query}",
                "clarification": "To clarify: {query}"
            }
        }
    
    def process_message(self, session_id: str, message: str, 
                       current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process message with conversation flow awareness
        """
        
        # Get or create flow
        flow = self._get_or_create_flow(session_id, current_state)
        
        # Analyze message for flow patterns
        flow_analysis = self._analyze_message_flow(message, flow)
        
        # Determine routing decision
        routing_decision = self._make_routing_decision(flow_analysis, flow, current_state)
        
        # Update flow state
        self._update_flow_state(flow, routing_decision, message)
        
        # Generate response with flow context
        return self._generate_flow_response(routing_decision, flow, current_state)
    
    def _get_or_create_flow(self, session_id: str, current_state: Dict[str, Any]) -> ConversationFlow:
        """Get existing flow or create new one"""
        
        if session_id not in self.active_flows:
            current_agent = current_state.get("active_agent", "conversation_manager")
            
            self.active_flows[session_id] = ConversationFlow(
                session_id=session_id,
                current_agent=current_agent,
                previous_agent="",
                topic_history=["general"],
                agent_history=[current_agent]
            )
        
        return self.active_flows[session_id]
    
    def _analyze_message_flow(self, message: str, flow: ConversationFlow) -> Dict[str, Any]:
        """Analyze message for conversation flow patterns"""
        
        message_lower = message.lower().strip()
        
        analysis = {
            "message": message,
            "flow_type": "continuation",  # Default
            "target_agent": flow.current_agent,
            "confidence": 0.8,
            "reasoning": "",
            "requires_transition": False
        }
        
        # Check for explicit topic switches
        topic_switches = {
            "user": "user_management",
            "service": "service_management", 
            "help": "knowledge_base",
            "question": "knowledge_base",
            "problem": "knowledge_base"
        }
        
        for keyword, agent in topic_switches.items():
            if keyword in message_lower and agent != flow.current_agent:
                analysis.update({
                    "flow_type": "topic_switch",
                    "target_agent": agent,
                    "confidence": 0.9,
                    "reasoning": f"Explicit topic switch to {keyword}",
                    "requires_transition": True
                })
                break
        
        # Check for natural transitions
        transition_phrases = [
            "what about", "how about", "tell me about", "what else",
            "also", "another", "different", "switch", "change"
        ]
        
        for phrase in transition_phrases:
            if phrase in message_lower:
                # Infer target from context
                target_agent = self._infer_target_from_context(message_lower, flow)
                if target_agent != flow.current_agent:
                    analysis.update({
                        "flow_type": "natural_transition", 
                        "target_agent": target_agent,
                        "confidence": 0.85,
                        "reasoning": f"Natural transition with phrase: {phrase}",
                        "requires_transition": True
                    })
                break
        
        # Check for continuation indicators
        continuation_phrases = ["and", "also", "plus", "furthermore", "additionally"]
        
        if any(phrase in message_lower for phrase in continuation_phrases):
            analysis.update({
                "flow_type": "continuation",
                "target_agent": flow.current_agent,
                "confidence": 0.95,
                "reasoning": "Continuation of current topic"
            })
        
        # Check for clarification requests
        clarification_phrases = ["what", "huh", "unclear", "explain", "meaning", "confused"]
        
        if any(phrase in message_lower for phrase in clarification_phrases) and len(message.split()) < 5:
            analysis.update({
                "flow_type": "clarification",
                "target_agent": "conversation_manager",
                "confidence": 0.9,
                "reasoning": "Clarification request",
                "requires_transition": flow.current_agent != "conversation_manager"
            })
        
        return analysis
    
    def _make_routing_decision(self, flow_analysis: Dict[str, Any], 
                              flow: ConversationFlow,
                              current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Make routing decision based on flow analysis"""
        
        decision = {
            "target_agent": flow_analysis["target_agent"],
            "flow_type": flow_analysis["flow_type"],
            "confidence": flow_analysis["confidence"],
            "requires_transition": flow_analysis["requires_transition"],
            "reasoning": flow_analysis["reasoning"],
            "transition_response": None
        }
        
        # Generate transition response if needed
        if decision["requires_transition"]:
            decision["transition_response"] = self._generate_transition_response(
                flow.current_agent, 
                decision["target_agent"],
                flow_analysis["message"]
            )
        
        return decision
    
    def _update_flow_state(self, flow: ConversationFlow, 
                          decision: Dict[str, Any], 
                          message: str):
        """Update conversation flow state"""
        
        # Record transition if agent changes
        if decision["target_agent"] != flow.current_agent:
            transition = FlowTransition(
                from_agent=flow.current_agent,
                to_agent=decision["target_agent"],
                trigger_message=message,
                transition_type=decision["flow_type"],
                confidence=decision["confidence"],
                transition_response=decision.get("transition_response", "")
            )
            
            flow.transitions.append(transition)
            flow.previous_agent = flow.current_agent
            flow.current_agent = decision["target_agent"]
            
            # Update history
            if decision["target_agent"] not in flow.agent_history[-3:]:  # Avoid immediate repeats
                flow.agent_history.append(decision["target_agent"])
        
        # Update topic history
        topic = self._infer_topic_from_agent(decision["target_agent"])
        if topic not in flow.topic_history[-2:]:  # Avoid immediate repeats
            flow.topic_history.append(topic)
        
        # Trim histories to prevent memory bloat
        flow.agent_history = flow.agent_history[-10:]
        flow.topic_history = flow.topic_history[-10:]
        flow.transitions = flow.transitions[-5:]
    
    def _generate_flow_response(self, decision: Dict[str, Any], 
                               flow: ConversationFlow,
                               current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response with flow context"""
        
        response = {
            "target_agent": decision["target_agent"],
            "flow_type": decision["flow_type"],
            "confidence": decision["confidence"],
            "routing_method": "conversation_flow",
            "updated_state": {
                **current_state,
                "active_agent": decision["target_agent"],
                "conversation_flow": {
                    "previous_agent": flow.previous_agent,
                    "transition_count": len(flow.transitions),
                    "topic_history": flow.topic_history[-3:],  # Last 3 topics
                    "requires_transition_response": decision["requires_transition"]
                }
            }
        }
        
        # Add transition response if needed
        if decision["requires_transition"] and decision["transition_response"]:
            response["transition_response"] = decision["transition_response"]
        
        # Add flow context for agents
        response["flow_context"] = {
            "previous_agent": flow.previous_agent,
            "topic_history": flow.topic_history[-3:],
            "recent_transitions": [
                {
                    "from": t.from_agent,
                    "to": t.to_agent, 
                    "type": t.transition_type
                } for t in flow.transitions[-3:]
            ]
        }
        
        return response
    
    def _generate_transition_response(self, from_agent: str, to_agent: str, message: str) -> str:
        """Generate natural transition response"""
        
        # Try specific transition
        key = (from_agent, to_agent)
        if key in self.transition_templates:
            template = self.transition_templates[key][0]  # Use first template
            return template.format(question="What would you like to know?")
        
        # Fall back to generic transition
        generic_templates = self.transition_templates[("any", "conversation_manager")]
        return generic_templates[0]
    
    def _infer_target_from_context(self, message: str, flow: ConversationFlow) -> str:
        """Infer target agent from message context"""
        
        # Keyword mapping
        keywords = {
            "user": "user_management",
            "service": "service_management",
            "help": "knowledge_base",
            "question": "knowledge_base",
            "problem": "knowledge_base",
            "issue": "knowledge_base"
        }
        
        for keyword, agent in keywords.items():
            if keyword in message:
                return agent
        
        # If unclear, return conversation manager
        return "conversation_manager"
    
    def _infer_topic_from_agent(self, agent: str) -> str:
        """Infer topic from agent"""
        
        agent_topic_map = {
            "user_management": "users",
            "service_management": "services", 
            "knowledge_base": "information",
            "conversation_manager": "general"
        }
        
        return agent_topic_map.get(agent, "general")
    
    def get_flow_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation flow summary"""
        
        if session_id not in self.active_flows:
            return {"error": "No active flow"}
        
        flow = self.active_flows[session_id]
        
        return {
            "current_agent": flow.current_agent,
            "previous_agent": flow.previous_agent,
            "topic_history": flow.topic_history,
            "transition_count": len(flow.transitions),
            "recent_transitions": [
                {
                    "from": t.from_agent,
                    "to": t.to_agent,
                    "type": t.transition_type,
                    "confidence": t.confidence
                } for t in flow.transitions[-3:]
            ]
        }
    
    def clear_flow(self, session_id: str):
        """Clear conversation flow (for testing/reset)"""
        if session_id in self.active_flows:
            del self.active_flows[session_id]

# Global conversation flow manager
flow_manager = ConversationFlowManager()
