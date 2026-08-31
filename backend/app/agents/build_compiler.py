import json
from typing import Any, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class BuildCompilationAgent:
    """
    BuildCompilationAgent for Sarthi.
    Orchestrates the final application build structure assembly, cross-module
    dependency resolving, environment configuration mapping, route checks, and production folder packaging.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "BuildCompilationAgent"

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
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize all upstream implementation parameters to compile the final build assembly roadmap.
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
            "api_implementation": api_implementation,
            "frontend_code_generation": frontend_code_generation,
            "ui_component_generation": ui_component_generation,
            "state_implementation": state_implementation,
            "integration_generation": integration_generation,
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(
                self._get_fallback_build_compilation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Compile Sarthi application codebase modules and configurations into a production-ready runnable packaging outline."
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
        API Implementation: {json.dumps(api_implementation, indent=2)}
        Frontend Code Generation: {json.dumps(frontend_code_generation, indent=2)}
        UI Component Generation: {json.dumps(ui_component_generation, indent=2)}
        State Implementation: {json.dumps(state_implementation, indent=2)}
        Integration Generation: {json.dumps(integration_generation, indent=2)}
        Global Project Context: {json.dumps(global_project_context or {{}}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "build_compilation_strategy": {{
            "project_architecture": "e.g. Next.js SPA coupled with FastAPI microservice.",
            "runtime_strategy": "e.g. Uvicorn webserver orchestrating Next.js frontend builds.",
            "dependency_strategy": "e.g. Bundled requirements.txt with package.json dependencies.",
            "build_assembly_strategy": "e.g. Multi-stage Docker packaging compiling assets."
          }},
          "project_structure_generation": {{
            "root_structure": ["backend", "frontend", "docker-compose.yml"],
            "backend_structure": ["app/main.py", "app/api/v1"],
            "frontend_structure": ["src/App.tsx", "src/components"],
            "shared_runtime_modules": ["shared/types", "shared/utils"]
          }},
          "dependency_compilation": {{
            "resolved_dependencies": ["fastapi>=0.100.0", "react>=18.2.0"],
            "shared_package_integrations": ["shared-types -> backend & frontend"],
            "runtime_dependency_graph": ["app/main.py -> app/api -> app/services"]
          }},
          "runtime_assembly": {{
            "startup_workflows": ["runMigrations -> startUvicorn -> runFrontendBuild"],
            "environment_runtime_bindings": ["VITE_API_URL -> http://localhost:8000"],
            "cross_module_runtime_flows": ["Client UI calls REST API endpoints on Mount"]
          }},
          "frontend_backend_compilation": {{
            "api_runtime_integrations": ["HTTP REST integrations bridging CORS APIs"],
            "auth_runtime_integrations": ["JWT bearer token validation middleware checking route actions"],
            "realtime_runtime_integrations": ["Websocket subscriptions synching dashboard store models"]
          }},
          "configuration_assembly": {{
            "environment_configs": ["VITE_API_URL=http://localhost:8000"],
            "runtime_configs": ["next.config.js", "uvicorn.conf.json"],
            "secret_runtime_dependencies": ["JWT_SECRET", "MONGODB_URI"]
          }},
          "realtime_compilation": {{
            "websocket_runtime_systems": ["Websocket router mapping channels"],
            "event_runtime_flows": ["backendTriggerBroadcast -> clientEventUpdate"],
            "distributed_sync_integrations": ["Redis adapter mapping websocket pub/sub events"]
          }},
          "build_validation": {{
            "validated_modules": ["backend/app", "frontend/src"],
            "resolved_runtime_conflicts": ["Port collision resolved by mapping API to 8000 & frontend to 3000"],
            "compilation_integrity_rules": ["All typescript packages compile with zero --noEmit warnings"]
          }},
          "production_assembly": {{
            "production_ready_modules": ["build/dist", "app/compiled"],
            "deployment_safe_structures": ["Dockerfile.frontend", "Dockerfile.backend"],
            "export_ready_packages": ["eco-footprint-app-v1.zip"]
          }},
          "generation_dependencies": {{
            "blocking_build_dependencies": ["npm install", "pip install -r requirements.txt"],
            "shared_runtime_dependencies": ["react", "fastapi"],
            "cross_module_compilation_rules": ["Backend ORM models compile before launching main server route."]
          }},
          "future_generation_context": {{
            "important_notes_for_export_agents": ["Compile zip artifacts preserving internal symlinks."],
            "important_notes_for_deployment_agents": ["Inject secrets into AWS ECS task configurations."],
            "important_notes_for_validation_agents": ["Verify runtime health checks before launching service instances."]
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
            return enrich_agent_output(
                self._get_fallback_build_compilation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_build_compilation(
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
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 24.
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

        db_strategy = db_architecture.get("database_strategy", {}) if db_architecture else {}
        primary_db = db_strategy.get("primary_database", "PostgreSQL")
        is_sql = primary_db.lower() in ["postgresql", "sqlite", "mysql"]

        if is_sql:
            db_dep = "sqlalchemy>=2.0.0"
            db_uri = f"{primary_db.upper()}_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dbname"
            db_secret = f"{primary_db.upper()}_URL"
        else:
            db_dep = "pymongo>=4.3.3"
            db_uri = "MONGODB_URI=mongodb://localhost:27017"
            db_secret = "MONGODB_URI"

        backend_structure = ["app/main.py", "app/core/config.py", "app/db/session.py"]
        frontend_structure = ["app/page.tsx", "app/layout.tsx", "app/globals.css"]
        resolved_dependencies = ["fastapi>=0.100.0", "uvicorn>=0.22.0", "pydantic>=2.0", db_dep, "react>=18.2.0", "zustand>=4.3.8", "swr>=2.2.0"]
        api_runtime_integrations = ["HTTP REST integrations bridging CORS APIs"]
        event_runtime_flows = []
        compilation_integrity_rules = ["All typescript packages compile with zero --noEmit warnings", "Python routes match router definitions"]

        for name in entity_names:
            plural = f"{name.lower()}s"
            backend_structure.append(f"app/api/v1/{plural}.py")
            backend_structure.append(f"app/services/{name.lower()}_service.py")
            backend_structure.append(f"app/repositories/{name.lower()}_repository.py")
            
            frontend_structure.append(f"app/dashboard/{plural}/page.tsx")
            frontend_structure.append(f"components/Create{name}Form.tsx")
            frontend_structure.append(f"stores/use{name}Store.ts")
            
            api_runtime_integrations.append(f"use{name}Query -> GET /api/v1/{plural}")
            event_runtime_flows.append(f"wsChannel{plural} -> update{name}MetricsState")

        return {
            "status": "success",
            "build_compilation_strategy": {
                "project_architecture": "Next.js 14 App Router layout integrated with modular FastAPI async microservices.",
                "runtime_strategy": "Uvicorn asynchronous worker processes orchestrating Next.js frontend builds.",
                "dependency_strategy": "Consolidated npm packages paired with virtualenv Python modules.",
                "build_assembly_strategy": "Multi-stage production build building client static assets and package servers."
            },
            "project_structure_generation": {
                "root_structure": ["backend", "frontend", "docker-compose.yml", "README.md"],
                "backend_structure": backend_structure,
                "frontend_structure": frontend_structure,
                "shared_runtime_modules": ["shared/types", "shared/validators"]
            },
            "dependency_compilation": {
                "resolved_dependencies": resolved_dependencies,
                "shared_package_integrations": ["shared/types -> backend & frontend definitions"],
                "runtime_dependency_graph": ["app/main.py -> app/api/v1 -> app/services -> app/repositories"]
            },
            "runtime_assembly": {
                "startup_workflows": ["runDatabaseMigrations -> launchFastAPIApp -> runFrontendBuild"],
                "environment_runtime_bindings": ["VITE_API_URL -> http://localhost:8000"],
                "cross_module_runtime_flows": ["Client UI calls REST API endpoints on Mount"]
            },
            "frontend_backend_compilation": {
                "api_runtime_integrations": api_runtime_integrations,
                "auth_runtime_integrations": ["JWT bearer token validation middleware checking route actions"],
                "realtime_runtime_integrations": ["Websocket subscriptions synching dashboard store models"]
            },
            "configuration_assembly": {
                "environment_configs": ["VITE_API_URL=http://localhost:8000", db_uri],
                "runtime_configs": ["next.config.js", "tsconfig.json", "requirements.txt"],
                "secret_runtime_dependencies": ["JWT_SECRET", db_secret]
            },
            "realtime_compilation": {
                "websocket_runtime_systems": ["Websocket router mapping channels"],
                "event_runtime_flows": event_runtime_flows,
                "distributed_sync_integrations": ["Redis adapter mapping websocket pub/sub events"]
            },
            "build_validation": {
                "validated_modules": ["backend/app", "frontend/src"],
                "resolved_runtime_conflicts": ["Port collision resolved by mapping API to 8000 & frontend to 3000"],
                "compilation_integrity_rules": compilation_integrity_rules
            },
            "production_assembly": {
                "production_ready_modules": ["build/dist", "app/compiled"],
                "deployment_safe_structures": ["Dockerfile.frontend", "Dockerfile.backend", "nginx.conf"],
                "export_ready_packages": ["fullstack-app-v1.zip"]
            },
            "generation_dependencies": {
                "blocking_build_dependencies": ["npm install", "pip install -r requirements.txt"],
                "shared_runtime_dependencies": ["react", "fastapi"],
                "cross_module_compilation_rules": ["Backend ORM models compile before launching main server route."]
            },
            "future_generation_context": {
                "important_notes_for_export_agents": [
                    "Ensure build folders contain clean README deployment logs."
                ],
                "important_notes_for_deployment_agents": [
                    "Verify uvicorn target port variables are configured in Dockerfile runtime commands."
                ],
                "important_notes_for_validation_agents": [
                    "Verify websocket connection handshakes run successfully on staging routes."
                ]
            }
        }
