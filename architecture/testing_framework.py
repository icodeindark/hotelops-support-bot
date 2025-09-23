"""
Testing Framework for Hotel Multi-Agent System
Inspired by LangSmith testing patterns but simplified for our needs
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import time

@dataclass
class TestCase:
    """Individual test case for agent behavior"""
    test_id: str
    name: str
    input_query: str
    expected_intent: str
    expected_agent: str
    expected_complexity: str
    context: Dict[str, Any]
    success_criteria: List[str]
    created_at: datetime

@dataclass
class TestResult:
    """Result of running a test case"""
    test_id: str
    status: str  # passed, failed, error
    actual_intent: str
    actual_agent: str
    actual_complexity: str
    response_time: float
    response_content: str
    errors: List[str]
    timestamp: datetime

class HotelTestFramework:
    """
    Testing framework for systematic validation of multi-agent behavior
    Focuses on hotel management scenarios
    """
    
    def __init__(self):
        self.test_cases = []
        self.test_results = []
        self.baseline_performance = {}
        
        # Load predefined test cases
        self._initialize_core_test_cases()
    
    def _initialize_core_test_cases(self):
        """Initialize core test cases for hotel management scenarios"""
        
        core_tests = [
            # User Management Tests
            {
                "name": "Simple User Creation",
                "input_query": "create a new user named John Doe",
                "expected_intent": "create_user_with_permissions",
                "expected_agent": "user_management",
                "expected_complexity": "medium",
                "context": {},
                "success_criteria": [
                    "Intent correctly identified as user creation",
                    "Routed to user management agent",
                    "Response includes confirmation of user creation"
                ]
            },
            {
                "name": "User List Request",
                "input_query": "show me all users",
                "expected_intent": "list_users",
                "expected_agent": "user_management", 
                "expected_complexity": "simple",
                "context": {},
                "success_criteria": [
                    "Intent correctly identified as user listing",
                    "Response contains user list or empty state message"
                ]
            },
            
            # Service Management Tests
            {
                "name": "Service Creation",
                "input_query": "add a new room service called breakfast delivery",
                "expected_intent": "setup_new_service",
                "expected_agent": "service_management",
                "expected_complexity": "medium",
                "context": {},
                "success_criteria": [
                    "Intent correctly identified as service creation",
                    "Response includes service setup confirmation"
                ]
            },
            
            # Knowledge Base Tests
            {
                "name": "FAQ Query",
                "input_query": "how do I reset my password",
                "expected_intent": "information_retrieval",
                "expected_agent": "knowledge_base",
                "expected_complexity": "simple",
                "context": {},
                "success_criteria": [
                    "Intent correctly identified as information request",
                    "Response contains password reset instructions"
                ]
            },
            
            # Complex Workflow Tests
            {
                "name": "Multi-Step Troubleshooting",
                "input_query": "the wifi is not working in room 305 and guest is complaining",
                "expected_intent": "resolve_system_issue",
                "expected_agent": "knowledge_base",
                "expected_complexity": "complex",
                "context": {"room": "305", "issue_type": "connectivity"},
                "success_criteria": [
                    "Intent correctly identified as troubleshooting",
                    "Response includes systematic troubleshooting steps",
                    "Multiple sub-tasks identified"
                ]
            },
            
            # Conversation Flow Tests
            {
                "name": "Topic Transition",
                "input_query": "what about services",
                "expected_intent": "service_management_general",
                "expected_agent": "service_management",
                "expected_complexity": "simple",
                "context": {"previous_agent": "user_management"},
                "success_criteria": [
                    "Topic switch correctly detected",
                    "Natural transition to service management"
                ]
            },
            
            # Edge Cases
            {
                "name": "Ambiguous Query",
                "input_query": "help",
                "expected_intent": "information_retrieval",
                "expected_agent": "conversation_manager",
                "expected_complexity": "simple",
                "context": {},
                "success_criteria": [
                    "Graceful handling of ambiguous request",
                    "Clarification or general help provided"
                ]
            },
            
            # Typo Handling
            {
                "name": "Typo Tolerance",
                "input_query": "usr manaegment",
                "expected_intent": "user_management_general",
                "expected_agent": "user_management",
                "expected_complexity": "simple",
                "context": {},
                "success_criteria": [
                    "Typos correctly interpreted",
                    "Routed to user management despite spelling errors"
                ]
            }
        ]
        
        # Convert to TestCase objects
        for i, test_data in enumerate(core_tests):
            test_case = TestCase(
                test_id=f"core_test_{i+1:03d}",
                name=test_data["name"],
                input_query=test_data["input_query"],
                expected_intent=test_data["expected_intent"],
                expected_agent=test_data["expected_agent"],
                expected_complexity=test_data["expected_complexity"],
                context=test_data["context"],
                success_criteria=test_data["success_criteria"],
                created_at=datetime.now()
            )
            self.test_cases.append(test_case)
    
    def run_single_test(self, test_case: TestCase, system_under_test) -> TestResult:
        """Run a single test case against the system"""
        
        start_time = time.time()
        errors = []
        status = "passed"
        
        try:
            # Run the test
            result = system_under_test.process_request(
                test_case.input_query, 
                test_case.context
            )
            
            response_time = time.time() - start_time
            
            # Extract actual values
            actual_intent = result.get("intent", "unknown")
            actual_agent = result.get("agent_used", "unknown")
            actual_complexity = result.get("complexity", "unknown")
            response_content = result.get("response", "")
            
            # Validate against expectations
            if actual_intent != test_case.expected_intent:
                errors.append(f"Intent mismatch: expected {test_case.expected_intent}, got {actual_intent}")
            
            if actual_agent != test_case.expected_agent:
                errors.append(f"Agent mismatch: expected {test_case.expected_agent}, got {actual_agent}")
            
            if actual_complexity != test_case.expected_complexity:
                errors.append(f"Complexity mismatch: expected {test_case.expected_complexity}, got {actual_complexity}")
            
            # Check success criteria
            for criterion in test_case.success_criteria:
                if not self._check_success_criterion(criterion, result, response_content):
                    errors.append(f"Success criterion not met: {criterion}")
            
            if errors:
                status = "failed"
            
        except Exception as e:
            response_time = time.time() - start_time
            actual_intent = "error"
            actual_agent = "error"
            actual_complexity = "error"
            response_content = str(e)
            errors.append(f"Test execution error: {str(e)}")
            status = "error"
        
        return TestResult(
            test_id=test_case.test_id,
            status=status,
            actual_intent=actual_intent,
            actual_agent=actual_agent,
            actual_complexity=actual_complexity,
            response_time=response_time,
            response_content=response_content,
            errors=errors,
            timestamp=datetime.now()
        )
    
    def _check_success_criterion(self, criterion: str, result: Dict[str, Any], response: str) -> bool:
        """Check if a success criterion is met"""
        
        criterion_lower = criterion.lower()
        response_lower = response.lower()
        
        # Basic keyword matching for success criteria
        if "confirmation" in criterion_lower:
            return any(word in response_lower for word in ["created", "added", "confirmed", "success"])
        
        elif "list" in criterion_lower:
            return any(word in response_lower for word in ["user", "service", "found", "available"])
        
        elif "instructions" in criterion_lower:
            return any(word in response_lower for word in ["step", "follow", "how to", "procedure"])
        
        elif "troubleshooting" in criterion_lower:
            return any(word in response_lower for word in ["check", "verify", "troubleshoot", "issue"])
        
        elif "transition" in criterion_lower:
            return result.get("success", False)
        
        else:
            # Default: check if criterion keywords appear in response
            criterion_words = criterion_lower.split()
            return any(word in response_lower for word in criterion_words)
    
    def run_test_suite(self, system_under_test, test_filter: str = None) -> Dict[str, Any]:
        """Run complete test suite"""
        
        # Filter tests if specified
        if test_filter:
            filtered_tests = [t for t in self.test_cases if test_filter.lower() in t.name.lower()]
        else:
            filtered_tests = self.test_cases
        
        results = []
        start_time = time.time()
        
        print(f"Running {len(filtered_tests)} tests...")
        
        for i, test_case in enumerate(filtered_tests, 1):
            print(f"  [{i}/{len(filtered_tests)}] {test_case.name}... ", end="")
            
            result = self.run_single_test(test_case, system_under_test)
            results.append(result)
            
            status_symbol = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            print(f"{status_symbol} ({result.response_time:.2f}s)")
            
            if result.errors:
                for error in result.errors:
                    print(f"    • {error}")
        
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        passed = len([r for r in results if r.status == "passed"])
        failed = len([r for r in results if r.status == "failed"])
        errors = len([r for r in results if r.status == "error"])
        
        avg_response_time = sum(r.response_time for r in results) / len(results) if results else 0
        
        summary = {
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": (passed / len(results)) * 100 if results else 0,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "results": results
        }
        
        # Store results for historical tracking
        self.test_results.extend(results)
        
        return summary
    
    def compare_with_baseline(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current test results with baseline performance"""
        
        if not self.baseline_performance:
            self.baseline_performance = current_results
            return {"message": "Baseline established"}
        
        comparison = {
            "pass_rate_change": current_results["pass_rate"] - self.baseline_performance["pass_rate"],
            "response_time_change": current_results["avg_response_time"] - self.baseline_performance["avg_response_time"],
            "regression_tests": [],
            "improvement_tests": []
        }
        
        # Identify regressions and improvements
        baseline_by_id = {r.test_id: r for r in self.baseline_performance["results"]}
        
        for current_result in current_results["results"]:
            baseline_result = baseline_by_id.get(current_result.test_id)
            
            if baseline_result:
                if baseline_result.status == "passed" and current_result.status != "passed":
                    comparison["regression_tests"].append(current_result.test_id)
                elif baseline_result.status != "passed" and current_result.status == "passed":
                    comparison["improvement_tests"].append(current_result.test_id)
        
        return comparison
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        
        report = f"""
🧪 **Hotel Multi-Agent System Test Report**
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 **Summary**
• Total Tests: {results['total_tests']}
• Passed: {results['passed']} ✅
• Failed: {results['failed']} ❌  
• Errors: {results['errors']} ⚠️
• Pass Rate: {results['pass_rate']:.1f}%
• Total Time: {results['total_time']:.2f}s
• Avg Response Time: {results['avg_response_time']:.3f}s

📋 **Test Results by Category**
"""
        
        # Group results by category
        categories = {}
        for result in results["results"]:
            test_case = next(t for t in self.test_cases if t.test_id == result.test_id)
            category = test_case.name.split()[0]  # First word as category
            
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "errors": 0}
            
            categories[category][result.status] += 1
        
        for category, counts in categories.items():
            total = sum(counts.values())
            pass_rate = (counts["passed"] / total) * 100 if total > 0 else 0
            report += f"\n**{category}**: {counts['passed']}/{total} passed ({pass_rate:.1f}%)"
        
        # Add failed test details
        failed_tests = [r for r in results["results"] if r.status != "passed"]
        if failed_tests:
            report += "\n\n❌ **Failed Tests**"
            for result in failed_tests:
                test_case = next(t for t in self.test_cases if t.test_id == result.test_id)
                report += f"\n• {test_case.name} ({result.status})"
                for error in result.errors:
                    report += f"\n  - {error}"
        
        return report
    
    def add_custom_test(self, name: str, query: str, expected_intent: str, 
                       expected_agent: str, context: Dict[str, Any] = None) -> str:
        """Add a custom test case"""
        
        test_id = f"custom_test_{len(self.test_cases) + 1:03d}"
        
        test_case = TestCase(
            test_id=test_id,
            name=name,
            input_query=query,
            expected_intent=expected_intent,
            expected_agent=expected_agent,
            expected_complexity="medium",  # Default
            context=context or {},
            success_criteria=[f"Intent correctly identified as {expected_intent}"],
            created_at=datetime.now()
        )
        
        self.test_cases.append(test_case)
        return test_id

# Global testing framework instance
test_framework = HotelTestFramework()
