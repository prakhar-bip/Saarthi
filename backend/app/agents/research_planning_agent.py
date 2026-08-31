import json
from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import enrich_agent_output, parse_json_response, generate_agent_prompt

class ResearchPlanningAgent:
    """
    ResearchPlanningAgent for Sarthi.
    Performs environment and requirement research, generates a detailed implementation
    plan, and creates the implementation_plan.md blueprint.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "ResearchPlanningAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def generate_plan(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        codebase: List[Dict[str, Any]],
        generation_type: str = "full_stack"
    ) -> Dict[str, Any]:
        """
        Generate a detailed implementation plan based on requirements, plan, and current files.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "codebase_summary": [{"name": f["name"], "path": f["path"]} for f in codebase],
            "generation_type": generation_type
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_plan(requirements, planning, codebase, generation_type), self.agent_name, agent_inputs)

        # Construct state dict for dynamic prompt generation
        state = {
            "requirements": requirements,
            "planning": planning,
            "implementation_plan": {
                "codebase_summary": [{"name": f["name"], "path": f["path"]} for f in codebase]
            },
            "generation_type": generation_type
        }
        system_prompt = generate_agent_prompt(self.agent_name, state)

        user_content = f"""
Analyze the project requirements, design theme styling, target audience, and current files list, then produce a highly dynamic file-by-file implementation plan for the target scope: '{generation_type}'.

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Current Files: {json.dumps(agent_inputs["codebase_summary"], indent=2)}

Crucial Dynamic Design & Scope Constraints:
1. Dynamic Theme Integration: Inspect the theme palette and styling details (`requirements.theme`). In the `plan_markdown` and file descriptions, explicitly mandate that UI components, layouts, and style pages apply this specific color theme (e.g. primary/secondary colors, background, dark/light settings) to achieve a cohesive, beautiful design.
2. Target Audience Alignment: Inspect the `requirements.project_overview.target_audience`. Ensure the UI layouts, copy style, feature flow, and page spacing described in the plan are optimized specifically to match this audience's personas and preferences.
3. Scope Constraint:
   - The project is '{generation_type}'.
   - If '{generation_type}' is 'frontend_only', your implementation plan MUST only create or modify frontend files (inside 'frontend/'). Do NOT propose backend files, databases, or main.py.
   - If '{generation_type}' is 'backend_only' or 'microservice', your implementation plan MUST only create or modify backend/DB files (inside 'backend/'). Do NOT propose UI pages, React elements, or package.json files.

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "plan_markdown": "string — A detailed Markdown document detailing the implementation steps (e.g. Database changes, backend routes, frontend UI updates with design theme settings, and verification checks)",
  "proposed_changes": [
    {{
      "path": "string — absolute or relative file path, e.g. 'backend/app/models.py'",
      "action": "string — 'create' or 'modify'",
      "description": "string — description of what will be added or changed"
    }}
  ],
  "recommended_sdlc": "string — one of: agile, waterfall, v_model, spiral, kanban. Choose based on: complexity (high=spiral/waterfall), compliance/safety-critical=v_model, startup/MVP/fast-iteration=agile, continuous flow/support=kanban",
  "sdlc_reasoning": "string — 1-2 sentences explaining why this SDLC was chosen for this project",
  "implementation_phases": [
    {{
      "phase_name": "string — e.g. Phase 1: Core Authentication",
      "deliverables": ["string"]
    }}
  ]
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
            return enrich_agent_output(self._get_fallback_plan(requirements, planning, codebase, generation_type), self.agent_name, agent_inputs)

    def _get_fallback_plan(self, requirements: Dict[str, Any], planning: Dict[str, Any], codebase: List[Dict[str, Any]], generation_type: str = "full_stack") -> Dict[str, Any]:
        proj_name = requirements.get("project_overview", {}).get("name", "Project")
        target_audience = requirements.get("project_overview", {}).get("target_audience", "General Users")
        theme_info = requirements.get("theme", {})
        design_style = theme_info.get("design_style", "Slate Minimal")
        palette = theme_info.get("theme_palette", {})
        palette_desc = f"Palette: {json.dumps(palette)}" if palette else "Standard colors"
        
        if generation_type == "frontend_only":
            plan_markdown = f"""# Implementation Plan: {proj_name} (Frontend Only)

