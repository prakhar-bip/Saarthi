import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

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
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback backend design.")
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
            logger.error(f"Failed to run BackendArchitectureAgent: {e}")
            return enrich_agent_output(self._get_fallback_backend_architecture(requirements, planning, db_architecture), self.agent_name, agent_inputs)

    def _get_fallback_backend_architecture(self, requirements: Dict[str, Any], planning: Dict[str, Any], db_architecture: Dict[str, Any]) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        name = overview.get("name", "FinSight")
        tech_stack = requirements.get("tech_stack", {})
        modules = requirements.get("core_modules", ["UserAuth", "Portfolio"])
        entities = db_architecture.get("entities", [])
        
        # Check backend tech framework
        be_list = tech_stack.get("backend", [])
        primary_framework = be_list[0] if be_list else "FastAPI"
        
        # Build features and services mapping
        services = []
        repositories = []
        api_groups = []
        workflows = []
        
        # Check realtime and task queues
        realtime_needed = planning.get("realtime_architecture", {}).get("required", False)
        async_needed = len(planning.get("risk_analysis", {}).get("optimization_suggestions", [])) > 0
        
        for ent in entities:
            ent_name = ent.get("entity_name", "Core")
            services.append({
                "service_name": f"{ent_name}Service",
                "responsibility": f"Executes core business operations and logic validation for {ent_name} domain.",
                "dependencies": [f"{ent_name}Repository"]
            })
            repositories.append(f"{ent_name}Repository")
            api_groups.append({
                "group_name": f"{ent_name} Endpoints",
                "related_entities": [ent_name],
                "priority": "High" if ent_name in ["User", "Auth"] else "Medium"
            })
            workflows.append({
                "workflow_name": f"Process {ent_name.lower()} logic",
                "execution_flow": [
                    f"Validate request inputs.",
                    f"Invoke {ent_name}Service processing actions.",
                    f"Query and persist data using {ent_name}Repository.",
                    f"Generate response serialization models."
                ]
            })

        return {
            "status": "success",
            "backend_strategy": {
                "architecture_style": "Feature-Folder modular MVC architecture.",
                "backend_framework": f"{primary_framework} (Python Uvicorn)",
                "execution_model": "Asynchronous event-loop execution mapping async/await calls.",
                "scalability_model": "Stateless app configuration allowing multi-container horizontally scaled pods."
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
                "pattern_type": "Repository and Unit of Work patterns for abstracting data layers.",
                "repositories": repositories
            },
            "middleware_architecture": [
                {
                    "middleware": "CORSMiddleware",
                    "purpose": "Allow cross-origin frontend requests from local dev servers."
                },
                {
                    "middleware": "JWTAuthMiddleware",
                    "purpose": "Intercept requests to protected API endpoints, validating auth bearer token values."
                },
                {
                    "middleware": "LoggingAndErrorHandlingMiddleware",
                    "purpose": "Intercept global exceptions to return standard JSON error payload wrappers."
                }
            ],
            "authentication_backend_flow": {
                "auth_strategy": "OAuth2 Password Flow with Bearer Access and Refresh tokens.",
                "protected_modules": [m.lower() for m in modules if m.lower() not in ["auth", "userauth"]],
                "token_flow": [
                    "User credentials received at POST /api/auth/login.",
                    "Verify password hash match.",
                    "Generate access token (24-hour expiration) and cryptographically signed refresh token.",
                    "Return access token keys in standard JSON header."
                ],
                "session_management": "Stateless session authentication with refresh token validations stored in cache memory."
            },
            "api_groupings": api_groups,
            "websocket_architecture": {
                "required": realtime_needed,
                "channels": ["ws/notifications", "ws/feed"] if realtime_needed else [],
                "realtime_modules": [m for m in modules if "Realtime" in m or "Live" in m] or ["NotificationBroker"] if realtime_needed else []
            },
            "async_task_architecture": {
                "required": async_needed,
                "background_jobs": ["Process auto round-up savings log", "Execute model portfolio optimizer"],
                "queue_strategy": "Redis-backed background tasks queue running async workers."
            },
            "dependency_injection_strategy": {
                "required": True,
                "shared_dependencies": ["get_database_pool", "get_redis_client", "get_current_active_user"],
                "service_bindings": [
                    "Inject Repository class into Service layer constructor.",
                    "Bind FastAPI router Dependencies directly into controller routes."
                ]
            },
            "backend_workflows": workflows,
            "scalability_architecture": {
                "microservice_ready": True,
                "horizontal_scaling": True,
                "high_load_modules": ["Transaction", "RoundupApi"] if async_needed else ["MainApi"],
                "optimization_targets": ["Redis caching targets for heavy dashboard aggregation metrics API calls."]
            },
            "future_agent_context": {
                "important_notes_for_api_agents": [
                    "Map routes using Pydantic serialization models to ensure clean input validation.",
                    "Document all routes using OpenAPI/Swagger models."
                ],
                "important_notes_for_frontend_agents": [
                    "Write API helper hooks referencing the API endpoint routing groupings.",
                    "Utilize standard HTTP response wrappers for error handling dialogues."
                ],
                "important_notes_for_devops_agents": [
                    "Configure multi-stage Docker build files optimizing dependencies sizing.",
                    "Register environment settings variables mapping database pools size values."
                ]
            }
        }
