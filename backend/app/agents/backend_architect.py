import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class BackendArchitectureAgent:
    """
    BackendArchitectureAgent for Sarthi.
    Designs backend folders, routers, business service flows, and integration settings.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "BackendArchitectureAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(self, requirements: Dict[str, Any], planning: Dict[str, Any], db_architecture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze requirements, planning, and db architecture to output backend architecture design metadata.
        """
        agent_inputs = {"requirements": requirements, "planning": planning, "db_architecture": db_architecture}
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_backend_architecture(requirements, planning, db_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior backend architect. Design the complete server-side architecture: module structure, service layer, repository patterns, middleware stack, dependency injection, and business workflows.\n\n"
                "## Instructions\n"
                "1. Think step by step: select framework from tech_stack → define folder structure → create one Service + Repository per entity from db_architecture → design middleware stack → map authentication flow → define workflows.\n"
                "2. Service names MUST follow the pattern: {EntityName}Service. Repository names MUST follow: {EntityName}Repository. These must match db_architecture.backend_integration_context exactly.\n"
                "3. Middleware must include CORS, auth, and error handling at minimum.\n"
                "4. backend_workflows must map real user actions to concrete execution steps.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- backend_structure.core_directories must use forward-slash paths (e.g. 'app/core').\n"
                "- All entity names, route groups, and module names must be consistent with upstream db_architecture contracts."
            )
        )

        user_content = f"""
Design the backend architecture for this project. Think step by step:
1. Choose the architecture style and framework from requirements.tech_stack.backend.
2. Create a service and repository for each entity in db_architecture.entities.
3. Design the middleware stack (CORS, auth, error handling, logging).
4. Map the authentication flow using db_architecture.authentication_storage.
5. Define backend workflows that trace user actions through service → repository → database.
6. Populate future_agent_context with guidance for APIAgent and FrontendArchitectureAgent.

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "backend_strategy": {{
    "architecture_style": "string — e.g. 'Modular MVC', 'Clean Architecture', 'Hexagonal'",
    "backend_framework": "string — exact framework name, e.g. 'FastAPI (Uvicorn)'",
    "execution_model": "string — 'Asynchronous', 'Multi-threaded', or 'Synchronous'",
    "scalability_model": "string — scaling strategy description"
  }},
  "backend_structure": {{
    "root_modules": ["string — top-level module names like 'core', 'db', 'api', 'models', 'services'"],
    "feature_modules": ["string — feature area names matching core_modules, lowercase"],
    "shared_modules": ["string — utility/helper module names"],
    "core_directories": ["string — forward-slash directory paths like 'app/core', 'app/api'"]
  }},
  "service_architecture": [
    {{
      "service_name": "string — format: {{EntityName}}Service",
      "responsibility": "string — what business logic this service handles",
      "dependencies": ["string — repository/helper class names this service depends on"]
    }}
  ],
  "repository_patterns": {{
    "pattern_type": "string — 'Repository', 'Data Mapper', 'Active Record', or 'None'",
    "repositories": ["string — format: {{EntityName}}Repository, one per entity"]
  }},
  "middleware_architecture": [
    {{
      "middleware": "string — middleware class/component name",
      "purpose": "string — what this middleware does"
    }}
  ],
  "authentication_backend_flow": {{
    "auth_strategy": "string — e.g. 'OAuth2 Password Bearer with JWT tokens'",
    "protected_modules": ["string — lowercase module names requiring auth"],
    "token_flow": ["string — ordered steps in token generation"],
    "session_management": "string — session/token persistence strategy"
  }},
  "api_groupings": [
    {{
      "group_name": "string — route group label",
      "related_entities": ["string — entity names this group operates on"],
      "priority": "string — 'High', 'Medium', or 'Low'"
    }}
  ],
  "websocket_architecture": {{
    "required": "boolean",
    "channels": ["string — WebSocket channel paths"],
    "realtime_modules": ["string — modules using realtime features"]
  }},
  "async_task_architecture": {{
    "required": "boolean",
    "background_jobs": ["string — background task descriptions"],
    "queue_strategy": "string — queue/worker strategy description"
  }},
  "dependency_injection_strategy": {{
    "required": "boolean",
    "shared_dependencies": ["string — injectable dependency function names"],
    "service_bindings": ["string — how services are injected into routes"]
  }},
  "backend_workflows": [
    {{
      "workflow_name": "string — user action name",
      "execution_flow": ["string — ordered steps: validate → service → repository → respond"]
    }}
  ],
  "scalability_architecture": {{
    "microservice_ready": "boolean",
    "horizontal_scaling": "boolean",
    "high_load_modules": ["string — modules with heaviest traffic"],
    "optimization_targets": ["string — specific optimization actions"]
  }},
  "future_agent_context": {{
    "important_notes_for_api_agents": ["string — route design guidance for APIAgent"],
    "important_notes_for_frontend_agents": ["string — API consumption guidance for frontend"],
    "important_notes_for_devops_agents": ["string — deployment/container guidance"]
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
            return enrich_agent_output(self._get_fallback_backend_architecture(requirements, planning, db_architecture), self.agent_name, agent_inputs)

    def _get_fallback_backend_architecture(self, requirements: Dict[str, Any], planning: Dict[str, Any], db_architecture: Dict[str, Any]) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        tech_stack = requirements.get("tech_stack", {})
        modules = requirements.get("core_modules", ["UserAuth", "Core"])
        entities = db_architecture.get("entities", [])
        
        entity_names = []
        for ent in entities:
            if isinstance(ent, str):
                entity_names.append(ent)
            elif isinstance(ent, dict) and ent.get("entity_name"):
                entity_names.append(ent["entity_name"])
                
        if not entity_names:
            entity_names = ["User", "Item"]

        be_list = tech_stack.get("backend", [])
        primary_framework = be_list[0] if be_list else "FastAPI"
        
        services = []
        repositories = []
        api_groups = []
        workflows = []
        
        for name in entity_names:
            services.append({
                "service_name": f"{name}Service",
                "responsibility": f"Executes core business operations and logic validation for {name} domain.",
                "dependencies": [f"{name}Repository"]
            })
            repositories.append(f"{name}Repository")
            api_groups.append({
                "group_name": f"{name} Endpoints",
                "related_entities": [name],
                "priority": "High" if name == "User" else "Medium"
            })
            workflows.append({
                "workflow_name": f"Process {name.lower()} logic",
                "execution_flow": [
                    f"Validate request inputs.",
                    f"Invoke {name}Service processing actions.",
                    f"Query and persist data using {name}Repository.",
                    f"Generate response serialization models."
                ]
            })

        return {
            "status": "success",
            "backend_strategy": {
                "architecture_style": "Feature-Folder modular MVC architecture.",
                "backend_framework": f"{primary_framework} (Python Uvicorn)",
                "execution_model": "Asynchronous event-loop execution mapping async/await calls.",
                "scalability_model": "Stateless app configuration allowing horizontally scaled containers."
            },
            "backend_structure": {
                "root_modules": ["core", "db", "api", "models", "services"],
                "feature_modules": [m.lower() for m in modules],
                "shared_modules": ["utils", "config"],
                "core_directories": [
                    "app/core",
                    "app/db",
                    "app/api",
                    "app/models",
                    "app/services"
                ]
            },
            "service_architecture": services,
            "repository_patterns": {
                "pattern_type": "Repository pattern abstracting data access.",
                "repositories": repositories
            },
            "middleware_architecture": [
                {
                    "middleware": "CORSMiddleware",
                    "purpose": "Allow cross-origin requests."
                },
                {
                    "middleware": "JWTAuthMiddleware",
                    "purpose": "Intercept requests to protected routes to validate authorization tokens."
                }
            ],
            "authentication_backend_flow": {
                "auth_strategy": "OAuth2 Password Flow with Bearer JWT tokens.",
                "protected_modules": [m.lower() for m in modules if m.lower() not in ["auth", "userauth"]],
                "token_flow": [
                    "User credentials received at login.",
                    "Verify password hash.",
                    "Generate and return cryptographically signed JWT token."
                ],
                "session_management": "Stateless session authentication."
            },
            "api_groupings": api_groups,
            "websocket_architecture": {
                "required": False,
                "channels": [],
                "realtime_modules": []
            },
            "async_task_architecture": {
                "required": False,
                "background_jobs": [],
                "queue_strategy": "None"
            },
            "dependency_injection_strategy": {
                "required": True,
                "shared_dependencies": ["get_db", "get_current_user"],
                "service_bindings": [
                    "Inject Repository classes into Service layer constructors.",
                    "Bind dependencies directly into controller routes."
                ]
            },
            "backend_workflows": workflows,
            "scalability_architecture": {
                "microservice_ready": False,
                "horizontal_scaling": True,
                "high_load_modules": [],
                "optimization_targets": []
            },
            "future_agent_context": {
                "important_notes_for_api_agents": ["Map routes using Pydantic serializers."],
                "important_notes_for_frontend_agents": ["Inject authorization tokens on requests."],
                "important_notes_for_devops_agents": ["Expose standard ports in Docker configs."]
            }
        }
