import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class PlannerAgent:
    """
    Planner Agent for Sarthi.
    Transforms structured technical requirements into a complete build & orchestration strategy
    for downstream generator agents.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "PlannerAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze requirements to generate a complete execution and orchestration plan.
        """
        agent_inputs = {"requirements": requirements}
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_planning(requirements), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a software build planner. Output a compact, deterministic execution plan with phases, module DAG, and agent scheduling.\n\n"
                "## Constraints\n"
                "- Output ONLY strict valid JSON. No conversational commentary, no markdown code blocks.\n"
                "- Keep descriptions brief (max 15 words per item).\n"
                "- module_execution_order must be topologically sorted.\n"
                "- recommended_next_agents must list the direct downstream architecture agents."
            )
        )

        user_content = f"""
Requirements: {json.dumps(requirements, default=str)}

Return ONLY valid JSON with this exact compact structure:
{{
  "status": "success",
  "execution_strategy": {{
    "project_type": "string — from requirements",
    "architecture_style": "Client-Server Modular",
    "development_strategy": "Database-first with parallel frontend/backend logic",
    "scalability_strategy": "Stateless horizontal scaling with cached reads"
  }},
  "project_phases": [
    {{
      "phase": 1,
      "title": "Data & Backend Architecture",
      "description": "Define data models, database schemas, and REST endpoints.",
      "tasks": ["Design schema entities", "Map API endpoints"],
      "expected_output": ["Database models", "API schemas"]
    }},
    {{
      "phase": 2,
      "title": "Frontend & UI/UX Assembly",
      "description": "Design pages, layouts, and component state bindings.",
      "tasks": ["Theme token design", "Component hierarchy"],
      "expected_output": ["UI wireframes", "State management"]
    }},
    {{
      "phase": 3,
      "title": "Security, Operations & Code Synthesis",
      "description": "Implement auth guards, testing suites, and compile codebase.",
      "tasks": ["Auth validation", "Code synthesis"],
      "expected_output": ["Complete production codebase"]
    }}
  ],
  "module_execution_order": ["string — module names"],
  "parallel_execution_groups": [["string — independent modules"]],
  "module_dependencies": [{{"module": "string", "depends_on": ["string"]}}],
  "agent_execution_plan": [
    {{"agent": "DatabaseArchitectureAgent", "responsibility": "Database schemas", "execution_stage": "Phase 1"}},
    {{"agent": "BackendArchitectureAgent", "responsibility": "Backend services", "execution_stage": "Phase 1"}},
    {{"agent": "APIAgent", "responsibility": "API endpoints", "execution_stage": "Phase 1"}},
    {{"agent": "FrontendArchitectureAgent", "responsibility": "UI architecture", "execution_stage": "Phase 2"}},
    {{"agent": "UIUXArchitectAgent", "responsibility": "Theme and styling", "execution_stage": "Phase 2"}},
    {{"agent": "AuthArchitectureAgent", "responsibility": "Auth & RBAC", "execution_stage": "Phase 3"}}
  ],
  "compilation_pipeline": [
    {{"stage": "Architecture Design", "purpose": "Data and service contracts"}},
    {{"stage": "Code Synthesis", "purpose": "File generation and validation"}}
  ],
  "system_workflow": {{
    "initialization": ["Initialize DB connections and auth keys"],
    "backend_flow": ["Route requests through JWT validation to services"],
    "frontend_flow": ["Render dashboard with reactive state"],
    "integration_flow": ["Process async background tasks"]
  }},
  "risk_analysis": {{
    "complex_modules": ["Core business logic"],
    "potential_bottlenecks": ["External API rate limits"],
    "optimization_suggestions": ["Use response caching"]
  }},
  "recommended_next_agents": ["DatabaseArchitectureAgent", "FrontendArchitectureAgent", "UIUXArchitectAgent"]
}}
"""

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
            return enrich_agent_output(self._get_fallback_planning(requirements), self.agent_name, agent_inputs)

    def _get_fallback_planning(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        name = overview.get("name", "Sarthi Project")
        p_type = overview.get("type", "Web App")
        modules = requirements.get("core_modules", ["Core"])
        features = requirements.get("features", [])
        
        # Build logical execution sequence
        execution_order = []
        dependencies = []
        parallel_groups = []
        
        if len(modules) > 0:
            execution_order.append(modules[0])  # Usually Auth or Core
            for m in modules[1:]:
                execution_order.append(m)
                dependencies.append({
                    "module": m,
                    "depends_on": [modules[0]]
                })
            if len(modules) > 2:
                parallel_groups.append(modules[1:3])
            else:
                parallel_groups.append([modules[-1]])
        else:
            execution_order = ["CoreModule"]
            parallel_groups = [["CoreModule"]]
            
        return {
            "status": "success",
            "execution_strategy": {
                "project_type": p_type,
                "architecture_style": "Client-Server Modular MVC",
                "development_strategy": "Database-first schema definition followed by parallel backend logic development and layout generation.",
                "scalability_strategy": "Horizontal scaling for backend web workers and utilizing managed relational DB pools."
            },
            "project_phases": [
                {
                    "phase": 1,
                    "title": "Database Schema & Onboarding Setup",
                    "description": "Establish core data persistence structures and session authentication workflows.",
                    "tasks": [
                        "Configure database tables/collections matching required entities.",
                        "Implement JWT authentication middleware and login/signup APIs."
                    ],
                    "expected_output": [
                        "Functional Auth modules",
                        "Verified database schemas and connection configurations"
                    ]
                },
                {
                    "phase": 2,
                    "title": "Business Logic & Core APIs Development",
                    "description": "Develop main backend functionalities and services required by features.",
                    "tasks": [
                        f"Implement core processing logic for modules: {', '.join(modules)}.",
                        "Integrate AI services or external APIs."
                    ],
                    "expected_output": [
                        "Full backend API codebase ready for consumption"
                    ]
                },
                {
                    "phase": 3,
                    "title": "Frontend UI Components & Dashboard Assembly",
                    "description": "Generate high-fidelity UI views and wireframes bound to the design theme.",
                    "tasks": [
                        "Create responsive layout skeleton matching selected visual theme.",
                        "Build interactive charts, dashboard forms, and state-bound views."
                    ],
                    "expected_output": [
                        "Complete React pages with active layout states"
                    ]
                }
            ],
            "module_execution_order": execution_order,
            "parallel_execution_groups": parallel_groups,
            "module_dependencies": dependencies,
            "agent_execution_plan": [
                {
                    "agent": "DatabaseArchitectAgent",
                    "responsibility": "Initialize database configuration files and schemas.",
                    "execution_stage": "Stage 2: Requirements Definition & Architecture"
                },
                {
                    "agent": "BackendCodeWriterAgent",
                    "responsibility": "Generate API controller code, models, and service classes.",
                    "execution_stage": "Stage 3: Business Logic Assembly"
                },
                {
                    "agent": "UIUXStylistAgent",
                    "responsibility": "Generate style layouts, pages, components, and user dashboard views.",
                    "execution_stage": "Stage 4: Frontend Compilation"
                }
            ],
            "compilation_pipeline": [
                {
                    "stage": "Requirements Analysis",
                    "purpose": "Define core technical boundaries and structured JSON requirements."
                },
                {
                    "stage": "System Planning & Scheduling",
                    "purpose": "Generate parallel build paths and dependencies roadmap."
                },
                {
                    "stage": "Code Generation & Assembly",
                    "purpose": "Assemble codebase components from models to visual interfaces."
                }
            ],
            "system_workflow": {
                "initialization": [
                    "Database connector establishes pooled connections.",
                    "Authentication modules initialize keys."
                ],
                "backend_flow": [
                    "User request hits JWT validation middleware.",
                    "Valid requests routed to specific module service logic."
                ],
                "frontend_flow": [
                    "Client loads dashboard with active visual theme settings.",
                    "Components trigger AJAX queries to load metrics dynamically."
                ],
                "integration_flow": [
                    "Third-party integrations run asynchronously under background tasks.",
                    "AI suggestions process using Nvidia NIM endpoints."
                ]
            },
            "risk_analysis": {
                "complex_modules": [m for m in modules if "AI" in m or "Integration" in m or "Automation" in m] or ["MainDashboard"],
                "potential_bottlenecks": [
                    "Latency in third-party API fetches during round-ups or transactions.",
                    "Rate limits on AI recommendation NIM APIs."
                ],
                "optimization_suggestions": [
                    "Use caching layers for external dashboard feeds.",
                    "Implement a background task worker to process heavy computations offline."
                ]
            },
            "recommended_next_agents": [
                "DatabaseArchitectAgent",
                "BackendGeneratorAgent",
                "FrontendGeneratorAgent"
            ]
        }
