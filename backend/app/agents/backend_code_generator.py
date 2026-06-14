import json
from loguru import logger
from typing import Any, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class BackendCodeGenerationAgent:
    """
    BackendCodeGenerationAgent for Sarthi.
    Orchestrates the generation of backend modular directory layouts, services implementations,
    repositories configurations, custom middlewares, dependency containers, and background worker systems.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "BackendCodeGenerationAgent"

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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream architecture blueprints to produce detailed backend packages layouts,
        service interfaces, repository templates, dependency containers, and async workers logic.
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
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback backend implementation design.")
            return enrich_agent_output(
                self._get_fallback_backend_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade FastAPI backend code structures, service wrappers, async dependencies, and worker loops. "
            "CRITICAL RULES:\n"
            "1. ALWAYS include 'python-dotenv' and database drivers like 'motor', 'pymongo', or 'Flask-PyMongo' in requirements.txt.\n"
            "2. ALWAYS generate a full '.env' file template alongside '.env.example' containing MONGODB_URI and SECRET_KEY.\n"
            "3. Database connections must use robust try-except blocks to catch connection failures and handle them gracefully.\n"
            "4. AVOID dummy logic or stubs. Generate complete business logic using real external APIs or comprehensive algorithms when required."
        )

        user_content = f"""
