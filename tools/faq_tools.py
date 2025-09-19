import json
import os
from typing import List, Dict, Any

FAQ_FILE = os.path.join("context", "faq.json")

def load_faq() -> List[Dict[str, Any]]:
    """Load FAQ data from JSON file"""
    with open(FAQ_FILE, "r") as f:
        faq_data = json.load(f)
        
    # Flatten the FAQ data from categorized structure to a single list
    all_faqs = []
    for category, faqs in faq_data.items():
        if isinstance(faqs, list):  # Only process list values (not metadata)
            for faq in faqs:
                # Add category info to each FAQ
                faq_with_category = faq.copy()
                faq_with_category["category"] = category
                # Add keywords if not present
                if "keywords" not in faq_with_category:
                    faq_with_category["keywords"] = []
                all_faqs.append(faq_with_category)
    
    return all_faqs

def search_faq(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search FAQ using simple keyword matching.
    For a prototype, this is more practical than embeddings for <1000 entries.
    """
    try:
        faq_data = load_faq()
        query_lower = query.lower()
    except Exception as e:
        print(f"Error loading FAQ data: {e}")
        return []
    
    # Score each FAQ entry based on keyword matches
    scored_faqs = []
    
    for faq in faq_data:
        if not isinstance(faq, dict):
            continue  # Skip invalid entries
            
        score = 0
        
        # Safely check if query words appear in question
        if "question" in faq and isinstance(faq["question"], str):
            if any(word in faq["question"].lower() for word in query_lower.split()):
                score += 3
            
        # Safely check if query words appear in answer
        if "answer" in faq and isinstance(faq["answer"], str):
            if any(word in faq["answer"].lower() for word in query_lower.split()):
                score += 2
            
        # Safely check if query words appear in keywords
        if "keywords" in faq and isinstance(faq["keywords"], list):
            if any(keyword in query_lower for keyword in faq["keywords"]):
                score += 4
            
        # Safely check if query words appear in category
        if "category" in faq and isinstance(faq["category"], str):
            if any(word in faq["category"].lower() for word in query_lower.split()):
                score += 1
            
        if score > 0:
            faq_copy = faq.copy()
            faq_copy["relevance_score"] = score
            scored_faqs.append(faq_copy)
    
    # Sort by score (descending) and return top results
    scored_faqs.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_faqs[:limit]

def get_faq_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all FAQs for a specific category"""
    faq_data = load_faq()
    return [faq for faq in faq_data if faq["category"].lower() == category.lower()]

def get_all_categories() -> List[str]:
    """Get list of all FAQ categories"""
    faq_data = load_faq()
    categories = list(set(faq["category"] for faq in faq_data))
    return sorted(categories)

def format_faq_results(faqs: List[Dict[str, Any]]) -> str:
    """Format FAQ results for display"""
    if not faqs:
        return "No relevant FAQs found for your query."
    
    result = f"Found {len(faqs)} relevant FAQ(s):\n\n"
    
    for i, faq in enumerate(faqs, 1):
        result += f"**{i}. {faq['question']}**\n"
        result += f"Category: {faq['category']}\n"
        result += f"Answer: {faq['answer']}\n\n"
    
    return result

def get_enhanced_troubleshooting_context(query: str) -> str:
    """
    Get comprehensive troubleshooting context including both
    specific troubleshooting steps and relevant FAQs
    """
    # Get FAQ results
    faq_results = search_faq(query, limit=3)
    
    if faq_results:
        context = "Here are relevant FAQs and troubleshooting information:\n\n"
        context += format_faq_results(faq_results)
        
        # Add categories for additional help
        categories = get_all_categories()
        context += f"\nAvailable FAQ categories: {', '.join(categories)}\n"
        
        return context
    else:
        return "No specific FAQs found, but I can help with general troubleshooting."
