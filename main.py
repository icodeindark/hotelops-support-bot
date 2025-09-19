import streamlit as st
import json
import traceback
from agents.support_agent import build_agent
from tools import user_tools, service_tools, troubleshooting, faq_tools
from logger_config import (
    main_logger, agent_logger, error_logger, log_action, 
    log_error
)

# Configure page
st.set_page_config(
    page_title="HotelOpsAI Support Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🏨 HotelOpsAI - Support Chatbot Prototype")
st.markdown("**AI-powered support for user management, services, and troubleshooting**")

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = build_agent()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Create two columns - main chat and debug panel
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat Interface")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.write(msg)
    
    # Chat input
    user_input = st.chat_input("Ask me about users, services, troubleshooting, or say 'help' for examples...")
    
    if user_input:
        with st.spinner("Processing..."):
            try:
                # Generate session ID based on Streamlit session
                session_id = st.session_state.get('session_id', 'default')
                if 'session_id' not in st.session_state:
                    import uuid
                    st.session_state.session_id = str(uuid.uuid4())[:8]
                    session_id = st.session_state.session_id
                    log_action("SESSION_START", f"New session created: {session_id}")
                
                # Log user input
                log_action("USER_INPUT", f"Query: {user_input[:100]}{'...' if len(user_input) > 100 else ''}", session_id=session_id)
                
                # Invoke agent
                agent_logger.info(f"Invoking agent for session {session_id}")
                result = st.session_state.agent.invoke({
                    "query": user_input, 
                    "session_id": session_id,
                    "conversation_state": "idle",  # Initialize state
                    "session_data": {}  # Initialize data
                })
                
                # Handle different possible result formats
                if result and "response" in result:
                    response = result["response"]
                    log_action("AGENT_RESPONSE", f"Success: {response[:100]}{'...' if len(response) > 100 else ''}", session_id=session_id)
                elif result:
                    # If result exists but no response key, try to extract the response
                    response = str(result)
                    log_error("RESPONSE_FORMAT", f"Unexpected result format: {type(result)}", session_id=session_id)
                else:
                    response = "I'm sorry, I couldn't process your request."
                    log_error("EMPTY_RESULT", "Agent returned None result", session_id=session_id)

                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("Agent", response))
                
                log_action("CHAT_UPDATE", f"Added to history. Total messages: {len(st.session_state.chat_history)}", session_id=session_id)
                st.rerun()
                
            except Exception as e:
                error_msg = str(e)
                error_traceback = traceback.format_exc()
                
                # Log the full error
                log_error("CRITICAL_ERROR", f"{error_msg}\n{error_traceback}", session_id=session_id)
                
                # Show user-friendly error
                st.error(f"❌ **Error:** {error_msg}")
                
                # Also add to chat history for debugging
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("System Error", f"Error: {error_msg}"))
                st.rerun()

with col2:
    st.header("🔧 Debug Panel")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        log_action("CHAT_CLEAR", "Chat history cleared by user")
        st.rerun()
    
    
    # Show example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        **User Management:**
        - "list users"
        - "create a new user" 
        - "edit user details"
        - "delete a user"
        
        **Service Management:**
        - "show services"
        - "create a service"
        - "add work order"
        
        **FAQ & Help:**
        - "how do I reset my password?"
        - "help with mobile app"
        - "faq about work orders"
        - "guide for housekeeping"
        
        **Troubleshooting:**
        - "wifi not working"
        - "AC not cooling"
        - "help with issues"
        """)
    
    # Display current data
    with st.expander("👥 Current Users"):
        try:
            users = user_tools.list_users()
            st.json(users)
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with st.expander("🔧 Current Services"):
        try:
            services = service_tools.list_services()
            st.json(services)
        except Exception as e:
            st.error(f"Error loading services: {e}")
    
    with st.expander("❓ FAQ Database"):
        try:
            faq_data = faq_tools.load_faq()
            st.write(f"**Total FAQs:** {len(faq_data)}")
            
            # Show categories
            categories = faq_tools.get_all_categories()
            st.write(f"**Categories:** {', '.join(categories)}")
            
            # Show sample FAQs
            st.write("**Sample FAQs:**")
            for i, faq in enumerate(faq_data[:3]):
                st.write(f"• {faq['question']} ({faq['category']})")
            
            if st.checkbox("Show full FAQ data"):
                st.json(faq_data)
        except Exception as e:
            st.error(f"Error loading FAQ: {e}")
    
    with st.expander("👤 User Data (Live)"):
        try:
            from tools.user_data_manager import user_manager
            users = user_manager.get_all_users()
            st.write(f"**Total Users:** {len(users)}")
            
            if users:
                for user_id, user_data in list(users.items())[:3]:  # Show first 3
                    status_icon = "🟢" if user_data.get('status') == 'active' else "🔴"
                    st.write(f"{status_icon} **{user_id}**: {user_data.get('first_name', '')} {user_data.get('last_name', '')} - {user_data.get('role', 'N/A')}")
                
                if len(users) > 3:
                    st.write(f"... and {len(users) - 3} more users")
                
                if st.checkbox("Show full user data"):
                    st.json(users)
            else:
                st.info("No users created yet. Try: 'Create a new user'")
        except Exception as e:
            st.error(f"Error loading user data: {e}")
    
    with st.expander("🚨 Troubleshooting KB"):
        try:
            trouble_data = troubleshooting.load_troubleshooting()
            st.json(trouble_data)
        except Exception as e:
            st.error(f"Error loading troubleshooting: {e}")

# Footer
st.markdown("---")
st.markdown("*Prototype v1.0 - JSON-based data storage | Future: API integration*")
