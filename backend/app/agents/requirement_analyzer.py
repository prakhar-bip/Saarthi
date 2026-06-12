import json
from loguru import logger
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class RequirementAnalyzerAgent:
    """
    Requirement Analyzer Agent for Sarthi.
    Analyzes confirmed project blueprint and design theme, and extracts
    structured technical requirements for downstream AI agents.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "RequirementAnalyzerAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def analyze(self, blueprint: Dict[str, Any], theme: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze project blueprint and theme to extract requirements.
        """
        agent_inputs = {"blueprint": blueprint, "theme": theme}
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback requirements.")
            return enrich_agent_output(self._get_fallback_requirements(blueprint, theme), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior technical requirements analyst. Your job is to decompose a project blueprint into precise, actionable technical requirements that downstream architecture agents can consume without ambiguity.\n\n"
                "## Instructions\n"
                "1. Think step by step: first identify the project type and complexity, then infer the optimal tech stack, then enumerate features, modules, and integrations.\n"
                "2. Infer missing details pragmatically — choose sensible defaults for a hackathon MVP.\n"
                "3. Classify complexity as 'Low', 'Medium', or 'High' based on feature count, integrations, and auth needs.\n"
                "4. Populate every field — use empty arrays [] only when genuinely not applicable, never omit keys.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary, no extra keys.\n"
                "- tech_stack arrays must contain specific library/framework names, not categories.\n"
                "- features must be snake_case identifiers (max 30 chars each).\n"
                "- core_modules must be PascalCase module names.\n"
                "- project_workflow_summary must be 3-6 user-facing workflow sentences."
            )
        )

        user_content = f"""
Analyze the following project blueprint and design theme. Think step by step:
1. Identify the project domain, type, and complexity level.
2. Select specific technologies for each tech_stack category based on the blueprint.
3. Extract features as snake_case identifiers and core_modules as PascalCase names.
4. Determine authentication and database needs from the feature set.
5. Produce actionable recommendations for the downstream architecture agents.

Blueprint: {json.dumps(blueprint, indent=2)}
Theme: {theme or 'Slate Minimal'}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "project_overview": {{
    "name": "string — project name from blueprint",
    "type": "string — e.g. 'Fintech SaaS', 'E-commerce Platform', 'Social Network'",
    "description": "string — 1-2 sentence summary of the project purpose",
    "complexity": "string — one of: 'Low', 'Medium', 'High'"
  }},
  "tech_stack": {{
    "frontend": ["specific framework/library names, e.g. 'React', 'Tailwind CSS'"],
    "backend": ["specific framework names, e.g. 'FastAPI', 'Python'"],
    "database": ["specific DB names, e.g. 'PostgreSQL', 'Redis'"],
    "ai_tools": ["AI/ML libraries if needed, e.g. 'Scikit-learn', 'LangChain'"],
    "deployment": ["deployment tools, e.g. 'Docker', 'Vercel'"]
  }},
  "theme": {{
    "design_style": "string — the selected visual theme name",
    "ui_type": "string — e.g. 'Dashboard', 'Landing Page', 'Admin Panel'",
    "special_effects": ["string — CSS/animation effects, e.g. 'Smooth transitions'"]
  }},
  "features": ["snake_case feature identifiers, max 30 chars each"],
  "core_modules": ["PascalCase module names, e.g. 'Authentication', 'UserManagement'"],
  "authentication": {{
    "required": "boolean",
    "type": "string — e.g. 'JWT Session Auth', 'OAuth2', '' if not required"
  }},
  "database_requirements": {{
    "required": "boolean",
    "entities": ["entity names derived from features, e.g. 'User', 'Order'"],
    "storage_type": "string — 'Relational', 'Document', 'Key-Value', or ''"
  }},
  "api_integrations": ["external API/service names needed"],
  "scalability": {{
    "realtime_features": "boolean — true if WebSocket/SSE needed",
    "high_scalability_needed": "boolean",
    "microservices_ready": "boolean"
  }},
  "project_workflow_summary": ["3-6 sentences describing the end-to-end user journey"],
  "recommendations": ["2-4 actionable technical recommendations for downstream agents"]
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
            logger.error(f"Failed to run Requirement Analyzer Agent: {e}")
            return enrich_agent_output(self._get_fallback_requirements(blueprint, theme), self.agent_name, agent_inputs)

    def _get_fallback_requirements(self, blueprint: Dict[str, Any], theme: Optional[str] = None) -> Dict[str, Any]:
        name = blueprint.get("name", "Saarthi Project")
        idea = blueprint.get("idea", "A customized Sarthi application.")
        features = blueprint.get("features", [])
        tech_stack_str = blueprint.get("tech_stack", "")

        # Try to infer some parameters from tech_stack_str
        tech_lower = tech_stack_str.lower() if tech_stack_str else ""
        
        frontend = ["React", "Tailwind CSS"]
        if "next" in tech_lower:
            frontend.append("Next.js")
        
        backend = ["FastAPI", "Python", "Uvicorn"]
        if "django" in tech_lower:
            backend = ["Django", "Python"]
        elif "express" in tech_lower or "node" in tech_lower:
            backend = ["Express", "Node.js"]

        database = ["MongoDB"]
        if "postgres" in tech_lower:
            database = ["PostgreSQL"]
        elif "mysql" in tech_lower:
            database = ["MySQL"]
        elif "sqlite" in tech_lower:
            database = ["SQLite"]

        db_type = "Document"
        if any(db in tech_lower for db in ["postgres", "mysql", "sqlite", "sql"]):
            db_type = "Relational"

        feature_identifiers = []
        core_modules = ["Authentication"]
        for f in features:
            fid = f.lower().replace(" ", "_").replace("-", "_").replace(",", "")[:30]
            feature_identifiers.append(fid)
            # Infer a module name in PascalCase
            words = [w.capitalize() for w in f.replace("-", " ").replace("_", " ").split() if w]
            module_name = "".join(words)[:20]
            if module_name and module_name not in core_modules and len(module_name) > 3:
                core_modules.append(module_name)
        
        if not feature_identifiers:
            feature_identifiers = ["dashboard_view", "user_profile"]
            core_modules.append("Dashboard")

        db_req = {
            "required": True,
            "entities": [m for m in core_modules if m != "Authentication"],
            "storage_type": db_type
        }
        if not db_req["entities"]:
            db_req["entities"] = ["Item"]

        return {
            "status": "success",
            "project_overview": {
                "name": name,
                "type": "Custom Application",
                "description": idea,
                "complexity": "Medium"
            },
            "tech_stack": {
                "frontend": frontend,
                "backend": backend,
                "database": database,
                "ai_tools": ["LangChain"] if "ai" in tech_lower or "gemini" in tech_lower else [],
                "deployment": ["Docker"]
            },
            "theme": {
                "design_style": theme or "Minimal Slate",
                "ui_type": "Dashboard",
                "special_effects": ["Smooth transitions"]
            },
            "features": feature_identifiers,
            "core_modules": core_modules,
            "authentication": {
                "required": True,
                "type": "JWT Session Auth"
            },
            "database_requirements": db_req,
            "api_integrations": [],
            "scalability": {
                "realtime_features": "websocket" in tech_lower or "socket" in tech_lower,
                "high_scalability_needed": False,
                "microservices_ready": False
            },
            "project_workflow_summary": [
                "User logs in and authenticates.",
                f"User navigates to the dashboard of {name}.",
                "User interacts with core features and views real-time data integrations."
            ],
            "recommendations": [
                "Implement secure encryption for passwords and user profiles.",
                "Ensure proper error boundaries are set up on the frontend."
            ]
        }
