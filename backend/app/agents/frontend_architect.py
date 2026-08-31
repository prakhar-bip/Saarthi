import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


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
            return enrich_agent_output(self._get_fallback_frontend_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior frontend architect. Design the complete client-side application structure: pages, layouts, component hierarchy, routing, state management, API integration layer, and responsive strategy.\n\n"
                "## Instructions\n"
                "1. Think step by step: choose framework from tech_stack → derive pages from api_architecture.endpoints (one dashboard/list page per entity + auth pages) → design layouts (auth layout, dashboard layout) → build component hierarchy → map state stores → connect API endpoints.\n"
                "2. Every page must reference its related API endpoints from api_architecture and its data entity from db_architecture.\n"
                "3. Component hierarchy must follow atomic design: atoms (Button, Input) → molecules (FormField, StatCard) → organisms (DataTable, Sidebar) → templates (layouts) → pages.\n"
                "4. State management must distinguish: global states (auth, theme), entity cache states (per-entity lists), and local states (form errors, modals).\n"
                "5. authentication_ui_flow must align with api_architecture auth endpoints and backend_architecture.authentication_backend_flow.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- Page names must be PascalCase. Route paths must be lowercase with slashes.\n"
                "- All entity names must exactly match db_architecture.entities[].entity_name.\n"
                "- The pages and routing_structure are the primary contract for UIUXArchitectAgent — accuracy is critical."
            )
        )

        user_content = f"""
Design the frontend architecture for this project. Think step by step:
1. Choose framework and rendering strategy from requirements.tech_stack.frontend.
2. Derive pages: create auth pages (Login, Signup) if auth is required, then one list/dashboard page per entity in db_architecture.entities, plus a landing page.
3. Design layouts: AuthLayout (centered card) for auth pages, DashboardLayout (sidebar + header) for protected pages.
4. Build component hierarchy per page — list components that each page renders.
5. Map state stores: one global auth store, one cache store per entity, local states for form/modal visibility.
6. Connect each page to its corresponding api_architecture.endpoints.

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "frontend_strategy": {{
    "architecture_style": "string — 'SPA', 'MPA', or 'JAMstack'",
    "frontend_framework": "string — exact framework, e.g. 'React (Vite)', 'Next.js'",
    "rendering_strategy": "string — 'CSR', 'SSR', or 'ISR'",
    "state_management_strategy": "string — e.g. 'Zustand stores + React Query caching'"
  }},
  "frontend_structure": {{
    "root_modules": ["string — top-level directories like 'src/app', 'src/components'"],
    "feature_modules": ["string — feature area names, lowercase"],
    "shared_components": ["string — reusable UI component names (PascalCase)"],
    "core_directories": ["string — forward-slash paths like 'src/components/ui'"]
  }},
  "pages": [
    {{
      "page_name": "string — PascalCase page name, e.g. 'UserDashboard'",
      "purpose": "string — what this page shows/does",
      "route": "string — URL path for this page, e.g. '/dashboard/users'",
      "protected": "boolean — requires authentication?",
      "related_modules": ["string — feature modules this page uses"]
    }}
  ],
  "layouts": [
    {{
      "layout_name": "string — PascalCase, e.g. 'DashboardLayout'",
      "used_for": ["string — route paths using this layout"],
      "components": ["string — layout shell components like 'Sidebar', 'Header'"]
    }}
  ],
  "component_hierarchy": [
    {{
      "component_name": "string — PascalCase component name",
      "type": "string — 'Page Section', 'Data Display', 'Form', 'Navigation', 'Layout'",
      "children": ["string — child component names"],
      "reusable": "boolean"
    }}
  ],
  "routing_structure": {{
    "routing_style": "string — e.g. 'React Router DOM', 'Next.js App Router'",
    "route_groups": ["string — route group names"],
    "protected_routes": ["string — route paths requiring auth"]
  }},
  "state_management_architecture": {{
    "global_states": ["string — snake_case global state names"],
    "local_states": ["string — component-scoped state names"],
    "realtime_states": ["string — WebSocket-driven state names"]
  }},
  "api_integrations": {{
    "connected_api_groups": ["string — API group names from api_architecture"],
    "high_frequency_routes": ["string — METHOD /path for frequently polled routes"],
    "realtime_integrations": ["string — WebSocket integration descriptions"]
  }},
  "authentication_ui_flow": {{
    "auth_pages": ["string — auth route paths"],
    "protected_ui_modules": ["string — protected route paths or component names"],
    "session_handling": ["string — ordered steps for session persistence"]
  }},
  "dashboard_architecture": {{
    "required": "boolean",
    "dashboard_modules": ["string — dashboard section component names"],
    "analytics_components": ["string — chart/metric component names"]
  }},
  "responsive_strategy": {{
    "mobile_support": "boolean",
    "tablet_support": "boolean",
    "desktop_support": "boolean",
    "responsive_modules": ["string — components with responsive behavior"]
  }},
  "frontend_workflows": [
    {{
      "workflow_name": "string — user action name",
      "execution_flow": ["string — ordered UI steps: open form → validate → API call → update state → close"]
    }}
  ],
  "frontend_data_flow": {{
    "state_updates": ["string — what triggers state changes"],
    "api_to_ui_flows": ["string — how API responses map to UI state"],
    "realtime_data_flows": ["string — how WebSocket messages update UI"]
  }},
  "future_generation_context": {{
    "important_notes_for_ui_generation": ["string — styling/layout guidance for UIUXArchitectAgent"],
    "important_notes_for_frontend_code_generation": ["string — code generation guidance"],
    "important_notes_for_testing_agents": ["string — what to test in the frontend"]
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
                "route": "/",
                "protected": False,
                "related_modules": ["landing"]
            }
        ]
        
        auth_req = requirements.get("authentication", {}).get("required", True)
        if auth_req:
            pages.append({
                "page_name": "LoginPage",
                "purpose": "Accept user access credentials and issue token session.",
                "route": "/login",
                "protected": False,
                "related_modules": ["auth"]
            })
            pages.append({
                "page_name": "SignupPage",
                "purpose": "Register and onboarding profiles details.",
                "route": "/signup",
                "protected": False,
                "related_modules": ["auth"]
            })
            
        dashboard_modules = []
        for ent in entities:
            ent_name = ent.get("entity_name", "Core") if isinstance(ent, dict) else ent
            ent_lower = ent_name.lower()
            pages.append({
                "page_name": f"{ent_name}Dashboard",
                "purpose": f"Manage and display list of {ent_name} elements.",
                "route": f"/{ent_lower}s",
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
