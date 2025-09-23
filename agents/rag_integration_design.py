"""
RAG-Enhanced Multi-Agent System Architecture
Seamless Cross-Agent Knowledge Sharing

DESIGN: Shared Knowledge Base + Agent Specialization
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class ConversationContext:
    """Shared context across all agents"""
    session_id: str
    user_id: str
    current_topic: str
    entities_mentioned: List[str]  # users, services, issues mentioned
    conversation_history: List[Dict]
    active_operations: List[Dict]  # ongoing user creation, service requests, etc.
    resolved_entities: Dict[str, Any]  # resolved references like "john" → user_id_123

class RAGKnowledgeBase:
    """
    Unified knowledge base that all agents can query and update
    """
    
    def __init__(self):
        self.vector_store = None  # ChromaDB, Pinecone, etc.
        self.conversation_memory = {}
        self.entity_resolver = EntityResolver()
    
    def store_conversation_context(self, context: ConversationContext):
        """Store conversation context for cross-agent access"""
        
        # Index conversation for semantic search
        conversation_text = " ".join([msg["content"] for msg in context.conversation_history])
        
        # Store with metadata for filtering
        metadata = {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "timestamp": datetime.now().isoformat(),
            "topic": context.current_topic,
            "entities": context.entities_mentioned
        }
        
        self.vector_store.add(
            documents=[conversation_text],
            metadatas=[metadata],
            ids=[f"conversation_{context.session_id}_{datetime.now().timestamp()}"]
        )
    
    def query_cross_agent_context(self, query: str, current_agent: str, 
                                  session_id: str) -> Dict[str, Any]:
        """
        Get relevant context from other agents' interactions
        """
        
        # Semantic search for relevant conversations
        results = self.vector_store.query(
            query_texts=[query],
            where={"session_id": session_id},
            n_results=5
        )
        
        # Extract entities mentioned in query
        mentioned_entities = self.entity_resolver.extract_entities(query)
        
        # Get resolved entity data
        entity_data = {}
        for entity in mentioned_entities:
            resolved = self.entity_resolver.resolve_entity(entity, session_id)
            if resolved:
                entity_data[entity] = resolved
        
        return {
            "relevant_conversations": results,
            "mentioned_entities": mentioned_entities,
            "entity_data": entity_data,
            "conversation_context": self.conversation_memory.get(session_id, {})
        }
    
    def update_entity_state(self, entity_type: str, entity_id: str, 
                           data: Dict[str, Any], session_id: str):
        """Update entity state across agents"""
        
        # Store in vector database for semantic search
        entity_text = f"{entity_type} {entity_id}: " + " ".join([f"{k}: {v}" for k, v in data.items()])
        
        metadata = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        self.vector_store.add(
            documents=[entity_text],
            metadatas=[metadata],
            ids=[f"entity_{entity_type}_{entity_id}_{session_id}"]
        )

class EntityResolver:
    """
    Resolves entity references across conversation context
    Example: "john" → user_id_123, "that user" → last mentioned user
    """
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract entity references from text"""
        
        entities = []
        
        # Names (potential user references)
        import re
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(names)
        
        # Pronouns and references
        references = re.findall(r'\b(?:that user|this user|him|her|they|that service|this service)\b', text, re.IGNORECASE)
        entities.extend(references)
        
        # Service names
        services = re.findall(r'\b(?:room service|housekeeping|maintenance|wifi|ac)\b', text, re.IGNORECASE)
        entities.extend(services)
        
        return entities
    
    def resolve_entity(self, entity: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Resolve entity reference to actual data"""
        
        # This would query your RAG system for entity resolution
        # Example: "john" → search for recently created user named john
        pass

class RAGEnhancedAgent:
    """
    Base class for agents with RAG integration
    All agents inherit shared context awareness
    """
    
    def __init__(self, agent_name: str, rag_kb: RAGKnowledgeBase):
        self.agent_name = agent_name
        self.rag_kb = rag_kb
    
    def process_with_context(self, message: str, session_state: Dict) -> Dict[str, Any]:
        """Process message with full cross-agent context"""
        
        # 1. Get relevant context from other agents
        context = self.rag_kb.query_cross_agent_context(
            message, self.agent_name, session_state["session_id"]
        )
        
        # 2. Process with enhanced context
        response = self._process_message_with_context(message, context, session_state)
        
        # 3. Update shared knowledge
        self._update_shared_knowledge(message, response, session_state)
        
        return response
    
    def _process_message_with_context(self, message: str, context: Dict, 
                                     session_state: Dict) -> Dict[str, Any]:
        """Override in each agent"""
        pass
    
    def _update_shared_knowledge(self, message: str, response: Dict, 
                                session_state: Dict):
        """Update RAG knowledge base with new information"""
        
        # Store conversation context
        conv_context = ConversationContext(
            session_id=session_state["session_id"],
            user_id=session_state["user_id"],
            current_topic=self.agent_name,
            entities_mentioned=self.rag_kb.entity_resolver.extract_entities(message),
            conversation_history=[{"role": "user", "content": message}, 
                                {"role": "assistant", "content": response.get("response", "")}],
            active_operations=session_state.get("active_operations", []),
            resolved_entities={}
        )
        
        self.rag_kb.store_conversation_context(conv_context)

# IMPLEMENTATION EXAMPLE:

class RAGUserManagementAgent(RAGEnhancedAgent):
    """User Management with RAG context awareness"""
    
    def _process_message_with_context(self, message: str, context: Dict, 
                                     session_state: Dict) -> Dict[str, Any]:
        
        # Check if user is referencing previously mentioned entities
        if "john" in message.lower() and context["entity_data"]:
            john_data = context["entity_data"].get("john")
            if john_data:
                return {
                    "response": f"I found John {john_data['last_name']} in our system. What would you like to do with his account?",
                    "entity_context": john_data
                }
        
        # Normal user management processing...
        return self._create_user_normally(message, session_state)

class RAGServiceManagementAgent(RAGEnhancedAgent):
    """Service Management with cross-agent user awareness"""
    
    def _process_message_with_context(self, message: str, context: Dict, 
                                     session_state: Dict) -> Dict[str, Any]:
        
        # If user mentions someone from previous conversation
        if context["entity_data"]:
            user_context = ""
            for entity, data in context["entity_data"].items():
                if data.get("type") == "user":
                    user_context += f"User {entity}: {data['role']} at {data.get('department', 'Unknown')}. "
            
            if user_context:
                return {
                    "response": f"I have context about: {user_context}. What service would you like to set up?",
                    "context_aware": True
                }
        
        return self._normal_service_processing(message, session_state)

# CONVERSATION FLOW EXAMPLE:
"""
User: "create user john doe, manager, john@hotel.com"
→ UserMgmtAgent creates user + stores to RAG

User: "what services can john access?"
→ ServiceMgmtAgent queries RAG → finds john → "John Doe (Manager) can access: Executive services, Room service priority..."

User: "john's wifi isn't working" 
→ TroubleshootAgent queries RAG → finds john's info → "I'll help troubleshoot WiFi for John Doe (Manager, Room 205)..."
"""
