"""
Dependency Directed Acyclic Graph (DAG) for Sarthi AI pipeline.
Provides explicit artifact-level dependency modeling, topological sorting,
downstream invalidation closure, dependency hash computation, and minimal context extraction.
"""
from typing import Dict, Any, List, Set, Optional
import hashlib
import json


# Canonical mapping of Artifact Type -> producing Agent
ARTIFACT_TO_AGENT: Dict[str, str] = {
    "requirements": "RequirementAnalyzerAgent",
    "trd": "TRDGeneratorAgent",
    "execution_plan": "PlannerAgent",
    "implementation_plan": "ResearchPlanningAgent",
    "database_architecture": "DatabaseArchitectureAgent",
    "database_model": "DatabaseModelGenerationAgent",
    "backend_architecture": "BackendArchitectureAgent",
    "api_architecture": "APIAgent",
    "api_implementation": "APIImplementationAgent",
    "frontend_architecture": "FrontendArchitectureAgent",
    "theme_styling": "UIUXArchitectAgent",
    "ui_components": "UIComponentGenerationAgent",
    "state_management": "StateManagementAgent",
    "state_implementation": "StateImplementationAgent",
    "auth_architecture": "AuthArchitectureAgent",
    "realtime_architecture": "RealtimeArchitectureAgent",
    "security_architecture": "SecurityArchitectureAgent",
    "devops_architecture": "DevOpsArchitectureAgent",
    "testing_architecture": "TestingArchitectureAgent",
    "validation_architecture": "ValidationArchitectureAgent",
    "optimization_architecture": "OptimizationArchitectureAgent",
    "code_generation_plan": "CodeGenerationPlannerAgent",
    "backend_code_generation": "BackendCodeGenerationAgent",
    "frontend_code_generation": "FrontendCodeGenerationAgent",
    "integration_generation": "IntegrationGenerationAgent",
    "build_compilation": "BuildCompilationAgent",
    "error_correction": "ErrorCorrectionAgent",
    "project_export": "ProjectExportAgent",
}

# Reverse mapping: Agent -> Artifact Type
AGENT_TO_ARTIFACT: Dict[str, str] = {v: k for k, v in ARTIFACT_TO_AGENT.items()}

# Mapping Artifact Type -> DB key in MongoDB
ARTIFACT_TO_DB_KEY: Dict[str, str] = {
    "requirements": "requirements",
    "trd": "trd",
    "execution_plan": "planning",
    "implementation_plan": "implementation_plan",
    "database_architecture": "db_architecture",
    "database_model": "database_model_generation",
    "backend_architecture": "backend_architecture",
    "api_architecture": "api_architecture",
    "api_implementation": "api_implementation",
    "frontend_architecture": "frontend_architecture",
    "theme_styling": "theme_styling",
    "ui_components": "ui_component_generation",
    "state_management": "state_management",
    "state_implementation": "state_implementation",
    "auth_architecture": "auth_architecture",
    "realtime_architecture": "realtime_architecture",
    "security_architecture": "security_architecture",
    "devops_architecture": "devops_architecture",
    "testing_architecture": "testing_architecture",
    "validation_architecture": "validation_architecture",
    "optimization_architecture": "optimization_architecture",
    "code_generation_plan": "code_generation_plan",
    "backend_code_generation": "backend_code_generation",
    "frontend_code_generation": "frontend_code_generation",
    "integration_generation": "integration_generation",
    "build_compilation": "build_compilation",
    "error_correction": "error_correction",
    "project_export": "project_export",
}

