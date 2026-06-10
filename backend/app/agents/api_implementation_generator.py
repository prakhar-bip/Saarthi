import json
from loguru import logger
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class APIImplementationAgent:
    """
    APIImplementationAgent for Sarthi.
    Orchestrates the FastAPI route implementation, router modularization, request/response schema mapping,
    CRUD endpoint setups, authentication protection integration, async execute loops, and exception handlers.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "APIImplementationAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_planner: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream blueprints to produce FastAPI API implementations mappings, endpoints routes,
        request/response models, auth dependencies, and websocket connectors.
        """
        agent_inputs = {
            "requirements": requirements,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "auth_architecture": auth_architecture,
            "validation_architecture": validation_architecture,
            "optimization_architecture": optimization_architecture,
            "code_generation_planner": code_generation_planner,
            "database_model_generation": database_model_generation,
            "backend_code_generation": backend_code_generation,
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback API implementation design.")
            return enrich_agent_output(
                self._get_fallback_api_implementation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade FastAPI endpoints, router modules mappings, request/response payload schemas, CRUD routing groups, and exception mappings. "
            "CRITICAL RULES:\n"
            "1. NEVER use raw datetime parsing without strict try-except validation blocks to prevent 500 server crashes.\n"
            "2. ALL API routes MUST have strict Pydantic payload validation.\n"
            "3. AVOID dummy logic or API stubs. Routes must contain complete real-world logic."
        )

        user_content = f"""
Analyze Sarthi blueprints:
Requirements: {json.dumps(requirements, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
Validation Architecture: {json.dumps(validation_architecture, indent=2)}
Optimization Architecture: {json.dumps(optimization_architecture, indent=2)}
Code Generation Planner: {json.dumps(code_generation_planner, indent=2)}
Database Model Generation: {json.dumps(database_model_generation, indent=2)}
Backend Code Generation: {json.dumps(backend_code_generation, indent=2)}
Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "api_generation_strategy": {{
    "routing_architecture": "e.g. Modular FastAPI APIRouter grouping routes by features resource tags.",
    "validation_strategy": "e.g. Pydantic request body parser models capturing runtime schema issues.",
    "async_execution_strategy": "e.g. Coroutine route loops with async database drivers executions.",
    "response_strategy": "e.g. Serialized JSON structures conforming to global unified wrapper schemas."
  }},
  "generated_routes": [
    {{
      "route_name": "e.g. create_user",
      "route_path": "e.g. /api/v1/auth/signup",
      "http_method": "POST",
      "service_binding": "UserService.create_user",
      "dependencies": ["get_db"]
    }}
  ],
  "router_generation": {{
    "router_modules": ["e.g. app/api/auth.py"],
    "route_groupings": ["auth", "users"],
    "shared_router_dependencies": ["get_db"]
  }},
  "request_response_generation": {{
    "request_models": ["UserCreate", "UserLogin"],
    "response_models": ["UserResponse", "TokenResponse"],
    "shared_validation_contracts": ["StrictEmailValidationRule"]
  }},
  "crud_generation": {{
    "crud_groups": ["User CRUD", "Portfolio CRUD"],
    "entity_route_mappings": ["User -> /api/v1/users"],
    "repository_bindings": ["UserRepository -> db_session"]
  }},
  "protected_route_generation": {{
    "protected_routes": ["/api/v1/users/me"],
    "permission_bindings": ["/api/v1/users/me -> read:profile"],
    "auth_dependencies": ["get_current_user"]
  }},
  "async_api_generation": {{
    "async_routes": ["/api/v1/projects"],
    "background_execution_routes": ["POST /api/v1/projects -> run_project_compilation"],
    "event_trigger_routes": []
  }},
  "websocket_route_generation": {{
    "websocket_routes": ["/ws/v1/updates"],
    "event_bindings": ["milestone_reached -> broadcast_update"],
    "realtime_dependencies": ["RedisPubSub"]
  }},
  "pagination_filter_generation": {{
    "pagination_routes": ["GET /api/v1/projects"],
    "filtering_contracts": ["limit", "offset", "category"],
    "sorting_rules": ["created_at_dt -> DESC"]
  }},
  "exception_handling_generation": {{
    "generated_error_handlers": ["HTTPExceptionHandler"],
    "validation_error_groups": ["RequestValidationError"],
    "custom_exception_mappings": ["EntityNotFoundError -> 404", "AuthenticationFailedError -> 401"]
  }},
  "generation_dependencies": {{
    "blocking_routes": ["/api/v1/auth/login"],
    "shared_dependencies": ["app/api/deps.py"],
    "cross_module_generation_rules": [
      "Router files must import dependencies from shared module apps."
    ]
  }},
  "future_generation_context": {{
    "important_notes_for_frontend_generation": [
      "Ensure API Client queries match custom authentication parameters schemas."
    ],
    "important_notes_for_integration_agents": [
      "Websocket streams must validate connection token handshake headers."
    ],
    "important_notes_for_compilation_agents": [
      "FastAPI entrypoint main.py must mount router sub-modules in correct sequences."
    ]
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
            logger.error(f"Failed to run APIImplementationAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_api_implementation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_api_implementation(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_planner: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 19.
        """
        entities = db_architecture.get("entities", []) if db_architecture else []
        entity_names = []
        for e in entities:
            if isinstance(e, str):
                entity_names.append(e)
            elif isinstance(e, dict) and e.get("entity_name"):
                entity_names.append(e["entity_name"])

        if not entity_names:
            entity_names = ["User", "Portfolio", "Asset", "Transaction"]

        generated_routes = []
        router_modules = ["app/api/v1/auth.py"]
        route_groupings = ["auth"]
        request_models = ["UserSignupSchema", "UserLoginSchema"]
        response_models = ["UserResponseSchema", "TokenResponseSchema"]
        crud_groups = []
        entity_route_mappings = []
        protected_routes = []
        permission_bindings = []

        # Login and Signup
        generated_routes.append({
            "route_name": "auth_signup",
            "route_path": "/api/v1/auth/signup",
            "http_method": "POST",
            "service_binding": "UserService.signup",
            "dependencies": ["get_db"]
        })
        generated_routes.append({
            "route_name": "auth_login",
            "route_path": "/api/v1/auth/login",
            "http_method": "POST",
            "service_binding": "UserService.login",
            "dependencies": ["get_db"]
        })

        for name in entity_names:
            plural = f"{name.lower()}s"
            module_path = f"app/api/v1/{plural}.py"
            router_modules.append(module_path)
            route_groupings.append(plural)
            
            request_models.append(f"{name}CreateSchema")
            request_models.append(f"{name}UpdateSchema")
            response_models.append(f"{name}ResponseSchema")

            crud_groups.append(f"{name} CRUD")
            entity_route_mappings.append(f"{name} -> /api/v1/{plural}")

            # Routes definition
            generated_routes.append({
                "route_name": f"create_{name.lower()}",
                "route_path": f"/api/v1/{plural}",
                "http_method": "POST",
                "service_binding": f"{name}Service.create_{name.lower()}",
                "dependencies": ["get_db", "get_current_user"]
            })
            generated_routes.append({
                "route_name": f"get_{name.lower()}",
                "route_path": f"/api/v1/{plural}/{{id}}",
                "http_method": "GET",
                "service_binding": f"{name}Service.get_{name.lower()}_by_id",
                "dependencies": ["get_db", "get_current_user"]
            })
            generated_routes.append({
                "route_name": f"update_{name.lower()}",
                "route_path": f"/api/v1/{plural}/{{id}}",
                "http_method": "PUT",
                "service_binding": f"{name}Service.update_{name.lower()}",
                "dependencies": ["get_db", "get_current_user"]
            })
            generated_routes.append({
                "route_name": f"delete_{name.lower()}",
                "route_path": f"/api/v1/{plural}/{{id}}",
                "http_method": "DELETE",
                "service_binding": f"{name}Service.delete_{name.lower()}",
                "dependencies": ["get_db", "get_current_user"]
            })

            protected_routes.append(f"/api/v1/{plural}")
            protected_routes.append(f"/api/v1/{plural}/{{id}}")
            permission_bindings.append(f"/api/v1/{plural} -> user")
            permission_bindings.append(f"/api/v1/{plural}/{{id}} -> user")

        return {
            "status": "success",
            "api_generation_strategy": {
                "routing_architecture": "Modular FastAPI APIRouter structures grouped by sub-domain modules, registered inside app/main.py",
                "validation_strategy": "Pydantic v2 schemas executing strict types checking with clean validation mappings.",
                "async_execution_strategy": "Async-first controller routes executing non-blocking service tasks.",
                "response_strategy": "Standardized envelopes containing user payloads, metadata timestamps, and success descriptors."
            },
            "generated_routes": generated_routes,
            "router_generation": {
                "router_modules": router_modules,
                "route_groupings": route_groupings,
                "shared_router_dependencies": ["get_db", "get_current_user"]
            },
            "request_response_generation": {
                "request_models": request_models,
                "response_models": response_models,
                "shared_validation_contracts": ["UUIDValidationRule", "PaginationLimitsValidationRule"]
            },
            "crud_generation": {
                "crud_groups": crud_groups,
                "entity_route_mappings": entity_route_mappings,
                "repository_bindings": [f"{name}Repository -> db" for name in entity_names]
            },
            "protected_route_generation": {
                "protected_routes": protected_routes,
                "permission_bindings": permission_bindings,
                "auth_dependencies": ["get_current_user"]
            },
            "async_api_generation": {
                "async_routes": [f"POST /api/v1/{name.lower()}s" for name in entity_names],
                "background_execution_routes": ["POST /api/v1/projects -> compile_project_background"],
                "event_trigger_routes": []
            },
            "websocket_route_generation": {
                "websocket_routes": ["/ws/v1/updates"],
                "event_bindings": ["milestone_reached -> broadcast_update"],
                "realtime_dependencies": ["RedisPubSubClient"]
            },
            "pagination_filter_generation": {
                "pagination_routes": [f"GET /api/v1/{name.lower()}s" for name in entity_names],
                "filtering_contracts": ["limit", "offset", "sort_by", "sort_order"],
                "sorting_rules": ["created_at -> DESC"]
            },
            "exception_handling_generation": {
                "generated_error_handlers": ["HTTPExceptionHandler", "RequestValidationError", "ServiceException"],
                "validation_error_groups": ["PydanticValidationError"],
                "custom_exception_mappings": ["EntityNotFound -> 404", "AuthenticationFailed -> 401", "DatabaseOperationFailed -> 500"]
            },
            "generation_dependencies": {
                "blocking_routes": ["/api/v1/auth/login", "/api/v1/auth/signup"],
                "shared_dependencies": ["app/api/deps.py", "app/core/security.py"],
                "cross_module_generation_rules": [
                  "Sub-routers must import the global dependency bindings from app/api/deps.py."
                ]
            },
            "future_generation_context": {
                "important_notes_for_frontend_generation": [
                    "Frontend request interceptors must append bearer tokens to routes requiring authentication."
                ],
                "important_notes_for_integration_agents": [
                    "Websockets routing must resolve connection upgrades securely."
                ],
                "important_notes_for_compilation_agents": [
                    "Ensure main.py imports and aggregates all routes to the main app instance."
                ]
            }
        }
