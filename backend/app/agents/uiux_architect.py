import json
from loguru import logger
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


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
            (
                "## Role\n"
                "You are a senior UI/UX design system architect. Create a complete visual design system: color palette, typography, spacing, component styling, animations, accessibility rules, and Tailwind/shadcn configuration — all derived from the project's theme preference.\n\n"
                "## Instructions\n"
                "1. Think step by step: read the theme from requirements.theme.design_style → derive a cohesive color palette (primary, secondary, accent, status colors as hex values) → define typography (font families, heading/body styles) → design component styling rules → set responsive breakpoints → define motion/animation patterns → ensure WCAG AA accessibility.\n"
                "2. color_palette must use valid hex color codes (e.g. '#10b981'), NOT color names.\n"
                "3. component_styling_system must cover at minimum: Button, Input, CardPanel. Each with TailwindCSS utility classes.\n"
                "4. All styling rules must be valid TailwindCSS class strings.\n"
                "5. visual_workflows must correspond to frontend_architecture.frontend_workflows — same workflow names, but describing the visual/animation aspects.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- Color values must be 6-digit hex codes (e.g. '#10b981'), not CSS names or RGB.\n"
                "- Font families must be real Google Font or system font names.\n"
                "- accessibility_system.contrast_rules must reference WCAG AA (4.5:1 minimum for text)."
            )
        )

        user_content = f"""
Design the complete UI/UX design system for this project. Think step by step:
1. Read the theme from requirements.theme.design_style and derive a matching color palette (3 primary, 3 secondary, 2 accent, 2 background, 3 text, 4 status colors — all as hex codes).
2. Select font families that match the theme mood (e.g. geometric sans-serif for modern, rounded for friendly).
3. Define component styling for at minimum: Button, Input, CardPanel — each with TailwindCSS utility classes and interactive states (hover, focus, active, disabled).
4. Create visual_workflows that match frontend_architecture.frontend_workflows by the same workflow_name but describe the animation/visual behavior.
5. Ensure all contrast ratios meet WCAG AA (4.5:1 minimum for normal text).

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "design_system": {{
    "design_style": "string — theme name, e.g. 'Minimal Emerald', 'Slate Soft Glow'",
    "ui_philosophy": "string — 1 sentence describing the visual personality",
    "theme_strategy": "string — how the theme is implemented (e.g. 'TailwindCSS custom palette')",
    "component_styling_approach": "string — component library strategy (e.g. 'shadcn/ui with custom tokens')"
  }},
  "color_palette": {{
    "primary_colors": ["string — 3 hex codes, darkest to lightest, e.g. '#047857', '#059669', '#10b981'"],
    "secondary_colors": ["string — 3 hex codes for backgrounds/surfaces"],
    "accent_colors": ["string — 2 hex codes for highlights/CTAs"],
    "background_colors": ["string — 2 hex codes for page/card backgrounds"],
    "text_colors": ["string — 3 hex codes: heading, body, muted"],
    "status_colors": {{
      "success": "string — hex code",
      "warning": "string — hex code",
      "error": "string — hex code",
      "info": "string — hex code"
    }}
  }},
  "typography_system": {{
    "font_families": ["string — real Google Font or system font names"],
    "heading_styles": ["string — TailwindCSS heading class combinations"],
    "body_styles": ["string — TailwindCSS body text class combinations"],
    "responsive_typography": "boolean"
  }},
  "spacing_layout_system": {{
    "spacing_scale": ["string — rem values in ascending order"],
    "container_rules": ["string — TailwindCSS container utility classes"],
    "grid_strategy": "string — grid system description",
    "layout_consistency_rules": ["string — visual consistency rules"]
  }},
  "component_styling_system": [
    {{
      "component_type": "string — component name: Button, Input, CardPanel, etc.",
      "styling_rules": ["string — TailwindCSS base utility classes"],
      "interactive_states": ["string — TailwindCSS hover:/focus:/active:/disabled: variants"]
    }}
  ],
  "responsive_design_system": {{
    "mobile_strategy": "string — mobile layout approach",
    "tablet_strategy": "string — tablet layout approach",
    "desktop_strategy": "string — desktop layout approach",
    "breakpoints": ["string — TailwindCSS breakpoint definitions"]
  }},
  "animation_motion_system": {{
    "animation_style": "string — animation library/approach",
    "transition_rules": ["string — timing/easing specifications"],
    "interactive_animations": ["string — named animation patterns"],
    "motion_principles": ["string — UX motion design rules"]
  }},
  "theme_modes": {{
    "dark_mode_supported": "boolean",
    "light_mode_supported": "boolean",
    "theme_switching_strategy": ["string — how theme mode is detected/toggled"]
  }},
  "dashboard_styling": {{
    "dashboard_theme": "string — dashboard visual style name",
    "widget_styles": ["string — TailwindCSS classes for dashboard widgets"],
    "analytics_ui_patterns": ["string — chart/metric component pattern names"]
  }},
  "accessibility_system": {{
    "contrast_rules": ["string — WCAG compliance requirements"],
    "keyboard_navigation_support": "boolean",
    "accessibility_features": ["string — ARIA, screen reader, focus management features"]
  }},
  "tailwind_shadcn_architecture": {{
    "tailwind_strategy": ["string — tailwind.config.js customization steps"],
    "shadcn_components": ["string — shadcn/ui component names to configure"],
    "utility_patterns": ["string — custom utility class pattern names"]
  }},
  "visual_workflows": [
    {{
      "workflow_name": "string — MUST match a frontend_architecture.frontend_workflows[].workflow_name",
      "visual_flow": ["string — ordered animation/visual steps for this workflow"]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_ui_generation": ["string — color/theme application guidance"],
    "important_notes_for_component_generation": ["string — component styling guidance"],
    "important_notes_for_frontend_code_generation": ["string — font/asset import guidance"]
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