This implementation plan is compiled by Sarthi's Research & Planning Agent for a Frontend-Only workspace.

## 🎨 Design & Styling Constraints (Dynamic)
- **Theme**: {design_style} ({palette_desc})
- **Target Audience & Personas**: {target_audience}

## 🎨 Frontend UI & Components
- **Layout**: Setup pages and navigation.
- **UI Components**: Implement dashboard tiles, form editors, and tables using dynamic theme styling: {palette_desc}.
"""
            proposed_changes = [
                {"path": "frontend/src/app/page.tsx", "action": "modify", "description": f"Develop main dashboard UI and workspace views matching theme '{design_style}' and targeting '{target_audience}'"}
            ]
        elif generation_type in ("backend_only", "microservice"):
            plan_markdown = f"""# Implementation Plan: {proj_name} (Backend Only)

This implementation plan is compiled by Sarthi's Research & Planning Agent for a Headless/Backend-Only workspace.

## 🗄️ Database & Schema Changes
- **Models**: Configure appropriate database model files (e.g. SQLAlchemy models or Motor collection schemes) based on derived entities.
- **Relationships**: Define One-to-Many and Many-to-Many relationships among tables.

## ⚙️ Backend & API endpoints
- **API Routes**: Create route definitions for core feature operations (CRUD endpoints).
- **Security**: Implement token-based authentication and endpoint security filters.
"""
            proposed_changes = [
                {"path": "backend/app/models.py", "action": "modify" if codebase else "create", "description": "Configure core entity schema models"},
                {"path": "backend/app/main.py", "action": "modify", "description": "Expose router endpoints and initialize middleware"}
            ]
        else:
            plan_markdown = f"""# Implementation Plan: {proj_name}

This implementation plan is compiled by Sarthi's Research & Planning Agent.

## 🎨 Design & Styling Constraints (Dynamic)
- **Theme**: {design_style} ({palette_desc})
- **Target Audience & Personas**: {target_audience}

## 🗄️ Database & Schema Changes
- **Models**: Configure appropriate database model files (e.g. SQLAlchemy models or Motor collection schemes) based on derived entities.
- **Relationships**: Define One-to-Many and Many-to-Many relationships among tables.

## ⚙️ Backend & API endpoints
- **API Routes**: Create route definitions for core feature operations (CRUD endpoints).
- **Security**: Implement token-based authentication and endpoint security filters.

## 🎨 Frontend UI & Components
- **Layout**: Setup pages and navigation.
- **UI Components**: Implement dashboard tiles, form editors, and tables using Tailwind CSS styling matching theme '{design_style}'.
"""
            proposed_changes = [
                {"path": "backend/app/models.py", "action": "modify" if codebase else "create", "description": "Configure core entity schema models"},
                {"path": "backend/app/main.py", "action": "modify", "description": "Expose router endpoints and initialize middleware"},
                {"path": "frontend/src/app/page.tsx", "action": "modify", "description": f"Develop main dashboard UI and workspace views matching theme '{design_style}' and targeting '{target_audience}'"}
            ]
        
        return {
            "status": "success",
            "plan_markdown": plan_markdown,
            "proposed_changes": proposed_changes,
            "recommended_sdlc": "agile",
            "sdlc_reasoning": "Default fallback: Agile is recommended for most projects when SDLC cannot be determined.",
            "implementation_phases": [
                {"phase_name": "Phase 1: Core Setup", "deliverables": ["Database models", "Core API routes"]},
                {"phase_name": "Phase 2: Features", "deliverables": ["Feature modules", "UI pages"]}
            ]
        }
