import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

class FrontendArchitectureAgent:
    """
    FrontendArchitectureAgent for Sarthi.
    Designs front-end strategic routes, components hierarchy, layouts, and state management trees.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "FrontendArchitectureAgent"

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
        api_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze requirements, planning, db, backend, and API outputs to design the frontend architecture.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback frontend architecture design.")
            return enrich_agent_output(self._get_fallback_frontend_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design frontend routes, pages, layout hierarchy, component contracts, data flow, state boundaries, and API integrations."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "frontend_strategy": {{
    "architecture_style": "SPA / Monolithic / JAMstack",
    "frontend_framework": "React / Next.js / Vite",
    "rendering_strategy": "Client-side rendering (CSR) / Server-side rendering (SSR)",
    "state_management_strategy": "Global Store / React Context Hooks"
  }},
  "frontend_structure": {{
    "root_modules": ["src/app", "src/components"],
    "feature_modules": ["auth", "dashboard"],
    "shared_components": ["Button", "Input", "Card"],
    "core_directories": ["src/components/ui", "src/hooks"]
  }},
  "pages": [
    {{
      "page_name": "Dashboard",
      "purpose": "Renders user metric overview and charts.",
      "protected": true,
      "related_modules": ["analytics", "charts"]
    }}
  ],
  "layouts": [
    {{
      "layout_name": "DashboardLayout",
      "used_for": ["/dashboard", "/settings"],
      "components": ["Sidebar", "Header"]
    }}
  ],
  "component_hierarchy": [
    {{
      "component_name": "MetricsGrid",
      "type": "Layout Component",
      "children": ["StatCard"],
      "reusable": true
    }}
  ],
  "routing_structure": {{
    "routing_style": "File-based App Router",
    "route_groups": ["auth", "dashboard"],
    "protected_routes": ["/dashboard", "/profile"]
  }},
  "state_management_architecture": {{
    "global_states": ["auth_session", "theme_preference"],
    "local_states": ["active_tabs_index", "form_errors"],
    "realtime_states": ["ws_connection_status", "inbox_notifications"]
  }},
  "api_integrations": {{
    "connected_api_groups": ["Auth API", "Metrics API"],
    "high_frequency_routes": ["GET /api/v1/notifications"],
    "realtime_integrations": ["Websocket alerts push"]
  }},
  "authentication_ui_flow": {{
    "auth_pages": ["/login", "/register"],
    "protected_ui_modules": ["DashboardPanel"],
    "session_handling": ["Read bearer token keys on mount"]
  }},
  "dashboard_architecture": {{
    "required": true,
    "dashboard_modules": ["AnalyticsGrid", "RecentActivity"],
    "analytics_components": ["LineChart", "PieChart"]
  }},
  "responsive_strategy": {{
    "mobile_support": true,
    "tablet_support": true,
    "desktop_support": true,
    "responsive_modules": ["Collapsible Sidebar Grid"]
  }},
  "frontend_workflows": [
    {{
      "workflow_name": "Submit log entry",
      "execution_flow": ["Validate client inputs", "Dispatch API POST call", "Update query state cache"]
    }}
  ],
  "frontend_data_flow": {{
    "state_updates": ["Set user session on login success"],
    "api_to_ui_flows": ["Query GET /api/v1/metrics sets lines state"],
    "realtime_data_flows": ["WS message pushes to activity log feed"]
  }},
  "future_generation_context": {{
    "important_notes_for_ui_generation": [],
    "important_notes_for_frontend_code_generation": [],
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
            logger.error(f"Failed to run FrontendArchitectureAgent: {e}")
            return enrich_agent_output(self._get_fallback_frontend_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture), self.agent_name, agent_inputs)

    def _get_fallback_frontend_architecture(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        name = overview.get("name", "FinSight")
        category = requirements.get("project_overview", {}).get("type", "Web App").lower()
        features = requirements.get("features", [])
        entities = db_architecture.get("entities", [])
        endpoints = api_architecture.get("endpoints", [])
        
        # Determine pages based on entities and endpoints
        pages = [
            {
                "page_name": "LandingPage",
                "purpose": "Marketing splash page introducing Sarthi compiled elements.",
                "protected": False,
                "related_modules": ["landing"]
            }
        ]
        
        auth_req = requirements.get("authentication", {}).get("required", True)
        if auth_req:
            pages.append({
                "page_name": "LoginPage",
                "purpose": "Accept user access credentials and issue token session.",
                "protected": False,
                "related_modules": ["auth"]
            })
            pages.append({
                "page_name": "SignupPage",
                "purpose": "Register and onboarding profiles details.",
                "protected": False,
                "related_modules": ["auth"]
            })
            
        dashboard_modules = []
        for ent in entities:
            ent_name = ent.get("entity_name", "Core")
            ent_lower = ent_name.lower()
            pages.append({
                "page_name": f"{ent_name}Dashboard",
                "purpose": f"Manage and display list of {ent_name} elements.",
                "protected": auth_req,
                "related_modules": [ent_lower]
            })
            dashboard_modules.append(f"{ent_name}ListPanel")
            dashboard_modules.append(f"{ent_name}CreateForm")

        # Layout mapping
        layouts = [
            {
                "layout_name": "AuthLayout",
                "used_for": ["/login", "/register"] if auth_req else [],
                "components": ["CenteredCardPanel"]
            },
            {
                "layout_name": "DashboardLayout",
                "used_for": [f"/{e.get('entity_name', '').lower()}s" for e in entities],
                "components": ["SidebarNavigation", "AppHeaderBar"]
            }
        ]

        # Component hierarchy construction
        hierarchy = []
        for ent in entities:
            ent_name = ent.get("entity_name", "Core")
            hierarchy.append({
                "component_name": f"{ent_name}Panel",
                "type": "Dashboard Section Widget",
                "children": [f"{ent_name}DataTableGrid", f"{ent_name}FormDialog"],
                "reusable": True
            })

        # State management fields
        global_states = ["theme_preference"]
        if auth_req:
            global_states.append("active_jwt_token")
            global_states.append("authenticated_user_profile")

        for ent in entities:
            ent_lower = ent.get("entity_name", "").lower()
            global_states.append(f"cached_{ent_lower}_list")

        # Routing structures
        route_groups = ["dashboard"]
        if auth_req:
            route_groups.append("auth")

        protected_routes = []
        if auth_req:
            for ent in entities:
                protected_routes.append(f"/{ent.get('entity_name', '').lower()}s")

        # Connected API groups mapping
        connected_groups = list(set([ep.get("group_name") for ep in endpoints]))

        # High frequency routes
        high_freq = [ep.get("path") for ep in endpoints if ep.get("method") == "GET" and "list" in ep.get("description", "").lower()]

        # Workflows
        workflows = []
        for ent in entities:
            ent_name = ent.get("entity_name", "Core")
            workflows.append({
                "workflow_name": f"Create new {ent_name.lower()} entry",
                "execution_flow": [
                    f"Open {ent_name}FormDialog modal.",
                    "Validate client input schemas.",
                    f"Dispatch API POST /api/v1/{ent_name.lower()}s request.",
                    f"Prepend response to cached_{ent_name.lower()}_list.",
                    "Close dialog."
                ]
            })

        return {
            "status": "success",
            "frontend_strategy": {
                "architecture_style": "SPA Client-Side Dashboard Architecture.",
                "frontend_framework": "React (Vite Compiler / Next.js SPA Mode)",
                "rendering_strategy": "Client-Side Rendering (CSR) dynamic routing.",
                "state_management_strategy": "Zustand custom hook stores and React SWR data caches."
            },
            "frontend_structure": {
                "root_modules": ["src/app", "src/components", "src/context", "src/hooks"],
                "feature_modules": [e.get("entity_name", "").lower() for e in entities],
                "shared_components": ["Button", "Input", "CardPanel", "ModalWrapper", "FormInput"],
                "core_directories": [
                    "src/components/ui",
                    "src/components/shared",
                    "src/hooks",
                    "src/stores"
                ]
            },
            "pages": pages,
            "layouts": layouts,
            "component_hierarchy": hierarchy,
            "routing_structure": {
                "routing_style": "React Router DOM client routes.",
                "route_groups": route_groups,
                "protected_routes": protected_routes
            },
            "state_management_architecture": {
                "global_states": global_states,
                "local_states": [
                    "form_validation_errors",
                    "is_loading_spinner_active",
                    "modal_dialog_visibility"
                ],
                "realtime_states": [
                    "ws_connection_active",
                    "realtime_activity_logs"
                ]
            },
            "api_integrations": {
                "connected_api_groups": connected_groups,
                "high_frequency_routes": high_freq or ["GET /api/v1/users/me"],
                "realtime_integrations": ["Websocket connection handler mapping realtime triggers."]
            },
            "authentication_ui_flow": {
                "auth_pages": ["/login", "/signup"] if auth_req else [],
                "protected_ui_modules": protected_routes,
                "session_handling": [
                    "Verify JWT token on mount.",
                    "Store session key inside LocalStorage.",
                    "Auto redirect back to /login on HTTP 401 response status."
                ]
            },
            "dashboard_architecture": {
                "required": True,
                "dashboard_modules": dashboard_modules,
                "analytics_components": ["SummaryCardsListGrid", "ActivityLogsTimelineFeed"]
            },
            "responsive_strategy": {
                "mobile_support": True,
                "tablet_support": True,
                "desktop_support": True,
                "responsive_modules": ["SidebarNavigationDrawer", "DataTableResponsiveWrap"]
            },
            "frontend_workflows": workflows,
            "frontend_data_flow": {
                "state_updates": [
                    "JWT token state update triggers layout state transitions.",
                    "Form submissions update cache stores on API response success."
                ],
                "api_to_ui_flows": [
                    "GET list queries serialize into custom data tables.",
                    "Fetch queries bind state variables directly to form inputs."
                ],
                "realtime_data_flows": [
                    "Realtime event logs feed into UI list updates dynamically via WebSocket state hook."
                ]
            },
            "future_generation_context": {
                "important_notes_for_ui_generation": [
                    "Utilize consistent flexbox grid layouts to support responsive breakpoints.",
                    "Inject appropriate color tokens matching primary/secondary palettes in cards background styling."
                ],
                "important_notes_for_frontend_code_generation": [
                    "Configure Zustand stores to manage global state preferences.",
                    "Enforce strict TypeScript validation checking props definitions."
                ],
                "important_notes_for_testing_agents": [
                    "Mock SWR / Axios calls targeting API endpoint namespaces.",
                    "Test that navigation path links match declared routers lists."
                ]
            }
        }
