import json
from loguru import logger
from typing import Any, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class CodeGenerationPlannerAgent:
    """
    CodeGenerationPlannerAgent for Sarthi.
    Designs deterministic generation phases, dependency graphs, and compilation batches.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "CodeGenerationPlannerAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        theme_styling: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        realtime_architecture: Dict[str, Any],
        state_management: Dict[str, Any],
        devops_architecture: Dict[str, Any],
        security_architecture: Dict[str, Any],
        testing_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze all architecture layers to produce deterministic code generation planning intelligence.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
            "theme_styling": theme_styling,
            "auth_architecture": auth_architecture,
            "realtime_architecture": realtime_architecture,
            "state_management": state_management,
            "devops_architecture": devops_architecture,
            "security_architecture": security_architecture,
            "testing_architecture": testing_architecture,
            "validation_architecture": validation_architecture,
            "optimization_architecture": optimization_architecture,
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using fallback code generation planning.")
            return enrich_agent_output(
                self._get_fallback_code_generation_plan(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design deterministic file generation sequencing, import dependency orchestration, compilation batches, and build graph metadata."
        )

        user_content = f"""
Analyze these connected Sarthi architecture inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}
Theme Styling: {json.dumps(theme_styling, indent=2)}
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
Realtime Architecture: {json.dumps(realtime_architecture, indent=2)}
State Management: {json.dumps(state_management, indent=2)}
DevOps Architecture: {json.dumps(devops_architecture, indent=2)}
Security Architecture: {json.dumps(security_architecture, indent=2)}
Testing Architecture: {json.dumps(testing_architecture, indent=2)}
Validation Architecture: {json.dumps(validation_architecture, indent=2)}
Optimization Architecture: {json.dumps(optimization_architecture, indent=2)}
Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "generation_strategy": {{
    "generation_model": "",
    "dependency_resolution_strategy": "",
    "build_orchestration_strategy": "",
    "compilation_strategy": ""
  }},
  "generation_phases": [
    {{
      "phase_name": "",
      "generation_targets": [],
      "dependencies": []
    }}
  ],
  "backend_generation_sequence": {{
    "generation_order": [],
    "shared_dependencies": [],
    "service_generation_groups": []
  }},
  "frontend_generation_sequence": {{
    "generation_order": [],
    "shared_ui_dependencies": [],
    "component_generation_groups": []
  }},
  "database_generation_sequence": {{
    "entity_generation_order": [],
    "relationship_dependencies": [],
    "migration_dependencies": []
  }},
  "api_generation_sequence": {{
    "route_generation_order": [],
    "request_response_dependencies": [],
    "authentication_dependencies": []
  }},
  "authentication_generation_sequence": {{
    "auth_generation_order": [],
    "permission_dependencies": [],
    "session_dependencies": []
  }},
  "realtime_generation_sequence": {{
    "websocket_generation_order": [],
    "event_dependencies": [],
    "sync_dependencies": []
  }},
  "shared_generation_dependencies": {{
    "shared_modules": [],
    "cross_module_dependencies": [],
    "blocking_dependencies": []
  }},
  "compilation_batches": [
    {{
      "batch_name": "",
      "included_generation_targets": [],
      "execution_priority": ""
    }}
  ],
  "build_graph": {{
    "root_generation_nodes": [],
    "dependent_generation_nodes": [],
    "final_compilation_targets": []
  }},
  "generation_workflows": [
    {{
      "workflow_name": "",
      "generation_flow": []
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_backend_generation": [],
    "important_notes_for_frontend_generation": [],
    "important_notes_for_compilation_agents": []
  }}
}}
"""

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
            logger.error(f"Failed to run CodeGenerationPlannerAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_code_generation_plan(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_code_generation_plan(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        theme_styling: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        realtime_architecture: Dict[str, Any],
        state_management: Dict[str, Any],
        devops_architecture: Dict[str, Any],
        security_architecture: Dict[str, Any],
        testing_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        entities = db_architecture.get("entities", []) if db_architecture else []
        entity_names = [e.get("entity_name", "Core") for e in entities if isinstance(e, dict)] or ["User", "Project"]
        relationships = db_architecture.get("relationships", []) if db_architecture else []

        endpoints = api_architecture.get("endpoints", []) if api_architecture else []
        route_nodes = []
        auth_route_nodes = []
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            route_name = f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}"
            route_nodes.append(route_name)
            if endpoint.get("requires_auth"):
                auth_route_nodes.append(route_name)

        backend_services = backend_architecture.get("service_architecture", []) if backend_architecture else []
        service_names = [s.get("service_name", "CoreService") for s in backend_services if isinstance(s, dict)]
        if not service_names:
            service_names = [f"{name}Service" for name in entity_names]

        pages = frontend_architecture.get("pages", []) if frontend_architecture else []
        page_names = [p.get("page_name", "Dashboard") for p in pages if isinstance(p, dict)] or ["Dashboard"]
        components = frontend_architecture.get("component_hierarchy", []) if frontend_architecture else []
        component_names = [c.get("component_name", "CorePanel") for c in components if isinstance(c, dict)]
        if not component_names:
            component_names = [f"{name}Panel" for name in entity_names]

        stores = []
        for store in state_management.get("global_state_architecture", {}).get("global_states", []) if state_management else []:
            if isinstance(store, dict):
                stores.append(store.get("store_name", "useAppStore"))
        if not stores:
            stores = ["useAuthStore", "useDashboardStore"]

        websocket_channels = (
            realtime_architecture.get("websocket_architecture", {}).get("websocket_channels", [])
            if realtime_architecture else []
        )
        event_types = (
            realtime_architecture.get("event_driven_architecture", {}).get("event_types", [])
            if realtime_architecture else []
        )

        container_groups = (
            devops_architecture.get("containerization_architecture", {}).get("container_groups", [])
            if devops_architecture else []
        ) or ["frontend", "backend"]

        blocking_issues = (
            validation_architecture.get("compilation_readiness", {}).get("blocking_issues", [])
            if validation_architecture else []
        )
        optimization_targets = (
            optimization_architecture.get("backend_optimization", {}).get("high_load_services", [])
            if optimization_architecture else []
        )

        database_files = [f"models/{name}Model" for name in entity_names]
        repository_files = [f"repositories/{name}Repository" for name in entity_names]
        service_files = [f"services/{name}" for name in service_names]
        route_files = [f"api/{route.replace(' ', '_').replace('/', '_').strip('_')}" for route in route_nodes[:12]]
        component_files = [f"components/{name}" for name in component_names]
        page_files = [f"pages/{name}" for name in page_names]
        store_files = [f"stores/{name}" for name in stores]

        return {
            "status": "success",
            "generation_strategy": {
                "generation_model": "Deterministic architecture-first generation using validated contracts as immutable inputs for all files.",
                "dependency_resolution_strategy": "Generate shared types, configuration, and data contracts before services, routes, stores, pages, and tests.",
                "build_orchestration_strategy": "Batch generation by dependency layer so backend, frontend, realtime, and deployment artifacts remain import-consistent.",
                "compilation_strategy": "Compile only after validation, optimization, route contracts, state stores, and shared module dependency graph are available."
            },
            "generation_phases": [
                {
                    "phase_name": "Shared contracts and configuration",
                    "generation_targets": ["shared/types", "shared/constants", "environment_config", "theme_tokens"],
                    "dependencies": ["requirements", "validation_architecture", "theme_styling"]
                },
                {
                    "phase_name": "Persistence and backend foundation",
                    "generation_targets": database_files + repository_files + service_files,
                    "dependencies": ["database_architecture", "backend_architecture", "security_architecture", "optimization_architecture"]
                },
                {
                    "phase_name": "API, auth, and realtime interfaces",
                    "generation_targets": route_files + ["auth/session", "auth/permissions"] + [f"realtime/{c}" for c in websocket_channels],
                    "dependencies": ["api_architecture", "auth_architecture", "realtime_architecture", "backend_services"]
                },
                {
                    "phase_name": "Frontend state and UI assembly",
                    "generation_targets": store_files + component_files + page_files,
                    "dependencies": ["frontend_architecture", "state_management", "theme_styling", "api_contracts"]
                },
                {
                    "phase_name": "Deployment, tests, and final compilation",
                    "generation_targets": ["docker", "deployment", "test_fixtures", "e2e_flows", "build_scripts"],
                    "dependencies": ["devops_architecture", "testing_architecture", "optimization_architecture", "validation_architecture"]
                }
            ],
            "backend_generation_sequence": {
                "generation_order": ["core/config", "db/connection"] + database_files + repository_files + service_files + route_files,
                "shared_dependencies": ["settings", "database_client", "error_models", "auth_dependencies", "cache_client"],
                "service_generation_groups": [
                    {
                        "group_name": "entity_services",
                        "services": service_names,
                        "depends_on": repository_files
                    },
                    {
                        "group_name": "high_load_services",
                        "services": optimization_targets,
                        "depends_on": ["cache_client", "async_task_boundary"]
                    }
                ]
            },
            "frontend_generation_sequence": {
                "generation_order": ["theme/provider", "api/client"] + store_files + component_files + page_files,
                "shared_ui_dependencies": ["theme_tokens", "api_client", "auth_guard", "loading_states", "error_boundary"],
                "component_generation_groups": [
                    {
                        "group_name": "data_bound_components",
                        "components": component_names,
                        "depends_on": stores
                    },
                    {
                        "group_name": "route_pages",
                        "components": page_names,
                        "depends_on": component_names
                    }
                ]
            },
            "database_generation_sequence": {
                "entity_generation_order": entity_names,
                "relationship_dependencies": [
                    f"{rel.get('from_entity')}->{rel.get('to_entity')}"
                    for rel in relationships
                    if isinstance(rel, dict)
                ],
                "migration_dependencies": ["base_schema", "entity_tables_or_collections", "indexes", "relationship_constraints"]
            },
            "api_generation_sequence": {
                "route_generation_order": route_nodes,
                "request_response_dependencies": ["shared DTO/schema contracts", "database entity models", "service return payloads"],
                "authentication_dependencies": auth_route_nodes
            },
            "authentication_generation_sequence": {
                "auth_generation_order": ["password_hashing", "token_generation", "session_refresh", "route_guards", "frontend_auth_store"],
                "permission_dependencies": auth_architecture.get("role_based_access_control", {}).get("permission_groups", []) if auth_architecture else [],
                "session_dependencies": auth_architecture.get("session_management_architecture", {}).get("session_persistence", []) if auth_architecture else []
            },
            "realtime_generation_sequence": {
                "websocket_generation_order": websocket_channels,
                "event_dependencies": event_types,
                "sync_dependencies": realtime_architecture.get("frontend_realtime_sync", {}).get("sync_states", []) if realtime_architecture else []
            },
            "shared_generation_dependencies": {
                "shared_modules": ["types", "config", "api_client", "theme_tokens", "auth_helpers", "cache_keys"],
                "cross_module_dependencies": [
                    "Database entity fields must match API payloads and frontend state variables.",
                    "Protected API routes must match frontend auth guards and test permission fixtures.",
                    "Realtime channel names must match websocket server routes and frontend subscription hooks.",
                    "Optimization cache keys must match mutation invalidation hooks."
                ],
                "blocking_dependencies": blocking_issues
            },
            "compilation_batches": [
                {
                    "batch_name": "contracts",
                    "included_generation_targets": ["shared/types", "schemas", "theme_tokens", "environment_config"],
                    "execution_priority": "critical"
                },
                {
                    "batch_name": "backend_core",
                    "included_generation_targets": database_files + repository_files + service_files,
                    "execution_priority": "high"
                },
                {
                    "batch_name": "api_and_auth",
                    "included_generation_targets": route_files + ["auth/session", "auth/guards"],
                    "execution_priority": "high"
                },
                {
                    "batch_name": "frontend_state_and_ui",
                    "included_generation_targets": store_files + component_files + page_files,
                    "execution_priority": "high"
                },
                {
                    "batch_name": "ops_tests_build",
                    "included_generation_targets": container_groups + ["test_suites", "build_validation"],
                    "execution_priority": "medium"
                }
            ],
            "build_graph": {
                "root_generation_nodes": ["requirements", "validation_architecture", "shared_contracts", "theme_tokens"],
                "dependent_generation_nodes": [
                    "database_models",
                    "repositories",
                    "backend_services",
                    "api_routes",
                    "auth_flows",
                    "frontend_stores",
                    "ui_components",
                    "pages",
                    "realtime_channels",
                    "tests",
                    "deployment_artifacts"
                ],
                "final_compilation_targets": ["frontend_bundle", "backend_application", "container_stack", "test_report", "deployment_manifest"]
            },
            "generation_workflows": [
                {
                    "workflow_name": "Backend route generation",
                    "generation_flow": [
                        "Read entity schema and repository contract.",
                        "Generate service method boundary for entity workflow.",
                        "Generate route handler matching API request/response contract.",
                        "Attach auth, validation, cache, and error handling from architecture memory.",
                        "Register tests against declared API and security constraints."
                    ]
                },
                {
                    "workflow_name": "Frontend page generation",
                    "generation_flow": [
                        "Read page/component hierarchy and theme tokens.",
                        "Generate typed API client and state store selectors.",
                        "Generate memoized data-bound component tree.",
                        "Attach auth guards and realtime subscriptions when declared.",
                        "Validate import graph before final build compilation."
                    ]
                }
            ],
            "future_generation_context": {
                "important_notes_for_backend_generation": [
                    "Generate backend files in contract order: config, database, models, repositories, services, routes, tests.",
                    "Do not create route names, entity fields, or auth behaviors outside architecture memory.",
                    "Apply optimization architecture to async boundaries, cache keys, indexes, and high-load services."
                ],
                "important_notes_for_frontend_generation": [
                    "Generate shared API client and state stores before pages/components that consume them.",
                    "Use theme styling and optimization instructions for lazy loading, memoization, and bundle shape.",
                    "Ensure frontend fetches and realtime subscriptions exactly match API and realtime architecture."
                ],
                "important_notes_for_compilation_agents": [
                    "Compile only after all critical batches resolve without blocking dependency issues.",
                    "Use the build graph to verify import order and cross-module references.",
                    "Include AI_OptimizationArchitecture.json and AI_CodeGenerationPlanner.json in orchestration memory outputs."
                ]
            }
        }
