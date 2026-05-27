import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

class UIUXArchitectAgent:
    """
    UIUXArchitectAgent for Sarthi.
    Designs global styling frameworks, Tailwind tokens, typography, component styling states, animations, and visual workflows.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "UIUXArchitectAgent"

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
        frontend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze requirements, planning, db, backend, api, and frontend outputs to design the visual UI/UX styling system.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback UI/UX design styling.")
            return enrich_agent_output(self._get_fallback_theme_styling(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design the UI/UX styling architecture, visual workflows, accessibility rules, theme tokens, typography, motion, and responsive behavior."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "design_system": {{
    "design_style": "e.g. Minimal Emerald / Slate Soft Glow",
    "ui_philosophy": "e.g. Calming wellness-focused UI with spacious typography and smooth state fades.",
    "theme_strategy": "e.g. TailwindCSS custom palette config mapping semantic color names.",
    "component_styling_approach": "e.g. shadcn/ui primitive configuration with custom micro-shadow utilities."
  }},
  "color_palette": {{
    "primary_colors": ["#10b981", "#059669", "#047857"],
    "secondary_colors": ["#f0fdf4", "#d1fae5", "#a7f3d0"],
    "accent_colors": ["#3b82f6", "#60a5fa"],
    "background_colors": ["#fafafa", "#ffffff"],
    "text_colors": ["#0f172a", "#334155", "#64748b"],
    "status_colors": {{
      "success": "#10b981",
      "warning": "#f59e0b",
      "error": "#ef4444",
      "info": "#3b82f6"
    }}
  }},
  "typography_system": {{
    "font_families": ["Outfit", "Inter", "ui-sans-serif"],
    "heading_styles": ["font-display text-slate-900 tracking-tight font-bold"],
    "body_styles": ["font-sans text-slate-600 antialiased"],
    "responsive_typography": true
  }},
  "spacing_layout_system": {{
    "spacing_scale": ["0.25rem", "0.5rem", "1rem", "1.5rem", "2rem", "3rem"],
    "container_rules": ["max-w-4xl mx-auto px-4 sm:px-6 lg:px-8"],
    "grid_strategy": "12-column responsive flexbox layouts with gap-6 spacing",
    "layout_consistency_rules": ["Align headers to central viewport grids", "Inject uniform cards border-radius tokens"]
  }},
  "component_styling_system": [
    {{
      "component_type": "Button",
      "styling_rules": ["px-4 py-2 rounded-xl transition-all select-none hover:scale-[1.01]"],
      "interactive_states": ["hover:shadow-sm", "focus:ring-2 focus:ring-emerald-500", "active:scale-[0.99]"]
    }}
  ],
  "responsive_design_system": {{
    "mobile_strategy": "Fluid single column container grids with bottom bar navigations.",
    "tablet_strategy": "Flexible dual sidebar triggers.",
    "desktop_strategy": "Side-by-side dashboard viewports.",
    "breakpoints": ["sm: 640px", "md: 768px", "lg: 1024px"]
  }},
  "animation_motion_system": {{
    "animation_style": "Framer Motion spring animations",
    "transition_rules": ["duration: 0.3s, ease: easeInOut"],
    "interactive_animations": ["pulse_expand", "slide_up"],
    "motion_principles": ["Avoid sudden layout shifts", "Align scaling limits to a maximum of 5% increment"]
  }},
  "theme_modes": {{
    "dark_mode_supported": false,
    "light_mode_supported": true,
    "theme_switching_strategy": ["Read media settings preference on mount"]
  }},
  "dashboard_styling": {{
    "dashboard_theme": "Dashboard styling preference name",
    "widget_styles": ["border border-slate-100 shadow-sm p-6 rounded-2xl bg-white"],
    "analytics_ui_patterns": ["SummaryStatCardsGrid", "TrendChartTimelineWrapper"]
  }},
  "accessibility_system": {{
    "contrast_rules": ["Contrast ratio target minimum 4.5:1"],
    "keyboard_navigation_support": true,
    "accessibility_features": ["Aria attributes for custom UI controls", "Screen-reader friendly text logs"]
  }},
  "tailwind_shadcn_architecture": {{
    "tailwind_strategy": ["Extend themes inside tailwind.config.js"],
    "shadcn_components": ["Button", "Dialog", "Card", "Progress"],
    "utility_patterns": ["glassmorphic_card_bg", "soothing_green_gradient"]
  }},
  "visual_workflows": [
    {{
      "workflow_name": "Submit log entry",
      "visual_flow": [
        "Open Form Dialog with slight spring transition.",
        "Fade out form and pop green checklist checkmark on success."
      ]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_ui_generation": [],
    "important_notes_for_component_generation": [],
    "important_notes_for_frontend_code_generation": []
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
            logger.error(f"Failed to run UIUXArchitectAgent: {e}")
            return enrich_agent_output(self._get_fallback_theme_styling(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

    def _get_fallback_theme_styling(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        proj_name = overview.get("name", "FinSight")
        theme_preference = requirements.get("theme", {}).get("design_style", "Minimal Slate")
        
        # Determine base colors depending on selected theme guidelines
        primary_color = "#10b981" # Emerald default
        secondary_bg = "#f0fdf4"
        accent_color = "#3b82f6"
        card_border = "#e2e8f0"
        
        lower_theme = theme_preference.lower()
        if "blue" in lower_theme or "ocean" in lower_theme:
            primary_color = "#3b82f6" # Blue
            secondary_bg = "#eff6ff"
            accent_color = "#10b981"
        elif "purple" in lower_theme or "indigo" in lower_theme:
            primary_color = "#6366f1" # Indigo
            secondary_bg = "#f5f3ff"
            accent_color = "#ec4899"
        elif "amber" in lower_theme or "orange" in lower_theme:
            primary_color = "#f59e0b" # Amber
            secondary_bg = "#fef3c7"
            accent_color = "#10b981"
        elif "red" in lower_theme or "rose" in lower_theme:
            primary_color = "#f43f5e" # Rose
            secondary_bg = "#fff1f2"
            accent_color = "#6366f1"

        # Read pages from frontend structure if available
        pages_list = [p.get("page_name") for p in frontend_architecture.get("pages", [])] if frontend_architecture else ["Dashboard"]
        
        # Read workflows
        workflows = []
        fe_workflows = frontend_architecture.get("frontend_workflows", []) if frontend_architecture else []
        for wf in fe_workflows:
            wf_name = wf.get("workflow_name", "Submit form")
            workflows.append({
                "workflow_name": wf_name,
                "visual_flow": [
                    f"Initiate {wf_name} event on element click trigger.",
                    "Animate submission loader spinner overlay.",
                    "Slide in green check badge status indicator."
                ]
            })

        if not workflows:
            workflows.append({
                "workflow_name": "Standard workspace submission",
                "visual_flow": [
                    "Open form block modal container.",
                    "Verify state errors highlighting borders red.",
                    "Save record and show clean alert header."
                ]
            })

        return {
            "status": "success",
            "design_system": {
                "design_style": f"{theme_preference} Theme System Blueprint",
                "ui_philosophy": "Modern clean SaaS user dashboard focusing on high readability, modular cards, and subtle border radius indicators.",
                "theme_strategy": "Extended custom configuration for tailwind.config.js semantic selectors.",
                "component_styling_approach": "Atomic tailwind components styled using standard classes and consistent hover state shadows."
            },
            "color_palette": {
                "primary_colors": [primary_color, f"{primary_color}dd", f"{primary_color}bb"],
                "secondary_colors": [secondary_bg, "#f8fafc", "#f1f5f9"],
                "accent_colors": [accent_color, f"{accent_color}cc"],
                "background_colors": ["#ffffff", "#f8fafc"],
                "text_colors": ["#0f172a", "#475569", "#94a3b8"],
                "status_colors": {
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "info": "#3b82f6"
                }
            },
            "typography_system": {
                "font_families": ["Inter", "Outfit", "ui-sans-serif", "system-ui"],
                "heading_styles": ["font-semibold tracking-tight text-slate-900"],
                "body_styles": ["text-slate-600 antialiased font-normal"],
                "responsive_typography": True
            },
            "spacing_layout_system": {
                "spacing_scale": ["0.25rem", "0.5rem", "1rem", "1.5rem", "2rem", "3.5rem"],
                "container_rules": ["max-w-6xl mx-auto px-4 md:px-6 lg:px-8"],
                "grid_strategy": "Flexible flex grids and responsive 12-column breakpoints.",
                "layout_consistency_rules": [
                    "Implement a uniform border-radius of 1rem for standard components.",
                    "Configure cards borders with 1px thickness mapping slate-100 colors."
                ]
            },
            "component_styling_system": [
                {
                    "component_type": "Button",
                    "styling_rules": ["px-4 py-2 rounded-xl transition-all cursor-pointer font-medium text-xs shadow-sm"],
                    "interactive_states": ["hover:shadow-md", "focus:ring-2 focus:ring-offset-2", "disabled:opacity-50"]
                },
                {
                    "component_type": "Input",
                    "styling_rules": ["w-full px-3.5 py-2 border rounded-xl bg-slate-50/50 text-xs transition-all"],
                    "interactive_states": ["focus:ring-1 focus:ring-indigo-500", "focus:border-indigo-500"]
                },
                {
                    "component_type": "CardPanel",
                    "styling_rules": ["bg-white p-6 border rounded-2xl shadow-sm hover:shadow-md transition-all"],
                    "interactive_states": ["hover:border-slate-200"]
                }
            ],
            "responsive_design_system": {
                "mobile_strategy": "Stack layout modules vertically, replacing sidebar navigation with collapsible hamburger items.",
                "tablet_strategy": "Maintain dual side layouts with reduced margins.",
                "desktop_strategy": "Renders two column responsive dashboard cards list viewports.",
                "breakpoints": ["sm: 640px", "md: 768px", "lg: 1024px", "xl: 1280px"]
            },
            "animation_motion_system": {
                "animation_style": "Framer Motion spring presets",
                "transition_rules": ["duration: 0.25s, type: spring, stiffness: 120"],
                "interactive_animations": [
                    "button_hover_scale",
                    "sidebar_slide_in_overlay",
                    "dialog_fade_in_zoom"
                ],
                "motion_principles": [
                    "Incorporate micro-animations sparingly to prevent visual fatigue.",
                    "Use hardware-accelerated transform translates on interactive cards scaling."
                ]
            },
            "theme_modes": {
                "dark_mode_supported": False,
                "light_mode_supported": True,
                "theme_switching_strategy": ["Enforce light theme settings context by default."]
            },
            "dashboard_styling": {
                "dashboard_theme": f"{theme_preference} Console Layout Style",
                "widget_styles": ["border border-slate-100 p-5 rounded-2xl shadow-sm bg-white"],
                "analytics_ui_patterns": [
                    "SummaryStatsHeaderList",
                    "LineTrendsTimelineWrapper",
                    "RecentActivityTimelineList"
                ]
            },
            "accessibility_system": {
                "contrast_rules": ["Ensure text labels satisfy WCAG AA 4.5:1 contrast metrics."],
                "keyboard_navigation_support": True,
                "accessibility_features": [
                    "Include focus outline rings on interactive inputs focus.",
                    "Inject descriptive alt text into custom graphics nodes."
                ]
            },
            "tailwind_shadcn_architecture": {
                "tailwind_strategy": ["Extend tailwind primary theme colors configurations."],
                "shadcn_components": ["Button", "Input", "Card", "Tabs", "Dialog"],
                "utility_patterns": [
                    "soothing_gradient_mesh",
                    "interactive_spring_fade"
                ]
            },
            "visual_workflows": workflows,
            "future_generation_context": {
                "important_notes_for_ui_generation": [
                    f"Consistently apply theme coloring matching {primary_color} to highlight stats."
                ],
                "important_notes_for_component_generation": [
                    "Implement semantic theme CSS variable names for elements background colors."
                ],
                "important_notes_for_frontend_code_generation": [
                    "Import Outfit and Inter web fonts inside document head templates."
                ]
            }
        }
