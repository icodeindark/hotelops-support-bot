"""
HotelOpsAI Multi-Agent State Management Schema
Senior AI Engineer Implementation
"""

from typing import List, Dict, Optional, Literal, Any
from typing_extensions import TypedDict
from enum import Enum
from datetime import datetime
import uuid

class AgentType(Enum):
    """Available specialized agents in the system"""
    ROUTER = "router"
    USER_MANAGEMENT = "user_management"
    SERVICE_MANAGEMENT = "service_management"
    KNOWLEDGE_BASE = "knowledge_base"
    DATA_EXTRACTION = "data_extraction"
    CONVERSATION_MANAGER = "conversation_manager"

class IntentType(Enum):
    """Classified user intents"""
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_LIST = "user_list"
    USER_SEARCH = "user_search"
    SERVICE_ADD = "service_add"
    SERVICE_LIST = "service_list"
    KNOWLEDGE_QUERY = "knowledge_query"
    TROUBLESHOOTING = "troubleshooting"
    GREETING = "greeting"
    UNCLEAR = "unclear"
    HANDOFF_REQUEST = "handoff_request"

class OperationStatus(Enum):
    """Status of ongoing operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    CANCELLED = "cancelled"

class ConversationState(Enum):
    """Conversation flow states"""
    IDLE = "idle"
    INTENT_CLASSIFICATION = "intent_classification"
    DATA_COLLECTION = "data_collection"
    COLLECTING_USER_DATA = "collecting_user_data"  # Natural conversation mode
    DATA_VALIDATION = "data_validation"
    CONFIRMATION_PENDING = "confirmation_pending"
    OPERATION_EXECUTION = "operation_execution"
    FOLLOW_UP = "follow_up"
    ERROR_RECOVERY = "error_recovery"
    HUMAN_HANDOFF = "human_handoff"

class Message(TypedDict):
    """Individual message structure"""
    id: str
    timestamp: datetime
    role: Literal["user", "assistant", "system"]
    content: str
    agent_id: Optional[str]
    intent: Optional[str]
    confidence: Optional[float]
    metadata: Dict[str, Any]

class ExtractedEntity(TypedDict):
    """Extracted entity with validation info"""
    entity_type: str  # "name", "email", "phone", "role", etc.
    value: str
    confidence: float
    is_valid: bool
    validation_error: Optional[str]
    source_text: str

class UserOperationData(TypedDict):
    """User management operation data"""
    operation_type: Literal["create", "update", "delete"]
    user_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    department: Optional[str]
    property: Optional[str]
    status: Optional[str]
    required_fields: List[str]
    collected_fields: List[str]
    missing_fields: List[str]

class ServiceOperationData(TypedDict):
    """Service management operation data"""
    operation_type: Literal["add", "update", "delete", "list"]
    service_id: Optional[str]
    service_name: Optional[str]
    service_type: Optional[str]
    description: Optional[str]
    priority: Optional[str]
    assigned_to: Optional[str]
    required_fields: List[str]
    collected_fields: List[str]

class KnowledgeQueryData(TypedDict):
    """Knowledge base query context"""
    original_query: str
    processed_query: str
    query_type: Literal["faq", "troubleshooting", "feature_help", "general"]
    search_results: List[Dict[str, Any]]
    selected_result: Optional[Dict[str, Any]]
    confidence_score: float

class ChatState(TypedDict):
    """Comprehensive chat state for multi-agent system"""
    
    # === CORE CONVERSATION STATE ===
    messages: List[Message]
    user_id: str
    session_id: str
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    
    # === INTENT & ROUTING STATE ===
    current_intent: Optional[IntentType]
    intent_confidence: float
    active_agent: Optional[AgentType]
    previous_agent: Optional[AgentType]
    routing_history: List[Dict[str, Any]]
    
    # === CONVERSATION FLOW STATE ===
    conversation_state: ConversationState
    conversation_complete: bool
    needs_human_handoff: bool
    handoff_reason: Optional[str]
    retry_count: int
    max_retries: int
    
    # === DATA EXTRACTION STATE ===
    extracted_entities: List[ExtractedEntity]
    extraction_confidence: float
    validation_errors: List[str]
    data_collection_progress: Dict[str, Any]
    
    # === OPERATION-SPECIFIC CONTEXTS ===
    user_operation: Optional[UserOperationData]
    service_operation: Optional[ServiceOperationData]
    knowledge_query: Optional[KnowledgeQueryData]
    
    # === GENERAL DATA CONTEXT ===
    extracted_data: Dict[str, Any]
    required_fields: List[str]
    missing_fields: List[str]
    collected_fields: List[str]
    
    # === AGENT PERFORMANCE METRICS ===
    agent_performance: Dict[str, Dict[str, float]]
    response_times: Dict[str, float]
    success_rates: Dict[str, float]
    
    # === ERROR HANDLING ===
    last_error: Optional[str]
    error_history: List[Dict[str, Any]]
    recovery_attempts: int
    
    # === CONTEXT PRESERVATION ===
    conversation_context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    session_metadata: Dict[str, Any]
    
    # === SYSTEM STATE ===
    system_status: Dict[str, str]
    api_quota_usage: Dict[str, int]
    rate_limit_status: Dict[str, Any]

def create_initial_state(user_id: str, session_id: Optional[str] = None) -> ChatState:
    """Create initial chat state for new conversation"""
    
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    conversation_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    return ChatState(
        # Core conversation
        messages=[],
        user_id=user_id,
        session_id=session_id,
        conversation_id=conversation_id,
        created_at=current_time,
        updated_at=current_time,
        
        # Intent & routing
        current_intent=None,
        intent_confidence=0.0,
        active_agent=None,
        previous_agent=None,
        routing_history=[],
        
        # Conversation flow  
        conversation_state=ConversationState.IDLE.value,
        conversation_complete=False,
        needs_human_handoff=False,
        handoff_reason=None,
        retry_count=0,
        max_retries=3,
        
        # Data extraction
        extracted_entities=[],
        extraction_confidence=0.0,
        validation_errors=[],
        data_collection_progress={},
        
        # Operations
        user_operation=None,
        service_operation=None,
        knowledge_query=None,
        
        # General data
        extracted_data={},
        required_fields=[],
        missing_fields=[],
        collected_fields=[],
        
        # Metrics
        agent_performance={},
        response_times={},
        success_rates={},
        
        # Error handling
        last_error=None,
        error_history=[],
        recovery_attempts=0,
        
        # Context
        conversation_context={},
        user_preferences={},
        session_metadata={},
        
        # System
        system_status={},
        api_quota_usage={},
        rate_limit_status={}
    )

def update_state_timestamp(state: ChatState) -> ChatState:
    """Update the timestamp for state modifications"""
    new_state = state.copy()
    new_state["updated_at"] = datetime.now()
    return new_state

def add_message_to_state(
    state: ChatState, 
    content: str, 
    role: Literal["user", "assistant", "system"],
    agent_id: Optional[str] = None,
    intent: Optional[str] = None,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ChatState:
    """Add a new message to the conversation state"""
    
    new_state = state.copy()
    
    message = Message(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        role=role,
        content=content,
        agent_id=agent_id,
        intent=intent,
        confidence=confidence,
        metadata=metadata or {}
    )
    
    new_state["messages"].append(message)
    return update_state_timestamp(new_state)

def transition_conversation_state(
    state: ChatState, 
    new_state: ConversationState,
    reason: Optional[str] = None
) -> ChatState:
    """Transition conversation to a new state"""
    
    updated_state = state.copy()
    
    # Log the transition
    current_state = state.get("conversation_state")
    
    # Handle both string and enum values for current state
    from_state_value = None
    if current_state:
        if isinstance(current_state, str):
            from_state_value = current_state
        else:
            from_state_value = current_state.value
    
    # Handle new state - ensure it's stored as string
    to_state_value = new_state.value if hasattr(new_state, 'value') else str(new_state)
    
    transition_log = {
        "from_state": from_state_value,
        "to_state": to_state_value,
        "timestamp": datetime.now(),
        "reason": reason
    }
    
    # Update state - store as string value for serialization
    updated_state["conversation_state"] = to_state_value
    
    # Add to conversation context
    if "state_transitions" not in updated_state["conversation_context"]:
        updated_state["conversation_context"]["state_transitions"] = []
    
    updated_state["conversation_context"]["state_transitions"].append(transition_log)
    
    return update_state_timestamp(updated_state)

def set_active_agent(
    state: ChatState, 
    agent: AgentType,
    confidence: float = 1.0,
    reason: Optional[str] = None
) -> ChatState:
    """Set the active agent and log routing decision"""
    
    updated_state = state.copy()
    
    # Store previous agent
    updated_state["previous_agent"] = state["active_agent"]
    updated_state["active_agent"] = agent
    
    # Log routing decision
    routing_entry = {
        "agent": agent.value if hasattr(agent, 'value') else str(agent),
        "confidence": confidence,
        "timestamp": datetime.now(),
        "reason": reason,
        "previous_agent": state.get("active_agent")
    }
    
    updated_state["routing_history"].append(routing_entry)
    
    return update_state_timestamp(updated_state)

def log_error_to_state(
    state: ChatState,
    error_message: str,
    error_type: str,
    agent_id: Optional[str] = None,
    recoverable: bool = True
) -> ChatState:
    """Log an error to the conversation state"""
    
    updated_state = state.copy()
    
    error_entry = {
        "error_message": error_message,
        "error_type": error_type,
        "agent_id": agent_id,
        "timestamp": datetime.now(),
        "recoverable": recoverable,
        "retry_count": state["retry_count"]
    }
    
    updated_state["error_history"].append(error_entry)
    updated_state["last_error"] = error_message
    
    if recoverable:
        updated_state["retry_count"] += 1
    
    return update_state_timestamp(updated_state)

# Utility functions for state validation
def validate_state_integrity(state: ChatState) -> List[str]:
    """Validate state integrity and return any issues"""
    issues = []
    
    # Check required fields
    required_keys = [
        "user_id", "session_id", "conversation_id", 
        "messages", "conversation_state"
    ]
    
    for key in required_keys:
        if key not in state or state[key] is None:
            issues.append(f"Missing required field: {key}")
    
    # Check data consistency
    if state.get("retry_count", 0) > state.get("max_retries", 3):
        issues.append("Retry count exceeds maximum allowed retries")
    
    if state.get("active_agent") and state.get("conversation_state") == ConversationState.IDLE:
        issues.append("Active agent set but conversation state is IDLE")
    
    return issues
