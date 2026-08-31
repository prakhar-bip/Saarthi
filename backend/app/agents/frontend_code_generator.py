import json
from typing import Any, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class FrontendCodeGenerationAgent:
    """
    FrontendCodeGenerationAgent for Sarthi.
    Orchestrates the generation of Next.js routing architecture, layouts modules, pages views,
    form schemas, client SWR API hooks, and error boundaries configurations.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "FrontendCodeGenerationAgent"

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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream blueprints to produce structured Next.js configurations, pages routes,
        layout architectures, API endpoints integration hooks, and authentication guards bindings.
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
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(
                self._get_fallback_frontend_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade Next.js routing architecture, page routers files, layouts modules, form handling states, and SWR integration hook scripts."
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
Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "frontend_generation_strategy": {{
    "frontend_architecture": "e.g. Next.js 14 App Router containing separate components layouts.",
    "routing_strategy": "e.g. Dynamic file-system routing matching dashboard routes layout rules.",
    "state_integration_strategy": "e.g. SWR fetch wrappers caches with global Zustand session synchronization.",
    "ui_rendering_strategy": "e.g. Client-side rendering (CSR) for pages requiring dashboard telemetry charts."
  }},
  "generated_frontend_structure": {{
    "app_routes": ["e.g. app/page.tsx", "app/dashboard/page.tsx"],
    "layout_modules": ["e.g. app/layout.tsx", "app/dashboard/layout.tsx"],
    "shared_components": ["e.g. components/Button.tsx", "components/Card.tsx"],
    "frontend_utilities": ["e.g. utils/fetcher.ts", "utils/helpers.ts"]
  }},
  "page_generation": {{
    "generated_pages": ["LandingPage", "UserDashboard"],
    "dashboard_views": ["OverviewTab", "AnalyticsTab"],
    "protected_pages": ["/dashboard"]
  }},
  "api_integration_generation": {{
    "api_hooks": ["useUser", "useProjectsList"],
    "request_handlers": ["GET /api/v1/projects -> fetchProjectsList"],
    "response_state_bindings": ["projectsList -> ZustandStateStore"]
  }},
  "authentication_frontend_generation": {{
    "auth_flows": ["Login credentials submit form validation"],
    "protected_route_bindings": ["/dashboard -> checkSessionAuthGuard"],
    "session_state_integrations": ["userProfile -> useAuthStore"]
  }},
  "realtime_frontend_generation": {{
    "websocket_integrations": ["useWebSocketUpdatesConnection"],
    "realtime_ui_bindings": ["milestone_broadcast -> showToastNotification"],
    "live_state_dependencies": ["activeWebSocketClientSession"]
  }},
  "form_generation": {{
    "generated_forms": ["LoginForm", "ProjectCreateForm"],
    "validation_integrations": ["React Hook Form schema checking"],
    "submission_workflows": ["submitProjectMetadata -> dispatchPOSTAction"]
  }},
  "error_boundary_generation": {{
    "error_boundaries": ["GlobalErrorBoundary", "DashboardWidgetErrorBoundary"],
    "fallback_ui_flows": ["showWidgetErrorFallbackWidget"],
    "frontend_exception_rules": ["apiExceptionStatus401 -> redirectToLoginScreen"]
  }},
  "responsive_generation": {{
    "responsive_layouts": ["TwoColumnDesktopLayout", "SingleColumnMobileDrawerLayout"],
    "mobile_adaptations": ["BottomNavTabBarMobile"],
    "accessibility_integrations": ["AriaLabelsForBreathing Ring"]
  }},
  "generation_dependencies": {{
    "blocking_modules": ["app/layout.tsx", "context/WorkspaceContext.tsx"],
    "shared_dependencies": ["components/Button.tsx"],
    "cross_module_generation_rules": [
      "Common layouts compile before pages routes modules are initialized."
    ]
  }},
  "future_generation_context": {{
    "important_notes_for_ui_generation": [
      "Buttons styling rules must match HSL themes parameters."
    ],
    "important_notes_for_theme_generation": [
      "Typography styling classes must inherit fonts from Outfit config."
    ],
    "important_notes_for_integration_agents": [
      "SWR validation requests require valid bearer token authorization headers."
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
            return enrich_agent_output(
                self._get_fallback_frontend_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_frontend_generation(
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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 20.
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

        app_routes = ["app/page.tsx", "app/layout.tsx", "app/globals.css", "app/login/page.tsx", "app/signup/page.tsx"]
        layout_modules = ["app/layout.tsx", "app/dashboard/layout.tsx"]
        generated_pages = ["LandingPage", "LoginPage", "SignupPage"]
        dashboard_views = []
        protected_pages = []
        api_hooks = ["useAuth", "useUpdatesWebSocket"]
        request_handlers = []
        response_state_bindings = []
        protected_route_bindings = []
        generated_forms = ["LoginForm", "SignupForm"]

        # Loop through entities to mock routes, pages, and integrations
        for name in entity_names:
            plural = f"{name.lower()}s"
            app_routes.append(f"app/dashboard/{plural}/page.tsx")
            generated_pages.append(f"{name}DashboardPage")
            dashboard_views.append(f"{name}ManagementView")
            protected_pages.append(f"/dashboard/{plural}")
            
            api_hooks.append(f"use{name}List")
            api_hooks.append(f"use{name}Details")

            request_handlers.append(f"GET /api/v1/{plural} -> fetch{name}List")
            request_handlers.append(f"POST /api/v1/{plural} -> submit{name}Create")

            response_state_bindings.append(f"{plural}Data -> use{name}Store")
            protected_route_bindings.append(f"/dashboard/{plural} -> AuthSessionGuard")

            generated_forms.append(f"Create{name}Form")
            generated_forms.append(f"Update{name}Form")

        return {
            "status": "success",
            "frontend_generation_strategy": {
                "frontend_architecture": "Next.js 14 App Router layout separating presentation components from client-side state managers.",
                "routing_strategy": "Static and dynamic folder routing mappings backed by AuthSessionGuard layouts.",
                "state_integration_strategy": "Consolidated Zustand client stores synced with SWR background query caches.",
                "ui_rendering_strategy": "React Server Components (RSC) for metadata, client-side dynamic widgets (CSR) for charts."
            },
            "generated_frontend_structure": {
                "app_routes": app_routes,
                "layout_modules": layout_modules,
                "shared_components": ["components/Button.tsx", "components/Input.tsx", "components/Card.tsx", "components/Navbar.tsx"],
                "frontend_utilities": ["utils/api_client.ts", "utils/date_helpers.ts"]
            },
            "page_generation": {
                "generated_pages": generated_pages,
                "dashboard_views": dashboard_views,
                "protected_pages": protected_pages
            },
            "api_integration_generation": {
                "api_hooks": api_hooks,
                "request_handlers": request_handlers,
                "response_state_bindings": response_state_bindings
            },
            "authentication_frontend_generation": {
                "auth_flows": ["Email Credentials Signin", "Register account verification form"],
                "protected_route_bindings": protected_route_bindings,
                "session_state_integrations": ["userProfileInfo -> useAuthStore", "jwtCredentials -> localStorageSession"]
            },
            "realtime_frontend_generation": {
                "websocket_integrations": ["useWebSocketUpdatesStreamListener"],
                "realtime_ui_bindings": ["alerts_event -> dispatchToastAlertNotification"],
                "live_state_dependencies": ["webSocketConnectedStateVariable"]
            },
            "form_generation": {
                "generated_forms": generated_forms,
                "validation_integrations": ["Zod Schema Validation bindings inside React Hook Form controllers"],
                "submission_workflows": ["submitFormAction -> apiRequestPayloadSerializer"]
            },
            "error_boundary_generation": {
                "error_boundaries": ["AppLevelGlobalErrorBoundary", "ComponentLevelFallbackWrapper"],
                "fallback_ui_flows": ["displayErrorStateToastMessageUI"],
                "frontend_exception_rules": ["status401Error -> clearSessionAndRedirectToLoginScreen"]
            },
            "responsive_generation": {
                "responsive_layouts": ["GridTwoColumnSidebarDesktopView", "ResponsiveFlexColumnMobileView"],
                "mobile_adaptations": ["CollapsibleSideDrawerNavTabs", "SwipeableDataCardActions"],
                "accessibility_integrations": ["AriaTogglesForThemeMode", "AccessibleFormInputLabelsWithAriaDescriptors"]
            },
            "generation_dependencies": {
                "blocking_modules": ["app/layout.tsx", "utils/api_client.ts"],
                "shared_dependencies": ["components/Button.tsx", "components/Input.tsx"],
                "cross_module_generation_rules": [
                    "Next.js Global Root Layout compiles first.",
                    "Common component elements compile before pages routes modules are initialized."
                ]
            },
            "future_generation_context": {
                "important_notes_for_ui_generation": [
                    "Ensure Tailwind config supports HSL values to match active palette parameters."
                ],
                "important_notes_for_theme_generation": [
                    "Typography font config inherits configurations from Tailwind tailwind.config.js."
                ],
                "important_notes_for_integration_agents": [
                    "All SWR fetch requests must check valid JWT signatures in state stores."
                ]
            }
        }
