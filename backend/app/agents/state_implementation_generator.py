import json
from loguru import logger
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class StateImplementationAgent:
    """
    StateImplementationAgent for Sarthi.
    Orchestrates the design and metadata generation of Zustand stores, SWR queries,
    optimistic UI state updates, realtime websocket sync, and auth session state configurations.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "StateImplementationAgent"

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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream blueprints to produce structured global Zustand stores, SWR cache query hooks,
        optimistic state updates rollback rules, and realtime websocket sync bindings.
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
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback frontend state design.")
            return enrich_agent_output(
                self._get_fallback_state_implementation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade global Zustand stores config, SWR data query cache hooks, optimistic UI state update patterns, and websocket sync workflows."
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
        Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "state_generation_strategy": {{
            "state_architecture": "e.g. Zustand consolidated store routing coupled with SWR caches.",
            "cache_strategy": "e.g. Automatic window refetch invalidation with mutation triggers.",
            "realtime_strategy": "e.g. Websocket event decoding mapping updates into state variables.",
            "session_strategy": "e.g. JWT rotation checks refreshing access tokens in auth layouts."
          }},
          "zustand_generation": {{
            "generated_stores": ["useAuthStore", "useDashboardStore"],
            "shared_state_groups": ["authSessionGroup", "dashboardMetricsGroup"],
            "cross_store_dependencies": ["useDashboardStore checks useAuthStore.isAuthenticated before fetching data"]
          }},
          "cache_generation": {{
            "swr_query_hooks": ["useUserQuery", "useProjectsQuery"],
            "cache_invalidation_rules": ["mutate(projects_key) on project create/delete actions"],
            "async_refetch_flows": ["fetchUserQuery -> validateSessionClaims"]
          }},
          "optimistic_ui_generation": {{
            "optimistic_update_flows": ["addProjectOptimistic -> insertProjectPendingIntoLocalList"],
            "rollback_rules": ["apiPOSTFailure -> revertProjectListToPreTransactionSnapshot"],
            "sync_recovery_rules": ["onNetworkReconnect -> triggerSWRCacheRefetchForceRevalidate"]
          }},
          "realtime_state_generation": {{
            "websocket_state_bindings": ["websocketMessageStream -> dispatchStoreUpdateAction"],
            "event_sync_flows": ["onEventReceived -> updateDashboardRealtimeCounters"],
            "live_dashboard_states": ["realtimeProjectCompletionsCount"]
          }},
          "session_state_generation": {{
            "auth_state_flows": ["onSubmitLoginForm -> setAuthenticatedCredentialsState"],
            "protected_session_bindings": ["useAuthStore.token -> appendBearerHeaderToSWRFetchCalls"],
            "token_refresh_sync_rules": ["tokenExpiryCountdown -> triggerTokenRotationRefreshQuery"]
          }},
          "shared_hook_generation": {{
            "custom_hooks": ["useActiveThemeState", "useSessionStoreData"],
            "shared_ui_bindings": ["useThemeState -> applyStylingClasses"],
            "frontend_state_utilities": ["mergerStatePayload", "formatDatetimeTimestamp"]
          }},
          "loading_error_state_generation": {{
            "loading_state_flows": ["setSubmitActionLoadingStateSpinner"],
            "error_recovery_flows": ["fetchAPIFailure -> triggerFallbackBannerAlertView"],
            "fallback_state_rules": ["apiUnauthError401 -> clearAuthSessionAndRedirect"]
          }},
          "state_persistence_generation": {{
            "persisted_states": ["themeModeSelectionSetting", "lastVisitedDashboardRoute"],
            "local_storage_rules": ["persistToLocalStorageWithSessionExpiryCheck"],
            "hydration_flows": ["onAppMountHydrateThemeStateFromLocalStorage"]
          }},
          "generation_dependencies": {{
            "blocking_state_dependencies": ["useAuthStore.ts", "utils/api_client.ts"],
            "shared_dependencies": ["zustand/middleware", "swr"],
            "cross_module_generation_rules": [
              "useAuthStore compiles first to configure session token tokens headers for SWR."
            ]
          }},
          "future_generation_context": {{
            "important_notes_for_integration_agents": [
              "All REST calls require valid JWT signatures in authorization header mappings."
            ],
            "important_notes_for_validation_agents": [
              "Zustand selectors should isolate components states updates to prevent extra render cycles."
            ],
            "important_notes_for_compilation_agents": [
              "Ensure requirements.txt builds asyncpg and PyJWT correctly."
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
            logger.error(f"Failed to run StateImplementationAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_state_implementation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_state_implementation(
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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 22.
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

        generated_stores = ["useAuthStore"]
        shared_state_groups = ["authSessionState"]
        cross_store_dependencies = []
        swr_query_hooks = ["useAuthProfile"]
        cache_invalidation_rules = ["mutate('/api/v1/auth/me') on profile update"]
        async_refetch_flows = ["fetchAuthMe -> syncAuthStoreState"]
        optimistic_update_flows = []
        rollback_rules = []
        sync_recovery_rules = ["onFocus -> triggerCacheRefetchRevalidate"]
        websocket_state_bindings = ["webSocketConnectionStream -> dispatchUpdatesStoreAction"]
        event_sync_flows = []
        live_dashboard_states = []
        auth_state_flows = ["onSubmitLoginForm -> setAuthenticatedState"]
        protected_session_bindings = ["useAuthStore.token -> appendBearerHeaderToFetch"]
        token_refresh_sync_rules = ["refreshSessionTimer -> queryNewTokenRotation"]
        custom_hooks = ["useActiveTheme", "useUpdatesWebSocket"]
        shared_ui_bindings = ["useTheme -> applyClassThemeNames"]
        frontend_state_utilities = ["cnClassNamesMerger"]
        loading_state_flows = ["setFormSubmittingSpinnerState"]
        error_recovery_flows = ["fetchFailure -> triggerFallbackBannerAlert"]
        fallback_state_rules = ["status401Error -> clearSessionAndRedirectToLogin"]
        persisted_states = ["themeModeChoiceSetting"]
        local_storage_rules = ["persistThemeChoiceToLocalStorage"]
        hydration_flows = ["onMountHydrateThemeStateFromLocalStorage"]
        blocking_state_dependencies = ["useAuthStore.ts", "utils/api_client.ts"]
        shared_dependencies = ["zustand/middleware", "swr"]
        cross_module_generation_rules = ["useAuthStore compiles first to configure session token headers for SWR."]

        for name in entity_names:
            plural = f"{name.lower()}s"
            generated_stores.append(f"use{name}Store")
            shared_state_groups.append(f"{name.lower()}ListState")
            cross_store_dependencies.append(f"use{name}Store checks useAuthStore.isAuthenticated before API calls")
            
            swr_query_hooks.append(f"use{name}ListQuery")
            swr_query_hooks.append(f"use{name}DetailsQuery")
            
            cache_invalidation_rules.append(f"mutate('/api/v1/{plural}') on create/delete {name.lower()}")
            async_refetch_flows.append(f"fetch{name}List -> sync{name}StoreListState")
            
            optimistic_update_flows.append(f"add{name}Optimistic -> preInsert{name}IntoList")
            rollback_rules.append(f"api{name}POSTFailure -> revert{name}StoreSnapshot")
            sync_recovery_rules.append(f"onNetworkReconnect -> trigger{name}ListCacheRefetch")
            
            websocket_state_bindings.append(f"wsChannel{plural} -> update{name}MetricsState")
            event_sync_flows.append(f"on{name}UpdateEvent -> refreshDashboard{name}Widget")
            live_dashboard_states.append(f"realtime{name}MetricsCounter")
            
            auth_state_flows.append(f"unauth{name}Call -> triggerRedirect")
            protected_session_bindings.append(f"query{plural} -> verifyTokenHeaderExists")
            
            custom_hooks.append(f"use{name}Queries")
            custom_hooks.append(f"use{name}Mutations")
            
            shared_ui_bindings.append(f"use{name}Queries -> bindListToDataGrid")
            frontend_state_utilities.append(f"format{name}StateMetadata")
            
            loading_state_flows.append(f"set{name}ActionSubmittingStateSpinner")
            error_recovery_flows.append(f"fetch{name}ListFailure -> show{name}BannerMessageAlert")
            fallback_state_rules.append(f"api{name}Error404 -> redirect{name}ListScreenView")
            
            persisted_states.append(f"lastSelected{name}ViewTab")
            local_storage_rules.append(f"persistLastSelected{name}ViewTabToLocalStorage")
            hydration_flows.append(f"onMountHydrateLastSelected{name}ViewTabFromLocalStorage")
            
            blocking_state_dependencies.append(f"use{name}Store.ts")
            cross_module_generation_rules.append(f"use{name}Store compiles after SWR hook setup resolves.")

        return {
            "status": "success",
            "state_generation_strategy": {
                "state_architecture": "Zustand stores orchestration decoupled from SWR dynamic caching controllers.",
                "cache_strategy": "Declarative cache mutation triggers coupled with automatic revalidation on tab focus.",
                "realtime_strategy": "WebSocket events listener streams mapped into unified Zustand dashboard stores.",
                "session_strategy": "Bearers JWT token rotation timer checks validating refresh sessions in background layouts."
            },
            "zustand_generation": {
                "generated_stores": generated_stores,
                "shared_state_groups": shared_state_groups,
                "cross_store_dependencies": cross_store_dependencies
            },
            "cache_generation": {
                "swr_query_hooks": swr_query_hooks,
                "cache_invalidation_rules": cache_invalidation_rules,
                "async_refetch_flows": async_refetch_flows
            },
            "optimistic_ui_generation": {
                "optimistic_update_flows": optimistic_update_flows,
                "rollback_rules": rollback_rules,
                "sync_recovery_rules": sync_recovery_rules
            },
            "realtime_state_generation": {
                "websocket_state_bindings": websocket_state_bindings,
                "event_sync_flows": event_sync_flows,
                "live_dashboard_states": live_dashboard_states
            },
            "session_state_generation": {
                "auth_state_flows": auth_state_flows,
                "protected_session_bindings": protected_session_bindings,
                "token_refresh_sync_rules": token_refresh_sync_rules
            },
            "shared_hook_generation": {
                "custom_hooks": custom_hooks,
                "shared_ui_bindings": shared_ui_bindings,
                "frontend_state_utilities": frontend_state_utilities
            },
            "loading_error_state_generation": {
                "loading_state_flows": loading_state_flows,
                "error_recovery_flows": error_recovery_flows,
                "fallback_state_rules": fallback_state_rules
            },
            "state_persistence_generation": {
                "persisted_states": persisted_states,
                "local_storage_rules": local_storage_rules,
                "hydration_flows": hydration_flows
            },
            "generation_dependencies": {
                "blocking_state_dependencies": blocking_state_dependencies,
                "shared_dependencies": shared_dependencies,
                "cross_module_generation_rules": cross_module_generation_rules
            },
            "future_generation_context": {
                "important_notes_for_integration_agents": [
                    "Verify all REST requests dynamically fetch latest Bearer token from useAuthStore."
                ],
                "important_notes_for_validation_agents": [
                    "Zustand selectors should isolate components states update triggers to avoid re-renders overhead."
                ],
                "important_notes_for_compilation_agents": [
                    "Ensure frontend builds configure SWR cache boundary wrapper configurations correctly."
                ]
            }
        }
