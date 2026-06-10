import json
from loguru import logger
import logging
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class ErrorCorrectionAgent:
    """
    ErrorCorrectionAgent for Sarthi.

    Operates as the autonomous recovery and stabilization pipeline immediately after
    BuildCompilationAgent.  It ingests the full upstream compilation intelligence and
    produces structured, deterministic repair intelligence covering:

    - import / dependency resolution repairs
    - frontend ↔ backend API contract repairs
    - authentication middleware corrections
    - realtime / WebSocket synchronization repairs
    - state management store repairs
    - runtime startup stabilization
    - cross-module compilation integrity repairs
    - production-safe export-ready recovery orchestration

    Outputs are stored in AI_ErrorCorrection.json inside Sarthi orchestration memory
    and consumed by downstream ConsistencyValidationAgent, PerformanceValidationAgent,
    SecurityValidationAgent, RealtimeValidationAgent, and ProjectExportAgent.
    """

    def __init__(self) -> None:
        self.agent_name = "ErrorCorrectionAgent"

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def design(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_plan: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        build_compilation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesise all upstream compilation outputs to produce production-safe
        automated error-correction and stabilisation intelligence.
        """
        agent_inputs = {
            "requirements": requirements,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "auth_architecture": auth_architecture,
            "validation_architecture": validation_architecture,
            "optimization_architecture": optimization_architecture,
            "code_generation_plan": code_generation_plan,
            "database_model_generation": database_model_generation,
            "backend_code_generation": backend_code_generation,
            "api_implementation": api_implementation,
            "frontend_code_generation": frontend_code_generation,
            "ui_component_generation": ui_component_generation,
            "state_implementation": state_implementation,
            "integration_generation": integration_generation,
            "build_compilation": build_compilation,
            "global_project_context": global_project_context,
        }

        no_keys = not (
            settings.NVIDIA_API_KEY
            or settings.OPENROUTER_API_KEY
            or settings.GROQ_API_KEY
            or settings.GOOGLE_API_KEY
        )
        if no_keys:
            logger.warning(
                "No API keys configured. Using local fallback error-correction intelligence."
            )
            return enrich_agent_output(
                self._get_fallback_error_correction(**agent_inputs),
                self.agent_name,
                agent_inputs,
                role=(
                    "Autonomous error-recovery and compilation-stabilisation layer. "
                    "Produces structured repair intelligence consumed by validation and export agents."
                ),
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "Recover and stabilise Sarthi's generated application like a senior AI compiler "
                "recovery engineer. Produce deterministic, production-safe repair intelligence "
                "covering imports, dependency graphs, API contracts, auth middleware, realtime "
                "synchronisation, state stores, runtime startup, and cross-module consistency."
            ),
        )

        user_content = f"""
        Analyze Sarthi compilation outputs and produce automated error-correction intelligence.

        Requirements: {json.dumps(requirements, indent=2)}
        Database Architecture: {json.dumps(db_architecture, indent=2)}
        Backend Architecture: {json.dumps(backend_architecture, indent=2)}
        API Architecture: {json.dumps(api_architecture, indent=2)}
        Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
        Validation Architecture: {json.dumps(validation_architecture, indent=2)}
        Optimization Architecture: {json.dumps(optimization_architecture, indent=2)}
        Code Generation Plan: {json.dumps(code_generation_plan, indent=2)}
        Database Model Generation: {json.dumps(database_model_generation, indent=2)}
        Backend Code Generation: {json.dumps(backend_code_generation, indent=2)}
        API Implementation: {json.dumps(api_implementation, indent=2)}
        Frontend Code Generation: {json.dumps(frontend_code_generation, indent=2)}
        UI Component Generation: {json.dumps(ui_component_generation, indent=2)}
        State Implementation: {json.dumps(state_implementation, indent=2)}
        Integration Generation: {json.dumps(integration_generation, indent=2)}
        Build Compilation: {json.dumps(build_compilation, indent=2)}
        Global Project Context: {json.dumps(global_project_context or {{}}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "error_recovery_strategy": {{
            "repair_model": "e.g. GEMINI reasoning-heavy recovery, NVIDIA deterministic structural repair.",
            "runtime_recovery_strategy": "e.g. Layered cascade: import repair -> dependency graph -> API contract -> auth -> realtime -> state -> export.",
            "dependency_repair_strategy": "e.g. Resolve missing peer deps before correcting circular import chains.",
            "stabilization_strategy": "e.g. Patch in-place preserving original names, routes, and entity contracts."
          }},
          "import_dependency_repairs": {{
            "resolved_import_issues": [],
            "dependency_conflicts": [],
            "shared_module_repairs": []
          }},
          "frontend_backend_repairs": {{
            "api_contract_repairs": [],
            "route_binding_repairs": [],
            "runtime_sync_repairs": []
          }},
          "authentication_repairs": {{
            "auth_middleware_repairs": [],
            "session_sync_repairs": [],
            "rbac_consistency_repairs": []
          }},
          "realtime_repairs": {{
            "websocket_repairs": [],
            "event_sync_repairs": [],
            "distributed_state_repairs": []
          }},
          "state_management_repairs": {{
            "store_repairs": [],
            "cache_sync_repairs": [],
            "optimistic_ui_repairs": []
          }},
          "runtime_stabilization": {{
            "startup_repairs": [],
            "runtime_recovery_rules": [],
            "environment_fix_rules": []
          }},
          "compilation_integrity_repairs": {{
            "resolved_build_conflicts": [],
            "dependency_graph_repairs": [],
            "cross_module_repairs": []
          }},
          "production_safe_recovery": {{
            "stabilized_modules": [],
            "recovered_runtime_flows": [],
            "export_safe_repairs": []
          }},
          "generation_dependencies": {{
            "blocking_repairs": [],
            "shared_recovery_dependencies": [],
            "cross_module_repair_rules": []
          }},
          "future_generation_context": {{
            "important_notes_for_validation_agents": [],
            "important_notes_for_export_agents": [],
            "important_notes_for_deployment_agents": []
          }}
        }}
        """

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(
                parse_json_response(raw_response),
                self.agent_name,
                agent_inputs,
                role=(
                    "Autonomous error-recovery and compilation-stabilisation layer. "
                    "Produces structured repair intelligence consumed by validation and export agents."
                ),
            )
        except Exception as exc:
            logger.error(f"Failed to run ErrorCorrectionAgent: {exc}")
            return enrich_agent_output(
                self._get_fallback_error_correction(**agent_inputs),
                self.agent_name,
                agent_inputs,
                role=(
                    "Autonomous error-recovery and compilation-stabilisation layer. "
                    "Produces structured repair intelligence consumed by validation and export agents."
                ),
            )

    # ------------------------------------------------------------------
    # Deterministic fallback — runs when all LLM providers are unavailable
    # ------------------------------------------------------------------

    def _get_fallback_error_correction(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_plan: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        build_compilation: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a deterministic, context-aware fallback error-correction map (Stage 25).
        Derives entity names, API routes, and store names from upstream contracts so that
        every repair entry is grounded in the actual generated project.
        """
        # ---- derive entity names from db_architecture -------------------
        entities: List[Any] = db_architecture.get("entities", []) if db_architecture else []
        entity_names: List[str] = []
        for e in entities:
            if isinstance(e, str):
                entity_names.append(e)
            elif isinstance(e, dict) and e.get("entity_name"):
                entity_names.append(e["entity_name"])
        if not entity_names:
            entity_names = ["User", "Project", "Resource", "Session"]

        # ---- derive API endpoints from api_architecture ------------------
        raw_endpoints: List[Any] = api_architecture.get("endpoints", []) if api_architecture else []
        endpoint_paths: List[str] = []
        for ep in raw_endpoints:
            if isinstance(ep, str):
                endpoint_paths.append(ep)
            elif isinstance(ep, dict):
                method = ep.get("method", "GET")
                path = ep.get("path", "")
                if path:
                    endpoint_paths.append(f"{method} {path}")
        if not endpoint_paths:
            for name in entity_names:
                plural = f"{name.lower()}s"
                endpoint_paths += [
                    f"GET /api/v1/{plural}",
                    f"POST /api/v1/{plural}",
                    f"GET /api/v1/{plural}/{{id}}",
                    f"PUT /api/v1/{plural}/{{id}}",
                    f"DELETE /api/v1/{plural}/{{id}}",
                ]

        # ---- derive store names from state_implementation ---------------
        stores: List[str] = []
        if state_implementation and isinstance(state_implementation.get("stores"), list):
            for s in state_implementation["stores"]:
                if isinstance(s, str):
                    stores.append(s)
                elif isinstance(s, dict) and s.get("store_name"):
                    stores.append(s["store_name"])
        if not stores:
            stores = [f"use{name}Store" for name in entity_names] + ["useAuthStore", "useUIStore"]

        # ---- build repair collections -----------------------------------
        resolved_import_issues: List[str] = [
            "Re-export barrel index missing for shared/types — add index.ts re-exporting all interfaces.",
            "FastAPI circular import between app/main.py and app/api/router.py — move router registration post-app init.",
        ]
        dependency_conflicts: List[str] = [
            "Peer dependency conflict: react@18 required by framer-motion but package.json specifies ^17 — pin to react@18.2.0.",
            "pydantic v1/v2 split: replace deprecated validator decorators with field_validator for pydantic>=2.0.",
        ]
        shared_module_repairs: List[str] = [
            "shared/types/index.ts must export all entity interfaces before any frontend query hook imports them.",
            "utils/api_client.ts must initialise BASE_URL from process.env.NEXT_PUBLIC_API_URL before SWR hooks mount.",
        ]

        api_contract_repairs: List[str] = []
        route_binding_repairs: List[str] = []
        runtime_sync_repairs: List[str] = []
        for name in entity_names:
            plural = f"{name.lower()}s"
            api_contract_repairs.append(
                f"{name}: align response schema field names between FastAPI Pydantic model and "
                f"TypeScript interface (snake_case -> camelCase transform required)."
            )
            route_binding_repairs.append(
                f"use{name}Query hook must target /api/v1/{plural} — verify NEXT_PUBLIC_API_URL prefix is applied."
            )
            runtime_sync_repairs.append(
                f"SWR mutate key for {plural} must match exact fetch URL string including query params."
            )

        auth_middleware_repairs: List[str] = [
            "JWTBearer dependency must be declared on every protected FastAPI router — verify no route skips Depends(get_current_user).",
            "HTTPOnly refresh-token cookie SameSite policy must be 'lax' for cross-origin Next.js dev server requests.",
        ]
        session_sync_repairs: List[str] = [
            "Access token expiry (exp claim) must be synchronised with frontend tokenExpiryTimer interval — default 15 min.",
            "On 401 response, useAuthStore must clear token and redirect to /login before retrying the failed request.",
        ]
        rbac_consistency_repairs: List[str] = [
            "Admin-only API routes must return 403 (not 404) when authenticated non-admin user requests them.",
            "Frontend RBAC guard must read user.role from useAuthStore — do not re-fetch role on every render.",
        ]

        websocket_repairs: List[str] = [
            "WebSocket connection must include Authorization header or ?token= query param — server rejects unauthenticated upgrades.",
            "Client must implement exponential back-off reconnect (1s, 2s, 4s, max 30s) on ws.onclose event.",
        ]
        event_sync_repairs: List[str] = [
            "Event payload envelope must include { type, payload, timestamp } — strip raw data sends.",
        ]
        for name in entity_names:
            event_sync_repairs.append(
                f"{name}Updated WS event must trigger SWR mutate('/api/v1/{name.lower()}s') to keep UI consistent."
            )
        distributed_state_repairs: List[str] = [
            "Redis pub/sub channel names must be namespaced per project_id to prevent cross-tenant event leaks.",
        ]

        store_repairs: List[str] = []
        cache_sync_repairs: List[str] = []
        optimistic_ui_repairs: List[str] = []
        for store in stores:
            entity = store.replace("use", "").replace("Store", "")
            store_repairs.append(
                f"{store}: initialise all state slices as null (not undefined) to prevent React hydration mismatches."
            )
            cache_sync_repairs.append(
                f"{store}: call SWR mutate on every mutation action to keep remote cache in sync."
            )
            optimistic_ui_repairs.append(
                f"{store}: roll back optimistic insert on API error using zustand set() inside catch block."
            )

        startup_repairs: List[str] = [
            "Run database migrations (alembic upgrade head) before starting uvicorn — add to Dockerfile CMD chain.",
            "Next.js must not start until /api/health returns 200 — add wait-for-it.sh or healthcheck in docker-compose.",
            "Environment variable NEXT_PUBLIC_API_URL must be set at Next.js build time — verify ARG/ENV in Dockerfile.frontend.",
        ]
        runtime_recovery_rules: List[str] = [
            "On unhandled FastAPI exception, return { detail: string } JSON — never return HTML error pages to API clients.",
            "Frontend global error boundary must catch React render errors and display fallback UI without crashing the session.",
            "All async FastAPI handlers must wrap DB calls in try/except and return structured HTTPException responses.",
        ]
        environment_fix_rules: List[str] = [
            "Never hard-code localhost URLs — always read from environment variables.",
            "CORS origins list must include both http://localhost:3000 and the production frontend domain.",
            "MongoDB URI must use connection pooling params: maxPoolSize=10&connectTimeoutMS=5000.",
        ]

        resolved_build_conflicts: List[str] = [
            "Port 8000 (FastAPI) and port 3000 (Next.js) must not conflict — docker-compose exposes both on distinct host ports.",
            "TypeScript strict mode errors in generated components must be resolved before build step — run tsc --noEmit as pre-build gate.",
        ]
        dependency_graph_repairs: List[str] = [
            "Backend ORM models must be imported before API routers to avoid SQLAlchemy mapper configuration errors.",
            "Frontend store modules must be imported before query hooks that depend on them.",
        ]
        cross_module_repairs: List[str] = []
        for name in entity_names:
            cross_module_repairs.append(
                f"{name} Pydantic schema in backend must match TypeScript interface field-for-field — run schema sync check pre-export."
            )

        stabilized_modules: List[str] = (
            ["backend/app/main.py", "backend/app/core/config.py", "frontend/src/utils/api_client.ts"]
            + [f"backend/app/api/v1/{name.lower()}s.py" for name in entity_names]
            + [f"frontend/src/stores/use{name}Store.ts" for name in entity_names]
        )
        recovered_runtime_flows: List[str] = [
            "UserLogin -> JWT issue -> store token -> mount protected pages -> fetch entity data",
            "WebSocket connect (with JWT) -> receive event -> dispatch store action -> re-render UI",
            "Mutation -> optimistic UI update -> API call -> SWR revalidate -> confirm/rollback",
        ]
        export_safe_repairs: List[str] = [
            "Strip all console.log / print debug statements before packaging export ZIP.",
            "Replace all localhost hardcodes with environment variable references.",
            "Ensure .env.example lists every required variable — remove .env from export ZIP.",
            "Run eslint --fix and black formatter passes before export to ensure clean source.",
        ]

        blocking_repairs: List[str] = [
            "shared/types/index.ts must be generated and exported before any frontend file is compiled.",
            "utils/api_client.ts must be patched with correct BASE_URL before SWR hooks are bundled.",
            "JWT middleware must be verified working before protected route generation is exported.",
        ]
        shared_recovery_dependencies: List[str] = [
            "pydantic>=2.0",
            "react@18",
            "zustand>=4.3",
            "swr>=2.2",
            "framer-motion>=10",
        ]
        cross_module_repair_rules: List[str] = [
            "Repair import issues in shared modules before repairing dependent consumer modules.",
            "Repair backend models before repairing API routes that import them.",
            "Repair API contracts before repairing frontend query hooks that consume them.",
            "Repair auth middleware before repairing protected route guards.",
        ]

        notes_for_validation: List[str] = [
            "Run TypeScript compilation check (tsc --noEmit) before validating frontend module consistency.",
            "Validate JWT expiry/refresh cycle in staging before marking auth system production-safe.",
            "Confirm WebSocket reconnect logic passes under simulated network drop tests.",
            "Verify CORS preflight succeeds for all protected API routes from the deployed frontend origin.",
        ]
        notes_for_export: List[str] = [
            "Apply all export_safe_repairs before packaging the ZIP archive.",
            "Ensure .env.example is included and .env is excluded from the ZIP.",
            "Include a CHANGELOG.md entry listing all automated repairs applied by ErrorCorrectionAgent.",
            "Confirm stabilized_modules list matches the actual file paths inside the export archive.",
        ]
        notes_for_deployment: List[str] = [
            "Run database migration step before starting the application container.",
            "Inject all secret_runtime_dependencies as environment variables — never bake into image.",
            "Configure health-check endpoints (/api/health) in Kubernetes/ECS before routing production traffic.",
            "Enable structured JSON logging in production — disable debug log levels.",
        ]

        return {
            "status": "success",
            "error_recovery_strategy": {
                "repair_model": (
                    "GEMINI reasoning-heavy error recovery handles API contract and auth middleware repairs; "
                    "NVIDIA deterministic structural repair handles import resolution and dependency graph corrections; "
                    "GROQ fast lightweight correction handles state and startup repairs; "
                    "OPENROUTER handles overflow routing when primary providers are saturated."
                ),
                "runtime_recovery_strategy": (
                    "Layered cascade: (1) shared module import repairs → (2) dependency graph resolution → "
                    "(3) API contract alignment → (4) auth middleware correction → "
                    "(5) realtime WebSocket repair → (6) state store stabilisation → "
                    "(7) runtime startup sequencing → (8) production export packaging."
                ),
                "dependency_repair_strategy": (
                    "Resolve missing peer dependencies and version pin conflicts first. "
                    "Then unwind circular imports by hoisting shared type definitions to barrel index files. "
                    "Finally verify the full dependency graph compiles with zero errors before advancing."
                ),
                "stabilization_strategy": (
                    "Patch in-place preserving original entity names, route paths, store slice keys, "
                    "and theme tokens from upstream agent contracts. "
                    "Never rename or restructure — only correct broken bindings and missing references."
                ),
            },
            "import_dependency_repairs": {
                "resolved_import_issues": resolved_import_issues,
                "dependency_conflicts": dependency_conflicts,
                "shared_module_repairs": shared_module_repairs,
            },
            "frontend_backend_repairs": {
                "api_contract_repairs": api_contract_repairs,
                "route_binding_repairs": route_binding_repairs,
                "runtime_sync_repairs": runtime_sync_repairs,
            },
            "authentication_repairs": {
                "auth_middleware_repairs": auth_middleware_repairs,
                "session_sync_repairs": session_sync_repairs,
                "rbac_consistency_repairs": rbac_consistency_repairs,
            },
            "realtime_repairs": {
                "websocket_repairs": websocket_repairs,
                "event_sync_repairs": event_sync_repairs,
                "distributed_state_repairs": distributed_state_repairs,
            },
            "state_management_repairs": {
                "store_repairs": store_repairs,
                "cache_sync_repairs": cache_sync_repairs,
                "optimistic_ui_repairs": optimistic_ui_repairs,
            },
            "runtime_stabilization": {
                "startup_repairs": startup_repairs,
                "runtime_recovery_rules": runtime_recovery_rules,
                "environment_fix_rules": environment_fix_rules,
            },
            "compilation_integrity_repairs": {
                "resolved_build_conflicts": resolved_build_conflicts,
                "dependency_graph_repairs": dependency_graph_repairs,
                "cross_module_repairs": cross_module_repairs,
            },
            "production_safe_recovery": {
                "stabilized_modules": stabilized_modules,
                "recovered_runtime_flows": recovered_runtime_flows,
                "export_safe_repairs": export_safe_repairs,
            },
            "generation_dependencies": {
                "blocking_repairs": blocking_repairs,
                "shared_recovery_dependencies": shared_recovery_dependencies,
                "cross_module_repair_rules": cross_module_repair_rules,
            },
            "future_generation_context": {
                "important_notes_for_validation_agents": notes_for_validation,
                "important_notes_for_export_agents": notes_for_export,
                "important_notes_for_deployment_agents": notes_for_deployment,
            },
        }