Analyze the Sarthi blueprints:
Requirements: {json.dumps(requirements, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
Validation Architecture: {json.dumps(validation_architecture, indent=2)}
Optimization Architecture: {json.dumps(optimization_architecture, indent=2)}
Code Generation Planner: {json.dumps(code_generation_planner, indent=2)}
Database Model Generation: {json.dumps(database_model_generation, indent=2)}
Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "backend_generation_strategy": {{
    "architecture_style": "e.g. Clean architecture with separated domain services and repository layers.",
    "service_pattern": "e.g. Single-responsibility services injected with transactional databases sessions.",
    "dependency_injection_strategy": "e.g. FastAPI dependency parameters routing using global yield overrides.",
    "async_execution_strategy": "e.g. Asyncpg connection pools with Celery background worker tasks."
  }},
  "generated_backend_structure": {{
    "root_modules": ["e.g. app/main.py", "app/core/config.py"],
    "service_modules": ["e.g. app/services/user_service.py"],
    "repository_modules": ["e.g. app/repositories/user_repository.py"],
    "middleware_modules": ["e.g. app/middlewares/auth.py"],
    "utility_modules": ["e.g. app/utils/helpers.py"]
  }},
  "service_generation": {{
    "generated_services": [
      {{
        "service_name": "e.g. UserService",
        "methods": ["create_user", "get_user_by_email"],
        "injected_repositories": ["UserRepository"]
      }}
    ],
    "transactional_workflows": [
      "e.g. Signup workflow validating passwords, creating DB entities, and returning JWT credentials."
    ],
    "cross_service_dependencies": []
  }},
  "repository_generation": {{
    "generated_repositories": [
      {{
        "repository_name": "e.g. UserRepository",
        "mapped_model": "User",
        "custom_queries": ["find_by_email"]
      }}
    ],
    "orm_bindings": [
      "UserRepository is bound to users table."
    ],
    "persistence_dependencies": []
  }},
  "middleware_generation": {{
    "generated_middlewares": [
      {{
        "name": "CORSMiddleware",
        "configuration": "e.g. Allow origins, methods, and headers."
      }}
    ],
    "auth_middlewares": [
      "e.g. JWTMiddleware decoding bearer token headers."
    ],
    "request_validation_middlewares": []
  }},
  "dependency_injection_generation": {{
    "generated_dependencies": ["get_db_session", "get_current_user"],
    "shared_bindings": ["db_session -> DatabaseSessionManager"],
    "service_container_rules": [
      "Initialize database session pools before service injection."
    ]
  }},
  "background_worker_generation": {{
    "async_workers": ["e.g. Celery worker listening on compilation queues."],
    "scheduled_tasks": ["e.g. Periodic cleanup tasks running every night."],
    "event_processing_flows": []
  }},
  "exception_handling_generation": {{
    "global_exception_handlers": ["HTTPExceptionHandler", "RequestValidationErrorHandler"],
    "custom_error_groups": ["EntityNotFoundError", "AuthenticationFailedError"],
    "validation_error_handlers": []
  }},
  "configuration_generation": {{
    "environment_configs": ["DATABASE_URL", "JWT_SECRET_KEY"],
    "runtime_configs": ["PORT", "DEBUG"],
    "secret_dependencies": ["ASymmetric encryption keys"]
  }},
  "websocket_backend_generation": {{
    "websocket_integrations": ["e.g. SocketManager broadcasting updates packets."],
    "event_handlers": ["subscribe_to_chat", "unsubscribe_from_chat"],
    "realtime_dependencies": ["RedisPubSubClient"]
  }},
  "generation_dependencies": {{
    "blocking_modules": ["app/core/config.py"],
    "shared_dependencies": ["app/db/session.py"],
    "cross_module_generation_rules": [
      "Generate base mixing classes before creating specific service entities."
    ]
  }},
  "future_generation_context": {{
    "important_notes_for_frontend_generation": [
      "Ensure API client fetch handles standard unified error formats."
    ],
    "important_notes_for_auth_generation": [
      "Use secure cookie extraction patterns."
    ],
    "important_notes_for_compilation_agents": [
      "Verify connection pool size matches container limits."
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
            logger.error(f"Failed to run BackendCodeGenerationAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_backend_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_backend_generation(
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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 18.
        """
        entities = db_architecture.get("entities", []) if db_architecture else []
        entity_names = []
        for e in entities:
            if isinstance(e, str):
                entity_names.append(e)
            elif isinstance(e, dict) and e.get("entity_name"):
                entity_names.append(e["entity_name"])
        
        if not entity_names:
            entity_names = ["User", "Item"]

        services = []
        repositories = []
        root_modules = ["app/main.py", "app/core/config.py", "app/db/session.py"]
        service_modules = []
        repository_modules = []

        for name in entity_names:
            tbl_name = f"{name.lower()}s"
            service_modules.append(f"app/services/{name.lower()}_service.py")
            repository_modules.append(f"app/repositories/{name.lower()}_repository.py")

            services.append({
                "service_name": f"{name}Service",
                "methods": [f"create_{name.lower()}", f"get_{name.lower()}_by_id", f"update_{name.lower()}", f"delete_{name.lower()}"],
                "injected_repositories": [f"{name}Repository"]
            })

            repositories.append({
                "repository_name": f"{name}Repository",
                "mapped_model": name,
                "custom_queries": [f"find_{name.lower()}_by_id"]
            })

        return {
            "status": "success",
            "backend_generation_strategy": {
                "architecture_style": "FastAPI clean service-repository layout separating controllers from persistence operations.",
                "service_pattern": "Stateless service modules wrapping generic repositories and injecting database sessions.",
                "dependency_injection_strategy": "Hierarchical FastAPI dependencies for database connection retrieval and JWT validations.",
                "async_execution_strategy": "Async-first service routines using SQLAlchemy async database drivers."
            },
            "generated_backend_structure": {
                "root_modules": root_modules,
                "service_modules": service_modules,
                "repository_modules": repository_modules,
                "middleware_modules": ["app/middlewares/auth_middleware.py", "app/middlewares/logging_middleware.py"],
                "utility_modules": ["app/utils/security.py", "app/utils/datetime_utils.py"]
            },
            "service_generation": {
                "generated_services": services,
                "transactional_workflows": [
                    "User signup workflow executing password hashing, unique check, database write, and JWT response generation."
                ] + [
                    f"Create {name} transaction workflow modifying records within database transaction boundaries."
                    for name in entity_names if name != "User"
                ],
                "cross_service_dependencies": []
            },
            "repository_generation": {
                "generated_repositories": repositories,
                "orm_bindings": [f"{name}Repository connects to {name} database model." for name in entity_names],
                "persistence_dependencies": []
            },
            "middleware_generation": {
                "generated_middlewares": [
                    {
                        "name": "CORSMiddleware",
                        "configuration": "Configure trusted origins list with allowed headers and request methods."
                    }
                ],
                "auth_middlewares": [
                    "JWTMiddleware validating Authorization Bearer headers and storing payload in request state."
                ],
                "request_validation_middlewares": []
            },
            "dependency_injection_generation": {
                "generated_dependencies": ["get_db", "get_current_user_from_token"],
                "shared_bindings": ["db -> get_db session dependency mapper"],
                "service_container_rules": [
                    "All repositories must receive the active db session dependency.",
                    "All services receive their respective repository containers."
                ]
            },
            "background_worker_generation": {
                "async_workers": ["Celery app utilizing Redis brokers"],
                "scheduled_tasks": ["Daily cache cleanup", "Weekly transaction reports generation"],
                "event_processing_flows": []
            },
            "exception_handling_generation": {
                "global_exception_handlers": ["HTTPException handler", "ValidationError handler", "SQLAlchemyError handler"],
                "custom_error_groups": ["EntityNotFound", "DuplicateKeyError", "InsufficientPermissions"],
                "validation_error_handlers": []
            },
            "configuration_generation": {
                "environment_configs": ["DATABASE_URL", "JWT_SECRET", "REDIS_URL"],
                "runtime_configs": ["PORT", "WORKERS_COUNT"],
                "secret_dependencies": ["Access Token Secret key", "Refresh Token Secret key"]
            },
            "websocket_backend_generation": {
                "websocket_integrations": ["WebSocketConnectionManager routing live socket connections"],
                "event_handlers": ["broadcast_update", "handle_disconnect"],
                "realtime_dependencies": ["Redis channels pub/sub connector"]
            },
            "generation_dependencies": {
                "blocking_modules": ["app/core/config.py", "app/db/session.py"],
                "shared_dependencies": ["app/models/project.py"],
                "cross_module_generation_rules": [
                    "Core configurations must compile first.",
                    "Database model schemas compile before service classes."
                ]
            },
            "future_generation_context": {
                "important_notes_for_frontend_generation": [
                    "Frontend API actions must match controller endpoint path structures."
                ],
                "important_notes_for_auth_generation": [
                    "Authorize decorators must matches authentication claims models."
                ],
                "important_notes_for_compilation_agents": [
                    "Verify requirements.txt installs asyncpg and PyJWT correctly."
                ]
            }
        }
