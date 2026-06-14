from typing import Any, Tuple
from loguru import logger
from app.agents.context import IncompleteJSONError

class VerifierAgent:
    """
    VerifierAgent checks the output of upstream agents for completeness and validity.
    It returns a tuple: (is_complete, feedback)
    """
    def __init__(self):
        self.agent_name = "VerifierAgent"

    async def verify(self, agent_name: str, agent_output: Any) -> Tuple[bool, str]:
        """
        Evaluate if the output is complete.
        If it's an IncompleteJSONError, it means the LLM truncated the JSON.
        If it's a dict, we can do semantic checks if needed.
        """
        if isinstance(agent_output, IncompleteJSONError):
            logger.warning(f"[VerifierAgent] {agent_name} output was truncated. Requesting retry.")
            # We don't append the raw output in the feedback directly if it's too large,
            # but we tell the LLM exactly what went wrong.
            feedback = (
                f"Your previous JSON response was truncated and invalid: {str(agent_output)}. "
                "Please generate the complete JSON object from the beginning. Ensure it is fully closed."
            )
            return False, feedback
            
        if not isinstance(agent_output, dict):
            return False, "Output was not a valid JSON dictionary."
            
        # Basic check to ensure it has a status
        if "status" not in agent_output:
            logger.warning(f"[VerifierAgent] {agent_name} output missing 'status' key.")
            return False, "The generated JSON is missing the required 'status' key. Please ensure it adheres to the requested schema."

        # Agent-specific schema checks
        required_keys = {
            "RequirementAnalyzerAgent": ["project_overview", "tech_stack", "features", "core_modules"],
            "PlannerAgent": ["execution_strategy", "project_phases", "module_execution_order"],
            "ResearchPlanningAgent": ["plan_markdown", "proposed_changes"],
            "DatabaseArchitectureAgent": ["database_strategy", "entities", "relationships"],
            "BackendArchitectureAgent": ["backend_strategy", "backend_structure", "service_architecture"],
            "APIAgent": ["api_strategy", "endpoints", "global_configurations"],
            "FrontendArchitectureAgent": ["frontend_strategy", "pages", "layouts"],
            "UIUXArchitectAgent": ["design_system", "color_palette", "typography_system"],
            "AuthArchitectureAgent": ["authentication_strategy", "authentication_workflows", "authentication_entities"],
            "RealtimeArchitectureAgent": ["realtime_strategy", "websocket_architecture", "event_driven_architecture"],
            "StateManagementAgent": ["state_management_strategy", "global_state_architecture", "api_cache_architecture"],
            "DevOpsArchitectureAgent": ["infrastructure_strategy", "containerization_architecture", "cicd_architecture"],
            "SecurityArchitectureAgent": ["security_strategy", "api_security_architecture", "authentication_security"],
            "TestingArchitectureAgent": ["testing_strategy", "unit_testing_architecture", "integration_testing_architecture"],
            "ValidationArchitectureAgent": ["validation_strategy", "entity_validation", "api_validation"],
            "OptimizationArchitectureAgent": ["optimization_strategy", "backend_optimization", "database_optimization"],
            "CodeGenerationPlannerAgent": ["generation_strategy", "generation_phases", "build_graph"],
            "DatabaseModelGenerationAgent": ["persistence_generation_strategy", "generated_models", "relationship_generation"],
            "BackendCodeGenerationAgent": ["backend_generation_strategy", "generated_backend_structure", "service_generation"],
            "APIImplementationAgent": ["api_generation_strategy", "generated_routes", "router_generation"],
            "FrontendCodeGenerationAgent": ["frontend_generation_strategy", "generated_frontend_structure", "page_generation"],
            "UIComponentGenerationAgent": ["ui_generation_strategy", "generated_components"],
            "StateImplementationAgent": ["state_generation_strategy", "zustand_generation"],
            "IntegrationGenerationAgent": ["integration_generation_strategy", "frontend_backend_integration"],
            "BuildCompilationAgent": ["build_compilation_strategy", "project_structure_generation"],
            "ErrorCorrectionAgent": ["error_recovery_strategy", "import_dependency_repairs"],
            "ProjectExportAgent": ["export_generation_strategy", "repository_generation", "deployment_export_generation"]
        }
        
        keys = required_keys.get(agent_name, [])
        missing = [k for k in keys if k not in agent_output]
        if missing:
            logger.warning(f"[VerifierAgent] {agent_name} output missing keys: {missing}")
            return False, f"The generated JSON is missing the following required keys: {', '.join(missing)}. Please regenerate the output adhering exactly to the requested schema."

        # If it reached here, it's a complete JSON dict that passed parsing!
        logger.info(f"[VerifierAgent] {agent_name} output verified successfully.")
        return True, ""
