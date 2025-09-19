import streamlit as st
import json
from agents.support_agent import build_agent
from tools import user_tools, service_tools, troubleshooting, faq_tools

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
            # Generate session ID based on Streamlit session
            session_id = st.session_state.get('session_id', 'default')
            if 'session_id' not in st.session_state:
                import uuid
                st.session_state.session_id = str(uuid.uuid4())[:8]
                session_id = st.session_state.session_id
            
            result = st.session_state.agent.invoke({
                "query": user_input, 
                "session_id": session_id,
                "conversation_state": "idle",  # Initialize state
                "session_data": {}  # Initialize data
            })
            
            # Handle different possible result formats
            if result and "response" in result:
                response = result["response"]
            elif result:
                # If result exists but no response key, try to extract the response
                response = str(result)
            else:
                response = "I'm sorry, I couldn't process your request."

            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Agent", response))
            st.rerun()

with col2:
    st.header("🔧 Debug Panel")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
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
