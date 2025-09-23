"""
Scalable Multi-Agent Architecture for Hotel Management
Inspired by successful e-commerce multi-agent patterns
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

class TaskType(Enum):
    """Types of hotel management tasks"""
    USER_OPERATIONS = "user_operations"
    SERVICE_OPERATIONS = "service_operations"
    INFORMATION_RETRIEVAL = "information_retrieval"
    TROUBLESHOOTING = "troubleshooting"
    COMPLEX_WORKFLOW = "complex_workflow"

@dataclass
class SubTask:
    """Individual sub-task within a larger operation"""
    task_id: str
    task_type: TaskType
    description: str
    assigned_agent: str
    status: str  # pending, in_progress, completed, failed
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    dependencies: List[str]  # IDs of tasks this depends on
    priority: int = 1

@dataclass
class TaskPlan:
    """Complete execution plan for a user request"""
    plan_id: str
    original_query: str
    sub_tasks: List[SubTask]
    execution_order: List[str]  # Task IDs in execution order
    estimated_complexity: str  # simple, medium, complex
    requires_confirmation: bool = False

class HotelPlannerAgent:
    """
    Planner Agent - Breaks down complex hotel operations into manageable sub-tasks
    Similar to the e-commerce example but adapted for hotel management
    """
    
    def __init__(self):
        self.task_templates = {
            # User management workflows
            "create_user_with_permissions": [
                {"type": "information_retrieval", "description": "Validate user data requirements"},
                {"type": "user_operations", "description": "Create user account"},
                {"type": "user_operations", "description": "Assign role and permissions"},
                {"type": "information_retrieval", "description": "Send confirmation to user"}
            ],
            
            # Service management workflows
            "setup_new_service": [
                {"type": "information_retrieval", "description": "Check service requirements and pricing"},
                {"type": "service_operations", "description": "Create service entry"},
                {"type": "service_operations", "description": "Configure service parameters"},
                {"type": "information_retrieval", "description": "Update service catalog"}
            ],
            
            # Complex troubleshooting workflows
            "resolve_system_issue": [
                {"type": "information_retrieval", "description": "Gather issue details and symptoms"},
                {"type": "troubleshooting", "description": "Diagnose root cause"},
                {"type": "troubleshooting", "description": "Apply resolution steps"},
                {"type": "information_retrieval", "description": "Verify fix and document solution"}
            ]
        }
        
        self.complexity_indicators = {
            "simple": ["list", "show", "what is", "help"],
            "medium": ["create", "update", "configure", "setup"],
            "complex": ["migrate", "integrate", "troubleshoot", "analyze", "optimize"]
        }
    
    def analyze_and_plan(self, user_query: str, context: Dict[str, Any]) -> TaskPlan:
        """
        Analyze user query and create execution plan
        This is the key scalability improvement - proper task decomposition
        """
        
        # Step 1: Classify the overall intent and complexity
        primary_intent = self._classify_primary_intent(user_query)
        complexity = self._assess_complexity(user_query)
        
        # Step 2: Break down into sub-tasks
        sub_tasks = self._decompose_into_subtasks(user_query, primary_intent, context)
        
        # Step 3: Determine execution order and dependencies
        execution_order = self._plan_execution_order(sub_tasks)
        
        # Step 4: Create the execution plan
        plan = TaskPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            original_query=user_query,
            sub_tasks=sub_tasks,
            execution_order=execution_order,
            estimated_complexity=complexity,
            requires_confirmation=complexity == "complex"
        )
        
        return plan
    
    def _classify_primary_intent(self, query: str) -> str:
        """Classify the main intent of the query"""
        
        query_lower = query.lower()
        
        # User management intents
        if any(word in query_lower for word in ["user", "account", "employee", "staff"]):
            if any(word in query_lower for word in ["create", "add", "new"]):
                return "create_user_with_permissions"
            elif any(word in query_lower for word in ["list", "show", "all"]):
                return "list_users"
            else:
                return "user_management_general"
        
        # Service management intents
        elif any(word in query_lower for word in ["service", "offering", "amenity"]):
            if any(word in query_lower for word in ["create", "add", "new", "setup"]):
                return "setup_new_service"
            elif any(word in query_lower for word in ["list", "show", "available"]):
                return "list_services"
            else:
                return "service_management_general"
        
        # Troubleshooting intents
        elif any(word in query_lower for word in ["problem", "issue", "error", "broken", "fix"]):
            return "resolve_system_issue"
        
        # Information retrieval
        elif any(word in query_lower for word in ["help", "how", "what", "explain"]):
            return "information_retrieval"
        
        else:
            return "general_inquiry"
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity to determine resource allocation"""
        
        query_lower = query.lower()
        
        # Check for complexity indicators
        for complexity_level, indicators in self.complexity_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return complexity_level
        
        # Default to simple for unclear cases
        return "simple"
    
    def _decompose_into_subtasks(self, query: str, intent: str, context: Dict[str, Any]) -> List[SubTask]:
        """Break down the query into specific sub-tasks"""
        
        sub_tasks = []
        task_counter = 1
        
        # Use templates if available
        if intent in self.task_templates:
            template = self.task_templates[intent]
            
            for i, task_template in enumerate(template):
                sub_task = SubTask(
                    task_id=f"task_{task_counter}",
                    task_type=TaskType(task_template["type"]),
                    description=task_template["description"],
                    assigned_agent=self._assign_agent_for_task_type(task_template["type"]),
                    status="pending",
                    input_data={"original_query": query, "context": context},
                    output_data={},
                    dependencies=[] if i == 0 else [f"task_{i}"],  # Sequential by default
                    priority=1
                )
                sub_tasks.append(sub_task)
                task_counter += 1
        
        else:
            # Create a simple single-task plan for unrecognized intents
            sub_task = SubTask(
                task_id="task_1",
                task_type=TaskType.INFORMATION_RETRIEVAL,
                description=f"Handle general query: {query}",
                assigned_agent="conversation_manager",
                status="pending",
                input_data={"original_query": query, "context": context},
                output_data={},
                dependencies=[],
                priority=1
            )
            sub_tasks.append(sub_task)
        
        return sub_tasks
    
    def _assign_agent_for_task_type(self, task_type: str) -> str:
        """Assign the most appropriate agent for each task type"""
        
        agent_mapping = {
            "user_operations": "user_management",
            "service_operations": "service_management",
            "information_retrieval": "knowledge_base",
            "troubleshooting": "knowledge_base"
        }
        
        return agent_mapping.get(task_type, "conversation_manager")
    
    def _plan_execution_order(self, sub_tasks: List[SubTask]) -> List[str]:
        """Determine optimal execution order considering dependencies"""
        
        # For now, simple sequential execution
        # In the future, this could include parallel execution of independent tasks
        execution_order = []
        
        # Sort by dependencies and priority
        remaining_tasks = sub_tasks.copy()
        
        while remaining_tasks:
            # Find tasks with no pending dependencies
            ready_tasks = []
            for task in remaining_tasks:
                dependencies_met = all(
                    dep_id in execution_order for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Break potential circular dependencies
                ready_tasks = [remaining_tasks[0]]
            
            # Sort by priority and add to execution order
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            next_task = ready_tasks[0]
            execution_order.append(next_task.task_id)
            remaining_tasks.remove(next_task)
        
        return execution_order

class HotelResearchAgent:
    """
    Research Agent - Handles information gathering and knowledge retrieval
    Specialized for hotel domain knowledge
    """
    
    def __init__(self):
        self.knowledge_sources = {
            "user_policies": ["context/users.json", "policies/user_management.json"],
            "service_catalog": ["context/services.json", "policies/service_policies.json"],
            "troubleshooting": ["context/troubleshooting.json", "context/faq.json"],
            "procedures": ["context/procedures.json"]
        }
    
    def research_subtask(self, sub_task: SubTask) -> Dict[str, Any]:
        """
        Research information needed for a specific sub-task
        This is where RAG integration would happen
        """
        
        research_result = {
            "task_id": sub_task.task_id,
            "research_type": sub_task.task_type.value,
            "findings": [],
            "confidence": 0.0,
            "sources": [],
            "recommendations": []
        }
        
        # Determine what information to research based on task
        if sub_task.task_type == TaskType.USER_OPERATIONS:
            research_result = self._research_user_requirements(sub_task)
        
        elif sub_task.task_type == TaskType.SERVICE_OPERATIONS:
            research_result = self._research_service_requirements(sub_task)
        
        elif sub_task.task_type == TaskType.INFORMATION_RETRIEVAL:
            research_result = self._research_general_information(sub_task)
        
        elif sub_task.task_type == TaskType.TROUBLESHOOTING:
            research_result = self._research_troubleshooting_steps(sub_task)
        
        return research_result
    
    def _research_user_requirements(self, sub_task: SubTask) -> Dict[str, Any]:
        """Research user management requirements and policies"""
        # This would integrate with RAG system or knowledge base
        return {
            "task_id": sub_task.task_id,
            "research_type": "user_requirements",
            "findings": [
                "User creation requires: name, email, role",
                "Available roles: admin, manager, staff, guest",
                "Email validation is mandatory"
            ],
            "confidence": 0.9,
            "sources": ["user_policies"],
            "recommendations": ["Validate email format before creation"]
        }
    
    def _research_service_requirements(self, sub_task: SubTask) -> Dict[str, Any]:
        """Research service management requirements"""
        return {
            "task_id": sub_task.task_id,
            "research_type": "service_requirements",
            "findings": [
                "Service creation requires: name, description, pricing",
                "Services must be categorized",
                "Pricing must be in valid currency format"
            ],
            "confidence": 0.85,
            "sources": ["service_catalog"],
            "recommendations": ["Verify pricing format and category assignment"]
        }
    
    def _research_general_information(self, sub_task: SubTask) -> Dict[str, Any]:
        """Research general information requests"""
        return {
            "task_id": sub_task.task_id,
            "research_type": "general_information",
            "findings": ["General help information available"],
            "confidence": 0.7,
            "sources": ["faq", "procedures"],
            "recommendations": ["Provide relevant FAQ or procedure links"]
        }
    
    def _research_troubleshooting_steps(self, sub_task: SubTask) -> Dict[str, Any]:
        """Research troubleshooting procedures"""
        return {
            "task_id": sub_task.task_id,
            "research_type": "troubleshooting",
            "findings": [
                "Common troubleshooting steps: identify, diagnose, resolve, verify",
                "Escalation required for complex issues"
            ],
            "confidence": 0.8,
            "sources": ["troubleshooting"],
            "recommendations": ["Follow standard troubleshooting protocol"]
        }

class HotelExecutionAgent:
    """
    Execution Agent - Handles actual operations and tool calls
    Executes the planned tasks with proper logging and validation
    """
    
    def __init__(self):
        self.execution_log = []
        self.available_tools = {
            "user_management": ["create_user", "update_user", "delete_user", "list_users"],
            "service_management": ["create_service", "update_service", "list_services"],
            "knowledge_base": ["search_faq", "get_procedures", "troubleshoot"]
        }
    
    def execute_task_plan(self, task_plan: TaskPlan, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete task plan with proper sequencing
        """
        
        execution_result = {
            "plan_id": task_plan.plan_id,
            "overall_status": "in_progress",
            "task_results": {},
            "execution_log": [],
            "final_response": "",
            "errors": []
        }
        
        # Execute tasks in planned order
        for task_id in task_plan.execution_order:
            task = next(t for t in task_plan.sub_tasks if t.task_id == task_id)
            
            # Get research data for this task
            research_data = research_results.get(task_id, {})
            
            # Execute the individual task
            task_result = self._execute_individual_task(task, research_data)
            
            execution_result["task_results"][task_id] = task_result
            execution_result["execution_log"].append({
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "status": task_result["status"],
                "action": task_result.get("action", ""),
                "result": task_result.get("result", "")
            })
            
            # Stop execution if a critical task fails
            if task_result["status"] == "failed" and task.priority > 3:
                execution_result["overall_status"] = "failed"
                execution_result["errors"].append(f"Critical task {task_id} failed")
                break
        
        # Generate final response based on execution results
        if execution_result["overall_status"] != "failed":
            execution_result["overall_status"] = "completed"
            execution_result["final_response"] = self._generate_final_response(task_plan, execution_result)
        
        return execution_result
    
    def _execute_individual_task(self, task: SubTask, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with appropriate agent"""
        
        # This would call the actual agent methods
        # For now, return a mock execution result
        
        return {
            "task_id": task.task_id,
            "status": "completed",
            "action": f"Executed {task.description}",
            "result": f"Task {task.task_id} completed successfully",
            "agent_used": task.assigned_agent,
            "research_used": len(research_data.get("findings", [])) > 0
        }
    
    def _generate_final_response(self, task_plan: TaskPlan, execution_result: Dict[str, Any]) -> str:
        """Generate comprehensive final response"""
        
        completed_tasks = sum(1 for result in execution_result["task_results"].values() 
                            if result["status"] == "completed")
        total_tasks = len(task_plan.sub_tasks)
        
        response = f"I've completed {completed_tasks} out of {total_tasks} tasks for your request: '{task_plan.original_query}'"
        
        if completed_tasks == total_tasks:
            response += "\n\n✅ All tasks completed successfully!"
        else:
            response += f"\n\n⚠️ {total_tasks - completed_tasks} tasks encountered issues."
        
        # Add specific results
        response += "\n\nDetails:"
        for task_id, result in execution_result["task_results"].items():
            task = next(t for t in task_plan.sub_tasks if t.task_id == task_id)
            response += f"\n• {task.description}: {result['status']}"
        
        return response

class ScalableMultiAgentOrchestrator:
    """
    Main orchestrator that coordinates all three specialized agents
    This replaces the monolithic approach with proper task decomposition
    """
    
    def __init__(self):
        self.planner = HotelPlannerAgent()
        self.researcher = HotelResearchAgent()
        self.executor = HotelExecutionAgent()
        
        self.active_plans = {}  # Track ongoing complex operations
    
    def process_request(self, user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing pipeline using multi-agent approach
        """
        
        try:
            # Step 1: Plan the operation
            task_plan = self.planner.analyze_and_plan(user_query, context)
            
            # Step 2: Research each sub-task
            research_results = {}
            for sub_task in task_plan.sub_tasks:
                if sub_task.task_type in [TaskType.INFORMATION_RETRIEVAL, TaskType.TROUBLESHOOTING]:
                    research_results[sub_task.task_id] = self.researcher.research_subtask(sub_task)
            
            # Step 3: Execute the plan
            execution_result = self.executor.execute_task_plan(task_plan, research_results)
            
            # Step 4: Return comprehensive result
            return {
                "success": execution_result["overall_status"] == "completed",
                "response": execution_result["final_response"],
                "agent_used": "multi_agent_orchestrator",
                "complexity": task_plan.estimated_complexity,
                "tasks_completed": len([r for r in execution_result["task_results"].values() 
                                     if r["status"] == "completed"]),
                "total_tasks": len(task_plan.sub_tasks),
                "execution_time": "calculated",
                "architecture_version": "scalable_v3"
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"I encountered an issue processing your request: {str(e)}",
                "agent_used": "multi_agent_orchestrator",
                "error": str(e)
            }

# Global orchestrator instance
scalable_orchestrator = ScalableMultiAgentOrchestrator()