DB_KEY_TO_ARTIFACT: Dict[str, str] = {v: k for k, v in ARTIFACT_TO_DB_KEY.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Canonical Dependency DAG
# Defines exact artifact-level prerequisites.
# ─────────────────────────────────────────────────────────────────────────────
DEPENDENCY_DAG: Dict[str, List[str]] = {
    "requirements": [],
    "trd": ["requirements"],
    "execution_plan": ["requirements"],
    "implementation_plan": ["requirements", "execution_plan"],
    
    # Architecture branches — can execute independently / concurrently
    "database_architecture": ["execution_plan"],
    "frontend_architecture": ["execution_plan"],
    "theme_styling": ["execution_plan"],
    
    # DB / Backend branch
    "database_model": ["database_architecture"],
    "backend_architecture": ["database_architecture"],
    "api_architecture": ["backend_architecture", "database_model"],
    "api_implementation": ["api_architecture"],
    
    # Frontend branch (isolated from backend where possible)
    "ui_components": ["frontend_architecture", "theme_styling"],
    "state_management": ["frontend_architecture"],
    "state_implementation": ["state_management", "ui_components"],
    
    # Cross-cutting Ops & Security branches
    "auth_architecture": ["api_architecture"],
    "realtime_architecture": ["api_architecture"],
    "security_architecture": ["auth_architecture", "api_architecture"],
    "devops_architecture": ["backend_architecture"],
    "testing_architecture": ["api_architecture", "backend_architecture"],
    "validation_architecture": ["database_architecture", "api_architecture"],
    "optimization_architecture": ["backend_architecture", "api_architecture"],
    
    # Code generation and packaging
    "code_generation_plan": ["validation_architecture", "api_implementation", "state_implementation"],
    "backend_code_generation": ["api_implementation", "code_generation_plan"],
    "frontend_code_generation": ["state_implementation", "code_generation_plan"],
    "integration_generation": ["backend_code_generation", "frontend_code_generation"],
    "build_compilation": ["integration_generation"],
    "error_correction": ["build_compilation"],
    "project_export": ["error_correction"],
}


class DependencyDAG:
    """DAG Manager for artifact dependencies, invalidation subtrees, and context pruning."""

    @classmethod
    def get_direct_dependencies(cls, artifact_type: str) -> List[str]:
        """Returns direct prerequisite artifact types for the given artifact."""
        return list(DEPENDENCY_DAG.get(artifact_type, []))

    @classmethod
    def get_downstream_dependents(cls, artifact_type: str) -> Set[str]:
        """
        Recursively calculates all downstream artifacts that depend on `artifact_type`.
        Uses topological traversal to compute the exact affected subtree.
        """
        dependents: Set[str] = set()
        to_process: List[str] = [artifact_type]

        while to_process:
            current = to_process.pop(0)
            for art, prereqs in DEPENDENCY_DAG.items():
                if current in prereqs and art not in dependents:
                    dependents.add(art)
                    to_process.append(art)

        return dependents

    @classmethod
    def get_affected_agents(cls, responsible_agent: str) -> List[str]:
        """
        Given a failing agent, returns the minimal ordered list of agents to invalidate and rerun.
        Includes the responsible agent followed by its downstream dependents.
        """
        art_type = AGENT_TO_ARTIFACT.get(responsible_agent)
        if not art_type:
            return [responsible_agent]

        downstream_artifacts = cls.get_downstream_dependents(art_type)
        affected_agents = [responsible_agent]
        for art in downstream_artifacts:
            ag = ARTIFACT_TO_AGENT.get(art)
            if ag and ag not in affected_agents:
                affected_agents.append(ag)

        return affected_agents

    @classmethod
    def get_db_keys_for_artifacts(cls, artifact_types: Set[str]) -> List[str]:
        """Returns all database keys associated with the given set of artifact types."""
        keys = []
        for art in artifact_types:
            base_key = ARTIFACT_TO_DB_KEY.get(art, art)
            keys.extend([
                base_key,
                f"{base_key}_full",
                f"{base_key}_summary",
                f"{base_key}_compressed",
                f"{base_key}_contracts"
            ])
        return keys

    @classmethod
    def compute_dependency_hash(cls, project_doc: Dict[str, Any], artifact_type: str) -> str:
        """
        Computes a deterministic hash of all direct upstream prerequisite artifacts for `artifact_type`.
        If any upstream dependency changed, this hash will change, causing a deterministic cache miss.
        """
        prereqs = cls.get_direct_dependencies(artifact_type)
        if not prereqs:
            return "root"

        hashes = []
        for p in sorted(prereqs):
            db_key = ARTIFACT_TO_DB_KEY.get(p, p)
            val = project_doc.get(db_key) or {}
            # Hash content of the prerequisite
            val_str = json.dumps(val, sort_keys=True, default=str)
            h = hashlib.sha256(val_str.encode("utf-8")).hexdigest()[:16]
            hashes.append(f"{p}:{h}")

        combined = "|".join(hashes)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def get_pruned_context_for_agent(
        cls, agent_name: str, project_doc: Dict[str, Any], is_backtrack: bool = False
    ) -> Dict[str, Any]:
        """
        Builds the minimal required context for an agent by extracting ONLY its declared direct prerequisites.
        Prevents prompt context explosion and eliminates passing 11 unrelated giant JSON documents.
        On backtrack re-runs, uses compressed summaries and contracts where available to avoid context bloat.
        """
        art_type = AGENT_TO_ARTIFACT.get(agent_name)
        prereqs = cls.get_direct_dependencies(art_type) if art_type else []

        pruned: Dict[str, Any] = {
            "_id": project_doc.get("_id"),
            "name": project_doc.get("name"),
            "category": project_doc.get("category"),
            "generation_type": project_doc.get("generation_type", "full_stack"),
            "theme": project_doc.get("theme"),
            "theme_palette": project_doc.get("theme_palette"),
            "blueprint": project_doc.get("blueprint") or project_doc.get("initial_prompt"),
            "trd": project_doc.get("trd", ""),
            "active_healing_context": project_doc.get("active_healing_context"),
        }

        # Include ONLY the direct dependency artifacts
        for p in prereqs:
            db_key = ARTIFACT_TO_DB_KEY.get(p, p)
            if db_key in project_doc:
                pruned[db_key] = project_doc.get(db_key)
            if f"{db_key}_contracts" in project_doc:
                pruned[f"{db_key}_contracts"] = project_doc.get(f"{db_key}_contracts")

        return pruned
