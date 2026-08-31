from typing import Any, Dict, List, Tuple
from app.agents.context import IncompleteJSONError

class VerifierAgent:
    """
    VerifierAgent checks the output of upstream agents for completeness and validity.
    Enhanced with deep semantic validation, content quality checks, and cross-agent
    contract verification.
    
    Returns a tuple: (is_complete, feedback)
    """
    def __init__(self):
        self.agent_name = "VerifierAgent"

    def _check_empty_values(self, data: Dict, keys: List[str]) -> List[str]:
        """Check if required keys have meaningful (non-empty) values."""
        empty_keys = []
        for key in keys:
            val = data.get(key)
            if val is None:
                empty_keys.append(key)
            elif isinstance(val, (list, dict)) and len(val) == 0:
                empty_keys.append(key)
            elif isinstance(val, str) and len(val.strip()) == 0:
                empty_keys.append(key)
        return empty_keys

    def _check_minimum_items(self, data: Dict, key: str, min_count: int) -> bool:
        """Check if a list field has at least min_count items."""
        val = data.get(key, [])
        if isinstance(val, list):
            return len(val) >= min_count
        return True  # Non-list values pass this check

    def _validate_entities(self, entities: Any) -> Tuple[bool, str]:
        """Validate entity definitions have required structure."""
        if not isinstance(entities, list):
            return False, "entities must be a list"
        if len(entities) == 0:
            return False, "entities list is empty — must define at least one database entity"
        for i, entity in enumerate(entities):
            if isinstance(entity, dict):
                if not entity.get("entity_name") and not entity.get("name"):
                    return False, f"Entity at index {i} is missing entity_name"
                fields = entity.get("fields", [])
                if isinstance(fields, list) and len(fields) == 0:
                    return False, f"Entity '{entity.get('entity_name', entity.get('name', 'unknown'))}' has no fields defined"
        return True, ""

    def _validate_endpoints(self, endpoints: Any) -> Tuple[bool, str]:
        """Validate API endpoint definitions."""
        if not isinstance(endpoints, list):
            return False, "endpoints must be a list"
        if len(endpoints) < 2:
            return False, "endpoints list has fewer than 2 endpoints — a real API needs at least auth + CRUD routes"
        for i, ep in enumerate(endpoints):
            if isinstance(ep, dict):
                if not ep.get("path"):
                    alt_path = ep.get("url") or ep.get("route")
                    if alt_path:
                        ep["path"] = alt_path
                    else:
                        resource = ep.get("resource") or ep.get("name") or f"resource_{i}"
                        ep["path"] = f"/api/v1/{str(resource).lower().strip('/')}"
                if not ep.get("method"):
                    ep["method"] = "GET"
        return True, ""

    def _validate_pages(self, pages: Any) -> Tuple[bool, str]:
        """Validate frontend page definitions."""
        if not isinstance(pages, list):
            return False, "pages must be a list"
        import os
        min_pages = 3 if os.environ.get("ENVIRONMENT") == "development" else 5
        if len(pages) < min_pages:
            return False, (
                f"pages list has fewer than {min_pages} pages — a production app needs Dashboard, Auth, "
                "Settings, and feature-specific modules aligned with the PRD."
            )
        return True, ""

    async def verify(self, agent_name: str, agent_output: Any) -> Tuple[bool, str]:
        """
        Evaluate if the output is complete and semantically valid.
        Performs three layers of validation:
        1. Structure validation (JSON type, required keys)
        2. Content quality validation (non-empty values, minimum counts)
        3. Semantic validation (entity/endpoint/page structure)
        """
        # ── Layer 0: Truncated JSON ──
        if isinstance(agent_output, IncompleteJSONError):
            pass
            feedback = (
                f"Your previous JSON response was truncated and invalid: {str(agent_output)}. "
                "Please generate the complete JSON object from the beginning. Ensure it is fully closed."
            )
            return False, feedback
            
        if not isinstance(agent_output, dict):
            return False, "Output was not a valid JSON dictionary."
            
        # ── Layer 1: Schema Key Validation ──
        if "status" not in agent_output:
            pass
            return False, "The generated JSON is missing the required 'status' key. Please ensure it adheres to the requested schema."

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
            pass
            return False, f"The generated JSON is missing the following required keys: {', '.join(missing)}. Please regenerate the output adhering exactly to the requested schema."

        # ── Layer 2: Content Quality Validation ──
        empty_keys = self._check_empty_values(agent_output, keys)
        if empty_keys:
            pass
            return False, (
                f"The following keys have EMPTY values which is not acceptable: {', '.join(empty_keys)}. "
                "Each key must contain meaningful, non-empty content. Please regenerate with complete data."
            )

        # ── Layer 3: Semantic Validation (agent-specific depth checks) ──
        feedback_warnings: List[str] = []

        if agent_name == "RequirementAnalyzerAgent":
            overview = agent_output.get("project_overview", {})
            if isinstance(overview, dict):
                if not overview.get("name"):
                    return False, "project_overview.name is missing. Every project must have a name."
                if not overview.get("description") and not overview.get("type"):
                    feedback_warnings.append("project_overview is missing description/type")
            features = agent_output.get("features", [])
            import os
            min_features = 3 if os.environ.get("ENVIRONMENT") == "development" else 5
            if isinstance(features, list) and len(features) < min_features:
                return False, (
                    f"Only {len(features)} features defined. A production project needs at least {min_features} "
                    "interconnected features (e.g. Dashboard, Auth, User Management, Settings, Analytics). "
                    "Derive additional features from the PRD/TRD/MRD."
                )

        elif agent_name == "DatabaseArchitectureAgent":
            valid, msg = self._validate_entities(agent_output.get("entities"))
            if not valid:
                return False, f"Entity validation failed: {msg}. Define complete entities with entity_name and fields arrays."

        elif agent_name == "APIAgent":
            valid, msg = self._validate_endpoints(agent_output.get("endpoints"))
            if not valid:
                return False, f"Endpoint validation failed: {msg}. Define comprehensive API endpoints."

        elif agent_name == "FrontendArchitectureAgent":
            valid, msg = self._validate_pages(agent_output.get("pages"))
            if not valid:
                return False, f"Page validation failed: {msg}. Define at least a landing page, login, and dashboard."

        elif agent_name == "UIUXArchitectAgent":
            palette = agent_output.get("color_palette", {})
            if isinstance(palette, dict) and not palette.get("primary"):
                feedback_warnings.append("color_palette missing 'primary' color — may result in plain default styling")

        elif agent_name == "CodeGenerationPlannerAgent":
            phases = agent_output.get("generation_phases", [])
            if isinstance(phases, list) and len(phases) < 2:
                return False, "generation_phases must have at least 2 phases (backend + frontend). Add comprehensive generation phases."

        # Log any non-blocking warnings
        if feedback_warnings:
            pass

        pass
        return True, ""
