"""
Simple Flow Enhancer - Drop-in replacement for better conversation flow
Integrates directly with existing system without breaking changes
"""

import re
from typing import Dict, Any, Optional

class SimpleFlowEnhancer:
    """
    Simple drop-in enhancement for conversation flow
    """
    
    def __init__(self):
        # Cache for reducing API calls
        self.intent_cache = {}
        
        # Simple pattern matching to avoid API calls
        self.patterns = {
            "user_management": [
                r'\buser\s*(?:management|admin|mgt)\b',
                r'\b(?:manage|handle)\s+users?\b',
                r'\bcreate\s+user\b',
                r'\badd\s+user\b'
            ],
            "service_management": [
                r'\bservice\s*(?:management|admin|mgt)\b',
                r'\b(?:manage|handle)\s+services?\b',
                r'\bcreate\s+service\b',
                r'\badd\s+service\b'
            ],
            "knowledge_query": [
                r'\b(?:help|how|what|when|where|why)\b',
                r'\bfaq\b',
                r'\bquestion\b',
                r'\binformation\b'
            ],
            "troubleshooting": [
                r'\b(?:problem|issue|error|trouble|broken)\b',
                r'\bnot\s+working\b',
                r'\bfix\b'
            ]
        }
        
        # Typo corrections to avoid API calls
        self.typo_corrections = {
            "manaegment": "management",
            "managment": "management", 
            "srvice": "service",
            "sevice": "service",
            "usr": "user",
            "usre": "user"
        }
        
        # Flow transition templates
        self.transitions = {
            "user_to_service": "Great! Now let's talk about services. What do you need help with?",
            "service_to_user": "Perfect! Switching to user management. How can I help?",
            "any_to_knowledge": "I can help with that! Let me find the information for you.",
            "general": "Sure! What would you like to know about?"
        }
    
    def enhance_routing(self, message: str, current_agent: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance routing decision to reduce API calls and improve flow
        """
        
        # Normalize message
        normalized = self._normalize_message(message)
        
        # Try pattern matching first (no API call)
        pattern_result = self._match_patterns(normalized)
        
        if pattern_result["confidence"] > 0.7:
            # High confidence pattern match - no API needed
            target_agent = self._map_intent_to_agent(pattern_result["intent"])
            
            return {
                "use_api": False,
                "target_agent": target_agent,
                "intent": pattern_result["intent"],
                "confidence": pattern_result["confidence"],
                "method": "pattern_match",
                "transition_message": self._get_transition_message(current_agent, target_agent)
            }
        
        # Check for conversation flow keywords
        flow_result = self._check_conversation_flow(normalized, current_agent)
        
        if flow_result["detected"]:
            return {
                "use_api": False,
                "target_agent": flow_result["target_agent"],
                "intent": "conversation_flow",
                "confidence": flow_result["confidence"],
                "method": "conversation_flow",
                "transition_message": flow_result["transition_message"]
            }
        
        # If unclear, use API but cache result
        cache_key = self._get_cache_key(normalized)
        if cache_key in self.intent_cache:
            cached = self.intent_cache[cache_key]
            return {
                "use_api": False,
                "target_agent": cached["target_agent"],
                "intent": cached["intent"],
                "confidence": cached["confidence"],
                "method": "cached"
            }
        
        # Need API call
        return {
            "use_api": True,
            "method": "api_required"
        }
    
    def cache_api_result(self, message: str, result: Dict[str, Any]):
        """Cache API result to avoid future calls"""
        cache_key = self._get_cache_key(message)
        self.intent_cache[cache_key] = {
            "target_agent": result.get("active_agent"),
            "intent": result.get("intent", "unclear"),
            "confidence": 0.8
        }
    
    def _normalize_message(self, message: str) -> str:
        """Normalize message with typo correction"""
        words = message.lower().split()
        corrected = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            corrected.append(self.typo_corrections.get(clean_word, word))
        
        return ' '.join(corrected)
    
    def _match_patterns(self, message: str) -> Dict[str, Any]:
        """Match message against patterns"""
        
        best_intent = None
        best_confidence = 0.0
        
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    # Calculate confidence based on pattern specificity
                    confidence = 0.8 + (len(pattern) / 1000)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        return {
            "intent": best_intent,
            "confidence": min(best_confidence, 1.0) if best_intent else 0.0
        }
    
    def _check_conversation_flow(self, message: str, current_agent: str) -> Dict[str, Any]:
        """Check for conversation flow patterns"""
        
        # Topic switch phrases
        switch_phrases = ["what about", "how about", "tell me about", "what else"]
        
        for phrase in switch_phrases:
            if phrase in message:
                # Infer target from remaining message
                remaining = message.replace(phrase, "").strip()
                
                if "service" in remaining:
                    return {
                        "detected": True,
                        "target_agent": "service_management",
                        "confidence": 0.9,
                        "transition_message": self.transitions["any_to_service"] if current_agent != "service_management" else ""
                    }
                elif "user" in remaining:
                    return {
                        "detected": True,
                        "target_agent": "user_management", 
                        "confidence": 0.9,
                        "transition_message": self.transitions["service_to_user"] if current_agent == "service_management" else ""
                    }
                elif any(word in remaining for word in ["help", "question", "how"]):
                    return {
                        "detected": True,
                        "target_agent": "knowledge_base",
                        "confidence": 0.85,
                        "transition_message": self.transitions["any_to_knowledge"]
                    }
        
        # Continuation phrases
        continuation_phrases = ["also", "and", "plus"]
        
        if any(phrase in message for phrase in continuation_phrases):
            # Continue with current agent unless explicit switch
            return {
                "detected": True,
                "target_agent": current_agent,
                "confidence": 0.95,
                "transition_message": ""
            }
        
        return {"detected": False}
    
    def _map_intent_to_agent(self, intent: str) -> str:
        """Map intent to agent"""
        
        mapping = {
            "user_management": "user_management",
            "service_management": "service_management",
            "knowledge_query": "knowledge_base", 
            "troubleshooting": "knowledge_base"
        }
        
        return mapping.get(intent, "conversation_manager")
    
    def _get_transition_message(self, from_agent: str, to_agent: str) -> str:
        """Get transition message"""
        
        if from_agent == to_agent:
            return ""
        
        key = f"{from_agent}_to_{to_agent.split('_')[0]}"
        return self.transitions.get(key, self.transitions["general"])
    
    def _get_cache_key(self, message: str) -> str:
        """Get cache key for message"""
        # Simple key based on main words
        words = [w for w in message.split() if len(w) > 3]
        return "_".join(sorted(words[:3]))  # Top 3 significant words

# Global instance
flow_enhancer = SimpleFlowEnhancer()
