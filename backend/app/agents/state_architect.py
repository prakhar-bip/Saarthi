import json
from loguru import logger
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class StateManagementAgent:
    """
    StateManagementAgent for Sarthi.
    Designs global, local, cache, and realtime state systems for frontend interfaces.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "StateManagementAgent"

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
        realtime_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to design the frontend and application state model.
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
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback state management design.")
            return enrich_agent_output(self._get_fallback_state_management(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture, auth_architecture, realtime_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design global stores, local states, API cache keys, optimistic updates, auth state, realtime sync, and performance state boundaries."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}
Theme Styling: {json.dumps(theme_styling, indent=2)}
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
Realtime Architecture: {json.dumps(realtime_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "state_management_strategy": {{
    "global_state_strategy": "e.g. Zustand custom hook stores representing key domain modules.",
    "local_state_strategy": "e.g. React useState/useReducer hook definitions inside presentational UI layers.",
    "cache_strategy": "e.g. SWR cache management mapping GET endpoints with automatic mutations-driven invalidation.",
    "realtime_sync_strategy": "e.g. WS client actions syncing updates directly to Zustand global stores."
  }},
  "global_state_architecture": {{
    "global_states": [
      {{
        "store_name": "e.g. useUserStore",
        "state_variables": ["variable_name"],
        "actions": ["action_name"]
      }}
    ],
    "shared_state_groups": ["group_name"],
    "cross_module_dependencies": ["dependency_description"]
  }},
  "local_state_architecture": {{
    "component_states": [
      {{
        "component_name": "component_filename",
        "state_variables": ["variable_name"]
      }}
    ],
    "isolated_states": ["state_name"],
    "ui_interaction_states": ["state_name"]
  }},
  "api_cache_architecture": {{
    "cache_layers": ["layer_name"],
    "cache_targets": [
      {{
        "endpoint": "path",
        "cache_key": "key_string",
        "ttl_seconds": 300
      }}
    ],
    "cache_invalidation_rules": [
      "rule_description"
    ]
  }},
  "realtime_state_synchronization": {{
    "realtime_states": ["variable_name"],
    "websocket_state_flows": [
      "flow_step_description"
    ],
    "live_update_groups": ["group_name"]
  }},
  "authentication_state_management": {{
    "auth_states": ["state_variable_name"],
    "session_persistence": ["persistence_method"],
    "protected_state_flows": [
      "step_description"
    ]
  }},
  "frontend_data_synchronization": {{
    "api_sync_flows": [
      "step_description"
    ],
    "async_state_updates": ["action_or_thunk_name"],
    "data_refresh_patterns": ["pattern_description"]
  }},
  "optimistic_ui_architecture": {{
    "enabled": false,
    "optimistic_update_flows": [
      "flow_step_description"
    ],
    "rollback_strategies": [
      "strategy_description"
    ]
  }},
  "dashboard_state_architecture": {{
    "dashboard_states": ["variable_name"],
    "analytics_sync_patterns": ["pattern_description"],
    "widget_update_flows": ["flow_description"]
  }},
  "performance_optimization": {{
    "memoization_targets": ["memo_target_name"],
    "lazy_loading_targets": ["lazy_component_name"],
    "high_frequency_update_optimizations": [
      "optimization_description"
    ]
  }},
  "state_workflows": [
    {{
      "workflow_name": "workflow_title",
      "state_flow": [
        "step_1",
        "step_2"
      ]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_frontend_generation": [],
    "important_notes_for_realtime_generation": [],
    "important_notes_for_testing_agents": []
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
            logger.error(f"Failed to run StateManagementAgent: {e}")
            return enrich_agent_output(self._get_fallback_state_management(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture, auth_architecture, realtime_architecture), self.agent_name, agent_inputs)

    def _get_fallback_state_management(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        realtime_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Detect context from planning, requirements, and frontend architectures
        features = requirements.get("features", []) or []
        db_entities = db_architecture.get("entities", []) if db_architecture else []
        endpoints = api_architecture.get("endpoints", []) if api_architecture else []
        pages = frontend_architecture.get("pages", []) if frontend_architecture else []
        
        # Determine features that need state hooks
        has_auth = auth_architecture is not None
        has_realtime = realtime_architecture is not None
        
        # Build global state hooks based on category and features
        global_states = []
        shared_state_groups = ["application_configurations"]
        cross_module_dependencies = []
        
        # 1. User Auth Store
        if has_auth:
            global_states.append({
                "store_name": "useAuthStore",
                "state_variables": ["user", "token", "isAuthenticated", "isVerifying"],
                "actions": ["login", "logout", "setToken", "fetchCurrentUser"]
            })
            shared_state_groups.append("session_management_context")
            cross_module_dependencies.append("Dashboard components check useAuthStore.isAuthenticated before mounting views.")

        # 2. Main Dashboard & Data Store
        entity_names = []
        for e in db_entities:
            if isinstance(e, str):
                entity_names.append(e)
            elif isinstance(e, dict) and e.get("entity_name"):
                entity_names.append(e["entity_name"])
        if not entity_names:
            entity_names = ["Item"]
        state_vars = [f"{e.lower()}_list" for e in entity_names] + ["is_loading", "active_errors"]
        actions_list = [f"fetch_{e.lower()}s" for e in entity_names] + [f"create_{e.lower()}" for e in entity_names]
        
        global_states.append({
            "store_name": "useDashboardStore",
            "state_variables": state_vars,
            "actions": actions_list
        })
        shared_state_groups.append("dashboard_metrics_data")
        
        # Check for wellness / breathing
        has_wellness = any("breathing" in f.lower() or "stress" in f.lower() or "timer" in f.lower() for f in features)
        if has_wellness:
            global_states.append({
                "store_name": "useWellnessStore",
                "state_variables": ["active_session_seconds", "breathing_cycles_completed", "active_timer_phase"],
                "actions": ["incrementCycles", "setTimerPhase", "resetTimerCycle"]
            })
            shared_state_groups.append("wellness_timer_pacing")

        # Local Component States
        component_states = []
        for p in pages:
            page_name = p if isinstance(p, str) else p.get("page_name", "Dashboard")
            component_states.append({
                "component_name": page_name,
                "state_variables": ["is_modal_open", "form_errors_payload", "search_query"]
            })

        # Cache architecture targets
        cache_targets = []
        for ep in endpoints:
            ep_path = ep if isinstance(ep, str) else ep.get("path", "")
            if ep_path and ("get" in ep_path.lower() or "list" in ep_path.lower() or "me" in ep_path.lower() or ep_path.startswith("/api/v1/users")):
                cache_targets.append({
                    "endpoint": ep_path,
                    "cache_key": f"swr_{ep_path.replace('/', '_').strip('_')}",
                    "ttl_seconds": 120
                })
        
        if not cache_targets:
            cache_targets.append({
                "endpoint": "/api/v1/users/me",
                "cache_key": "swr_user_me",
                "ttl_seconds": 300
            })

        # WebSocket sync
        ws_states = []
        ws_flows = []
        if has_realtime:
            ws_states = ["unread_alerts_count", "live_data_heartbeat"]
            ws_flows = [
                "Receive packet on WebSocket connection -> Decode JSON event -> Update global Zustand dashboard store -> Reactive component re-render triggers."
            ]

        # Workflows
        state_workflows = [
            {
                "workflow_name": "Optimistic Data Creation Log",
                "state_flow": [
                    "User submits new item form payload.",
                    "Append item to local Zustand store list immediately using temporary uuid.",
                    "Execute POST request async callback payload.",
                    "On Success: Update list entry with server returned database ID.",
                    "On Failure: Rollback store state to previous list snapshot and trigger error banner toast."
                ]
            }
        ]

        return {
            "status": "success",
            "state_management_strategy": {
                "global_state_strategy": "Zustand stores isolating user auth sessions and consolidated dashboard metrics lists.",
                "local_state_strategy": "React useState hook handles isolated dialog toggles and input fields payloads.",
                "cache_strategy": "SWR data fetching hooks cache GET queries with automatic validation on window focus.",
                "realtime_sync_strategy": "WebSocket subscriptions push live updates directly into Zustand store layers."
            },
            "global_state_architecture": {
                "global_states": global_states,
                "shared_state_groups": shared_state_groups,
                "cross_module_dependencies": cross_module_dependencies
            },
            "local_state_architecture": {
                "component_states": component_states,
                "isolated_states": ["form_fields_buffer", "active_modal_id"],
                "ui_interaction_states": ["is_sidebar_collapsed", "current_menu_active_tab"]
            },
            "api_cache_architecture": {
                "cache_layers": ["SWR cache map providers"],
                "cache_targets": cache_targets,
                "cache_invalidation_rules": [
                    "Mutations (POST/PUT/DELETE) on endpoints automatically trigger SWR mutate() calls for corresponding GET keys."
                ]
            },
            "realtime_state_synchronization": {
                "realtime_states": ws_states,
                "websocket_state_flows": ws_flows,
                "live_update_groups": ["global_system_alerts"]
            },
            "authentication_state_management": {
                "auth_states": ["currentUserProfile", "jwtTokenString", "isAuthenticatedFlag"],
                "session_persistence": ["LocalStorage token caching", "Refresh Token secured cookie validation"],
                "protected_state_flows": [
                    "App mount -> read token from local storage -> verification fetch -> update isAuthenticated store state."
                ]
            },
            "frontend_data_synchronization": {
                "api_sync_flows": [
                    "Dashboard lists trigger cache reload on user pull-to-refresh actions."
                ],
                "async_state_updates": ["asyncThunkFetchOverviewStats"],
                "data_refresh_patterns": ["Focus refetch validations", "Slow polling intervals for stats widgets"]
            },
            "optimistic_ui_architecture": {
                "enabled": True,
                "optimistic_update_flows": [
                    "Pre-insert client entries before network callbacks resolve."
                ],
                "rollback_strategies": [
                    "Restore state stores from pre-transaction copy maps if API triggers invalid returns."
                ]
            },
            "dashboard_state_architecture": {
                "dashboard_states": ["selected_time_range_filter", "graph_metric_active_axes"],
                "analytics_sync_patterns": ["Time range change triggers reload of cached charts data structures."],
                "widget_update_flows": ["Widgets query shared Zustand store selectors to prevent child renders overhead."]
            },
            "performance_optimization": {
                "memoization_targets": ["useMemoizedAnalyticsGraphsData", "useCallbackTimerCallbacks"],
                "lazy_loading_targets": ["SettingsConfigurationPanel", "DetailedAnalyticsChartsTab"],
                "high_frequency_update_optimizations": [
                    "Throttle ranges and slider updates to reduce state dispatch actions.",
                    "Isolate high-frequency websocket counter states into small, memoized react sub-nodes."
                ]
            },
            "state_workflows": state_workflows,
            "future_generation_context": {
                "important_notes_for_frontend_generation": [
                    "Always define strictly typed TypeScript interfaces for Zustand store variables and actions."
                ],
                "important_notes_for_realtime_generation": [
                    "Isolate WebSocket event listening hooks inside single global context listeners to avoid duplicate socket connections."
                ],
                "important_notes_for_testing_agents": [
                    "Mock SWR providers and use wrapper hooks to assert store rollback outcomes."
                ]
            }
        }
