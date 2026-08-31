from typing import Dict, Any, List

class ContractAuditor:
    """
    Contract Auditor module for the Saarthi multi-agent pipeline.
    Its job is to cross-check agent JSON outputs against the Master Requirements / TRD blueprint
    to identify missing items.
    """

    @staticmethod
    def _extract_entity_names(entities_list: list) -> List[str]:
        """Extract entity names from various formats (string or dict with entity_name key)."""
        names = []
        for e in entities_list:
            if isinstance(e, str):
                names.append(e)
            elif isinstance(e, dict) and "entity_name" in e:
                names.append(e["entity_name"])
            elif isinstance(e, dict) and "name" in e:
                names.append(e["name"])
        return names

    @staticmethod
    def _extract_endpoint_paths(endpoints_list: list) -> List[str]:
        """Extract endpoint paths from various formats."""
        paths = []
        for ep in endpoints_list:
            if isinstance(ep, str):
                paths.append(ep)
            elif isinstance(ep, dict) and "path" in ep:
                paths.append(ep["path"])
            elif isinstance(ep, dict) and "endpoint" in ep:
                paths.append(ep["endpoint"])
        return paths

    @staticmethod
    def _extract_page_names(pages_list: list) -> List[str]:
        """Extract page names from various formats."""
        names = []
        for p in pages_list:
            if isinstance(p, str):
                names.append(p)
            elif isinstance(p, dict) and "name" in p:
                names.append(p["name"])
            elif isinstance(p, dict) and "page" in p:
                names.append(p["page"])
        return names

    @staticmethod
    def audit(agent_name: str, agent_output: dict, project_doc: dict) -> List[str]:
        """
        Audit the agent_output against the project_doc master requirements.
        """
        gaps = []

        if not isinstance(agent_output, dict):
            return [f"Output for {agent_name} must be a dictionary."]

        # General checks
        if "status" not in agent_output:
            gaps.append("Missing required key: 'status'")
        if len(agent_output) <= 2:
            gaps.append(f"Agent output is suspiciously small (len = {len(agent_output)})")

        reqs = project_doc.get("requirements", {})
        features = reqs.get("features", [])
        core_modules = reqs.get("core_modules", [])
        db_reqs = reqs.get("database_requirements", {})
        master_entities = db_reqs.get("entities", [])
        auth_reqs = reqs.get("authentication", {})
        scalability_reqs = reqs.get("scalability", {})


        if agent_name == "DatabaseArchitectureAgent":
            entities = agent_output.get("entities", [])
            output_entity_names = ContractAuditor._extract_entity_names(entities)
            for me in master_entities:
                if not any(me.lower() in oe.lower() for oe in output_entity_names):
                    gaps.append(f"Missing database entity from requirements: {me}")

        elif agent_name == "BackendArchitectureAgent":
            modules = agent_output.get("modules", []) + agent_output.get("services", [])
            # Try to extract module names
            out_modules = ContractAuditor._extract_entity_names(modules) 
            for cm in core_modules:
                if not any(cm.lower() in om.lower() for om in out_modules):
                    gaps.append(f"Missing core module from requirements: {cm}")

        elif agent_name == "APIAgent":
            if "api_strategy" not in agent_output:
                gaps.append("Missing required key: 'api_strategy'")
            if "endpoints" not in agent_output:
                gaps.append("Missing required key: 'endpoints'")
            else:
                endpoints = agent_output.get("endpoints", [])
                out_paths = ContractAuditor._extract_endpoint_paths(endpoints)
                for f in features:
                    if not any(f.lower().replace("_", "") in p.lower().replace("_", "").replace("/", "") for p in out_paths):
                        gaps.append(f"Feature '{f}' may not be covered by endpoints.")

        elif agent_name == "FrontendArchitectureAgent":
            if "frontend_strategy" not in agent_output:
                gaps.append("Missing required key: 'frontend_strategy'")
            if "pages" not in agent_output:
                gaps.append("Missing required key: 'pages'")
            else:
                pages = agent_output.get("pages", [])
                out_pages = ContractAuditor._extract_page_names(pages)
                for f in features:
                    if not any(f.lower().replace("_", "") in p.lower().replace("_", "") for p in out_pages):
                        gaps.append(f"Feature '{f}' may not have a dedicated frontend page.")

        elif agent_name == "UIUXArchitectAgent":
            if "design_system" not in agent_output:
                gaps.append("Missing required key: 'design_system'")

        elif agent_name == "AuthArchitectureAgent":
            if auth_reqs.get("required", False):
                if "authentication_strategy" not in agent_output:
                    gaps.append("Authentication required by master requirements, but missing 'authentication_strategy'.")

        elif agent_name == "RealtimeArchitectureAgent":
            if scalability_reqs.get("realtime_features", False):
                if "realtime_strategy" not in agent_output:
                    gaps.append("Realtime features required by master requirements, but missing 'realtime_strategy'.")

        elif agent_name == "StateManagementAgent":
            if "state_management_strategy" not in agent_output:
                gaps.append("Missing required key: 'state_management_strategy'")

        elif agent_name == "CodeGenerationPlannerAgent":
            if "generation_strategy" not in agent_output:
                gaps.append("Missing required key: 'generation_strategy'")
            elif "generation_phases" not in agent_output.get("generation_strategy", {}):
                if "generation_phases" not in agent_output:
                    gaps.append("Missing required key: 'generation_phases' in generation_strategy")

        return gaps
