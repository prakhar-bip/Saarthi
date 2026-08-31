import json
from typing import Dict, Any, List
from app.services.graph_store import GraphStore


# Complete agent-to-db-key mapping (mirrors workflow.py's get_agent_db_key)
AGENT_DB_KEY_MAP: Dict[str, str] = {
    "RequirementAnalyzerAgent": "requirements",
    "PlannerAgent": "planning",
    "ResearchPlanningAgent": "implementation_plan",
    "DatabaseArchitectureAgent": "db_architecture",
    "BackendArchitectureAgent": "backend_architecture",
    "APIAgent": "api_architecture",
    "FrontendArchitectureAgent": "frontend_architecture",
    "UIUXArchitectAgent": "theme_styling",
    "AuthArchitectureAgent": "auth_architecture",
    "RealtimeArchitectureAgent": "realtime_architecture",
    "StateManagementAgent": "state_management",
    "DevOpsArchitectureAgent": "devops_architecture",
    "SecurityArchitectureAgent": "security_architecture",
    "TestingArchitectureAgent": "testing_architecture",
    "ValidationArchitectureAgent": "validation_architecture",
    "OptimizationArchitectureAgent": "optimization_architecture",
    "CodeGenerationPlannerAgent": "code_generation_plan",
    "DatabaseModelGenerationAgent": "database_model_generation",
    "BackendCodeGenerationAgent": "backend_code_generation",
    "APIImplementationAgent": "api_implementation",
    "FrontendCodeGenerationAgent": "frontend_code_generation",
    "UIComponentGenerationAgent": "ui_component_generation",
    "StateImplementationAgent": "state_implementation",
    "IntegrationGenerationAgent": "integration_generation",
    "BuildCompilationAgent": "build_compilation",
    "ErrorCorrectionAgent": "error_correction",
    "ProjectExportAgent": "project_export",
}


class StateMerger:
    """State Merger for the Saarthi multi-agent pipeline.
    
    Deep-merges delta JSON (from SurgicalGapFiller) into the original agent output,
    persists the merged result to MongoDB, and updates the Knowledge Graph.
    """

    @staticmethod
    def deep_merge(base: dict, delta: dict) -> dict:
        """Deep-merge delta into base dict.
        
        Rules:
        - For list values: extend (append delta items that don't already exist, using dedup by name/path/entity_name)
        - For dict values: recursively merge
        - For scalar values: delta overwrites base only if base value is None/empty
        - Never removes existing data from base
        """
        if base is None:
            return delta
        if not isinstance(base, dict) or not isinstance(delta, dict):
            # For scalar values: delta overwrites base only if base value is None/empty
            if base is None or (isinstance(base, (str, list, dict)) and not base):
                return delta
            return base

        merged = base.copy()
        
        for key, delta_val in delta.items():
            if key not in merged:
                merged[key] = delta_val
                continue
                
            base_val = merged[key]
            
            if isinstance(base_val, dict) and isinstance(delta_val, dict):
                merged[key] = StateMerger.deep_merge(base_val, delta_val)
            elif isinstance(base_val, list) and isinstance(delta_val, list):
                # Dedup logic for lists
                deduped_list = list(base_val)
                for item in delta_val:
                    exists = False
                    if isinstance(item, dict):
                        for dedup_key in ["entity_name", "path", "page_name", "component_name", "name"]:
                            if dedup_key in item:
                                if any(isinstance(existing, dict) and existing.get(dedup_key) == item[dedup_key] for existing in deduped_list):
                                    exists = True
                                break
                    elif isinstance(item, str):
                        exists = item in deduped_list
                    else:
                        exists = item in deduped_list
                    
                    if not exists:
                        deduped_list.append(item)
                        
                merged[key] = deduped_list
            else:
                # Scalar or mixed types: delta overwrites only if base is empty/None
                if base_val is None or (isinstance(base_val, (str, list, dict)) and not base_val):
                    merged[key] = delta_val
                    
        return merged

    @staticmethod
    async def merge_and_persist(
        agent_name: str,
        base_output: dict,
        delta_output: dict,
        project_doc: dict,
        db: Any
    ) -> dict:
        """Merge delta into base, update project_doc in-memory, and persist to MongoDB.
        Also updates the Knowledge Graph via GraphStore.
        """
        try:
            merged_result = StateMerger.deep_merge(base_output, delta_output)
            
            db_key = AGENT_DB_KEY_MAP.get(agent_name, agent_name.lower())

            # Count what was added
            delta_keys = [k for k in delta_output.keys() if k not in ("status", "agent_handoff")]
            delta_item_count = 0
            for k, v in delta_output.items():
                if isinstance(v, list):
                    delta_item_count += len(v)
                elif isinstance(v, dict):
                    delta_item_count += 1


            # Update project_doc in-memory
            project_doc[db_key] = merged_result
            
            # Persist to MongoDB
            if "_id" in project_doc and db is not None:
                await db.projects.update_one(
                    {"_id": project_doc["_id"]}, 
                    {"$set": {db_key: merged_result}}
                )
            
            # Update Knowledge Graph
            try:
                updated_graph = GraphStore.ingest_agent_output(project_doc, agent_name, merged_result)
                project_doc["knowledge_graph"] = updated_graph
                if "_id" in project_doc and db is not None:
                    await db.projects.update_one(
                        {"_id": project_doc["_id"]}, 
                        {"$set": {
                            "knowledge_graph": updated_graph, 
                            "knowledge_base": project_doc.get("knowledge_base", {})
                        }}
                    )
            except Exception as graph_err:
                
                    pass
            return merged_result
            
        except Exception as e:
            return base_output

