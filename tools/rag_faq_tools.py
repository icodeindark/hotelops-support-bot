"""
RAG-Enhanced FAQ and Troubleshooting Tools
Simple, focused RAG for knowledge base queries
"""

import json
import os
from typing import List, Dict, Any, Optional
from agents.simple_rag_knowledge import SimpleRAGKnowledge

# Initialize RAG knowledge base (singleton pattern)
_rag_kb = None

def get_rag_knowledge_base() -> SimpleRAGKnowledge:
    """Get or create RAG knowledge base instance"""
    global _rag_kb
    if _rag_kb is None:
        _rag_kb = SimpleRAGKnowledge()
    return _rag_kb

def search_knowledge_base(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the RAG knowledge base for relevant information
    
    Args:
        query: User's question or search term
        max_results: Maximum number of results to return
        
    Returns:
        List of relevant knowledge items with scores
    """
    try:
        rag_kb = get_rag_knowledge_base()
        results = rag_kb.search_knowledge(query, max_results)
        
        # Format for compatibility with existing system
        formatted_results = []
        for result in results:
            formatted_results.append({
                "question": result["title"],
                "answer": result["content"].split("A: ")[-1] if "A: " in result["content"] else result["content"],
                "category": result["category"],
                "relevance_score": result["relevance_score"],
                "tags": result.get("tags", [])
            })
        
        return formatted_results
        
    except Exception as e:
        print(f"RAG search error: {e}")
        # Fallback to basic FAQ search
        return fallback_faq_search(query, max_results)

def search_faq_only(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Search only FAQ items"""
    try:
        rag_kb = get_rag_knowledge_base()
        faq_items = rag_kb.get_category_items("faq")
        
        # Simple keyword scoring for FAQ items
        query_lower = query.lower()
        scored_items = []
        
        for item in faq_items:
            score = 0
            title_lower = item["title"].lower()
            content_lower = item["content"].lower()
            
            # Score based on keyword matches
            query_words = query_lower.split()
            for word in query_words:
                if word in title_lower:
                    score += 3
                if word in content_lower:
                    score += 1
            
            if score > 0:
                scored_items.append({
                    "question": item["title"],
                    "answer": item["content"].split("A: ")[-1] if "A: " in item["content"] else item["content"],
                    "category": item["category"],
                    "relevance_score": score,
                    "tags": item.get("tags", [])
                })
        
        # Sort by score and return top results
        scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_items[:max_results]
        
    except Exception as e:
        print(f"FAQ search error: {e}")
        return []

def search_troubleshooting_only(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Search only troubleshooting items"""
    try:
        rag_kb = get_rag_knowledge_base()
        troubleshooting_items = rag_kb.get_category_items("troubleshooting")
        
        # Simple keyword scoring
        query_lower = query.lower()
        scored_items = []
        
        for item in troubleshooting_items:
            score = 0
            title_lower = item["title"].lower()
            content_lower = item["content"].lower()
            
            query_words = query_lower.split()
            for word in query_words:
                if word in title_lower:
                    score += 3
                if word in content_lower:
                    score += 1
                # Boost score for problem-related terms
                if word in ["problem", "issue", "error", "not working", "broken"]:
                    score += 2
            
            if score > 0:
                scored_items.append({
                    "question": item["title"],
                    "answer": item["content"].split("Solution: ")[-1] if "Solution: " in item["content"] else item["content"],
                    "category": item["category"],
                    "relevance_score": score,
                    "tags": item.get("tags", [])
                })
        
        scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_items[:max_results]
        
    except Exception as e:
        print(f"Troubleshooting search error: {e}")
        return []

def fallback_faq_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Fallback search using original FAQ file"""
    try:
        faq_file = os.path.join("context", "faq.json")
        with open(faq_file, 'r', encoding='utf-8') as f:
            faq_data = json.load(f)
        
        query_lower = query.lower()
        scored_items = []
        
        for question, answer in faq_data.items():
            score = 0
            question_lower = question.lower()
            answer_lower = answer.lower()
            
            query_words = query_lower.split()
            for word in query_words:
                if word in question_lower:
                    score += 3
                if word in answer_lower:
                    score += 1
            
            if score > 0:
                scored_items.append({
                    "question": question,
                    "answer": answer,
                    "category": "faq",
                    "relevance_score": score,
                    "tags": []
                })
        
        scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_items[:max_results]
        
    except Exception as e:
        print(f"Fallback FAQ search error: {e}")
        return []

def format_knowledge_results(results: List[Dict[str, Any]], query: str = "") -> str:
    """Format knowledge base results for display"""
    if not results:
        return f"💡 No specific information found for '{query}'. Try rephrasing your question or ask about:\n• User management\n• Password reset\n• Service setup\n• Troubleshooting"
    
    response = f"💡 **Found {len(results)} relevant answer(s):**\n\n"
    
    for i, result in enumerate(results, 1):
        question = result.get("question", "")
        answer = result.get("answer", "")
        category = result.get("category", "").title()
        
        response += f"**{i}. {question}**\n"
        if category and category != "Faq":
            response += f"*Category: {category}*\n"
        response += f"{answer}\n\n"
    
    return response.strip()

def get_enhanced_troubleshooting_context(query: str) -> str:
    """Get enhanced troubleshooting context using RAG"""
    
    # First try troubleshooting-specific search
    troubleshooting_results = search_troubleshooting_only(query, 2)
    
    # Then get general FAQ results
    faq_results = search_faq_only(query, 2)
    
    # Combine results
    all_results = troubleshooting_results + faq_results
    
    if all_results:
        return format_knowledge_results(all_results, query)
    else:
        return "💡 No specific troubleshooting information found. Please describe your issue in more detail."

def add_faq_item(question: str, answer: str, tags: List[str] = None) -> bool:
    """Add new FAQ item to knowledge base"""
    try:
        rag_kb = get_rag_knowledge_base()
        content = f"Q: {question}\nA: {answer}"
        rag_kb.add_knowledge_item(
            title=question,
            content=content,
            category="faq",
            tags=tags or []
        )
        return True
    except Exception as e:
        print(f"Error adding FAQ item: {e}")
        return False

def get_knowledge_stats() -> Dict[str, int]:
    """Get statistics about knowledge base"""
    try:
        rag_kb = get_rag_knowledge_base()
        
        stats = {
            "total_items": len(rag_kb.knowledge_items),
            "faq_items": len(rag_kb.get_category_items("faq")),
            "troubleshooting_items": len(rag_kb.get_category_items("troubleshooting")),
            "procedure_items": len(rag_kb.get_category_items("procedures"))
        }
        
        return stats
        
    except Exception as e:
        print(f"Error getting knowledge stats: {e}")
        return {"total_items": 0, "faq_items": 0, "troubleshooting_items": 0, "procedure_items": 0}

# Backward compatibility aliases
search_faq = search_knowledge_base
format_faq_results = format_knowledge_results
