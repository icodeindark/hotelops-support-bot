import json, os
from .faq_tools import search_faq, get_enhanced_troubleshooting_context

TROUBLE_FILE = os.path.join("context", "troubleshooting.json")

def load_troubleshooting():
    with open(TROUBLE_FILE, "r") as f:
        return json.load(f)

def get_troubleshooting(query):
    """
    Enhanced troubleshooting that checks both specific troubleshooting
    steps and FAQ database
    """
    # First check specific troubleshooting steps
    data = load_troubleshooting()
    for item in data:
        if item["question"].lower() in query.lower():
            return item["answer"]
    
    # If no specific troubleshooting found, search FAQ
    faq_results = search_faq(query, limit=3)
    if faq_results:
        return get_enhanced_troubleshooting_context(query)
    
    return "Sorry, I don't have specific troubleshooting steps for that yet, but I can provide general assistance."

def get_combined_help_context(query):
    """
    Get comprehensive help context combining troubleshooting and FAQ
    """
    # Check troubleshooting first
    trouble_data = load_troubleshooting()
    specific_answer = None
    
    for item in trouble_data:
        if item["question"].lower() in query.lower():
            specific_answer = item["answer"]
            break
    
    # Get FAQ context
    faq_context = get_enhanced_troubleshooting_context(query)
    
    if specific_answer:
        return f"Specific Troubleshooting:\n{specific_answer}\n\n{faq_context}"
    else:
        return faq_context
