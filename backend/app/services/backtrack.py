import os
from typing import Dict, Any, List, Set, Optional
import copy
from datetime import datetime, timezone
from app.core.progress_logger import progress_logger

# Maps each responsible agent to the workspace node that should be re-run (scoped backtrack)
AGENT_TO_WORKSPACE: dict = {
    "DatabaseArchitectureAgent": "architecture_design",
    "DatabaseModelGenerationAgent": "architecture_design",
    "BackendArchitectureAgent": "architecture_design",
    "APIAgent": "architecture_design",
    "APIImplementationAgent": "architecture_design",
    "FrontendArchitectureAgent": "architecture_design",
    "UIUXArchitectAgent": "architecture_design",
    "UIComponentGenerationAgent": "architecture_design",
    "StateManagementAgent": "architecture_design",
    "StateImplementationAgent": "architecture_design",
    "AuthArchitectureAgent": "ops_security_workspace",
    "RealtimeArchitectureAgent": "ops_security_workspace",
    "DevOpsArchitectureAgent": "ops_security_workspace",
    "SecurityArchitectureAgent": "ops_security_workspace",
    "TestingArchitectureAgent": "ops_security_workspace",
    "ValidationArchitectureAgent": "ops_security_workspace",
    "OptimizationArchitectureAgent": "ops_security_workspace",
}

