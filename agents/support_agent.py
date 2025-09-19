from langgraph.graph import StateGraph, END
from typing import TypedDict
from tools import user_tools, service_tools, troubleshooting, faq_tools
from tools.interactive_user_manager import interactive_user_manager
from tools.session_manager import session_manager, ConversationState
from context.role_context import get_contextual_prompt, is_user_management_query
from llm_utils import ask_gemini

class AgentState(TypedDict):
    query: str
    response: str
    session_id: str
    conversation_state: str  # Store session state in LangGraph state
    session_data: dict       # Store session data in LangGraph state

def load_session_state(state: AgentState):
    """Load session state into LangGraph state for persistence"""
    session_id = str(state.get("session_id", "default"))
    
    # Get existing session data from session manager
    session_data = session_manager.get_session(session_id)
    
    # Copy session data into LangGraph state for persistence
    new_state = dict(state)
    new_state["conversation_state"] = session_data["state"].value
    new_state["session_data"] = session_data["data"].copy()
    
    return new_state

def route_decider(state: AgentState):
    query = str(state.get("query", "")).lower()
    original_query = str(state.get("query", ""))
    conversation_state = state.get("conversation_state", "idle")
    
    # FIRST: Check if we're in an active conversation state
    if conversation_state == ConversationState.COLLECTING_USER_DATA.value:
        return "create_user_node"  # Continue user creation flow
    elif conversation_state == ConversationState.CONFIRMING_USER_CREATE.value:
        return "create_user_node"  # Handle confirmation
    elif conversation_state == ConversationState.COLLECTING_USER_UPDATES.value:
        return "edit_user_node"
    elif conversation_state == ConversationState.CONFIRMING_USER_UPDATE.value:
        return "edit_user_node"
    elif conversation_state == ConversationState.CONFIRMING_USER_DELETE.value:
        return "delete_user_node"
    
    # SECOND: Check for new requests (when not in active conversation)
    # Check for structured user data first (comma-separated with email)
    if "," in original_query and "@" in original_query:
        return "create_user_node"

    # User management operations - more comprehensive patterns
    if ("create" in query or "add" in query or "new" in query or "wanna add" in query or "want to add" in query) and "user" in query:
        return "create_user_node"
    elif ("edit" in query or "update" in query or "modify" in query or "change" in query) and "user" in query:
        return "edit_user_node"
    elif ("delete" in query or "remove" in query) and "user" in query:
        return "delete_user_node"
    elif ("list" in query and "user" in query) or ("show" in query and "user" in query) or ("all user" in query):
        return "list_users_node"

    # Service/Work Order management
    elif ("create" in query or "add" in query) and ("service" in query or "work order" in query):
        return "create_service_node"
    elif "service" in query or "work order" in query:
        return "list_services_node"

    # FAQ and Help
    elif ("faq" in query or "help" in query or "how do i" in query or "how to" in query or
          "question" in query or "guide" in query):
        return "faq_node"

    # Troubleshooting
    elif "trouble" in query or "error" in query or "not working" in query or "issue" in query:
        return "troubleshoot_node"

    return "fallback"

def save_session_state(state: AgentState):
    """Save LangGraph state back to session manager for persistence"""
    session_id = str(state.get("session_id", "default"))
    conversation_state = state.get("conversation_state", "idle")
    session_data = state.get("session_data", {})
    
    # Convert string back to enum if needed
    try:
        conv_state = ConversationState(conversation_state)
    except:
        conv_state = ConversationState.IDLE
    
    # Update session manager with current state
    session_manager.set_state(session_id, conv_state, session_data)
    
    return state

def router_node(state: AgentState):
    # Pass through the state unchanged - just a routing hub
    return state

def list_users_node(state: AgentState):
    q = str(state.get("query", ""))
    session_id = str(state.get("session_id", "default"))
    
    # Use interactive user manager for actual functionality
    response = interactive_user_manager.process_user_request(q, session_id)
    return {"query": q, "response": response, "session_id": session_id}

def create_user_node(state: AgentState):
    q = str(state.get("query", ""))
    session_id = str(state.get("session_id", "default"))
    
    # Use interactive user manager for actual user creation
    response = interactive_user_manager.process_user_request(q, session_id)
    
    # Get updated session state and sync with LangGraph state
    updated_session = session_manager.get_session(session_id)
    
    return {
        "query": q, 
        "response": response, 
        "session_id": session_id,
        "conversation_state": updated_session["state"].value,
        "session_data": updated_session["data"].copy()
    }

def edit_user_node(state: AgentState):
    q = str(state.get("query", ""))
    session_id = str(state.get("session_id", "default"))
    
    # Use interactive user manager for actual user editing
    response = interactive_user_manager.process_user_request(q, session_id)
    
    # Get updated session state and sync with LangGraph state
    updated_session = session_manager.get_session(session_id)
    
    return {
        "query": q, 
        "response": response, 
        "session_id": session_id,
        "conversation_state": updated_session["state"].value,
        "session_data": updated_session["data"].copy()
    }

def delete_user_node(state: AgentState):
    q = str(state.get("query", ""))
    session_id = str(state.get("session_id", "default"))
    
    # Use interactive user manager for actual user deletion
    response = interactive_user_manager.process_user_request(q, session_id)
    
    # Get updated session state and sync with LangGraph state
    updated_session = session_manager.get_session(session_id)
    
    return {
        "query": q, 
        "response": response, 
        "session_id": session_id,
        "conversation_state": updated_session["state"].value,
        "session_data": updated_session["data"].copy()
    }

def list_services_node(state: AgentState):
    q = str(state.get("query", ""))
    services_list = service_tools.list_services()
    prompt = f"The user asked: {q}\n\nHere is the current list of services/work orders in the system:\n{services_list}\n\nRespond naturally and helpfully. Format the services list in a clear, readable way."
    response = ask_gemini(prompt)
    return {"query": q, "response": response}

