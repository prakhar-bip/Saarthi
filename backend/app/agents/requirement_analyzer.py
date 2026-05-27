import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

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
            "Analyze a confirmed software project blueprint and extract structured technical requirements for every downstream architecture agent."
        )

        user_content = f"""
Analyze the following project blueprint and theme:
Blueprint: {json.dumps(blueprint, indent=2)}
Theme: {theme or 'Slate Minimal'}

Return ONLY valid JSON in this format:
{{
  "status": "success",
  "project_overview": {{
    "name": "Project Name",
    "type": "Project Type",
    "description": "Short Description",
    "complexity": "Complexity Level"
  }},
  "tech_stack": {{
    "frontend": [],
    "backend": [],
    "database": [],
    "ai_tools": [],
    "deployment": []
  }},
  "theme": {{
    "design_style": "Theme Style",
    "ui_type": "UI Type",
    "special_effects": []
  }},
  "features": [],
  "core_modules": [],
  "authentication": {{
    "required": false,
    "type": ""
  }},
  "database_requirements": {{
    "required": false,
    "entities": [],
    "storage_type": ""
  }},
  "api_integrations": [],
  "scalability": {{
    "realtime_features": false,
    "high_scalability_needed": false,
    "microservices_ready": false
  }},
  "project_workflow_summary": [],
  "recommendations": []
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
        name = blueprint.get("name", "FinSight")
        idea = blueprint.get("idea", "")
        features = blueprint.get("features", [])
        tech_stack = blueprint.get("tech_stack", "")

        frontend = []
        backend = []
        database = []
        ai_tools = []
        
        tech_stack_lower = tech_stack.lower()
        if "react" in tech_stack_lower:
            frontend.append("React")
        if "tailwind" in tech_stack_lower:
            frontend.append("Tailwind CSS")
        if "node" in tech_stack_lower:
            backend.append("Node.js")
        if "express" in tech_stack_lower:
            backend.append("Express")
        if "postgresql" in tech_stack_lower:
            database.append("PostgreSQL")
            db_req = {"required": True, "entities": ["User", "Portfolio", "Asset", "Transaction"], "storage_type": "Relational"}
        elif "mongodb" in tech_stack_lower:
            database.append("MongoDB")
            db_req = {"required": True, "entities": ["User", "Portfolio", "Asset", "Transaction"], "storage_type": "NoSQL"}
        else:
            db_req = {"required": False, "entities": [], "storage_type": ""}
            
        if "python" in tech_stack_lower:
            backend.append("Python")
        if "scikit-learn" in tech_stack_lower:
            ai_tools.append("Scikit-learn")
        if "nvidia" in tech_stack_lower or "nim" in tech_stack_lower:
            ai_tools.append("Nvidia NIM")

        feature_identifiers = []
        for f in features:
            fid = f.lower().replace(" ", "_").replace("-", "_").replace(",", "")
            feature_identifiers.append(fid[:30])

        return {
            "status": "success",
            "project_overview": {
                "name": name,
                "type": "Fintech / Micro-investment SaaS",
                "description": idea,
                "complexity": "Medium"
            },
            "tech_stack": {
                "frontend": frontend,
                "backend": backend,
                "database": database,
                "ai_tools": ai_tools,
                "deployment": ["Docker", "Vercel / Render"]
            },
            "theme": {
                "design_style": theme or "Minimal Slate",
                "ui_type": "Dashboard",
                "special_effects": ["Smooth transitions", "Animated progress circles"]
            },
            "features": feature_identifiers,
            "core_modules": ["Authentication", "Portfolio Management", "AI Recommendations", "Gamified Learning"],
            "authentication": {
                "required": True,
                "type": "JWT Session Auth"
            },
            "database_requirements": db_req,
            "api_integrations": ["ETF pricing feeds"],
            "scalability": {
                "realtime_features": False,
                "high_scalability_needed": False,
                "microservices_ready": False
            },
            "project_workflow_summary": [
                "User authenticates and completes AI-driven risk assessment",
                "App suggests personalized portfolio allocation using Python and Scikit-learn",
                "User configures micro-savings to auto-convert into diversified ETFs",
                "User participates in gamified educational challenges and tracks leaderboard points"
            ],
            "recommendations": [
                "Use a secure banking aggregator API like Plaid for micro-savings auto-conversion",
                "Implement robust encryption for portfolios and user financial data"
            ]
        }
