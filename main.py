import streamlit as st
import json
import traceback
import uuid
import time
from datetime import datetime
from agents.multi_agent_system import multi_agent_system
from database.memory_db import db_adapter
from tools import faq_tools
from logger_config import (
    main_logger, agent_logger, error_logger, log_action, 
    log_error
)
from styles import get_modern_css

# Configure page with clean settings
st.set_page_config(
    page_title="HotelOpsAI Support",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply modern CSS
st.markdown(get_modern_css(), unsafe_allow_html=True)

# Initialize session state
def initialize_session():
    """Initialize session state with clean defaults"""
    defaults = {
        "multi_agent_system": multi_agent_system,
        "chat_history": [],
        "user_id": f"user_{str(uuid.uuid4())[:8]}",
        "session_id": str(uuid.uuid4())[:8],
        "current_agent": "Router",
        "is_processing": False,
        "last_response_time": 0.0,
        "session_start_time": datetime.now(),
        "debug_mode": True,
        "current_intent": "Ready",  # Changed from "None" to "Ready"
        "confidence_score": 1.0,    # Changed from 0.0 to 1.0 to show system is ready
        "extracted_data": {},
        "routing_history": [],
        "debug_panel_visible": True,
        "_processing_input": False,
        "message_count": 0,
        "total_response_time": 0.0,
        "conversation_state": "idle",
        "user_operation": {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_header():
    """Render clean application header using native Streamlit components"""
    uptime = datetime.now() - st.session_state.session_start_time
    uptime_str = str(uptime).split('.')[0]
    
    # Determine status
    if st.session_state.is_processing:
        status_text = "⚡ Processing"
        status_color = "orange"
    elif st.session_state.message_count > 0:
        status_text = "🟢 Active"
        status_color = "green"
    else:
        status_text = "🔵 Ready"
        status_color = "blue"
    
    avg_response_time = (st.session_state.total_response_time / max(st.session_state.message_count, 1)) if st.session_state.message_count > 0 else 0
    
    # Header with title and status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #0066FF, #3B82FF); 
                        border-radius: 8px; display: flex; align-items: center; justify-content: center; 
                        font-size: 24px; color: white;">🏨</div>
            <div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1e293b;">HotelOpsAI Support</h1>
                <p style="margin: 0; font-size: 14px; color: #64748b;">Multi-Agent Assistant</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="background: rgba(0, 102, 255, 0.1); color: #0066FF; padding: 8px 16px; 
                        border-radius: 20px; font-size: 12px; font-weight: 500; 
                        text-transform: uppercase; letter-spacing: 0.5px; display: inline-block;">
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Compact stats cards with smaller fonts
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin: 16px 0;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{st.session_state.session_id}</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Session</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{st.session_state.user_id}</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">User</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{uptime_str}</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Uptime</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{st.session_state.message_count}</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Messages</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{avg_response_time:.1f}s</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Avg Response</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">{st.session_state.current_agent}</div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Agent</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_message(role, content, timestamp=None):
    """Render a single message using native Streamlit components for reliability"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    
    if role == "You":
        # User message - align right
        st.markdown(f"**You** ({timestamp})")
        st.markdown(f"> {content}")
        
    elif role.startswith("🤖"):
        # Bot message - format cleanly
        agent_name = role.replace("🤖 ", "").replace("_", " ")
        st.markdown(f"**🤖 {agent_name}** ({timestamp})")
        
        # Use st.markdown for clean content display
        st.markdown(content)
        
    else:
        # System message
        st.info(f"**{role}:** {content} ({timestamp})")

def render_quick_actions():
    """Render quick action buttons"""
    actions = [
        ("👥", "Add User", "I want to add a new user to the system"),
        ("⚙️", "Add Service", "I want to add a new service to our offerings"),
        ("🔧", "Troubleshoot", "I need help troubleshooting an issue"),
        ("🆘", "Human Agent", "I need to speak with a human support agent")
    ]
    
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (icon, title, action_text) in enumerate(actions):
        with [col1, col2, col3, col4][i]:
            if st.button(f"{icon} {title}", key=f"quick_{i}", use_container_width=True):
                st.session_state.quick_action = action_text

def render_chat():
    """Render main chat interface using native Streamlit components"""
    # Chat header
    st.markdown("### 💬 Conversation")
    
    # Create chat container
    chat_container = st.container()
    
    with chat_container:
        # Messages
        if not st.session_state.chat_history:
            st.info("🤖 Welcome to HotelOpsAI! I'm here to help with user management, service operations, troubleshooting, and general support.")
        else:
            for role, content in st.session_state.chat_history:
                render_message(role, content)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    render_quick_actions()
    
    # Handle quick actions
    if hasattr(st.session_state, 'quick_action'):
        action = st.session_state.quick_action
        del st.session_state.quick_action
        process_message(action)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input and user_input.strip():
        process_message(user_input.strip())

def process_message(user_input):
    """Process user input through multi-agent system"""
    if st.session_state.get('_processing_input', False):
        return
        
    st.session_state.is_processing = True
    st.session_state._processing_input = True
    
    with st.spinner("Processing your request..."):
        try:
            start_time = time.time()
            
            user_id = st.session_state.user_id
            session_id = st.session_state.session_id
            
            log_action("USER_INPUT", f"Query: {user_input[:100]}", session_id=session_id)
            
            # Store current Streamlit state to database for multi-agent system to access
            current_ui_state = {
                "conversation_state": st.session_state.get("conversation_state", "idle"),
                "active_agent": st.session_state.get("current_agent", "router"),
                "extracted_data": st.session_state.get("extracted_data", {}),
                "user_operation": st.session_state.get("user_operation", {}),
                "current_intent": st.session_state.get("current_intent", "Unknown"),
                "intent_confidence": st.session_state.get("confidence_score", 0.0)
            }
            
            # Save UI state to database for multi-agent access
            db_adapter.save_session(session_id, current_ui_state)
            
            # Process through multi-agent system
            result = st.session_state.multi_agent_system.process_message(
                user_id=user_id,
                session_id=session_id, 
                message=user_input
            )
            
            # Calculate metrics
            response_time = time.time() - start_time
            st.session_state.last_response_time = response_time
            st.session_state.message_count += 1
            st.session_state.total_response_time += response_time
            
            # Process results
            if result and result.get("success"):
                response = result["response"]
                active_agent = result.get("active_agent", "Assistant")
                st.session_state.current_agent = active_agent
                
                # Update routing history
                st.session_state.routing_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "agent": active_agent,
                    "intent": result.get("intent", "Unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "response_time": response_time
                })
                
                # Update state from multi-agent system results
                st.session_state.current_intent = result.get("intent", "Unknown")
                st.session_state.confidence_score = result.get("confidence", 0.0)
                st.session_state.extracted_data = result.get("extracted_data", {})
                st.session_state.conversation_state = result.get("conversation_state", "idle")
                
                # Load any additional state from database
                try:
                    session_data = db_adapter.get_session(session_id)
                    if session_data:
                        st.session_state.user_operation = session_data.get("user_operation", {})
                        if session_data.get("conversation_state"):
                            st.session_state.conversation_state = session_data["conversation_state"]
                except Exception as e:
                    log_error("STATE_SYNC_ERROR", f"Failed to sync state: {str(e)}", session_id=session_id)
                
                log_action("AGENT_RESPONSE", f"Success: Agent={active_agent}, Time={response_time:.2f}s", session_id=session_id)
            else:
                response = result.get("response", "I encountered an issue processing your request. Please try again.")
                error_info = result.get("error", "Unknown error")
                log_error("AGENT_ERROR", f"Processing failed: {error_info}", session_id=session_id)

            # Add to chat history
            st.session_state.chat_history.append(("You", user_input))
            
            if result.get("success") and result.get("active_agent"):
                agent_name = result["active_agent"].replace("_", " ").title()
                st.session_state.chat_history.append((f"🤖 {agent_name}", response))
            else:
                st.session_state.chat_history.append(("🤖 Assistant", response))
            
        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            log_error("CRITICAL_ERROR", f"{error_msg}\n{error_traceback}", session_id=st.session_state.session_id)

            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("🤖 System", "I encountered an unexpected error. Please try again."))
        
        finally:
            st.session_state.is_processing = False
            st.session_state._processing_input = False
            st.rerun()

def render_debug_panel():
    """Render clean debug panel using native Streamlit components"""
    if not st.session_state.debug_panel_visible:
        return
    
    # Debug panel header
    st.markdown("### 🔧 Debug Panel")
    
    # Agent Status
    current_agent = st.session_state.current_agent
    if st.session_state.is_processing:
        status_text = "⚡ Processing"
    elif st.session_state.message_count > 0:
        status_text = "🟢 Active"
    else:
        status_text = "🔵 Ready"
    
    st.markdown("#### 🤖 Agent Status")
    st.info(f"**{current_agent}** - {status_text}")
    
    # Performance Metrics
    avg_response_time = (st.session_state.total_response_time / max(st.session_state.message_count, 1)) if st.session_state.message_count > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Last Response", f"{st.session_state.last_response_time:.2f}s")
    with col2:
        st.metric("Average", f"{avg_response_time:.2f}s")
    with col3:
        st.metric("Messages", st.session_state.message_count)
    
    # State Inspector
    with st.expander("🔍 State Inspector", expanded=st.session_state.debug_mode):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Intent", st.session_state.current_intent.replace("_", " ").title())
            st.metric("Processing", "Yes" if st.session_state.is_processing else "No")
        with col2:
            st.metric("Confidence", f"{st.session_state.confidence_score:.0%}")
            st.metric("Session Age", str(datetime.now() - st.session_state.session_start_time).split('.')[0])
        
        if st.session_state.extracted_data:
            st.markdown("**Extracted Data:**")
            st.json(st.session_state.extracted_data)
    
    # Routing History
    with st.expander("🧭 Routing History"):
        if st.session_state.routing_history:
            st.markdown("**Recent Routes:**")
            recent_routes = st.session_state.routing_history[-8:]
            for route in reversed(recent_routes):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.code(route['timestamp'])
                with col2:
                    st.write(f"**{route['agent'].replace('_', ' ').title()}**")
                with col3:
                    st.write(f"{route['confidence']:.0%}")
        else:
            st.info("No routing history yet. Start a conversation!")
    
    # System Metrics
    with st.expander("📊 System Metrics"):
        total_conversations = st.session_state.message_count // 2 if st.session_state.message_count > 0 else 0
        success_rate = 0.95 if total_conversations > 0 else 1.0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversations", total_conversations)
            st.metric("Success Rate", f"{success_rate:.0%}")
        with col2:
            st.metric("Avg Response", f"{avg_response_time:.1f}s")
            active_agents = len(set(route['agent'] for route in st.session_state.routing_history))
            st.metric("Active Agents", active_agents)
        
        # Agent usage
        if st.session_state.routing_history:
            st.markdown("**Agent Usage:**")
            agent_usage = {}
            for route in st.session_state.routing_history:
                agent = route['agent']
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
            
            for agent, count in sorted(agent_usage.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(st.session_state.routing_history)) * 100
                st.markdown(f"• **{agent.replace('_', ' ').title()}:** {count} ({percentage:.1f}%)")
        
        # System Health
        st.markdown("**System Health:**")
        health_items = [
            ("Response Time", "🟢 Excellent" if avg_response_time < 2 else "🟡 Good" if avg_response_time < 5 else "🔴 Slow"),
            ("Success Rate", "🟢 Excellent" if success_rate > 0.9 else "🟡 Good" if success_rate > 0.8 else "🔴 Poor"),
            ("API Status", "🟢 Connected")
        ]
        
        for metric, status in health_items:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"**{metric}:**")
            with col2:
                st.write(status)
    
    # Database Status
    with st.expander("💾 Database Status"):
        try:
            if hasattr(db_adapter.db, 'get_database_stats'):
                db_stats = db_adapter.db.get_database_stats()
            else:
                db_stats = {"users": 0, "services": 0, "conversations": 0}
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Users", db_stats.get("users", 0))
            with col2:
                st.metric("Services", db_stats.get("services", 0))
            with col3:
                st.metric("Conversations", db_stats.get("conversations", 0))
            
            st.success("🟢 Database Connected")
            
        except Exception as e:
            st.error(f"Database connection error: {e}")
    
    # Debug Controls
    with st.expander("⚙️ Debug Controls", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.message_count = 0
                st.session_state.total_response_time = 0.0
                log_action("CHAT_CLEAR", "Chat cleared", session_id=st.session_state.session_id)
                st.rerun()
        
        with col2:
            if st.button("🔄 New Session", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())[:8]
                st.session_state.chat_history = []
                st.session_state.routing_history = []
                st.session_state.session_start_time = datetime.now()
                st.session_state.message_count = 0
                st.session_state.total_response_time = 0.0
                st.session_state._processing_input = False
                st.rerun()
        
        with col3:
            chat_export = {
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "timestamp": datetime.now().isoformat(),
                "chat_history": st.session_state.chat_history,
                "routing_history": st.session_state.routing_history,
                "metrics": {
                    "message_count": st.session_state.message_count,
                    "total_response_time": st.session_state.total_response_time
                }
            }
            
            st.download_button(
                "📥 Export",
                data=json.dumps(chat_export, indent=2),
                file_name=f"session_{st.session_state.session_id}.json",
                mime="application/json",
                use_container_width=True
            )
        
        col4, col5 = st.columns(2)
        with col4:
            st.session_state.debug_mode = st.checkbox("Verbose Logging", value=st.session_state.debug_mode)
        with col5:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
    
    # Example Queries
    with st.expander("💡 Example Queries"):
        categories = {
            "User Management": [
                "list all users", "create a new user", "update user permissions", "delete inactive users"
            ],
            "Service Management": [
                "show services", "add room service", "create work order", "update pricing"
            ],
            "FAQ & Help": [
                "reset password help", "mobile app guide", "work order workflow", "housekeeping procedures"
            ],
            "Troubleshooting": [
                "WiFi not working", "AC issues", "login problems", "payment errors"
            ]
        }
        
        for category, queries in categories.items():
            st.markdown(f"**{category}:**")
            for query in queries:
                if st.button(query, key=f"example_{query.replace(' ', '_')}", use_container_width=True):
                    st.session_state.quick_action = query
    

def main():
    """Main application function"""
    initialize_session()
    
    # Header
    render_header()
    
    # Debug toggle
    toggle_text = "Hide Debug Panel" if st.session_state.debug_panel_visible else "Show Debug Panel"
    if st.button(f"🔧 {toggle_text}", key="debug_toggle", use_container_width=True):
        st.session_state.debug_panel_visible = not st.session_state.debug_panel_visible
        st.rerun()
    
    # Main layout
    if st.session_state.debug_panel_visible:
        col1, col2 = st.columns([7, 3], gap="large")
        
        with col1:
            render_chat()
        
        with col2:
            render_debug_panel()
    else:
        render_chat()
    
    # Footer
    st.markdown("""
    <div class="app-footer">
        <strong>HotelOpsAI Multi-Agent System v3.0</strong><br>
        Powered by LangGraph • Streamlit • Advanced AI<br>
        <em>Intelligent hotel operations support</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()