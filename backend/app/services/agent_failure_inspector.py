"""
AgentFailureInspector — Deep diagnostic inspection for backtrack events.

Fires whenever BacktrackManager triggers a backtrack. Reads the responsible
agent's raw output from the DB, compares it against the expected schema,
and produces a rich failure_report dict that explains exactly what went wrong.

Stored in project_doc["failure_reports"] (array) and broadcast over WebSocket.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Expected top-level keys per agent (mirrors VerifierAgent.required_keys)
AGENT_EXPECTED_KEYS: Dict[str, List[str]] = {
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
    "DatabaseModelGenerationAgent": ["persistence_generation_strategy", "generated_models", "relationship_generation"],
    "APIImplementationAgent": ["api_generation_strategy", "generated_routes", "router_generation"],
}

# DB key per agent (for fetching raw output)
AGENT_DB_KEY: Dict[str, str] = {
    "DatabaseArchitectureAgent": "db_architecture",
    "DatabaseModelGenerationAgent": "database_model_generation",
    "BackendArchitectureAgent": "backend_architecture",
    "APIAgent": "api_architecture",
    "APIImplementationAgent": "api_implementation",
    "FrontendArchitectureAgent": "frontend_architecture",
    "UIUXArchitectAgent": "theme_styling",
    "UIComponentGenerationAgent": "ui_component_generation",
    "StateManagementAgent": "state_management",
    "StateImplementationAgent": "state_implementation",
    "AuthArchitectureAgent": "auth_architecture",
    "RealtimeArchitectureAgent": "realtime_architecture",
    "DevOpsArchitectureAgent": "devops_architecture",
    "SecurityArchitectureAgent": "security_architecture",
    "TestingArchitectureAgent": "testing_architecture",
    "ValidationArchitectureAgent": "validation_architecture",
    "OptimizationArchitectureAgent": "optimization_architecture",
    "RequirementAnalyzerAgent": "requirements",
    "PlannerAgent": "planning",
    "ResearchPlanningAgent": "implementation_plan",
}


class AgentFailureInspector:
    """
    Inspects exactly WHY an agent's output triggered a backtrack.

    Call `inspect()` in BacktrackManager at the start of every backtrack to capture:
    - Which schema keys were missing or empty
    - What the actual bad value was
    - What cross-agent contract was violated
    - A concrete healing hint to inject into the retry prompt
    """

    @staticmethod
    def _truncate(val: Any, max_chars: int = 300) -> str:
        """Safely truncate any value to a short string for logging."""
        s = str(val)
        if len(s) > max_chars:
            return s[:max_chars] + "...[truncated]"
        return s

    @classmethod
    def _inspect_output(
        cls,
        agent_name: str,
        raw_output: Any,
        validation_error_msg: str,
    ) -> Dict[str, Any]:
        """
        Performs structural inspection of the agent's raw DB output.
        Returns a dict with findings.
        """
        expected_keys = AGENT_EXPECTED_KEYS.get(agent_name, [])
        findings = {
            "expected_schema_keys": expected_keys,
            "actual_keys_found": [],
            "missing_keys": [],
            "empty_keys": [],
            "first_bad_value": None,
            "output_type": type(raw_output).__name__,
            "output_is_valid_dict": isinstance(raw_output, dict),
        }

        if not isinstance(raw_output, dict):
            findings["first_bad_value"] = cls._truncate(raw_output)
            findings["missing_keys"] = expected_keys
            return findings

        findings["actual_keys_found"] = list(raw_output.keys())

        for key in expected_keys:
            val = raw_output.get(key)
            if val is None:
                findings["missing_keys"].append(key)
                if findings["first_bad_value"] is None:
                    findings["first_bad_value"] = f"Key '{key}' is entirely missing from output"
            elif isinstance(val, (list, dict)) and len(val) == 0:
                findings["empty_keys"].append(key)
                if findings["first_bad_value"] is None:
                    findings["first_bad_value"] = f"Key '{key}' exists but is empty ({type(val).__name__})"
            elif isinstance(val, str) and not val.strip():
                findings["empty_keys"].append(key)
                if findings["first_bad_value"] is None:
                    findings["first_bad_value"] = f"Key '{key}' is an empty string"

        # Agent-specific semantic checks
        if agent_name == "DatabaseArchitectureAgent":
            entities = raw_output.get("entities", [])
            if isinstance(entities, list) and len(entities) > 0:
                bad_entity = next(
                    (e for e in entities if isinstance(e, dict) and not e.get("entity_name") and not e.get("name")),
                    None
                )
                if bad_entity:
                    findings["first_bad_value"] = f"Entity missing 'entity_name': {cls._truncate(bad_entity)}"

        elif agent_name == "APIAgent":
            endpoints = raw_output.get("endpoints", [])
            if isinstance(endpoints, list) and len(endpoints) < 2:
                findings["first_bad_value"] = f"Only {len(endpoints)} endpoint(s) defined -- minimum 2 required"

        elif agent_name == "FrontendArchitectureAgent":
            pages = raw_output.get("pages", [])
            if isinstance(pages, list) and len(pages) < 3:
                findings["first_bad_value"] = f"Only {len(pages)} page(s) defined -- minimum 3 required"

        return findings

    @classmethod
    def _build_healing_hint(
        cls,
        agent_name: str,
        findings: Dict[str, Any],
        validation_error_msg: str,
        analyzer_result: Dict[str, Any],
    ) -> str:
        """Builds a targeted healing instruction to inject into the retry prompt."""
        parts = []

        if findings["missing_keys"]:
            parts.append(
                f"Your output is missing these required keys: {findings['missing_keys']}. "
                "You MUST include all of them in your JSON response."
            )
        if findings["empty_keys"]:
            parts.append(
                f"The following keys were present but empty: {findings['empty_keys']}. "
                "Each key must contain meaningful, non-empty content."
            )
        if not findings["output_is_valid_dict"]:
            parts.append(
                f"Your output was not a valid JSON dictionary (type: {findings['output_type']}). "
                "You MUST return a valid JSON object only."
            )

        recommended = analyzer_result.get("recommended_action", "")
        if recommended:
            parts.append(f"Recommended fix: {recommended}")

        cross_ref_error = validation_error_msg
        if cross_ref_error and cross_ref_error not in " ".join(parts):
            parts.append(f"Cross-validation error: {cross_ref_error}")

        return " | ".join(parts) if parts else f"Regenerate output for {agent_name} following the full schema."

    @classmethod
    async def inspect(
        cls,
        db: Any,
        project_id: str,
        project_doc: Dict[str, Any],
        responsible_agent: str,
        validation_logs: List[Dict[str, Any]],
        analyzer_result: Dict[str, Any],
        backtrack_depth: int,
    ) -> Dict[str, Any]:
        """
        Main entry point. Inspects the responsible agent's output and returns
        a structured failure_report dict.

        Also persists the report to project_doc["failure_reports"] in MongoDB.
        """
        # Fetch the raw output the agent saved to DB
        db_key = AGENT_DB_KEY.get(responsible_agent, responsible_agent.lower())
        raw_output = project_doc.get(db_key) or project_doc.get(f"{db_key}_full")

        # Extract the primary validation error message
        errors = [e for e in validation_logs if e.get("severity") == "error"]
        primary_error = errors[0] if errors else (validation_logs[0] if validation_logs else {})
        validation_error_msg = primary_error.get("error", "Unknown validation error")
        validation_module = primary_error.get("module", "Unknown")

        # Deep structural inspection
        findings = cls._inspect_output(responsible_agent, raw_output, validation_error_msg)

        # Build healing hint
        healing_hint = cls._build_healing_hint(
            responsible_agent, findings, validation_error_msg, analyzer_result
        )

        report = {
            "agent_name": responsible_agent,
            "backtrack_depth": backtrack_depth,
            "error_id": analyzer_result.get("error_id", "unknown"),
            "failure_type": analyzer_result.get("failure_type", "Unknown"),
            "validation_module": validation_module,
            "validation_error": validation_error_msg,
            "expected_schema_keys": findings["expected_schema_keys"],
            "actual_keys_found": findings["actual_keys_found"],
            "missing_keys": findings["missing_keys"],
            "empty_keys": findings["empty_keys"],
            "first_bad_value": findings["first_bad_value"],
            "output_type": findings["output_type"],
            "healing_hint": healing_hint,
            "recommended_action": analyzer_result.get("recommended_action", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Persist to DB
        if db is not None:
            try:
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$push": {"failure_reports": report}}
                )
            except Exception:
                pass

        return report
