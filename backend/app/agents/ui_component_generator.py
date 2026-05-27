import json
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)


class UIComponentGenerationAgent:
    """
    UIComponentGenerationAgent for Sarthi.
    Orchestrates the design and metadata generation of reusable components, forms,
    widgets, tables, dialogs, responsive patterns, and accessibility integrations.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "UIComponentGenerationAgent"

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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize upstream blueprints to produce structured UI components, dashboard widgets,
        forms validation flow specs, role-based visibility schemas, and accessibility integrations.
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
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback UI component generation design.")
            return enrich_agent_output(
                self._get_fallback_ui_component_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design production-grade reusable components structure, design system patterns, interactive widgets, validation bindings, and accessibility-safe layouts."
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
        Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "ui_generation_strategy": {{
            "component_architecture": "e.g. Atomic Component Architecture utilizing reusable visual primitives.",
            "design_system_strategy": "e.g. TailwindCSS config token injection matching shadcn/ui structures.",
            "responsive_strategy": "e.g. Fluid layouts resizing down to mobile drawer components.",
            "ui_rendering_strategy": "e.g. Next.js server component (RSC) shells with client-side reactive sub-islands."
          }},
          "generated_components": {{
            "shared_components": ["Button", "Input", "Card"],
            "dashboard_components": ["OverviewBanner", "SidebarNavbar"],
            "form_components": ["LoginFormElement", "SignupFormElement"],
            "navigation_components": ["TopNavMenu", "TabsGroupNav"],
            "modal_components": ["ConfirmActionDialog", "SettingsModal"]
          }},
          "dashboard_generation": {{
            "analytics_widgets": ["RevenueStatsChart", "UsageGrowthTimeline"],
            "chart_components": ["SimpleLineGraph", "ResponsiveBarWidget"],
            "realtime_dashboard_bindings": ["websocketConnectionStream -> updateZustandStoreData"]
          }},
          "form_generation": {{
            "generated_forms": ["LoginFormFields", "SignupFormFields"],
            "validation_integrations": ["Zod Schema validations matching form submit controls"],
            "submission_ui_flows": ["onSubmitAction -> toggleSubmittingStateSpinner"]
          }},
          "protected_ui_generation": {{
            "protected_components": ["AdminSettingsLayout", "BillingPanelWrapper"],
            "role_based_ui_rules": ["roleUser -> disableDashboardSettingsButton"],
            "session_visibility_bindings": ["useAuthStore.isAuthenticated -> renderDashboardSidebarView"]
          }},
          "responsive_generation": {{
            "responsive_components": ["MobileSidebarMenu", "ResponsiveGridLayout"],
            "mobile_adaptations": ["BottomTabMenuNavigation"],
            "adaptive_layout_rules": ["mdBreakpoint -> expandLeftSidebarDrawerMenu"]
          }},
          "loading_error_generation": {{
            "loading_components": ["CircularProgressLoadingIndicator", "DataLoadingCardSpinner"],
            "skeleton_components": ["DashboardSkeletonGrid", "FormInputPlaceholderSkeleton"],
            "error_state_components": ["SectionFailedLoadingMessage", "GlobalErrorFallbackBoundary"]
          }},
          "accessibility_generation": {{
            "accessibility_rules": ["ariaLabelAttrsOnActiveBreathingGuides", "colorContrastRatioTargetMinimum4.5"],
            "keyboard_navigation_rules": ["escKeyToCloseModalDialogs", "arrowKeysToSelectOptionItems"],
            "screen_reader_integrations": ["ariaLiveRegionToAnnounceTimerUpdates"]
          }},
          "shared_ui_utilities": {{
            "shared_hooks": ["useActiveThemeColors", "useDebounceSearchQuery"],
            "ui_helpers": ["cnClassNamesMerger", "formatDateRelativeString"],
            "component_abstractions": ["BasePrimitiveDialogShell"]
          }},
          "generation_dependencies": {{
            "blocking_components": ["app/layout.tsx", "components/Button.tsx"],
            "shared_dependencies": ["lucide-react", "framer-motion"],
            "cross_component_generation_rules": [
              "Design token primitives must compile first before components consume styling attributes."
            ]
          }},
          "future_generation_context": {{
            "important_notes_for_theme_generation": [
              "Tailwind CSS colors configurations must preserve HSL transparency scopes."
            ],
            "important_notes_for_state_generation": [
              "Zustand selectors should isolate components state to prevent unnecessary renders."
            ],
            "important_notes_for_integration_agents": [
              "Form submissions must enforce input length validations on the client side."
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
            logger.error(f"Failed to run UIComponentGenerationAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_ui_component_generation(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_ui_component_generation(
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
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive fallback configuration for Stage 21.
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

        shared_components = ["Button", "Input", "Card", "Badge", "Separator"]
        dashboard_components = ["SidebarNavigation", "DashboardHeader", "SummaryMetricCard"]
        form_components = ["LoginFormFields", "SignupFormFields"]
        navigation_components = ["TabsMenuSelector", "SidebarNavGroup"]
        modal_components = ["ConfirmActionDialog"]
        analytics_widgets = []
        chart_components = ["ResponsiveBarChart", "TrendLineWidget"]
        realtime_dashboard_bindings = ["webSocketConnectionStream -> updateDashboardViewports"]
        generated_forms = ["LoginForm", "SignupForm"]
        validation_integrations = ["Zod validations for credentials matches"]
        submission_ui_flows = ["onSubmit -> setSpinnerLoadingState"]
        protected_components = ["ProtectedDashboardLayout"]
        role_based_ui_rules = ["userPrivilegeRoleUser -> blockSettingsControlsEdit"]
        session_visibility_bindings = ["isAuthenticated -> renderSidebarNavigation"]
        responsive_components = ["MobileNavbar", "ResponsiveGridWrapper"]
        mobile_adaptations = ["BottomBarMobileNavigation"]
        adaptive_layout_rules = ["smBreakpoint -> toggleCollapsedSidebar"]
        loading_components = ["CircularLoadingSpinner"]
        skeleton_components = ["MetricCardSkeleton", "DashboardGridSkeleton"]
        error_state_components = ["LoadFailedBannerAlert", "GlobalErrorBoundaryBoundary"]
        shared_hooks = ["useThemeState", "useWebSocketUpdates"]
        ui_helpers = ["cnMerger", "formatDatetimeString"]
        component_abstractions = ["BaseModalShell"]

        for name in entity_names:
            plural = f"{name.lower()}s"
            dashboard_components.append(f"{name}CardRowWidget")
            form_components.append(f"Create{name}FormFields")
            form_components.append(f"Update{name}FormFields")
            modal_components.append(f"Create{name}ModalDialog")
            
            analytics_widgets.append(f"{name}SummaryOverviewWidget")
            analytics_widgets.append(f"{name}DistributionChart")
            
            generated_forms.append(f"Create{name}Form")
            generated_forms.append(f"Update{name}Form")
            validation_integrations.append(f"Zod validations for {name} payload fields")
            submission_ui_flows.append(f"submit{name}Action -> dispatchPOSTRequest")
            
            protected_components.append(f"Manage{name}AccessControl")
            role_based_ui_rules.append(f"adminRolePrivilege -> allowCreate{name}Button")
            session_visibility_bindings.append(f"userProfileInfo -> render{name}RowsData")
            
            responsive_components.append(f"{name}GridMobileLayout")
            mobile_adaptations.append(f"Swipeable{name}ActionMenu")
            adaptive_layout_rules.append(f"lgBreakpoint -> renderDetailed{name}Columns")
            
            skeleton_components.append(f"{name}ListSkeletonLoader")
            error_state_components.append(f"{name}NotFoundFallbackView")
            
            shared_hooks.append(f"use{name}Mutations")
            ui_helpers.append(f"format{name}MetadataPayload")
            component_abstractions.append(f"{name}PrimitiveRowAbstract")

        return {
            "status": "success",
            "ui_generation_strategy": {
                "component_architecture": "Atomic Component Architecture organizing UI elements into visual primitives.",
                "design_system_strategy": "TailwindCSS config token injection matching custom HSL palette mapping.",
                "responsive_strategy": "Fluid mobile-first responsive grids resizing into bottom navigation wrappers.",
                "ui_rendering_strategy": "Hybrid React Server Components (RSC) layout containing client-side interactive widgets."
            },
            "generated_components": {
                "shared_components": shared_components,
                "dashboard_components": dashboard_components,
                "form_components": form_components,
                "navigation_components": navigation_components,
                "modal_components": modal_components
            },
            "dashboard_generation": {
                "analytics_widgets": analytics_widgets,
                "chart_components": chart_components,
                "realtime_dashboard_bindings": realtime_dashboard_bindings
            },
            "form_generation": {
                "generated_forms": generated_forms,
                "validation_integrations": validation_integrations,
                "submission_ui_flows": submission_ui_flows
            },
            "protected_ui_generation": {
                "protected_components": protected_components,
                "role_based_ui_rules": role_based_ui_rules,
                "session_visibility_bindings": session_visibility_bindings
            },
            "responsive_generation": {
                "responsive_components": responsive_components,
                "mobile_adaptations": mobile_adaptations,
                "adaptive_layout_rules": adaptive_layout_rules
            },
            "loading_error_generation": {
                "loading_components": loading_components,
                "skeleton_components": skeleton_components,
                "error_state_components": error_state_components
            },
            "accessibility_generation": {
                "accessibility_rules": ["ariaLabelOnBreathingPacedRing", "colorContrastMinRatioRequirement4.5"],
                "keyboard_navigation_rules": ["escapeKeyToDismissModals", "tabIndexSequenceFocusControls"],
                "screen_reader_integrations": ["announceActiveMilestoneAlertMessage"]
            },
            "shared_ui_utilities": {
                "shared_hooks": shared_hooks,
                "ui_helpers": ui_helpers,
                "component_abstractions": component_abstractions
            },
            "generation_dependencies": {
                "blocking_components": ["app/layout.tsx", "components/Button.tsx"],
                "shared_dependencies": ["lucide-react", "framer-motion", "clsx"],
                "cross_component_generation_rules": [
                    "Design tokens are compiled first so that primitives resolve theme styles variables correctly."
                ]
            },
            "future_generation_context": {
                "important_notes_for_theme_generation": [
                    "Tailwind config must support standard HSL variables to match theme specifications."
                ],
                "important_notes_for_state_generation": [
                    "Always define type interfaces for components properties when binding stores values."
                ],
                "important_notes_for_integration_agents": [
                    "Ensure form handlers correctly toggle submission buttons loading indicators."
                ]
            }
        }
