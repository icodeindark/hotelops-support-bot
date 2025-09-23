"""
RAG-Enhanced Knowledge Base Agent
Handles FAQ and troubleshooting queries using LangChain + Gemini embeddings
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .state_schema import ChatState, add_message_to_state, update_state_timestamp
from rag.rag_system import get_rag_system
from logger_config import agent_logger, log_action, log_error

class KnowledgeBaseAgent:
    """
    Knowledge Base Agent with RAG integration
    Specialized for FAQ and troubleshooting assistance
    """
    
    def __init__(self):
        self.agent_name = "knowledge_base"
        self.knowledge_stats = {
            "total_queries": 0,
            "successful_responses": 0,
            "categories_accessed": set()
        }
        
        # Initialize RAG system
        self.rag_system = get_rag_system()
        
        agent_logger.info("Knowledge Base Agent initialized with LangChain RAG support")
    
    def handle_knowledge_query(self, state: ChatState, message: str) -> ChatState:
        """
        Main entry point for knowledge base queries
        """
        
        log_action("KNOWLEDGE_QUERY", f"Processing query: {message[:100]}", 
                  session_id=state["session_id"])
        
        self.knowledge_stats["total_queries"] += 1
        
        try:
            # Determine query type and route accordingly
            query_type = self._classify_query_type(message)
            
            if query_type == "troubleshooting":
                response = self._handle_troubleshooting_query(message, state)
            elif query_type == "faq":
                response = self._handle_faq_query(message, state)
            else:
                response = self._handle_general_query(message, state)
            
            # Add response to state
            updated_state = add_message_to_state(
                state, response, "assistant",
                agent_id="knowledge_base",
                metadata={
                    "query_type": query_type,
                    "search_terms": message[:50]
                }
            )
            
            self.knowledge_stats["successful_responses"] += 1
            
            log_action("KNOWLEDGE_RESPONSE", f"Response generated for {query_type} query", 
                      session_id=state["session_id"])
            
            return update_state_timestamp(updated_state)
            
        except Exception as e:
            error_msg = f"Knowledge base error: {str(e)}"
            log_error("KNOWLEDGE_ERROR", error_msg, session_id=state["session_id"])
            
            # Fallback response
            fallback_response = "I encountered an issue searching the knowledge base. Please try rephrasing your question or contact support."
            
            updated_state = add_message_to_state(
                state, fallback_response, "assistant",
                agent_id="knowledge_base",
                metadata={"error": error_msg}
            )
            
            return update_state_timestamp(updated_state)
    
    def _classify_query_type(self, message: str) -> str:
        """Classify the type of knowledge query"""
        
        message_lower = message.lower()
        
        # Troubleshooting indicators
        troubleshooting_terms = [
            "problem", "issue", "error", "not working", "broken", "fix",
            "trouble", "can't", "won't", "doesn't work", "help", "stuck"
        ]
        
        if any(term in message_lower for term in troubleshooting_terms):
            return "troubleshooting"
        
        # FAQ indicators
        faq_terms = [
            "how to", "how do i", "what is", "what are", "when", "where",
            "explain", "tell me", "guide", "steps", "procedure"
        ]
        
        if any(term in message_lower for term in faq_terms):
            return "faq"
        
        return "general"
    
    def _handle_troubleshooting_query(self, message: str, state: ChatState) -> str:
        """Handle troubleshooting-specific queries"""
        
        self.knowledge_stats["categories_accessed"].add("troubleshooting")
        
        # Use RAG to search for troubleshooting information
        rag_results = self.rag_system.search(message, max_results=3)
        
        if rag_results:
            # Prioritize troubleshooting and procedure results
            relevant_results = [r for r in rag_results if r['type'] in ['troubleshooting', 'procedure']]
            if not relevant_results:
                relevant_results = rag_results[:2]  # Fallback to any relevant results
            
            context = self._format_rag_results(relevant_results, message)
        else:
            context = self._generate_helpful_fallback(message, "troubleshooting")
        
        return context
    
    def _handle_faq_query(self, message: str, state: ChatState) -> str:
        """Handle FAQ-specific queries"""
        
        self.knowledge_stats["categories_accessed"].add("faq")
        
        # Use RAG to search for FAQ information
        rag_results = self.rag_system.search(message, max_results=3)
        
        if rag_results:
            # Prioritize FAQ results
            faq_results = [r for r in rag_results if r['type'] == 'faq']
            if not faq_results:
                faq_results = rag_results[:3]  # Fallback to any relevant results
            
            response = self._format_rag_results(faq_results, message)
        else:
            response = self._generate_helpful_fallback(message, "faq")
        
        return response
    
    def _handle_general_query(self, message: str, state: ChatState) -> str:
        """Handle general knowledge queries"""
        
        self.knowledge_stats["categories_accessed"].add("general")
        
        # Use RAG to search all knowledge
        rag_results = self.rag_system.search(message, max_results=3)
        
        if rag_results:
            response = self._format_rag_results(rag_results, message)
        else:
            response = self._generate_helpful_fallback(message, "general")
        
        return response
    
    def _format_rag_results(self, results: List[Dict[str, Any]], query: str = "") -> str:
        """Format RAG search results for clean Streamlit display"""
        
        if not results:
            return f"I couldn't find specific information about '{query}'. Could you try rephrasing your question?"
        
        if len(results) == 1:
            # Single result - format cleanly
            result = results[0]
            title = result.get("title", "Information")
            content = result.get("content", "")
            
            # Extract the answer part from content
            if "A: " in content:
                answer = content.split("A: ", 1)[1]
            elif "Solution: " in content:
                answer = content.split("Solution: ", 1)[1]
            elif "Steps:" in content:
                answer = content.split("Steps:", 1)[1].strip()
            else:
                answer = content
            
            return f"**{title}**\n\n{answer.strip()}"
        
        else:
            # Multiple results - format as clean list
            response = f"Here are {len(results)} relevant answers:\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "Information")
                content = result.get("content", "")
                
                # Extract the answer part from content
                if "A: " in content:
                    answer = content.split("A: ", 1)[1]
                elif "Solution: " in content:
                    answer = content.split("Solution: ", 1)[1]
                elif "Steps:" in content:
                    answer = content.split("Steps:", 1)[1].strip()
                else:
                    answer = content
                
                response += f"**{i}. {title}**\n{answer.strip()}\n\n"
            
            return response.strip()
    
    def _generate_helpful_fallback(self, message: str, query_type: str) -> str:
        """Generate helpful fallback when no specific answers are found"""
        
        # Get RAG system stats for suggestions
        stats = self.rag_system.get_stats()
        
        base_response = f"I couldn't find specific information about '{message[:50]}...' in the knowledge base."
        
        if query_type == "troubleshooting":
            suggestions = [
                "Try describing the issue in more detail",
                "Mention specific error messages if any",
                "Include what you were trying to do when the problem occurred"
            ]
        elif query_type == "faq":
            suggestions = [
                "Try rephrasing your question",
                "Ask about specific features or procedures",
                "Be more specific about what you want to know"
            ]
        else:
            suggestions = [
                "Try using different keywords",
                "Ask about user management, services, or troubleshooting",
                "Be more specific about what you need help with"
            ]
        
        response = f"{base_response}\n\n**Suggestions:**\n"
        for suggestion in suggestions:
            response += f"• {suggestion}\n"
        
        response += f"\n**Available topics:** We have {stats['total_documents']} knowledge items available through semantic search."
        
        return response
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        
        success_rate = (self.knowledge_stats["successful_responses"] / 
                       max(self.knowledge_stats["total_queries"], 1)) * 100
        
        return {
            "total_queries": self.knowledge_stats["total_queries"],
            "successful_responses": self.knowledge_stats["successful_responses"],
            "success_rate": f"{success_rate:.1f}%",
            "categories_accessed": list(self.knowledge_stats["categories_accessed"]),
            "rag_system_stats": self.rag_system.get_stats()
        }

# Create agent instance
knowledge_base_agent = KnowledgeBaseAgent()
