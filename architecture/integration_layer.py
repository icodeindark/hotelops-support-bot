"""
Integration Layer - Connects new architecture with existing agents
Provides backward compatibility while enabling new features
"""

from typing import Dict, Any, Optional
import traceback

class ArchitectureIntegrator:
    """
    Integrates new dialogue management architecture with existing agents
    Acts as a bridge to gradually migrate to new architecture
    """
    
    def __init__(self):
        self.dialogue_manager = None
        self.response_generator = None
        self.fallback_to_existing = True
        
        # Try to initialize new components
        try:
            from architecture.dialogue_manager import dialogue_manager
            from architecture.response_generator import response_generator
            
            self.dialogue_manager = dialogue_manager
            self.response_generator = response_generator
            self.new_architecture_available = True
            
        except ImportError:
            self.new_architecture_available = False
    
    def process_with_new_architecture(self, session_id: str, message: str, 
                                    current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Try processing with new dialogue manager architecture
        Returns None if new architecture should not be used
        """
        
        if not self.new_architecture_available or not self.dialogue_manager:
            return None
        
        try:
            # Use new dialogue manager
            result = self.dialogue_manager.process_conversation_turn(
                session_id, message, current_state
            )
            
            # Format response using new response generator
            if self.response_generator and result.get("response"):
                formatted_response = self.response_generator.generate_response({
                    "agent_type": result.get("agent_used", "conversation_manager"),
                    "response_type": "general", 
                    "raw_response": result["response"],
                    "data": result.get("data", {})
                })
                result["response"] = formatted_response
            
            # Add metadata to indicate new architecture was used
            result["architecture_version"] = "v2"
            result["processing_method"] = "dialogue_manager"
            
            return result
            
        except Exception as e:
            # Log error but don't break the system
            print(f"New architecture error: {e}")
            if self.fallback_to_existing:
                return None
            else:
                raise
    
    def enhance_existing_response(self, response: str, agent_type: str, 
                                data: Dict[str, Any] = None) -> str:
        """
        Enhance existing agent responses using new response generator
        """
        
        if not self.response_generator:
            return response
        
        try:
            enhanced = self.response_generator.generate_response({
                "agent_type": agent_type,
                "response_type": "general",
                "raw_response": response,
                "data": data or {}
            })
            return enhanced
            
        except Exception:
            # Fallback to original response
            return response
    
    def should_use_new_architecture(self, message: str, current_state: Dict[str, Any]) -> bool:
        """
        Decide whether to use new architecture for this request
        Can be based on message complexity, user preferences, etc.
        """
        
        if not self.new_architecture_available:
            return False
        
        # For now, always try new architecture if available
        # Later we can add logic to selectively use it
        return True
    
    def get_conversation_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation insights from new architecture
        """
        
        if self.dialogue_manager:
            try:
                return self.dialogue_manager.get_conversation_summary(session_id)
            except Exception:
                pass
        
        return {"error": "Insights not available"}

# Global integrator instance
architecture_integrator = ArchitectureIntegrator()
