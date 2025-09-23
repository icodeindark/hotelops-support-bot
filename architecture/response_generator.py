"""
Unified Response Generator for Hotel Management Bot
Handles consistent response formatting across all agents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class ResponseGenerator:
    """
    Centralized response generation with consistent formatting
    Replaces scattered response generation across agents
    """
    
    def __init__(self):
        # Response templates by category
        self.templates = {
            # User management responses
            "user_created": "✅ User '{name}' has been successfully created with {role} privileges.",
            "user_list": "Here are the current users in the system:",
            "user_not_found": "I couldn't find a user with that information. Could you double-check the details?",
            
            # Service management responses  
            "service_added": "✅ Service '{service_name}' has been added successfully.",
            "service_list": "Here are the available services:",
            "service_updated": "✅ Service '{service_name}' has been updated.",
            
            # Knowledge base responses
            "info_found": "Here's what I found about '{query}':",
            "info_not_found": "I don't have specific information about '{query}'. Would you like me to help with something else?",
            "multiple_results": "I found several relevant answers:",
            
            # Conversation flow
            "greeting": "Hello! I'm here to help with user management, services, and general support. What can I do for you?",
            "clarification": "I want to make sure I understand correctly. Are you asking about {topic}?",
            "confirmation": "Just to confirm: you want to {action}. Is that right?",
            "transition": "Sure! Let me help you with {topic}.",
            
            # Error handling
            "general_error": "I encountered an issue processing that request. Could you try rephrasing?",
            "data_missing": "I need a bit more information. Could you provide {missing_fields}?",
            "permission_denied": "You don't have permission to perform that action."
        }
        
        # Response formats by agent
        self.agent_formats = {
            "user_management": {
                "prefix": "👥 **User Management**",
                "style": "structured"
            },
            "service_management": {
                "prefix": "⚙️ **Service Management**", 
                "style": "structured"
            },
            "knowledge_base": {
                "prefix": "",  # No prefix for knowledge responses
                "style": "conversational"
            },
            "conversation_manager": {
                "prefix": "",
                "style": "conversational"
            }
        }
    
    def generate_response(self, response_data: Dict[str, Any]) -> str:
        """
        Generate unified response based on agent data and context
        """
        
        agent_type = response_data.get("agent_type", "conversation_manager")
        response_type = response_data.get("response_type", "general")
        data = response_data.get("data", {})
        raw_response = response_data.get("raw_response", "")
        
        # Get agent formatting preferences
        agent_format = self.agent_formats.get(agent_type, self.agent_formats["conversation_manager"])
        
        # Generate based on response type
        if response_type in self.templates:
            formatted_response = self._format_template_response(response_type, data)
        else:
            formatted_response = self._format_raw_response(raw_response, agent_format)
        
        # Apply agent-specific formatting
        final_response = self._apply_agent_formatting(formatted_response, agent_format, data)
        
        return final_response
    
    def _format_template_response(self, response_type: str, data: Dict[str, Any]) -> str:
        """Format response using templates"""
        
        template = self.templates[response_type]
        
        try:
            # Replace placeholders with actual data
            formatted = template.format(**data)
            return formatted
        except KeyError as e:
            # Missing data for template
            return f"Response template error: missing {e}"
        except Exception:
            # Fallback to template without formatting
            return template
    
    def _format_raw_response(self, raw_response: str, agent_format: Dict[str, Any]) -> str:
        """Format raw response text"""
        
        if not raw_response:
            return "I'm processing your request..."
        
        # Clean up formatting
        cleaned = self._clean_response_text(raw_response)
        
        return cleaned
    
    def _apply_agent_formatting(self, response: str, agent_format: Dict[str, Any], 
                               data: Dict[str, Any]) -> str:
        """Apply agent-specific formatting"""
        
        style = agent_format.get("style", "conversational")
        prefix = agent_format.get("prefix", "")
        
        # Apply prefix if exists
        if prefix:
            response = f"{prefix}\n\n{response}"
        
        # Apply style-specific formatting
        if style == "structured":
            response = self._apply_structured_formatting(response, data)
        elif style == "conversational":
            response = self._apply_conversational_formatting(response)
        
        return response
    
    def _apply_structured_formatting(self, response: str, data: Dict[str, Any]) -> str:
        """Apply structured formatting for operational responses"""
        
        # Add bullet points for lists
        if isinstance(data.get("items"), list):
            items = data["items"]
            if items:
                formatted_items = []
                for item in items:
                    if isinstance(item, dict):
                        # Format dict items nicely
                        item_str = self._format_dict_item(item)
                    else:
                        item_str = str(item)
                    formatted_items.append(f"• {item_str}")
                
                response += "\n\n" + "\n".join(formatted_items)
        
        # Add summary if available
        if data.get("summary"):
            response += f"\n\n**Summary:** {data['summary']}"
        
        return response
    
    def _apply_conversational_formatting(self, response: str) -> str:
        """Apply conversational formatting for natural responses"""
        
        # Ensure proper spacing
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Clean up markdown formatting for readability
        response = self._clean_markdown(response)
        
        return response
    
    def _format_dict_item(self, item: Dict[str, Any]) -> str:
        """Format dictionary item for display"""
        
        if "name" in item:
            main_field = item["name"]
        elif "title" in item:
            main_field = item["title"]
        elif "id" in item:
            main_field = item["id"]
        else:
            main_field = str(item)
        
        # Add secondary info if available
        secondary_fields = []
        for key in ["role", "status", "type", "email"]:
            if key in item and item[key]:
                secondary_fields.append(f"{key}: {item[key]}")
        
        if secondary_fields:
            return f"{main_field} ({', '.join(secondary_fields)})"
        else:
            return main_field
    
    def _clean_response_text(self, text: str) -> str:
        """Clean up response text"""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove HTML-like tags that might have leaked through
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up markdown formatting
        text = self._clean_markdown(text)
        
        return text
    
    def _clean_markdown(self, text: str) -> str:
        """Clean up markdown formatting for consistency"""
        
        # Ensure proper spacing around headers
        text = re.sub(r'(#+\s+.+?)\n+', r'\1\n\n', text)
        
        # Ensure proper list formatting
        text = re.sub(r'\n+([•\-\*])', r'\n\1', text)
        
        # Clean up excessive formatting
        text = re.sub(r'\*{3,}', '**', text)  # Too many asterisks
        text = re.sub(r'_{3,}', '__', text)   # Too many underscores
        
        return text
    
    def generate_error_response(self, error_type: str, details: Dict[str, Any] = None) -> str:
        """Generate consistent error responses"""
        
        error_templates = {
            "validation_error": "I noticed an issue with the information provided: {error_details}",
            "permission_error": "You don't have permission to perform that action.",
            "not_found": "I couldn't find what you're looking for. Could you provide more details?",
            "system_error": "I encountered a technical issue. Please try again in a moment.",
            "timeout_error": "That request is taking longer than expected. Please try again.",
            "data_error": "There's an issue with the data format. Could you check and try again?"
        }
        
        template = error_templates.get(error_type, error_templates["system_error"])
        
        if details:
            try:
                return template.format(**details)
            except KeyError:
                pass
        
        return template
    
    def generate_list_response(self, items: List[Any], item_type: str, 
                             empty_message: str = None) -> str:
        """Generate consistent list responses"""
        
        if not items:
            return empty_message or f"No {item_type} found."
        
        if len(items) == 1:
            return f"Found 1 {item_type}:\n\n• {self._format_list_item(items[0])}"
        
        formatted_items = [f"• {self._format_list_item(item)}" for item in items]
        return f"Found {len(items)} {item_type}:\n\n" + "\n".join(formatted_items)
    
    def _format_list_item(self, item: Any) -> str:
        """Format individual list item"""
        
        if isinstance(item, dict):
            return self._format_dict_item(item)
        else:
            return str(item)
    
    def generate_confirmation_response(self, action: str, details: Dict[str, Any]) -> str:
        """Generate confirmation responses"""
        
        confirmation_template = f"I understand you want to {action}."
        
        if details:
            detail_parts = []
            for key, value in details.items():
                if value:
                    detail_parts.append(f"{key}: {value}")
            
            if detail_parts:
                confirmation_template += f" Details: {', '.join(detail_parts)}."
        
        confirmation_template += " Is this correct?"
        
        return confirmation_template

# Global response generator instance
response_generator = ResponseGenerator()
