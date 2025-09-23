"""
HotelOpsAI Data Extraction Agent - Entity Recognition & Validation
Senior AI Engineer Implementation

The Data Extraction Agent specializes in:
1. Entity recognition from conversational input
2. Field validation and formatting
3. Missing data identification
4. Data standardization and normalization
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from .state_schema import (
    ChatState, ExtractedEntity, UserOperationData, ServiceOperationData,
    update_state_timestamp, log_error_to_state
)
from logger_config import agent_logger, log_action, log_error
from llm_utils import ask_gemini

class DataExtractionAgent:
    """
    Advanced Data Extraction Agent with ML-based entity recognition
    and comprehensive validation capabilities
    """
    
    def __init__(self):
        self.entity_patterns = self._initialize_entity_patterns()
        self.validation_rules = self._initialize_validation_rules()
        self.field_schemas = self._initialize_field_schemas()
        
        # Performance tracking
        self.extraction_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "validation_errors": 0,
            "entity_accuracy": {}
        }
        
        agent_logger.info("Data Extraction Agent initialized with entity recognition capabilities")
    
    def _initialize_entity_patterns(self) -> Dict[str, Dict]:
        """Initialize comprehensive entity recognition patterns"""
        
        return {
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "validation": self._validate_email,
                "normalize": self._normalize_email,
                "priority": 10
            },
            
            "phone": {
                "pattern": r'(?:phone[\s:]*)?(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})|(?:phone[\s:]+)(\d{10,15})',
                "validation": self._validate_phone,
                "normalize": self._normalize_phone,
                "priority": 8
            },
            
            "full_name": {
                "pattern": r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)(?:\s+([A-Z][a-z]+))?\b',
                "validation": self._validate_name,
                "normalize": self._normalize_name,
                "priority": 7
            },
            
            "first_name": {
                "pattern": r'\b(?:first\s+name|fname|given\s+name)[\s:]+([A-Z][a-z]+)\b',
                "validation": self._validate_single_name,
                "normalize": self._normalize_single_name,
                "priority": 6
            },
            
            "last_name": {
                "pattern": r'\b(?:last\s+name|lname|surname|family\s+name)[\s:]+([A-Z][a-z]+)\b',
                "validation": self._validate_single_name,
                "normalize": self._normalize_single_name,
                "priority": 6
            },
            
            "role": {
                "pattern": r'\b(?:role|position|job|title)[\s:]+([a-zA-Z\s-]+)\b',
                "validation": self._validate_role,
                "normalize": self._normalize_role,
                "priority": 5
            },
            
            "department": {
                "pattern": r'\b(?:department|dept|division)[\s:]+([a-zA-Z\s-]+)\b',
                "validation": self._validate_department,
                "normalize": self._normalize_department,
                "priority": 5
            },
            
            "service_name": {
                "pattern": r'\b(?:service|task|request)[\s:]+([a-zA-Z\s-]+)\b',
                "validation": self._validate_service_name,
                "normalize": self._normalize_service_name,
                "priority": 5
            },
            
            "priority": {
                "pattern": r'\b(?:priority|urgency)[\s:]+(?:is\s+)?(high|medium|low|urgent|normal)\b',
                "validation": self._validate_priority,
                "normalize": self._normalize_priority,
                "priority": 4
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Dict]:
        """Initialize field validation rules"""
        
        return {
            "email": {
                "required": True,
                "unique": True,
                "format_check": True,
                "min_length": 5,
                "max_length": 254
            },
            
            "first_name": {
                "required": True,
                "unique": False,
                "format_check": True,
                "min_length": 1,
                "max_length": 50,
                "allowed_chars": r"^[A-Za-z\s\-'\.]+$"
            },
            
            "last_name": {
                "required": True,
                "unique": False,
                "format_check": True,
                "min_length": 1,
                "max_length": 50,
                "allowed_chars": r"^[A-Za-z\s\-'\.]+$"
            },
            
            "phone": {
                "required": False,
                "unique": False,
                "format_check": True,
                "min_length": 10,
                "max_length": 15
            },
            
            "role": {
                "required": False,
                "unique": False,
                "format_check": True,
                "allowed_values": [
                    "manager", "supervisor", "front_desk", "housekeeping",
                    "maintenance", "security", "admin", "staff", "concierge"
                ]
            },
            
            "department": {
                "required": False,
                "unique": False,
                "format_check": True,
                "allowed_values": [
                    "front_office", "housekeeping", "maintenance", "security",
                    "food_beverage", "admin", "management", "concierge"
                ]
            }
        }
    
    def _initialize_field_schemas(self) -> Dict[str, Dict]:
        """Initialize field schemas for different operations"""
        
        return {
            "user_create": {
                "required": ["first_name", "last_name", "email"],
                "optional": ["phone", "role", "department", "property", "status"],
                "auto_generated": ["user_id", "created_at", "updated_at"]
            },
            
            "user_update": {
                "required": ["user_id"],  # Need to identify user first
                "optional": ["first_name", "last_name", "email", "phone", "role", "department", "status"],
                "immutable": ["user_id", "created_at"]
            },
            
            "service_create": {
                "required": ["service_name", "service_type"],
                "optional": ["description", "priority", "assigned_to", "due_date"],
                "auto_generated": ["service_id", "created_at", "status"]
            }
        }
    
    def extract_entities(self, message: str, operation_type: str, state: ChatState) -> ChatState:
        """
        Optimized entity extraction method with pattern-first approach
        
        Args:
            message: User input message
            operation_type: Type of operation (user_create, user_update, etc.)
            state: Current conversation state
            
        Returns:
            Updated state with extracted entities
        """
        
        log_action("DATA_EXTRACTION", f"Extracting entities for {operation_type}", 
                  session_id=state["session_id"])
        
        try:
            # Get field schema for operation
            schema = self.field_schemas.get(operation_type, {})
            
            # OPTIMIZATION: Try patterns first (no API cost)
            pattern_entities = self._extract_using_patterns(message)
            contextual_entities = self._extract_using_context(message, state)
            structured_entities = self._extract_structured_data(message, operation_type)
            
            # Combine pattern-based results
            pattern_based_entities = self._merge_entity_results(
                pattern_entities, contextual_entities, structured_entities
            )
            
            # Only use LLM if patterns found insufficient data
            llm_entities = []
            if len(pattern_based_entities) < 2 or not self._has_required_fields(pattern_based_entities, schema):
                log_action("LLM_FALLBACK", "Patterns insufficient, using LLM", session_id=state["session_id"])
                llm_entities = self._extract_with_llm_optimized(message, operation_type, state)
            
            # Combine all results
            all_entities = self._merge_entity_results(
                pattern_based_entities, llm_entities
            )
            
            # Validate extracted entities
            validated_entities = self._validate_entities(all_entities, schema)
            
            # Update state with extracted entities
            updated_state = state.copy()
            updated_state["extracted_entities"] = validated_entities
            
            # Calculate extraction confidence
            extraction_confidence = self._calculate_extraction_confidence(validated_entities)
            updated_state["extraction_confidence"] = extraction_confidence
            
            # Update operation-specific data
            updated_state = self._update_operation_data(updated_state, validated_entities, operation_type)
            
            # Track field collection progress
            updated_state = self._update_field_progress(updated_state, validated_entities, schema)
            
            log_action("EXTRACTION_SUCCESS", 
                      f"Extracted {len(validated_entities)} entities with confidence {extraction_confidence:.2f}",
                      session_id=state["session_id"])
            
            self.extraction_stats["total_extractions"] += 1
            self.extraction_stats["successful_extractions"] += 1
            
            return update_state_timestamp(updated_state)
            
        except Exception as e:
            error_msg = f"Entity extraction failed: {str(e)}"
            log_error("EXTRACTION_ERROR", error_msg, session_id=state["session_id"])
            
            self.extraction_stats["validation_errors"] += 1
            
            return log_error_to_state(
                state, error_msg, "extraction_error",
                agent_id="data_extraction", recoverable=True
            )
    
    def _extract_using_patterns(self, message: str) -> List[ExtractedEntity]:
        """Extract entities using regex patterns"""
        
        entities = []
        
        for entity_type, config in self.entity_patterns.items():
            pattern = config["pattern"]
            matches = re.finditer(pattern, message, re.IGNORECASE)
            
            for match in matches:
                # Extract the relevant group or full match
                if match.groups():
                    value = match.group(1).strip()
                else:
                    value = match.group(0).strip()
                
                # Skip if empty or too short
                if not value or len(value) < 2:
                    continue
                
                # Create entity
                entity = ExtractedEntity(
                    entity_type=entity_type,
                    value=value,
                    confidence=0.8,  # Pattern-based confidence
                    is_valid=False,  # Will be validated later
                    validation_error=None,
                    source_text=match.group(0)
                )
                
                entities.append(entity)
        
        return entities
    
    def _extract_using_context(self, message: str, state: ChatState) -> List[ExtractedEntity]:
        """Extract entities using conversation context"""
        
        entities = []
        
        # Look for single word responses that might be field values
        words = message.strip().split()
        
        # Check if we're in data collection mode
        if state.get("conversation_state") == "data_collection":
            # Get missing fields from state
            missing_fields = state.get("missing_fields", [])
            
            if len(words) == 1 and missing_fields:
                # Single word might be response to field request
                field_name = missing_fields[0]  # Assume first missing field
                value = words[0]
                
                entity = ExtractedEntity(
                    entity_type=field_name,
                    value=value,
                    confidence=0.7,  # Context-based confidence
                    is_valid=False,
                    validation_error=None,
                    source_text=message
                )
                
                entities.append(entity)
        
        return entities
    
    def _extract_structured_data(self, message: str, operation_type: str) -> List[ExtractedEntity]:
        """Extract entities from structured data (CSV-like input)"""
        
        entities = []
        
        # Check for comma-separated values
        if "," in message:
            parts = [part.strip() for part in message.split(",")]
            
            if operation_type == "user_create" and len(parts) >= 2:
                # Assume: Name, Email, Phone, Role format or variations
                field_mapping = self._determine_field_mapping(parts)
                
                for i, value in enumerate(parts):
                    if i < len(field_mapping) and value:
                        field_name = field_mapping[i]
                        
                        entity = ExtractedEntity(
                            entity_type=field_name,
                            value=value,
                            confidence=0.9,  # High confidence for structured data
                            is_valid=False,
                            validation_error=None,
                            source_text=message
                        )
                        
                        entities.append(entity)
        
        return entities
    
    def _determine_field_mapping(self, parts: List[str]) -> List[str]:
        """Determine field mapping for structured data"""
        
        mapping = []
        
        for part in parts:
            part_lower = part.lower().strip()
            
            # Email detection
            if "@" in part:
                mapping.append("email")
            # Phone detection
            elif re.match(r'^\+?[\d\s\-\(\)\.]+$', part) and len(re.sub(r'[\s\-\(\)\.+]', '', part)) >= 10:
                mapping.append("phone")
            # Name detection (first non-email, non-phone entry)
            elif re.match(r'^[A-Za-z\s\-\'\.]+$', part) and len(mapping) == 0:
                if " " in part:
                    mapping.append("full_name")
                else:
                    mapping.append("first_name")
            # Second name entry
            elif re.match(r'^[A-Za-z\s\-\'\.]+$', part) and "first_name" in mapping and "last_name" not in mapping:
                mapping.append("last_name")
            # Role/department detection
            elif any(role in part_lower for role in ["manager", "supervisor", "clerk", "agent", "staff"]):
                mapping.append("role")
            else:
                # Default to role for unknown text fields
                mapping.append("role")
        
        return mapping
    
    def _merge_entity_results(self, *entity_lists) -> List[ExtractedEntity]:
        """Merge and deduplicate entity extraction results"""
        
        merged_entities = {}
        
        for entity_list in entity_lists:
            for entity in entity_list:
                key = (entity["entity_type"], entity["value"].lower())
                
                # Keep entity with highest confidence
                if key not in merged_entities or entity["confidence"] > merged_entities[key]["confidence"]:
                    merged_entities[key] = entity
        
        return list(merged_entities.values())
    
    def _validate_entities(self, entities: List[ExtractedEntity], schema: Dict) -> List[ExtractedEntity]:
        """Validate and normalize extracted entities"""
        
        validated_entities = []
        
        for entity in entities:
            entity_type = entity["entity_type"]
            value = entity["value"]
            
            # Get validation config
            if entity_type in self.entity_patterns:
                validation_func = self.entity_patterns[entity_type]["validation"]
                normalize_func = self.entity_patterns[entity_type]["normalize"]
                
                # Validate
                is_valid, error_msg = validation_func(value)
                
                # Normalize if valid
                if is_valid:
                    normalized_value = normalize_func(value)
                else:
                    normalized_value = value
                
                # Update entity
                validated_entity = entity.copy()
                validated_entity["value"] = normalized_value
                validated_entity["is_valid"] = is_valid
                validated_entity["validation_error"] = error_msg
                
                validated_entities.append(validated_entity)
        
        return validated_entities
    
    def _calculate_extraction_confidence(self, entities: List[ExtractedEntity]) -> float:
        """Calculate overall extraction confidence"""
        
        if not entities:
            return 0.0
        
        total_confidence = sum(entity["confidence"] for entity in entities)
        avg_confidence = total_confidence / len(entities)
        
        # Adjust based on validation success
        valid_entities = [e for e in entities if e["is_valid"]]
        validation_rate = len(valid_entities) / len(entities) if entities else 0
        
        return avg_confidence * validation_rate
    
    def _update_operation_data(self, state: ChatState, entities: List[ExtractedEntity], operation_type: str) -> ChatState:
        """Update operation-specific data with extracted entities"""
        
        updated_state = state.copy()
        
        if operation_type.startswith("user_"):
            # Update user operation data
            if not updated_state.get("user_operation"):
                updated_state["user_operation"] = UserOperationData(
                    operation_type=operation_type.split("_")[1],  # create, update, delete
                    user_id=None,
                    first_name=None,
                    last_name=None,
                    email=None,
                    phone=None,
                    role=None,
                    department=None,
                    property=None,
                    status=None,
                    required_fields=[],
                    collected_fields=[],
                    missing_fields=[]
                )
            
            # Update with extracted data
            user_op = updated_state["user_operation"]
            for entity in entities:
                if entity["is_valid"]:
                    entity_type = entity["entity_type"]
                    if entity_type in user_op:
                        user_op[entity_type] = entity["value"]
                        if entity_type not in user_op["collected_fields"]:
                            user_op["collected_fields"].append(entity_type)
        
        elif operation_type.startswith("service_"):
            # Update service operation data
            if not updated_state.get("service_operation"):
                updated_state["service_operation"] = ServiceOperationData(
                    operation_type=operation_type.split("_")[1],
                    service_id=None,
                    service_name=None,
                    service_type=None,
                    description=None,
                    priority=None,
                    assigned_to=None,
                    required_fields=[],
                    collected_fields=[]
                )
            
            # Update with extracted data
            service_op = updated_state["service_operation"]
            for entity in entities:
                if entity["is_valid"]:
                    entity_type = entity["entity_type"]
                    if entity_type in service_op:
                        service_op[entity_type] = entity["value"]
                        if entity_type not in service_op["collected_fields"]:
                            service_op["collected_fields"].append(entity_type)
        
        return updated_state
    
    def _update_field_progress(self, state: ChatState, entities: List[ExtractedEntity], schema: Dict) -> ChatState:
        """Update field collection progress"""
        
        updated_state = state.copy()
        
        # Get required and collected fields
        required_fields = schema.get("required", [])
        collected_fields = [e["entity_type"] for e in entities if e["is_valid"]]
        
        # Calculate missing fields
        missing_fields = [field for field in required_fields if field not in collected_fields]
        
        # Update state
        updated_state["required_fields"] = required_fields
        updated_state["collected_fields"] = list(set(updated_state.get("collected_fields", []) + collected_fields))
        updated_state["missing_fields"] = missing_fields
        
        return updated_state
    
    # Validation functions for different entity types
    def _validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address"""
        try:
            validate_email(email)
            return True, None
        except EmailNotValidError as e:
            return False, str(e)
    
    def _validate_phone(self, phone: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number"""
        try:
            parsed = phonenumbers.parse(phone, "US")
            if phonenumbers.is_valid_number(parsed):
                return True, None
            else:
                return False, "Invalid phone number format"
        except:
            return False, "Invalid phone number format"
    
    def _validate_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate name field"""
        if not name or len(name.strip()) < 1:
            return False, "Name cannot be empty"
        
        if len(name) > 100:
            return False, "Name too long"
        
        if not re.match(r"^[A-Za-z\s\-'\.]+$", name):
            return False, "Name contains invalid characters"
        
        return True, None
    
    def _validate_single_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate single name field (first/last name)"""
        return self._validate_name(name)
    
    def _validate_role(self, role: str) -> Tuple[bool, Optional[str]]:
        """Validate role field"""
        if not role:
            return False, "Role cannot be empty"
        
        role_lower = role.lower().strip()
        valid_roles = self.validation_rules["role"]["allowed_values"]
        
        if role_lower in valid_roles:
            return True, None
        
        # Check for partial matches
        for valid_role in valid_roles:
            if valid_role in role_lower or role_lower in valid_role:
                return True, None
        
        return False, f"Invalid role. Valid roles: {', '.join(valid_roles)}"
    
    def _validate_department(self, department: str) -> Tuple[bool, Optional[str]]:
        """Validate department field"""
        if not department:
            return False, "Department cannot be empty"
        
        dept_lower = department.lower().strip()
        valid_depts = self.validation_rules["department"]["allowed_values"]
        
        if dept_lower in valid_depts:
            return True, None
        
        # Check for partial matches
        for valid_dept in valid_depts:
            if valid_dept in dept_lower or dept_lower in valid_dept:
                return True, None
        
        return False, f"Invalid department. Valid departments: {', '.join(valid_depts)}"
    
    def _validate_service_name(self, service_name: str) -> Tuple[bool, Optional[str]]:
        """Validate service name"""
        if not service_name or len(service_name.strip()) < 3:
            return False, "Service name must be at least 3 characters"
        
        if len(service_name) > 200:
            return False, "Service name too long"
        
        return True, None
    
    def _validate_priority(self, priority: str) -> Tuple[bool, Optional[str]]:
        """Validate priority field"""
        valid_priorities = ["high", "medium", "low", "urgent", "normal"]
        if priority.lower() in valid_priorities:
            return True, None
        
        return False, f"Invalid priority. Valid priorities: {', '.join(valid_priorities)}"
    
    # Normalization functions
    def _normalize_email(self, email: str) -> str:
        """Normalize email address"""
        return email.lower().strip()
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        try:
            parsed = phonenumbers.parse(phone, "US")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except:
            return phone
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name field"""
        return name.strip().title()
    
    def _normalize_single_name(self, name: str) -> str:
        """Normalize single name field"""
        return name.strip().title()
    
    def _normalize_role(self, role: str) -> str:
        """Normalize role field"""
        role_mappings = {
            "front desk": "front_desk",
            "front office": "front_desk",
            "reception": "front_desk",
            "housekeeper": "housekeeping",
            "cleaner": "housekeeping",
            "maintenance": "maintenance",
            "security": "security",
            "admin": "admin",
            "administrator": "admin",
            "staff": "staff",
            "employee": "staff"
        }
        
        role_lower = role.lower().strip()
        return role_mappings.get(role_lower, role_lower)
    
    def _normalize_department(self, department: str) -> str:
        """Normalize department field"""
        dept_mappings = {
            "front office": "front_office",
            "front desk": "front_office",
            "housekeeping": "housekeeping",
            "maintenance": "maintenance",
            "security": "security",
            "food and beverage": "food_beverage",
            "f&b": "food_beverage",
            "restaurant": "food_beverage",
            "admin": "admin",
            "administration": "admin",
            "management": "management"
        }
        
        dept_lower = department.lower().strip()
        return dept_mappings.get(dept_lower, dept_lower)
    
    def _normalize_service_name(self, service_name: str) -> str:
        """Normalize service name"""
        return service_name.strip().title()
    
    def _normalize_priority(self, priority: str) -> str:
        """Normalize priority field"""
        priority_mappings = {
            "urgent": "high",
            "normal": "medium"
        }
        
        priority_lower = priority.lower().strip()
        return priority_mappings.get(priority_lower, priority_lower)
    
    def get_extraction_stats(self) -> Dict:
        """Get data extraction performance statistics"""
        
        success_rate = 0.0
        if self.extraction_stats["total_extractions"] > 0:
            success_rate = self.extraction_stats["successful_extractions"] / self.extraction_stats["total_extractions"]
        
        return {
            **self.extraction_stats,
            "success_rate": success_rate
        }
    
    def _has_required_fields(self, entities: List[ExtractedEntity], schema: Dict) -> bool:
        """Check if we have enough required fields from pattern extraction"""
        if not schema.get("required"):
            return True
            
        required_fields = set(schema["required"])
        found_fields = set()
        
        for entity in entities:
            if entity.get("is_valid", False):
                found_fields.add(entity["entity_type"])
        
        # Check if we have at least 2 required fields or all of them
        return len(found_fields.intersection(required_fields)) >= min(2, len(required_fields))
    
    def _extract_with_llm_optimized(self, message: str, operation_type: str, state: ChatState) -> List[ExtractedEntity]:
        """Optimized LLM extraction with minimal prompt"""
        
        try:
            # OPTIMIZATION: Much smaller, focused prompt
            prompt = f"""Extract user info from: "{message}"

Return JSON: {{"entities": [{{"type": "first_name", "value": "John", "confidence": 0.9}}]}}

Extract: first_name, last_name, email, phone, role, department"""

            from llm_utils import ask_gemini
            
            response = ask_gemini(prompt)
            
            # Parse LLM response
            import json
            import re
            
            # Clean response - remove markdown if present
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            try:
                parsed = json.loads(clean_response)
                entities = []
                
                for entity_data in parsed.get("entities", []):
                    entity = ExtractedEntity(
                        entity_type=entity_data["type"],
                        value=str(entity_data["value"]).strip(),
                        confidence=float(entity_data.get("confidence", 0.8)),
                        extraction_method="llm",
                        source_text=message,
                        is_valid=True,  # Will be validated later
                        validation_error=None
                    )
                    entities.append(entity)
                
                log_action("LLM_EXTRACTION_SUCCESS", 
                          f"LLM extracted {len(entities)} entities from: '{message[:30]}...'",
                          session_id=state.get("session_id", "unknown"))
                
                return entities
                
            except json.JSONDecodeError as e:
                log_action("LLM_EXTRACTION_JSON_ERROR", 
                          f"Failed to parse LLM response: {clean_response[:50]}...",
                          session_id=state.get("session_id", "unknown"))
                return []
                
        except Exception as e:
            log_error("LLM_EXTRACTION_ERROR", f"LLM extraction failed: {str(e)}", 
                     session_id=state.get("session_id", "unknown"))
            return []

    def _extract_with_llm(self, message: str, operation_type: str, state: ChatState) -> List[ExtractedEntity]:
        """Legacy method - redirects to optimized version"""
        return self._extract_with_llm_optimized(message, operation_type, state)

# Initialize data extraction agent instance
data_extraction_agent = DataExtractionAgent()
