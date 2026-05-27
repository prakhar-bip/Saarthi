import json
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)


class IntegrationGenerationAgent:
    """
    IntegrationGenerationAgent for Sarthi.
    Orchestrates cross-system runtime integration mapping API endpoints, auth routes,
    websockets streams, Zustand stores bindings, and environmental variables.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "IntegrationGenerationAgent"

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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream layers to produce cross-system runtime integration configurations.
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
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("No API keys configured. Using intelligent fallback cross-system integration design.")
            return enrich_agent_output(
                self._get_fallback_integration_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade runtime integration specifications linking frontend queries, auth middleware routing, websocket channels, environment settings, and state synchronization flows."
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
        Global Project Context: {json.dumps(global_project_context or {{}}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "integration_generation_strategy": {{
            "runtime_architecture": "e.g. Next.js App Router API runtime integrating FastAPI uvicorn routing.",
            "integration_strategy": "e.g. Declarative state selectors mapping REST and WebSocket events flow.",
            "realtime_strategy": "e.g. WebSocket connection manager relaying backend pub/sub updates.",
            "session_sync_strategy": "e.g. JWT rotation sync executing validation checks."
          }},
          "frontend_backend_integration": {{
            "api_bindings": ["useUserQuery -> GET /api/v1/users", "usePortfolioQuery -> GET /api/v1/portfolios"],
            "service_integrations": ["FastAPI controllers mapping SQL databases"],
            "cross_module_runtime_flows": ["Auth token verification upgrading HTTP sessions to websockets"]
          }},
          "authentication_integration": {{
            "protected_route_integrations": ["/dashboard -> AuthSessionGuard", "/api/v1/stresslogs -> JWTBearerMiddleware"],
            "session_sync_flows": ["tokenRotationTimer -> fetchNewAccessToken"],
            "rbac_runtime_bindings": ["UserAuth.role -> toggleAdminControls"]
          }},
          "realtime_integration": {{
            "websocket_runtime_bindings": ["wsStream -> dispatchWellnessStoreUpdate"],
            "event_sync_flows": ["milestone_event -> triggerToastNotification"],
            "live_state_integrations": ["activeBreathingSecondsCompletedCount -> dashboardGauge"]
          }},
          "state_integration": {{
            "store_api_bindings": ["useAuthStore.token -> fetchInterceptors"],
            "cache_runtime_integrations": ["mutate('/api/v1/stresslogs') on log creation"],
            "optimistic_ui_runtime_flows": ["addStressLogOptimistically -> preInsertLocalLog"]
          }},
          "shared_dependency_integration": {{
            "shared_runtime_dependencies": ["zustand", "swr", "framer-motion", "clsx"],
            "cross_module_bindings": ["APIClient -> useAuthStore"],
            "global_runtime_utilities": ["cnMerger", "formatDatetimeTimestamp"]
          }},
          "environment_integration": {{
            "environment_bindings": ["VITE_API_URL -> http://localhost:8000"],
            "runtime_configuration_flows": ["loadEnvironmentVariables -> configureAPIClientUrl"],
            "secret_dependency_integrations": ["JWT_SECRET -> authMiddlewareSignatureVerifier"]
          }},
          "error_runtime_integration": {{
            "error_propagation_flows": ["apiFailure -> displayToastAlert"],
            "fallback_runtime_rules": ["status401Error -> clearSessionAndRedirect"],
            "runtime_recovery_systems": ["onNetworkReconnect -> triggerSWRCacheRefetch"]
          }},
          "workflow_integrations": {{
            "end_to_end_workflows": ["UserLogin -> RedirectDashboard -> FetchWellnessMetrics"],
            "async_runtime_flows": ["submitStressLog -> triggerBackgroundCompilation"],
            "distributed_execution_flows": ["WebSocketEvent -> BroadcastAllConnectedUsers"]
          }},
          "generation_dependencies": {{
            "blocking_integrations": ["utils/api_client.ts", "context/WorkspaceContext.tsx"],
            "shared_dependencies": ["react", "react-dom"],
            "cross_module_generation_rules": ["APIClient loads before SWR queries mount."]
          }},
          "future_generation_context": {{
            "important_notes_for_build_compilation": ["Ensure Docker Compose config maps correct port values."],
            "important_notes_for_validation_agents": ["Verify WebSocket handshake includes credentials upgrades."],
            "important_notes_for_export_agents": ["Bundle all environment variables into static config files."]
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
            logger.error(f"Failed to run IntegrationGenerationAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_integration_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_integration_generation(
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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 23.
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

        api_bindings = []
        service_integrations = []
        cross_module_runtime_flows = ["Auth tokens verify -> upgrade session -> webSocket connections"]
        protected_route_integrations = ["/dashboard -> AuthSessionGuard"]
        session_sync_flows = ["tokenExpiryCountdown -> triggerTokenRotationRefreshQuery"]
        rbac_runtime_bindings = ["User.role == 'admin' -> grantFullCRUDPermissions"]
        websocket_runtime_bindings = ["webSocketConnectionStream -> dispatchUpdatesStoreAction"]
        event_sync_flows = []
        live_state_integrations = []
        store_api_bindings = ["useAuthStore.token -> appendBearerHeaderToFetch"]
        cache_runtime_integrations = []
        optimistic_ui_runtime_flows = []
        shared_runtime_dependencies = ["zustand", "swr", "framer-motion", "clsx"]
        cross_module_bindings = ["APIClient -> useAuthStore"]
        global_runtime_utilities = ["cnClassNamesMerger"]
        environment_bindings = ["VITE_API_URL -> http://localhost:8000"]
        runtime_configuration_flows = ["loadEnvironmentVariables -> configureAPIClientUrl"]
        secret_dependency_integrations = ["JWT_SECRET -> authMiddlewareSignatureVerifier"]
        error_propagation_flows = ["apiFailure -> displayToastAlert"]
        fallback_runtime_rules = ["status401Error -> clearSessionAndRedirect"]
        runtime_recovery_systems = ["onNetworkReconnect -> triggerSWRCacheRefetch"]
        end_to_end_workflows = ["UserLogin -> RedirectDashboard -> FetchResourceMetrics"]
        async_runtime_flows = []
        distributed_execution_flows = []
        blocking_integrations = ["utils/api_client.ts", "context/WorkspaceContext.tsx"]
        shared_dependencies = ["react", "react-dom"]
        cross_module_generation_rules = ["APIClient loads before SWR queries mount."]

        for name in entity_names:
            plural = f"{name.lower()}s"
            api_bindings.append(f"use{name}ListQuery -> GET /api/v1/{plural}")
            api_bindings.append(f"use{name}DetailsQuery -> GET /api/v1/{plural}/{{id}}")
            api_bindings.append(f"create{name}Mutation -> POST /api/v1/{plural}")
            
            service_integrations.append(f"FastAPI router maps /api/v1/{plural} to {name}Service")
            
            protected_route_integrations.append(f"/api/v1/{plural} -> JWTBearer")
            protected_route_integrations.append(f"/dashboard/{plural} -> ProtectedLayout")
            
            event_sync_flows.append(f"wsChannel{plural} -> update{name}MetricsState")
            live_state_integrations.append(f"realtime{name}MetricsCounter -> Dashboard{name}Widget")
            
            cache_runtime_integrations.append(f"mutate('/api/v1/{plural}') on create/delete {name.lower()}")
            optimistic_ui_runtime_flows.append(f"add{name}Optimistic -> insert{name}PendingIntoLocalList")
            
            async_runtime_flows.append(f"submit{name}Action -> dispatchPOSTRequestBackground")
            distributed_execution_flows.append(f"{name}UpdateBroadcast -> triggerWebSocketRelayAllClients")
            
            blocking_integrations.append(f"use{name}Store.ts")

        return {
            "status": "success",
            "integration_generation_strategy": {
                "runtime_architecture": "Next.js 14 App Router integration coupled with modular FastAPI async microservices.",
                "integration_strategy": "Declarative API endpoint hooks bindings mapping into unified Zustand client stores.",
                "realtime_strategy": "Redis-mediated pub/sub WebSocket notifications synchronizing local view metrics.",
                "session_sync_strategy": "Secure HttpOnly cookie refresh token rotation synchronizing access levels."
            },
            "frontend_backend_integration": {
                "api_bindings": api_bindings,
                "service_integrations": service_integrations,
                "cross_module_runtime_flows": cross_module_runtime_flows
            },
            "authentication_integration": {
                "protected_route_integrations": protected_route_integrations,
                "session_sync_flows": session_sync_flows,
                "rbac_runtime_bindings": rbac_runtime_bindings
            },
            "realtime_integration": {
                "websocket_runtime_bindings": websocket_runtime_bindings,
                "event_sync_flows": event_sync_flows,
                "live_state_integrations": live_state_integrations
            },
            "state_integration": {
                "store_api_bindings": store_api_bindings,
                "cache_runtime_integrations": cache_runtime_integrations,
                "optimistic_ui_runtime_flows": optimistic_ui_runtime_flows
            },
            "shared_dependency_integration": {
                "shared_runtime_dependencies": shared_runtime_dependencies,
                "cross_module_bindings": cross_module_bindings,
                "global_runtime_utilities": global_runtime_utilities
            },
            "environment_integration": {
                "environment_bindings": environment_bindings,
                "runtime_configuration_flows": runtime_configuration_flows,
                "secret_dependency_integrations": secret_dependency_integrations
            },
            "error_runtime_integration": {
                "error_propagation_flows": error_propagation_flows,
                "fallback_runtime_rules": fallback_runtime_rules,
                "runtime_recovery_systems": runtime_recovery_systems
            },
            "workflow_integrations": {
                "end_to_end_workflows": end_to_end_workflows,
                "async_runtime_flows": async_runtime_flows,
                "distributed_execution_flows": distributed_execution_flows
            },
            "generation_dependencies": {
                "blocking_integrations": blocking_integrations,
                "shared_dependencies": shared_dependencies,
                "cross_module_generation_rules": cross_module_generation_rules
            },
            "future_generation_context": {
                "important_notes_for_build_compilation": [
                    "Verify uvicorn port variables map cleanly inside environment configuration files."
                ],
                "important_notes_for_validation_agents": [
                    "Ensure token verify checks do not block static client asset compilation routes."
                ],
                "important_notes_for_export_agents": [
                    "Compile and bundle all environment configurations into final production build images."
                ]
            }
        }