def create_service_node(state: AgentState):
    q = str(state.get("query", ""))
    prompt = f"""The user wants to create a new service/work order: {q}

To create a service or work order, I need the following information:
- Name/Title (required) - describe what the service is
- Department/Team (required) - which team will handle this (e.g., Housekeeping, Maintenance, Front Desk, etc.)
- SLA/Expected completion time (required) - how many hours this should take

Please respond naturally and ask the user to provide the missing information needed to create the service/work order. Be conversational and helpful."""
    response = ask_gemini(prompt)
    return {"query": q, "response": response}

def faq_node(state: AgentState):
    q = str(state.get("query", ""))
    
    # Search FAQ database
    faq_results = faq_tools.search_faq(q, limit=5)
    
    if faq_results:
        # Format FAQ results for context
        faq_context = faq_tools.format_faq_results(faq_results)
        
        # Check if this is a user management query to apply role context
        if is_user_management_query(q):
            context = f"""RELEVANT FAQ INFORMATION:
{faq_context}

As the HotelOpsAI User Management Assistant, provide professional guidance based on this FAQ information. Include specific UI references, step-by-step instructions, and role-based permission requirements where applicable."""
            prompt = get_contextual_prompt(q, context)
        else:
            prompt = f"""The user asked: {q}

I found relevant information in our FAQ database:

{faq_context}

Please provide a helpful, natural response based on this information. If multiple FAQs are relevant, summarize the key points. Be conversational and offer to help with any follow-up questions."""
    else:
        # No specific FAQs found, provide general help
        categories = faq_tools.get_all_categories()
        
        if is_user_management_query(q):
            context = f"""No specific FAQs found for this user management query.

Available FAQ categories: {', '.join(categories)}

As the HotelOpsAI User Management Assistant, guide the user to the appropriate resources or provide general user management assistance within your expertise area."""
            prompt = get_contextual_prompt(q, context)
        else:
            prompt = f"""The user asked: {q}

I couldn't find specific FAQs matching this query, but I can help with questions in these areas:
{', '.join(categories)}

Please respond helpfully and ask the user to be more specific or choose a category they're interested in."""
    
    response = ask_gemini(prompt)
    return {"query": q, "response": response}

def troubleshoot_node(state: AgentState):
    q = str(state.get("query", ""))
    
    # Get enhanced troubleshooting context (includes FAQ search)
    combined_context = troubleshooting.get_combined_help_context(q)
    
    prompt = f"""The user has a troubleshooting request: {q}

Here's the relevant information I found:

{combined_context}

Please provide a helpful, step-by-step response. Be clear and actionable. If this seems like a complex issue, suggest contacting support with specific details."""
    
    response = ask_gemini(prompt)
    return {"query": q, "response": response}

def fallback_node(state: AgentState):
    q = str(state.get("query", ""))
    session_id = str(state.get("session_id", "default"))
    
    try:
        # Check if this could be a user management query that didn't match other routes
        if is_user_management_query(q):
            # Use interactive user manager for actual user management operations
            response = interactive_user_manager.process_user_request(q, session_id)
            return {"query": q, "response": response, "session_id": session_id}
        else:
            prompt = f"The user asked: {q}. Respond naturally and helpfully as an AI assistant for HotelOpsAI."
            response = ask_gemini(prompt)
            return {"query": q, "response": response, "session_id": session_id}
    except Exception as e:
        return {"query": q, "response": "I encountered an error while processing your request. Please try again or contact support.", "session_id": session_id}

def build_agent():
    graph = StateGraph(AgentState)
    
    # State management nodes
    graph.add_node("load_session", load_session_state)
    graph.add_node("router", router_node)
    graph.add_node("save_session", save_session_state)
    
    # User management nodes
    graph.add_node("list_users_node", list_users_node)
    graph.add_node("create_user_node", create_user_node)
    graph.add_node("edit_user_node", edit_user_node)
    graph.add_node("delete_user_node", delete_user_node)
    
    # Service management nodes
    graph.add_node("list_services_node", list_services_node)
    graph.add_node("create_service_node", create_service_node)
    
    # FAQ and troubleshooting nodes
    graph.add_node("faq_node", faq_node)
    graph.add_node("troubleshoot_node", troubleshoot_node)
    graph.add_node("fallback", fallback_node)

    # Set entry point to load session state first
    graph.set_entry_point("load_session")
    
    # Flow: load_session -> router -> actual nodes -> save_session -> END
    graph.add_edge("load_session", "router")
    
    # All nodes go through save_session before END
    graph.add_edge("list_users_node", "save_session")
    graph.add_edge("create_user_node", "save_session")
    graph.add_edge("edit_user_node", "save_session")
    graph.add_edge("delete_user_node", "save_session")
    graph.add_edge("list_services_node", "save_session")
    graph.add_edge("create_service_node", "save_session")
    graph.add_edge("faq_node", "save_session")
    graph.add_edge("troubleshoot_node", "save_session")
    graph.add_edge("fallback", "save_session")
    
    # Save session then END
    graph.add_edge("save_session", END)

    # Conditional edges from router to destination nodes via decider
    graph.add_conditional_edges(
        "router",
        route_decider,
        {
            "list_users_node": "list_users_node",
            "create_user_node": "create_user_node",
            "edit_user_node": "edit_user_node",
            "delete_user_node": "delete_user_node",
            "list_services_node": "list_services_node",
            "create_service_node": "create_service_node",
            "faq_node": "faq_node",
            "troubleshoot_node": "troubleshoot_node",
            "fallback": "fallback",
        },
    )

    return graph.compile()
