"""
HotelOpsAI In-Memory Database Layer - Prototype Implementation
Senior AI Engineer Implementation

This provides a dictionary/list-based storage system that mimics a real database.
Easy to replace with actual DB calls later.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from threading import Lock
from copy import deepcopy

from logger_config import agent_logger, log_action, log_error

class MemoryDatabase:
    """
    In-memory database that mimics real database operations.
    Thread-safe with proper indexing for fast lookups.
    """
    
    def __init__(self):
        # Main data storage
        self._data = {
            "users": {},           # user_id -> user_data
            "services": {},        # service_id -> service_data
            "conversations": {},   # conversation_id -> conversation_data
            "sessions": {},        # session_id -> session_data
            "analytics": {},       # metric_name -> metric_data
        }
        
        # Indexes for fast lookups
        self._indexes = {
            "users_by_email": {},      # email -> user_id
            "users_by_phone": {},      # phone -> user_id
            "services_by_name": {},    # service_name -> service_id
            "sessions_by_user": {},    # user_id -> [session_ids]
        }
        
        # Thread safety
        self._lock = Lock()
        
        # Auto-increment counters
        self._counters = {
            "users": 1000,
            "services": 2000,
            "conversations": 3000,
        }
        
        agent_logger.info("Memory Database initialized")
    
    def _generate_id(self, table: str) -> str:
        """Generate unique ID for table"""
        with self._lock:
            if table in self._counters:
                self._counters[table] += 1
                return f"{table[:-1]}_{self._counters[table]}"
            else:
                return str(uuid.uuid4())[:8]
    
    def _update_indexes(self, table: str, item_id: str, data: Dict[str, Any]):
        """Update indexes when data is inserted/updated"""
        
        if table == "users":
            # Email index
            if "email" in data:
                self._indexes["users_by_email"][data["email"]] = item_id
            
            # Phone index
            if "phone" in data:
                self._indexes["users_by_phone"][data["phone"]] = item_id
                
        elif table == "services":
            # Service name index
            if "service_name" in data:
                self._indexes["services_by_name"][data["service_name"]] = item_id
    
    # === USER OPERATIONS ===
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        # Generate user ID OUTSIDE the lock to avoid deadlock
        user_id = self._generate_id("users")
        
        with self._lock:
            # Check for duplicate email first (within same lock)
            email = user_data.get("email")
            if email and email in self._indexes["users_by_email"]:
                raise ValueError(f"User with email '{email}' already exists")
            
            # Add metadata
            user_record = {
                **user_data,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": user_data.get("status", "active")
            }
            
            # Store user
            self._data["users"][user_id] = user_record
            
            # Update indexes
            self._update_indexes("users", user_id, user_record)
            
            log_action("USER_CREATED", f"User {user_id} created: {user_record.get('email', 'N/A')}")
            
            return deepcopy(user_record)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self._lock:
            user = self._data["users"].get(user_id)
            return deepcopy(user) if user else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        with self._lock:
            user_id = self._indexes["users_by_email"].get(email)
            if user_id:
                return deepcopy(self._data["users"][user_id])
            return None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone"""
        with self._lock:
            user_id = self._indexes["users_by_phone"].get(phone)
            if user_id:
                return deepcopy(self._data["users"][user_id])
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        with self._lock:
            if user_id not in self._data["users"]:
                return None
            
            # Update data
            user_record = self._data["users"][user_id]
            user_record.update(updates)
            user_record["updated_at"] = datetime.now().isoformat()
            
            # Update indexes
            self._update_indexes("users", user_id, user_record)
            
            log_action("USER_UPDATED", f"User {user_id} updated")
            
            return deepcopy(user_record)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)"""
        with self._lock:
            if user_id not in self._data["users"]:
                return False
            
            # Soft delete
            self._data["users"][user_id]["status"] = "deleted"
            self._data["users"][user_id]["deleted_at"] = datetime.now().isoformat()
            
            log_action("USER_DELETED", f"User {user_id} deleted")
            
            return True
    
    def list_users(self, limit: int = 100, status: str = "active") -> List[Dict[str, Any]]:
        """List users with optional filtering"""
        with self._lock:
            users = []
            count = 0
            
            for user in self._data["users"].values():
                if user.get("status") == status and count < limit:
                    users.append(deepcopy(user))
                    count += 1
            
            return users
    
    def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users by name, email, or role"""
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for user in self._data["users"].values():
                if user.get("status") != "active":
                    continue
                
                # Search in various fields
                searchable_text = " ".join([
                    user.get("first_name", ""),
                    user.get("last_name", ""),
                    user.get("email", ""),
                    user.get("role", ""),
                    user.get("department", "")
                ]).lower()
                
                if query_lower in searchable_text:
                    results.append(deepcopy(user))
                
                if len(results) >= limit:
                    break
            
            return results
    
    # === SERVICE OPERATIONS ===
    
    def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service"""
        # Generate service ID OUTSIDE the lock to avoid deadlock
        service_id = self._generate_id("services")
        
        with self._lock:
            service_record = {
                **service_data,
                "service_id": service_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": service_data.get("status", "pending")
            }
            
            self._data["services"][service_id] = service_record
            self._update_indexes("services", service_id, service_record)
            
            log_action("SERVICE_CREATED", f"Service {service_id} created")
            
            return deepcopy(service_record)
    
    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service by ID"""
        with self._lock:
            service = self._data["services"].get(service_id)
            return deepcopy(service) if service else None
    
    def list_services(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List services with optional filtering"""
        with self._lock:
            services = []
            count = 0
            
            for service in self._data["services"].values():
                if status and service.get("status") != status:
                    continue
                
                if count < limit:
                    services.append(deepcopy(service))
                    count += 1
            
            return services
    
    def update_service(self, service_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update service data"""
        with self._lock:
            if service_id not in self._data["services"]:
                return None
            
            service_record = self._data["services"][service_id]
            service_record.update(updates)
            service_record["updated_at"] = datetime.now().isoformat()
            
            log_action("SERVICE_UPDATED", f"Service {service_id} updated")
            
            return deepcopy(service_record)
    
    # === SESSION OPERATIONS ===
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session data"""
        with self._lock:
            session_record = {
                **session_data,
                "session_id": session_id,
                "updated_at": datetime.now().isoformat()
            }
            
            if session_id not in self._data["sessions"]:
                session_record["created_at"] = datetime.now().isoformat()
            
            self._data["sessions"][session_id] = session_record
            return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            session = self._data["sessions"].get(session_id)
            return deepcopy(session) if session else None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        with self._lock:
            if session_id in self._data["sessions"]:
                del self._data["sessions"][session_id]
                return True
            return False
    
    # === CONVERSATION OPERATIONS ===
    
    def save_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation data"""
        with self._lock:
            conv_record = {
                **conversation_data,
                "conversation_id": conversation_id,
                "updated_at": datetime.now().isoformat()
            }
            
            if conversation_id not in self._data["conversations"]:
                conv_record["created_at"] = datetime.now().isoformat()
            
            self._data["conversations"][conversation_id] = conv_record
            return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation data"""
        with self._lock:
            conversation = self._data["conversations"].get(conversation_id)
            return deepcopy(conversation) if conversation else None
    
    # === ANALYTICS OPERATIONS ===
    
    def record_metric(self, metric_name: str, value: Any, metadata: Optional[Dict] = None):
        """Record analytics metric"""
        with self._lock:
            if metric_name not in self._data["analytics"]:
                self._data["analytics"][metric_name] = []
            
            metric_record = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            self._data["analytics"][metric_name].append(metric_record)
            
            # Keep only last 1000 records per metric
            if len(self._data["analytics"][metric_name]) > 1000:
                self._data["analytics"][metric_name] = self._data["analytics"][metric_name][-1000:]
    
    def get_metrics(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get analytics metrics"""
        with self._lock:
            metrics = self._data["analytics"].get(metric_name, [])
            return deepcopy(metrics[-limit:])
    
    # === UTILITY OPERATIONS ===
    
    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        with self._lock:
            return email in self._indexes["users_by_email"]
    
    def check_phone_exists(self, phone: str) -> bool:
        """Check if phone already exists"""
        with self._lock:
            return phone in self._indexes["users_by_phone"]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._lock:
            stats = {}
            for table, data in self._data.items():
                if isinstance(data, dict):
                    stats[table] = len(data)
                elif isinstance(data, list):
                    stats[table] = len(data)
            
            return stats
    
    def export_data(self, table: str) -> List[Dict[str, Any]]:
        """Export table data (for backup/migration)"""
        with self._lock:
            if table in self._data and isinstance(self._data[table], dict):
                return list(self._data[table].values())
            return []
    
    def import_data(self, table: str, data: List[Dict[str, Any]]) -> bool:
        """Import table data (for backup/migration)"""
        try:
            with self._lock:
                if table not in self._data:
                    self._data[table] = {}
                
                for record in data:
                    if f"{table[:-1]}_id" in record:  # users -> user_id, services -> service_id
                        record_id = record[f"{table[:-1]}_id"]
                        self._data[table][record_id] = record
                        
                        # Rebuild indexes
                        if table == "users":
                            self._update_indexes("users", record_id, record)
                        elif table == "services":
                            self._update_indexes("services", record_id, record)
                
                return True
        except Exception as e:
            log_error("IMPORT_ERROR", f"Failed to import {table}: {str(e)}")
            return False
    
    def clear_table(self, table: str) -> bool:
        """Clear all data from a table"""
        with self._lock:
            if table in self._data:
                self._data[table] = {} if isinstance(self._data[table], dict) else []
                
                # Clear related indexes
                if table == "users":
                    self._indexes["users_by_email"] = {}
                    self._indexes["users_by_phone"] = {}
                elif table == "services":
                    self._indexes["services_by_name"] = {}
                
                log_action("TABLE_CLEARED", f"Table {table} cleared")
                return True
            return False

# Global database instance
memory_db = MemoryDatabase()

# === DATABASE ADAPTER INTERFACE ===
# This interface can be easily replaced with real database calls

class DatabaseAdapter:
    """
    Database adapter interface that can be easily swapped
    with real database implementations (PostgreSQL, MongoDB, etc.)
    """
    
    def __init__(self, db_instance=None):
        self.db = db_instance or memory_db
    
    # User operations
    def create_user(self, user_data: Dict) -> Dict:
        """TODO: Replace with actual DB call"""
        return self.db.create_user(user_data)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.get_user(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.get_user_by_email(email)
    
    def update_user(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.update_user(user_id, updates)
    
    def delete_user(self, user_id: str) -> bool:
        """TODO: Replace with actual DB call"""
        return self.db.delete_user(user_id)
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.list_users(limit)
    
    def search_users(self, query: str) -> List[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.search_users(query)
    
    # Service operations
    def create_service(self, service_data: Dict) -> Dict:
        """TODO: Replace with actual DB call"""
        return self.db.create_service(service_data)
    
    def list_services(self, limit: int = 100) -> List[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.list_services(limit)
    
    # Session operations
    def save_session(self, session_id: str, data: Dict) -> bool:
        """TODO: Replace with actual DB call"""
        return self.db.save_session(session_id, data)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.get_session(session_id)
    
    # Conversation operations
    def save_conversation(self, conversation_id: str, data: Dict) -> bool:
        """TODO: Replace with actual DB call"""
        return self.db.save_conversation(conversation_id, data)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """TODO: Replace with actual DB call"""
        return self.db.get_conversation(conversation_id)
    
    # Validation helpers
    def email_exists(self, email: str) -> bool:
        """TODO: Replace with actual DB call"""
        return self.db.check_email_exists(email)
    
    def phone_exists(self, phone: str) -> bool:
        """TODO: Replace with actual DB call"""
        return self.db.check_phone_exists(phone)

# Global database adapter
db_adapter = DatabaseAdapter()
