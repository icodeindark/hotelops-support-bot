"""
Natural Language Processor for Human-like Understanding
International standard NLP with context awareness
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from llm_utils import ask_gemini

@dataclass
class EntityMatch:
    """Represents a matched entity with confidence"""
    entity_type: str
    value: str
    confidence: float
    source: str  # "regex", "llm", "fuzzy", "context"
    span: Tuple[int, int]  # Start and end position in text

@dataclass
class IntentClassification:
    """Enhanced intent classification with reasoning"""
    intent: str
    confidence: float
    reasoning: str
    alternative_intents: List[Dict[str, float]]
    context_factors: List[str]

class NaturalLanguageProcessor:
    """
    Advanced NLP for natural conversation understanding
    """
    
    def __init__(self):
        self.fuzzy_threshold = 0.7
        self.context_weight = 0.3
        
        # Intent patterns with typo variations
        self.intent_patterns = self._initialize_flexible_patterns()
        
        # Common typos and corrections
        self.typo_corrections = {
            "manaegment": "management", "managment": "management", "mangement": "management",
            "srvice": "service", "sevice": "service", "serrvice": "service",
            "troubleshoot": "troubleshoot", "troubleshot": "troubleshoot",
            "pasword": "password", "passowrd": "password",
            "accont": "account", "acount": "account",
            "emaail": "email", "emial": "email",
            "usre": "user", "usr": "user"
        }
        
        # Contextual entity patterns
        self.contextual_patterns = {
            "email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'\b\w+\s*@\s*\w+\s*\.\s*\w+\b'  # Spaced emails
            ],
            "phone": [
                r'\b(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\d{10}\b'
            ],
            "name": [
                r'\b(?:name\s*[:=]\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b(?:call\s+me|i\s*am|my\s+name\s+is)\s+([A-Z][a-z]+)\b',
                r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b'  # First Last
            ]
        }
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process message with full NLP pipeline
        """
        # Normalize and correct typos
        normalized_message = self.normalize_text(message)
        
        # Enhanced intent classification
        intent_result = self.classify_intent_enhanced(normalized_message, context)
        
        # Advanced entity extraction
        entities = self.extract_entities_advanced(normalized_message, context, intent_result.intent)
        
        # Sentiment analysis
        sentiment = self.analyze_sentiment(normalized_message)
        
        # Context analysis
        context_analysis = self.analyze_context(normalized_message, context)
        
        return {
            "original_message": message,
            "normalized_message": normalized_message,
            "intent": intent_result.intent,
            "intent_confidence": intent_result.confidence,
            "intent_reasoning": intent_result.reasoning,
            "alternative_intents": intent_result.alternative_intents,
            "entities": entities,
            "sentiment": sentiment,
            "context_analysis": context_analysis,
            "requires_clarification": self.requires_clarification(intent_result, entities),
            "suggested_responses": self.generate_response_suggestions(intent_result, entities, context)
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text with typo correction"""
        # Basic normalization
        text = text.lower().strip()
        
        # Correct common typos
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.typo_corrections:
                corrected_words.append(self.typo_corrections[clean_word])
            else:
                # Fuzzy matching for unknown typos
                best_match = self.find_best_fuzzy_match(clean_word)
                corrected_words.append(best_match if best_match else word)
        
        return ' '.join(corrected_words)
    
    def classify_intent_enhanced(self, message: str, context: Dict[str, Any]) -> IntentClassification:
        """Enhanced intent classification with context"""
        
        # Get conversation context
        current_topic = context.get("current_topic")
        previous_intents = [turn["intent"] for turn in context.get("recent_turns", [])]
        
        # Pattern-based classification
        pattern_matches = self._match_intent_patterns(message)
        
        # Context-based boosting
        if current_topic and pattern_matches:
            pattern_matches = self._boost_contextual_intents(pattern_matches, current_topic)
        
        # LLM classification for unclear cases
        if not pattern_matches or max(pattern_matches.values()) < 0.7:
            llm_result = self._classify_with_llm(message, context)
            return llm_result
        
        # Get best pattern match
        best_intent = max(pattern_matches, key=pattern_matches.get)
        confidence = pattern_matches[best_intent]
        
        # Generate reasoning
        reasoning = f"Pattern-based match for '{best_intent}' with confidence {confidence:.2f}"
        if current_topic:
            reasoning += f". Context: Currently in {current_topic} topic."
        
        # Alternative intents
        alternatives = [
            {"intent": intent, "confidence": conf} 
            for intent, conf in sorted(pattern_matches.items(), key=lambda x: x[1], reverse=True)[1:4]
        ]
        
        return IntentClassification(
            intent=best_intent,
            confidence=confidence,
            reasoning=reasoning,
            alternative_intents=alternatives,
            context_factors=[current_topic] if current_topic else []
        )
    
    def extract_entities_advanced(self, message: str, context: Dict[str, Any], intent: str) -> List[EntityMatch]:
        """Advanced entity extraction with context awareness"""
        entities = []
        
        # Extract using multiple methods
        
        # 1. Regex-based extraction
        regex_entities = self._extract_with_regex(message)
        entities.extend(regex_entities)
        
        # 2. Context-aware extraction
        context_entities = self._extract_with_context(message, context, intent)
        entities.extend(context_entities)
        
        # 3. LLM-based extraction for complex cases
        if intent in ["user_create", "user_update"] and len(entities) < 2:
            llm_entities = self._extract_with_llm(message, intent)
            entities.extend(llm_entities)
        
        # 4. Fuzzy matching for partial data
        fuzzy_entities = self._extract_with_fuzzy_matching(message, context)
        entities.extend(fuzzy_entities)
        
        # Deduplicate and rank entities
        return self._deduplicate_entities(entities)
    
    def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze sentiment and emotional tone"""
        # Simple rule-based sentiment
        positive_words = ["thanks", "great", "awesome", "good", "excellent", "perfect"]
        negative_words = ["problem", "issue", "error", "bad", "terrible", "awful", "frustrated"]
        casual_words = ["bruh", "dude", "hey", "lol", "haha"]
        
        message_lower = message.lower()
        
        positive_score = sum(1 for word in positive_words if word in message_lower)
        negative_score = sum(1 for word in negative_words if word in message_lower)
        casual_score = sum(1 for word in casual_words if word in message_lower)
        
        if casual_score > 0:
            tone = "casual"
        elif positive_score > negative_score:
            tone = "positive"
        elif negative_score > positive_score:
            tone = "negative"
        else:
            tone = "neutral"
        
        return {
            "tone": tone,
            "formality": "informal" if casual_score > 0 else "formal",
            "urgency": "high" if negative_score > 1 else "normal"
        }
    
    def analyze_context(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversational context"""
        
        analysis = {
            "is_follow_up": False,
            "references_previous": False,
            "topic_continuity": True,
            "clarity_level": "clear"
        }
        
        # Check for follow-up indicators
        follow_up_phrases = ["also", "and", "what about", "how about", "what else"]
        analysis["is_follow_up"] = any(phrase in message.lower() for phrase in follow_up_phrases)
        
        # Check for references to previous conversation
        reference_phrases = ["that", "it", "this", "the one", "mentioned"]
        analysis["references_previous"] = any(phrase in message.lower() for phrase in reference_phrases)
        
        # Assess clarity
        if len(message.split()) < 3:
            analysis["clarity_level"] = "unclear"
        elif any(word in message.lower() for word in ["what", "how", "where", "when", "why"]):
            analysis["clarity_level"] = "question"
        else:
            analysis["clarity_level"] = "clear"
        
        return analysis
    
    def requires_clarification(self, intent_result: IntentClassification, entities: List[EntityMatch]) -> bool:
        """Determine if clarification is needed"""
        
        # Low intent confidence
        if intent_result.confidence < 0.6:
            return True
        
        # Ambiguous intent with close alternatives
        if (intent_result.alternative_intents and 
            intent_result.alternative_intents[0]["confidence"] > intent_result.confidence - 0.2):
            return True
        
        # Intent requires entities but none found
        entity_required_intents = ["user_create", "user_update", "service_add"]
        if intent_result.intent in entity_required_intents and len(entities) == 0:
            return True
        
        return False
    
    def generate_response_suggestions(self, intent_result: IntentClassification, 
                                    entities: List[EntityMatch], context: Dict[str, Any]) -> List[str]:
        """Generate natural response suggestions"""
        
        suggestions = []
        
        # Based on intent confidence
        if intent_result.confidence < 0.6:
            suggestions.append("I want to make sure I understand correctly...")
            
        # Based on entities found
        if entities:
            entity_types = [e.entity_type for e in entities]
            if "email" in entity_types:
                suggestions.append("I see you provided an email address...")
            if "name" in entity_types:
                suggestions.append("Got it! I have the name...")
        
        # Based on context
        if context.get("conversation_tone") == "casual":
            suggestions.append("Sure thing!")
        else:
            suggestions.append("I'd be happy to help with that.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _initialize_flexible_patterns(self) -> Dict[str, List[str]]:
        """Initialize flexible intent patterns"""
        return {
            "user_create": [
                r'\b(?:add|create|new|register)\s+(?:user|account|employee)\b',
                r'\buser\s+(?:creation|registration)\b',
                r'\bneed\s+to\s+(?:add|create)\b',
                r'\b(?:sign\s+up|onboard)\b'
            ],
            "user_management": [
                r'\buser\s+(?:management|admin)\b',
                r'\b(?:manage|handle)\s+users\b',
                r'\buser\s+operations\b'
            ],
            "service_management": [
                r'\bservice\s+(?:management|admin)\b',
                r'\b(?:manage|handle)\s+services\b',
                r'\bservice\s+operations\b'
            ],
            "knowledge_query": [
                r'\b(?:how\s+to|what\s+is|tell\s+me)\b',
                r'\b(?:explain|help\s+with|guide)\b',
                r'\b(?:information|details)\s+(?:about|on)\b'
            ],
            "troubleshooting": [
                r'\b(?:problem|issue|error|trouble)\b',
                r'\b(?:not\s+working|broken|fix)\b',
                r'\b(?:help|support)\b.*\b(?:with|for)\b'
            ]
        }
    
    def _match_intent_patterns(self, message: str) -> Dict[str, float]:
        """Match message against intent patterns"""
        matches = {}
        
        for intent, patterns in self.intent_patterns.items():
            max_confidence = 0
            
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    # Simple confidence based on pattern specificity
                    confidence = 0.8 + (len(pattern) / 1000)  # Longer patterns = higher confidence
                    max_confidence = max(max_confidence, confidence)
            
            if max_confidence > 0:
                matches[intent] = min(max_confidence, 1.0)
        
        return matches
    
    def _boost_contextual_intents(self, matches: Dict[str, float], current_topic: str) -> Dict[str, float]:
        """Boost intent confidence based on context"""
        
        topic_intent_map = {
            "user_management": ["user_create", "user_update", "user_delete", "user_list"],
            "service_management": ["service_add", "service_list"],
            "knowledge_base": ["knowledge_query"],
            "troubleshooting": ["troubleshooting"]
        }
        
        boosted_matches = matches.copy()
        
        for intent in matches:
            for topic, related_intents in topic_intent_map.items():
                if current_topic == topic and intent in related_intents:
                    boosted_matches[intent] = min(matches[intent] + self.context_weight, 1.0)
        
        return boosted_matches
    
    def _classify_with_llm(self, message: str, context: Dict[str, Any]) -> IntentClassification:
        """Classify intent using LLM"""
        
        # Enhanced prompt with context
        prompt = f"""
        Classify the user intent for this message in a hotel management system.
        
        Message: "{message}"
        
        Context:
        - Current topic: {context.get('current_topic', 'None')}
        - Recent conversation: {context.get('recent_turns', [])}
        - User preferences: {context.get('user_preferences', {})}
        
        Available intents:
        - user_create: Creating new users
        - user_update: Updating user information
        - user_delete: Deleting users
        - user_list: Listing users
        - service_add: Adding services
        - service_list: Listing services
        - knowledge_query: General questions
        - troubleshooting: Problem solving
        - greeting: Greetings
        - unclear: Unclear intent
        
        Return JSON with:
        - intent: best matching intent
        - confidence: confidence score (0-1)
        - reasoning: explanation of the classification
        """
        
        try:
            response = ask_gemini(prompt)
            result = json.loads(response)
            
            return IntentClassification(
                intent=result.get("intent", "unclear"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", "LLM classification"),
                alternative_intents=[],
                context_factors=[]
            )
        except Exception as e:
            return IntentClassification(
                intent="unclear",
                confidence=0.3,
                reasoning=f"LLM classification failed: {str(e)}",
                alternative_intents=[],
                context_factors=[]
            )
    
    def find_best_fuzzy_match(self, word: str) -> str:
        """Find best fuzzy match for a word"""
        if len(word) < 3:
            return word
        
        # Check against known corrections
        best_match = word
        best_ratio = 0
        
        for typo, correction in self.typo_corrections.items():
            ratio = SequenceMatcher(None, word, typo).ratio()
            if ratio > best_ratio and ratio > self.fuzzy_threshold:
                best_ratio = ratio
                best_match = correction
        
        return best_match
    
    def _extract_with_regex(self, message: str) -> List[EntityMatch]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.contextual_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, message, re.IGNORECASE)
                for match in matches:
                    entities.append(EntityMatch(
                        entity_type=entity_type,
                        value=match.group(0),
                        confidence=0.9,
                        source="regex",
                        span=(match.start(), match.end())
                    ))
        
        return entities
    
    def _extract_with_context(self, message: str, context: Dict[str, Any], intent: str) -> List[EntityMatch]:
        """Extract entities using conversational context"""
        entities = []
        
        # If we're in user creation and see potential names
        if intent == "user_create":
            words = message.split()
            for i, word in enumerate(words):
                if word.istitle() and len(word) > 2:
                    # Check if it's likely a name based on context
                    if i == 0 or words[i-1].lower() in ["name", "called", "hi", "hello"]:
                        entities.append(EntityMatch(
                            entity_type="first_name",
                            value=word,
                            confidence=0.7,
                            source="context",
                            span=(0, 0)  # Simplified
                        ))
        
        return entities
    
    def _extract_with_llm(self, message: str, intent: str) -> List[EntityMatch]:
        """Extract entities using LLM"""
        entities = []
        
        prompt = f"""
        Extract relevant entities from this message for intent: {intent}
        Message: "{message}"
        
        Return JSON array of entities:
        [
          {{"type": "entity_type", "value": "extracted_value", "confidence": 0.8}}
        ]
        
        Entity types: first_name, last_name, email, phone, role, department
        """
        
        try:
            response = ask_gemini(prompt)
            result = json.loads(response)
            
            for item in result:
                entities.append(EntityMatch(
                    entity_type=item["type"],
                    value=item["value"],
                    confidence=item["confidence"],
                    source="llm",
                    span=(0, 0)
                ))
        except Exception:
            pass  # Graceful degradation
        
        return entities
    
    def _extract_with_fuzzy_matching(self, message: str, context: Dict[str, Any]) -> List[EntityMatch]:
        """Extract entities using fuzzy matching"""
        entities = []
        
        # Look for potential emails with typos
        words = message.split()
        for word in words:
            if "@" in word and "." in word:
                # Likely an email, even with typos
                entities.append(EntityMatch(
                    entity_type="email",
                    value=word,
                    confidence=0.6,
                    source="fuzzy",
                    span=(0, 0)
                ))
        
        return entities
    
    def _deduplicate_entities(self, entities: List[EntityMatch]) -> List[EntityMatch]:
        """Remove duplicate entities and keep highest confidence"""
        
        # Group by entity type and value
        entity_groups = {}
        
        for entity in entities:
            key = (entity.entity_type, entity.value.lower())
            if key not in entity_groups or entity.confidence > entity_groups[key].confidence:
                entity_groups[key] = entity
        
        return list(entity_groups.values())

# Global NLP processor instance
nlp_processor = NaturalLanguageProcessor()
