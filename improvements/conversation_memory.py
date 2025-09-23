"""
Conversation Memory System for Natural Flow
Implements international-standard conversation management
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum

class ConversationTopic(Enum):
    USER_MANAGEMENT = "user_management"
    SERVICE_MANAGEMENT = "service_management"
    KNOWLEDGE_BASE = "knowledge_base"
    TROUBLESHOOTING = "troubleshooting"
    GENERAL_CHAT = "general_chat"

@dataclass
class ConversationTurn:
    """Single conversation turn"""
    timestamp: str
    user_message: str
    agent: str
    response: str
    intent: str
    confidence: float
    topic: ConversationTopic
    entities: Dict[str, Any]
    sentiment: str = "neutral"

@dataclass
class ConversationSummary:
    """Summary of conversation context"""
    current_topic: ConversationTopic
    previous_topics: List[ConversationTopic]
    user_preferences: Dict[str, Any]
    active_tasks: List[Dict[str, Any]]
    conversation_tone: str
    last_successful_action: Optional[str]
    failed_attempts: List[str]

class ConversationMemory:
    """
    Advanced conversation memory system for natural flow
    """
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.conversations: Dict[str, List[ConversationTurn]] = {}
        self.summaries: Dict[str, ConversationSummary] = {}
        
    def add_turn(self, session_id: str, turn: ConversationTurn):
        """Add a conversation turn"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append(turn)
        
        # Maintain history limit
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
        
        # Update summary
        self._update_summary(session_id)
    
    def get_context(self, session_id: str, last_n: int = 5) -> Dict[str, Any]:
        """Get conversation context for natural responses"""
        if session_id not in self.conversations:
            return self._empty_context()
        
        recent_turns = self.conversations[session_id][-last_n:]
        summary = self.summaries.get(session_id)
        
        return {
            "recent_turns": [asdict(turn) for turn in recent_turns],
            "current_topic": summary.current_topic.value if summary else None,
            "previous_topics": [topic.value for topic in summary.previous_topics] if summary else [],
            "user_preferences": summary.user_preferences if summary else {},
            "active_tasks": summary.active_tasks if summary else [],
            "conversation_tone": summary.conversation_tone if summary else "professional",
            "last_successful_action": summary.last_successful_action if summary else None,
            "failed_attempts": summary.failed_attempts if summary else [],
            "conversation_length": len(self.conversations[session_id]),
            "session_duration": self._calculate_duration(session_id)
        }
    
    def detect_topic_change(self, session_id: str, new_message: str, new_intent: str) -> bool:
        """Detect if topic has changed naturally"""
        if session_id not in self.summaries:
            return False
        
        current_topic = self.summaries[session_id].current_topic
        new_topic = self._infer_topic_from_intent(new_intent)
        
        # Check if it's a natural transition
        if current_topic != new_topic:
            recent_turns = self.conversations[session_id][-3:] if session_id in self.conversations else []
            
            # Natural transition indicators
            transition_phrases = [
                "what about", "how about", "tell me about", "what else",
                "can you help with", "also", "another question", "by the way"
            ]
            
            has_transition_phrase = any(phrase in new_message.lower() for phrase in transition_phrases)
            
            return True, has_transition_phrase
        
        return False, False
    
    def get_natural_transition(self, session_id: str, from_topic: str, to_topic: str) -> str:
        """Generate natural transition acknowledgment"""
        transitions = {
            ("user_management", "service_management"): [
                "Sure! Let me help you with service management now.",
                "Absolutely! Switching to service management topics.",
                "Of course! What would you like to know about services?"
            ],
            ("service_management", "knowledge_base"): [
                "Great question! Let me search our knowledge base for that.",
                "I can help with that! Checking our documentation...",
                "Perfect! Let me find that information for you."
            ],
            ("any", "any"): [
                "I understand you'd like to switch topics. What can I help you with?",
                "Sure thing! What would you like to know about?",
                "Of course! How can I assist you with that?"
            ]
        }
        
        key = (from_topic, to_topic)
        if key in transitions:
            return transitions[key][0]  # Could randomize
        else:
            return transitions[("any", "any")][0]
    
    def _update_summary(self, session_id: str):
        """Update conversation summary"""
        if session_id not in self.conversations:
            return
        
        turns = self.conversations[session_id]
        if not turns:
            return
        
        # Analyze conversation patterns
        topics = [turn.topic for turn in turns[-10:]]  # Last 10 turns
        current_topic = topics[-1] if topics else ConversationTopic.GENERAL_CHAT
        
        # Track topic changes
        unique_topics = []
        for topic in topics:
            if not unique_topics or unique_topics[-1] != topic:
                unique_topics.append(topic)
        
        # Extract user preferences
        preferences = self._extract_preferences(turns)
        
        # Track active tasks
        active_tasks = self._extract_active_tasks(turns)
        
        # Determine conversation tone
        tone = self._analyze_tone(turns)
        
        # Track success/failure patterns
        last_successful = self._find_last_successful_action(turns)
        failed_attempts = self._extract_failed_attempts(turns)
        
        self.summaries[session_id] = ConversationSummary(
            current_topic=current_topic,
            previous_topics=unique_topics[:-1],  # All except current
            user_preferences=preferences,
            active_tasks=active_tasks,
            conversation_tone=tone,
            last_successful_action=last_successful,
            failed_attempts=failed_attempts
        )
    
    def _infer_topic_from_intent(self, intent: str) -> ConversationTopic:
        """Infer topic from intent"""
        intent_topic_map = {
            "user_create": ConversationTopic.USER_MANAGEMENT,
            "user_update": ConversationTopic.USER_MANAGEMENT,
            "user_delete": ConversationTopic.USER_MANAGEMENT,
            "user_list": ConversationTopic.USER_MANAGEMENT,
            "user_search": ConversationTopic.USER_MANAGEMENT,
            "service_add": ConversationTopic.SERVICE_MANAGEMENT,
            "service_list": ConversationTopic.SERVICE_MANAGEMENT,
            "knowledge_query": ConversationTopic.KNOWLEDGE_BASE,
            "troubleshooting": ConversationTopic.TROUBLESHOOTING,
            "greeting": ConversationTopic.GENERAL_CHAT,
            "unclear": ConversationTopic.GENERAL_CHAT
        }
        
        return intent_topic_map.get(intent, ConversationTopic.GENERAL_CHAT)
    
    def _extract_preferences(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """Extract user preferences from conversation"""
        preferences = {}
        
        # Analyze communication style
        user_messages = [turn.user_message for turn in turns]
        avg_length = sum(len(msg.split()) for msg in user_messages) / len(user_messages) if user_messages else 0
        
        preferences["communication_style"] = "detailed" if avg_length > 10 else "concise"
        preferences["formality"] = "casual" if any("hi" in msg.lower() or "hey" in msg.lower() for msg in user_messages) else "formal"
        
        return preferences
    
    def _extract_active_tasks(self, turns: List[ConversationTurn]) -> List[Dict[str, Any]]:
        """Extract active tasks from conversation"""
        active_tasks = []
        
        for turn in reversed(turns[-5:]):  # Last 5 turns
            if turn.intent in ["user_create", "service_add"] and "collecting" in turn.response.lower():
                active_tasks.append({
                    "type": turn.intent,
                    "status": "in_progress",
                    "started": turn.timestamp,
                    "entities_collected": turn.entities
                })
        
        return active_tasks
    
    def _analyze_tone(self, turns: List[ConversationTurn]) -> str:
        """Analyze conversation tone"""
        user_messages = [turn.user_message.lower() for turn in turns[-5:]]
        
        # Simple tone analysis
        if any("please" in msg or "thank" in msg for msg in user_messages):
            return "polite"
        elif any("bruh" in msg or "dude" in msg for msg in user_messages):
            return "casual"
        elif any("!" in msg or "?" in msg for msg in user_messages):
            return "enthusiastic"
        else:
            return "professional"
    
    def _find_last_successful_action(self, turns: List[ConversationTurn]) -> Optional[str]:
        """Find last successful action"""
        for turn in reversed(turns):
            if "success" in turn.response.lower() or "created" in turn.response.lower():
                return turn.intent
        return None
    
    def _extract_failed_attempts(self, turns: List[ConversationTurn]) -> List[str]:
        """Extract failed attempts"""
        failed = []
        for turn in turns[-10:]:
            if "error" in turn.response.lower() or "sorry" in turn.response.lower():
                failed.append(turn.intent)
        return failed[-3:]  # Last 3 failures
    
    def _calculate_duration(self, session_id: str) -> str:
        """Calculate session duration"""
        if session_id not in self.conversations or not self.conversations[session_id]:
            return "0m"
        
        first_turn = self.conversations[session_id][0]
        last_turn = self.conversations[session_id][-1]
        
        try:
            start_time = datetime.fromisoformat(first_turn.timestamp)
            end_time = datetime.fromisoformat(last_turn.timestamp)
            duration = end_time - start_time
            
            minutes = int(duration.total_seconds() // 60)
            return f"{minutes}m"
        except:
            return "0m"
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context for new conversations"""
        return {
            "recent_turns": [],
            "current_topic": None,
            "previous_topics": [],
            "user_preferences": {},
            "active_tasks": [],
            "conversation_tone": "professional",
            "last_successful_action": None,
            "failed_attempts": [],
            "conversation_length": 0,
            "session_duration": "0m"
        }

# Global conversation memory instance
conversation_memory = ConversationMemory()