class ValidationFailureAnalyzer:
    """
    Parses validation errors and identifies the responsible agent and recommended action.
    """
    @staticmethod
    def analyze(validation_errors: List[Dict[str, Any]], current_agent: str, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        if not validation_errors:
            return {
                "failure_type": "None",
                "responsible_agent": "None",
                "severity": "info",
                "recommended_action": "No errors found."
            }
            
        # Prioritize analyzing "error" level issues, then fall back to "warning"
        errors_to_analyze = [e for e in validation_errors if e.get("severity") == "error"]
        if not errors_to_analyze:
            errors_to_analyze = validation_errors

        # Select the first prominent error
        error_item = errors_to_analyze[0]
        error_msg = error_item.get("error", "").lower()
        module = error_item.get("module", "").lower()
        
        failure_type = "Generic Validation Error"
        responsible_agent = "DatabaseArchitectureAgent"  # Safe default fallback
        severity = error_item.get("severity", "error")
        recommended_action = "Regenerate the architecture layer."

        if "api endpoint" in error_msg or "api endpoints" in error_msg or "endpoint" in error_msg or module == "api" or module == "crossref-api":
            failure_type = "Missing API Endpoint"
            responsible_agent = "APIAgent"
            recommended_action = "Regenerate API specifications and ensure all entities have CRUD endpoint mappings."
        elif "route" in error_msg or "routes" in error_msg or module == "crossref-routes" or "page" in error_msg:
            failure_type = "Missing Route"
            responsible_agent = "FrontendArchitectureAgent"
            recommended_action = "Regenerate frontend architecture, ensuring each page is properly assigned a routing path."
        elif "entity" in error_msg or "entities" in error_msg or module == "database" or "db_architecture" in error_msg:
            failure_type = "Missing Entity Mapping"
            responsible_agent = "DatabaseArchitectureAgent"
            recommended_action = "Regenerate database architecture and define the primary schema entities."
        elif "integration" in error_msg or module == "integration":
            failure_type = "Broken Integration"
            responsible_agent = "IntegrationGenerationAgent"
            recommended_action = "Re-analyze service boundaries and regenerate integration interfaces."
        elif "auth" in error_msg or module == "auth" or "security" in error_msg:
            failure_type = "Missing Auth Rule"
            responsible_agent = "AuthArchitectureAgent"
            recommended_action = "Regenerate authorization structures to ensure all protected endpoints have active policy gates."
        elif "backend" in error_msg or module == "backend":
            failure_type = "Missing Backend Architecture"
            responsible_agent = "BackendArchitectureAgent"
            recommended_action = "Regenerate backend infrastructure design contracts."
        elif "theme" in error_msg or "styling" in error_msg or module == "themestyling":
            failure_type = "Missing Theme Styling"
            responsible_agent = "UIUXArchitectAgent"
            recommended_action = "Regenerate the CSS styling tokens and UI/UX design theme attributes."
        elif "state" in error_msg or module == "statemanagement":
            failure_type = "Missing State Management"
            responsible_agent = "StateManagementAgent"
            recommended_action = "Regenerate reactive frontend state parameters and dispatcher schemes."

        return {
            "failure_type": failure_type,
            "responsible_agent": responsible_agent,
            "severity": severity,
            "recommended_action": recommended_action
        }


class BacktrackManager:
    """
    Manages topological backtracking, checkpoint snapshotting, and telemetry metrics in MongoDB.
    """
    # Complete topological dependency graph for Sarthi agents
    DEPENDENCY_GRAPH = {
        "DatabaseArchitectureAgent": [],
        "DatabaseModelGenerationAgent": ["DatabaseArchitectureAgent"],
        "BackendArchitectureAgent": ["DatabaseArchitectureAgent"],
        "APIAgent": ["BackendArchitectureAgent", "DatabaseArchitectureAgent"],
        "AuthArchitectureAgent": ["APIAgent"],
        "RealtimeArchitectureAgent": ["APIAgent"],
        "SecurityArchitectureAgent": ["AuthArchitectureAgent", "APIAgent"],
        "DevOpsArchitectureAgent": ["BackendArchitectureAgent"],
        "TestingArchitectureAgent": ["APIAgent", "BackendArchitectureAgent"],
        "ValidationArchitectureAgent": ["DatabaseArchitectureAgent", "APIAgent"],
        "OptimizationArchitectureAgent": ["BackendArchitectureAgent", "APIAgent"],
        
        "FrontendArchitectureAgent": [],
        "UIUXArchitectAgent": [],
        "UIComponentGenerationAgent": ["UIUXArchitectAgent", "FrontendArchitectureAgent"],
        "StateManagementAgent": ["FrontendArchitectureAgent"],
        "StateImplementationAgent": ["StateManagementAgent", "UIComponentGenerationAgent"],
    }

    # Map agent name to database key fields to unset during rollback
    AGENT_DB_KEYS = {
        "RequirementAnalyzerAgent": ["requirements", "requirements_full", "requirements_summary", "requirements_compressed", "requirements_contracts"],
        "PlannerAgent": ["planning", "planning_full", "planning_summary", "planning_compressed", "planning_contracts"],
        "ResearchPlanningAgent": ["implementation_plan", "implementation_plan_full", "implementation_plan_summary", "implementation_plan_compressed", "implementation_plan_contracts"],
        "DatabaseArchitectureAgent": ["db_architecture", "db_architecture_full", "db_architecture_summary", "db_architecture_compressed", "db_architecture_contracts"],
        "DatabaseModelGenerationAgent": ["database_model_generation", "database_model_generation_full", "database_model_generation_summary", "database_model_generation_compressed", "database_model_generation_contracts"],
        "BackendArchitectureAgent": ["backend_architecture", "backend_architecture_full", "backend_architecture_summary", "backend_architecture_compressed", "backend_architecture_contracts"],
        "APIAgent": ["api_architecture", "api_architecture_full", "api_architecture_summary", "api_architecture_compressed", "api_architecture_contracts"],
        "FrontendArchitectureAgent": ["frontend_architecture", "frontend_architecture_full", "frontend_architecture_summary", "frontend_architecture_compressed", "frontend_architecture_contracts"],
        "UIUXArchitectAgent": ["theme_styling", "theme_styling_full", "theme_styling_summary", "theme_styling_compressed", "theme_styling_contracts"],
        "UIComponentGenerationAgent": ["ui_component_generation", "ui_component_generation_full", "ui_component_generation_summary", "ui_component_generation_compressed", "ui_component_generation_contracts"],
        "StateManagementAgent": ["state_management", "state_management_full", "state_management_summary", "state_management_compressed", "state_management_contracts"],
        "StateImplementationAgent": ["state_implementation", "state_implementation_full", "state_implementation_summary", "state_implementation_compressed", "state_implementation_contracts"],
        "AuthArchitectureAgent": ["auth_architecture", "auth_architecture_full", "auth_architecture_summary", "auth_architecture_compressed", "auth_architecture_contracts"],
        "RealtimeArchitectureAgent": ["realtime_architecture", "realtime_architecture_full", "realtime_architecture_summary", "realtime_architecture_compressed", "realtime_architecture_contracts"],
        "DevOpsArchitectureAgent": ["devops_architecture", "devops_architecture_full", "devops_architecture_summary", "devops_architecture_compressed", "devops_architecture_contracts"],
        "SecurityArchitectureAgent": ["security_architecture", "security_architecture_full", "security_architecture_summary", "security_architecture_compressed", "security_architecture_contracts"],
        "TestingArchitectureAgent": ["testing_architecture", "testing_architecture_full", "testing_architecture_summary", "testing_architecture_compressed", "testing_architecture_contracts"],
        "ValidationArchitectureAgent": ["validation_architecture", "validation_architecture_full", "validation_architecture_summary", "validation_architecture_compressed", "validation_architecture_contracts"],
        "OptimizationArchitectureAgent": ["optimization_architecture", "optimization_architecture_full", "optimization_architecture_summary", "optimization_architecture_compressed", "optimization_architecture_contracts"],
    }

    def __init__(self, db: Any, project_id: str):
        self.db = db
        self.project_id = project_id

    def get_downstream_dependents(self, responsible_agent: str) -> Set[str]:
        """
        Recursively determines all downstream agents dependent on the responsible agent.
        """
        dependents = set()
        to_process = [responsible_agent]
        
        while to_process:
            current = to_process.pop(0)
            for agent, deps in self.DEPENDENCY_GRAPH.items():
                if current in deps and agent not in dependents:
                    dependents.add(agent)
                    to_process.append(agent)
                    
        return dependents

    async def backtrack(self, project_doc: Dict[str, Any], validation_logs: List[Dict[str, Any]], analyzer_result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restores checkpoint, unsets relevant DB keys for responsible and downstream agents, and logs progress.
        """
        MAX_AGENT_RETRIES = 2 if os.environ.get("ENVIRONMENT") == "development" else 3
        MAX_BACKTRACK_DEPTH = 1 if os.environ.get("ENVIRONMENT") == "development" else 5

        responsible_agent = analyzer_result["responsible_agent"]
        failure_type = analyzer_result["failure_type"]

        # Compute all dependent downstream agents that must also be re-run
        dependents = self.get_downstream_dependents(responsible_agent)
        triggered_agents = [responsible_agent] + sorted(list(dependents))

        # Retrieve current backtrack depth and agent retries from state or DB
        backtrack_depth = state.get("backtrack_depth", 0) + 1
        agent_retries = copy.deepcopy(state.get("agent_retries", {}) or {})
        
        current_retries = agent_retries.get(responsible_agent, 0) + 1
        agent_retries[responsible_agent] = current_retries

        target_ws = AGENT_TO_WORKSPACE.get(responsible_agent, "architecture_design")
        reason_msg = f"{len(validation_logs)} validation error(s) | Triggered agents: {', '.join(triggered_agents)}"
        project_id = self.project_id or str(project_doc.get("_id", ""))
        progress_logger.backtrack(
            responsible_agent=responsible_agent,
            target_workspace=target_ws,
            depth=backtrack_depth,
            reason=reason_msg,
            project_id=project_id
        )

        # Check thresholds
        if current_retries > MAX_AGENT_RETRIES or backtrack_depth > MAX_BACKTRACK_DEPTH:
            
            # Record human intervention metrics in MongoDB
            await self._record_metrics_db(
                failure_type=failure_type,
                responsible_agent=responsible_agent,
                is_backtrack=True,
                is_success=False,
                is_human_intervention=True
            )
            return {"status": "FAILED_REQUIRES_HUMAN_REVIEW", "project_doc": project_doc, "retry_count": backtrack_depth}

        # Backup current state as snapshot
        snapshot_time = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "timestamp": snapshot_time,
            "backtrack_depth": backtrack_depth,
            "responsible_agent": responsible_agent,
            "triggered_agents": triggered_agents,
            "data_snapshot": {k: project_doc.get(k) for agent in triggered_agents for k in self.AGENT_DB_KEYS.get(agent, []) if project_doc.get(k)}
        }

        # Select the prominent error message to display in the healing instructions
        errors_to_analyze = [e for e in validation_logs if e.get("severity") == "error"]
        if not errors_to_analyze:
            errors_to_analyze = validation_logs
        error_msg = errors_to_analyze[0].get("error", "Unknown validation error") if errors_to_analyze else "Unknown validation error"
        
        # Compile active healing context
        active_healing_context = {
            "responsible_agent": responsible_agent,
            "error_msg": error_msg,
            "failure_type": failure_type,
            "recommended_action": analyzer_result.get("recommended_action", "Regenerate the architecture layer."),
            "triggered_agents": triggered_agents,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Compile unset keys
        unset_fields = {}
        for agent in triggered_agents:
            keys = self.AGENT_DB_KEYS.get(agent, [])
            for key in keys:
                unset_fields[key] = ""

        # Perform atomic update on DB
        await self.db.projects.update_one(
            {"_id": self.project_id},
            {
                "$unset": unset_fields,
                "$push": {
                    "backtrack_history": snapshot,
                    "healing_history": active_healing_context
                },
                "$set": {
                    "backtrack_depth": backtrack_depth,
                    "agent_retries": agent_retries,
                    "active_healing_context": active_healing_context
                }
            }
        )

        # Log restored state and retry metrics

        # Update MongoDB telemetry metrics
        await self._record_metrics_db(
            failure_type=failure_type,
            responsible_agent=responsible_agent,
            is_backtrack=True,
            is_success=True,
            is_human_intervention=False
        )

        # Fetch clean, fresh project doc with cleared fields
        clean_doc = await self.db.projects.find_one({"_id": self.project_id}) or project_doc

        # Determine which workspace to re-run (scoped backtrack)
        responsible_agent = analyzer_result.get("responsible_agent", "")
        backtrack_target = AGENT_TO_WORKSPACE.get(responsible_agent, "architecture_design")

        return {
            "status": "BACKTRACK_SUCCESS",
            "project_doc": clean_doc,
            "retry_count": backtrack_depth,
            "backtrack_depth": backtrack_depth,
            "agent_retries": agent_retries,
            "backtrack_target": backtrack_target
        }

    async def record_regeneration_success(self, validation_errors: List[Dict[str, Any]] = None):
        """
        Records a successful validation loop and increments recovery metric counts in MongoDB.
        """
        # If we successfully revalidated (i.e. zero errors now), count it as a recovery success
        if not validation_errors:
            await self.db.projects.update_one(
                {"_id": self.project_id},
                {"$unset": {"active_healing_context": ""}}
            )
            await self.db.validation_backtrack_metrics.update_one(
                {"_id": "global_metrics"},
                {
                    "$inc": {
                        "total_backtracks_succeeded": 1,
                        "total_regenerations_succeeded": 1
                    }
                },
                upsert=True
            )

    async def _record_metrics_db(self, failure_type: str, responsible_agent: str, is_backtrack: bool, is_success: bool, is_human_intervention: bool):
        """
        Writes aggregated telemetry to MongoDB using atomic modifiers.
        """
        inc_fields = {
            "total_regenerations_triggered": 1,
            f"validation_failure_types.{failure_type}": 1,
            f"most_common_failing_agents.{responsible_agent}": 1
        }
        
        if is_backtrack:
            inc_fields["total_backtracks_triggered"] = 1
            
        if is_human_intervention:
            inc_fields["total_human_interventions"] = 1

        await self.db.validation_backtrack_metrics.update_one(
            {"_id": "global_metrics"},
            {"$inc": inc_fields},
            upsert=True
        )

    @classmethod
    async def clear_downstream_keys(cls, db: Any, project_id: str, target_agent: str) -> List[str]:
        """
        Calculates all downstream topologically dependent agents from the target agent
        and unsets their database keys in MongoDB, alongside the codebase compilation keys.
        Returns the list of triggered agents.
        """
        manager = cls(db, project_id)
        dependents = manager.get_downstream_dependents(target_agent)
        triggered_agents = [target_agent] + sorted(list(dependents))
        
        unset_fields = {}
        for agent in triggered_agents:
            keys = cls.AGENT_DB_KEYS.get(agent, [])
            for key in keys:
                unset_fields[key] = ""
                
        # Also always clear codebase-specific compile keys
        unset_fields["synthesized_codebase"] = ""
        unset_fields["codebase"] = ""
        unset_fields["validation_logs"] = ""
        unset_fields["active_healing_context"] = ""
        
        await db.projects.update_one(
            {"_id": project_id},
            {"$unset": unset_fields}
        )
        return triggered_agents

