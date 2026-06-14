import json
from loguru import logger
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
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback planning.")
            return enrich_agent_output(self._get_fallback_planning(requirements), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior software project planner and build orchestrator. You transform technical requirements into a deterministic build execution plan with clear phases, dependency graphs, and agent scheduling.\n\n"
                "## Instructions\n"
                "1. Think step by step: analyze the project type and modules, then define phases (setup → backend → frontend → integration), then map module dependencies, then identify risks.\n"
                "2. module_execution_order must be a topologically sorted list — foundational modules (Auth, Database) before dependent ones.\n"
                "3. parallel_execution_groups must only contain modules with NO inter-dependencies.\n"
                "4. agent_execution_plan must reference real Sarthi agent names: DatabaseArchitectureAgent, BackendArchitectureAgent, APIAgent, FrontendArchitectureAgent, UIUXArchitectAgent, AuthArchitectureAgent.\n"
                "5. risk_analysis must be specific to the project — avoid generic platitudes.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- project_phases must contain 3-5 phases, each with concrete tasks and expected_output.\n"
                "- recommended_next_agents must list agents in the correct pipeline invocation order."
            )
        )

        user_content = f"""
Analyze the following project requirements and produce a build execution plan.

Think step by step:
1. Determine the architecture style from the tech stack and project type.
2. Break the build into 3-5 sequential phases (setup → core backend → frontend → integration → polish).
3. Topologically sort modules so dependencies come first in module_execution_order.
4. Group independent modules into parallel_execution_groups.
5. Map each Sarthi agent to its execution stage.
6. Identify project-specific risks and bottlenecks.

Requirements: {json.dumps(requirements, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "execution_strategy": {{
    "project_type": "string — from requirements.project_overview.type",
    "architecture_style": "string — e.g. 'Client-Server MVC', 'Microservices', 'Serverless'",
    "development_strategy": "string — 1 sentence on build approach (e.g. 'Database-first with parallel frontend/backend')",
    "scalability_strategy": "string — 1 sentence on scaling approach"
  }},
  "project_phases": [
    {{
      "phase": "integer — sequential phase number starting at 1",
      "title": "string — short phase title",
      "description": "string — what this phase accomplishes",
      "tasks": ["string — specific actionable tasks"],
      "expected_output": ["string — concrete deliverables"]
    }}
  ],
  "module_execution_order": ["string — topologically sorted module names from requirements.core_modules"],
  "parallel_execution_groups": [
    ["string — modules with no inter-dependencies that can build concurrently"]
  ],
  "module_dependencies": [
    {{
      "module": "string — dependent module name",
      "depends_on": ["string — prerequisite module names"]
    }}
  ],
  "agent_execution_plan": [
    {{
      "agent": "string — exact Sarthi agent class name (e.g. 'DatabaseArchitectureAgent')",
      "responsibility": "string — what this agent produces",
      "execution_stage": "string — which phase this agent runs in"
    }}
  ],
  "compilation_pipeline": [
    {{
      "stage": "string — pipeline stage name",
      "purpose": "string — what this stage achieves"
    }}
  ],
  "system_workflow": {{
    "initialization": ["string — system startup steps"],
    "backend_flow": ["string — request processing steps"],
    "frontend_flow": ["string — UI rendering steps"],
    "integration_flow": ["string — third-party/async integration steps"]
  }},
  "risk_analysis": {{
    "complex_modules": ["string — modules with highest implementation risk"],
    "potential_bottlenecks": ["string — specific performance/integration risks"],
    "optimization_suggestions": ["string — actionable mitigation strategies"]
  }},
  "recommended_next_agents": ["string — Sarthi agent names in invocation order"]
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
            logger.error(f"Failed to run Planner Agent: {e}")
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
