import json
from collections.abc import Mapping
from typing import Any, Dict, List


AGENT_PIPELINE: List[str] = [
    "RequirementAnalyzerAgent",
    "PlannerAgent",
    "DatabaseArchitectureAgent",
    "BackendArchitectureAgent",
    "APIAgent",
    "FrontendArchitectureAgent",
    "UIUXArchitectAgent",
    "AuthArchitectureAgent",
    "RealtimeArchitectureAgent",
    "StateManagementAgent",
    "DevOpsArchitectureAgent",
    "SecurityArchitectureAgent",
    "TestingArchitectureAgent",
    "ValidationArchitectureAgent",
    "OptimizationArchitectureAgent",
    "CodeGenerationPlannerAgent",
    "DatabaseModelGenerationAgent",
    "BackendCodeGenerationAgent",
    "APIImplementationAgent",
    "FrontendCodeGenerationAgent",
    "UIComponentGenerationAgent",
    "StateImplementationAgent",
    "IntegrationGenerationAgent",
    "BuildCompilationAgent",
    "ErrorCorrectionAgent",
    "ProjectExportAgent",
]


AGENT_ROLES: Dict[str, str] = {
    "RequirementAnalyzerAgent": "Extracts structured product, technical, theme, and workflow requirements.",
    "PlannerAgent": "Turns requirements into execution order, dependencies, risks, and agent scheduling.",
    "DatabaseArchitectureAgent": "Defines persistence entities, relationships, indexes, and data contracts.",
    "BackendArchitectureAgent": "Designs backend modules, services, repositories, middleware, and workflows.",
    "APIAgent": "Defines API routes, payload contracts, errors, security schemes, and route groupings.",
    "FrontendArchitectureAgent": "Designs routes, pages, component hierarchy, data flow, and frontend states.",
    "UIUXArchitectAgent": "Defines design tokens, visual workflows, accessibility, and responsive styling rules.",
    "AuthArchitectureAgent": "Defines identity, sessions, RBAC, protected routes, and auth UI/backend flows.",
    "RealtimeArchitectureAgent": "Defines websocket channels, events, pub/sub, notifications, and sync rules.",
    "StateManagementAgent": "Defines global stores, cache policy, optimistic updates, and realtime state sync.",
    "DevOpsArchitectureAgent": "Defines containers, environments, CI/CD, deployment, monitoring, and scaling.",
    "SecurityArchitectureAgent": "Defines application, API, frontend, websocket, environment, and infra security.",
    "TestingArchitectureAgent": "Defines unit, integration, API, E2E, load, fixture, and CI quality gates.",
    "ValidationArchitectureAgent": "Checks cross-agent consistency and decides compilation readiness.",
    "OptimizationArchitectureAgent": "Defines performance, cache, latency, realtime, resource, and distributed scaling optimizations.",
    "CodeGenerationPlannerAgent": "Defines deterministic file generation sequencing, dependency graph orchestration, and compilation batches.",
    "DatabaseModelGenerationAgent": "Generates concrete database models, schemas, indexes, and persistence scaffolding from architecture contracts.",
    "BackendCodeGenerationAgent": "Generates backend services, repositories, middleware, and route handlers from validated backend contracts.",
    "APIImplementationAgent": "Generates concrete API endpoint implementations, request validation, and response payload handling.",
    "FrontendCodeGenerationAgent": "Generates route/page code and frontend integration contracts from API and UI architecture.",
    "UIComponentGenerationAgent": "Generates reusable UI components, responsive states, and accessibility-aligned interface modules.",
    "StateImplementationAgent": "Generates state stores, cache policies, optimistic updates, and realtime data synchronization code.",
    "IntegrationGenerationAgent": "Connects frontend, backend, database, auth, realtime, and environment contracts into a runnable application.",
    "BuildCompilationAgent": "Compiles build scripts, dependency manifests, validation commands, runtime instructions, and packaging checks.",
    "ErrorCorrectionAgent": "Autonomous error-recovery and compilation-stabilisation layer. Produces structured repair intelligence for import resolution, API contract alignment, auth correction, realtime repair, state stabilisation, and export-safe packaging.",
    "ProjectExportAgent": "Final delivery and export orchestration layer. Produces deployment-ready repository structures, ZIP artifacts, Docker packaging, Cloud Run configs, GitLab CI/CD export preparation, environment templates, and production-safe delivery intelligence.",
}


def _agent_index(agent_name: str) -> int:
    try:
        return AGENT_PIPELINE.index(agent_name)
    except ValueError:
        return -1


def get_upstream_agents(agent_name: str) -> List[str]:
    index = _agent_index(agent_name)
    return AGENT_PIPELINE[:index] if index > 0 else []


def get_downstream_agents(agent_name: str) -> List[str]:
    index = _agent_index(agent_name)
    return AGENT_PIPELINE[index + 1 :] if index >= 0 else []


def build_agent_system_prompt(agent_name: str, responsibility: str) -> str:
    """Create one connected-agent system prompt used by every architecture agent."""
    downstream = get_downstream_agents(agent_name)
    downstream_text = ", ".join(downstream) if downstream else "the final compiler"
    pipeline_text = " -> ".join(AGENT_PIPELINE)
    return (
        f"You are the {agent_name} for Sarthi, an AI-powered connected software architecture system.\n"
        f"Pipeline order: {pipeline_text}.\n"
        f"Your responsibility: {responsibility}\n"
        "Treat every upstream JSON input as a binding contract. Preserve names, entities, routes, theme tokens, "
        "workflow labels, and security assumptions unless a direct conflict requires a correction.\n"
        f"Optimize your output for handoff to: {downstream_text}.\n"
        "Return ONLY valid JSON. Do NOT ask questions. Do NOT generate source code. Do NOT explain reasoning.\n"
        "Include an `agent_handoff` object in the JSON with: agent, role, upstream_agents, downstream_agents, "
        "input_contracts_used, handoff_summary, integration_points, and quality_gates."
    )


def strip_json_code_fence(raw_response: str) -> str:
    raw = raw_response.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


class IncompleteJSONError(BaseException):
    def __init__(self, message, raw_response):
        super().__init__(message)
        self.raw_response = raw_response

def parse_json_response(raw_response: str) -> Dict[str, Any]:
    try:
        return json.loads(strip_json_code_fence(raw_response))
    except json.JSONDecodeError as e:
        # Raise BaseException so it bypasses the agent's `except Exception:` blocks
        raise IncompleteJSONError(f"JSONDecodeError: {e}", raw_response)


def _names_from_items(items: Any, name_key: str) -> List[str]:
    names: List[str] = []
    if not isinstance(items, list):
        return names
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, Mapping):
            value = item.get(name_key) or item.get("name") or item.get("path") or item.get("workflow_name")
            if value:
                names.append(str(value))
    return names


def summarize_contract(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"type": type(value).__name__, "value": str(value)[:160]}

    summary: Dict[str, Any] = {
        "status": value.get("status"),
        "top_level_keys": list(value.keys())[:14],
    }

    project_overview = value.get("project_overview")
    if isinstance(project_overview, Mapping):
        summary["project"] = {
            "name": project_overview.get("name"),
            "type": project_overview.get("type"),
            "complexity": project_overview.get("complexity"),
        }

    features = value.get("features")
    if isinstance(features, (list, str)):
        summary["features"] = features[:8]
    core_modules = value.get("core_modules")
    if isinstance(core_modules, (list, str)):
        summary["core_modules"] = core_modules[:8]
    if "tech_stack" in value:
        summary["tech_stack"] = value.get("tech_stack")
    exec_order = value.get("module_execution_order")
    if isinstance(exec_order, (list, str)):
        summary["module_execution_order"] = exec_order[:10]
    next_agents = value.get("recommended_next_agents")
    if isinstance(next_agents, (list, str)):
        summary["recommended_next_agents"] = next_agents[:10]

    if "entities" in value:
        summary["entities"] = _names_from_items(value.get("entities"), "entity_name")[:12]
    if "relationships" in value:
        summary["relationships"] = [
            f"{rel.get('from_entity')}->{rel.get('to_entity')}"
            for rel in value.get("relationships", [])
            if isinstance(rel, Mapping)
        ][:10]
    if "endpoints" in value:
        endpoints = []
        for endpoint in value.get("endpoints", []):
            if isinstance(endpoint, Mapping):
                endpoints.append(f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}")
            elif isinstance(endpoint, str):
                endpoints.append(endpoint)
        summary["endpoints"] = endpoints[:14]
    if "pages" in value:
        summary["pages"] = _names_from_items(value.get("pages"), "page_name")[:12]
    if "layouts" in value:
        summary["layouts"] = _names_from_items(value.get("layouts"), "layout_name")[:10]

    for section_name in (
        "database_strategy",
        "backend_strategy",
        "api_strategy",
        "frontend_strategy",
        "design_system",
        "authentication_strategy",
        "realtime_strategy",
        "state_management_strategy",
        "infrastructure_strategy",
        "security_strategy",
        "testing_strategy",
        "validation_strategy",
        "optimization_strategy",
        "generation_strategy",
    ):
        section = value.get(section_name)
        if isinstance(section, Mapping):
            summary[section_name] = {
                key: section.get(key)
                for key in list(section.keys())[:5]
            }

    handoff = value.get("agent_handoff")
    if isinstance(handoff, Mapping):
        handoff_sum = handoff.get("handoff_summary")
        if isinstance(handoff_sum, (list, str)):
            summary["handoff_summary"] = handoff_sum[:6]
        int_pts = handoff.get("integration_points")
        if isinstance(int_pts, (list, str)):
            summary["integration_points"] = int_pts[:6]

    return {key: val for key, val in summary.items() if val not in (None, [], {})}


def summarize_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return {
        input_name: summarize_contract(input_value)
        for input_name, input_value in inputs.items()
        if input_value is not None
    }


def _extract_integration_points(output: Mapping[str, Any]) -> List[str]:
    points: List[str] = []
    if output.get("database_strategy"):
        points.append("Database decisions must drive backend models, repositories, API payloads, and state entities.")
    if output.get("backend_strategy"):
        points.append("Backend module structure must drive API route grouping and deployment service boundaries.")
    if output.get("api_strategy") or output.get("endpoints"):
        points.append("API paths and response payloads are the frontend data contract.")
    if output.get("frontend_strategy") or output.get("pages"):
        points.append("Frontend pages, components, and state names must align with API and design-system contracts.")
    if output.get("design_system"):
        points.append("Theme tokens and accessibility rules must be reused by generated components.")
    if output.get("authentication_strategy"):
        points.append("Protected route and token choices must be enforced by API, frontend, realtime, and tests.")
    if output.get("realtime_strategy"):
        points.append("WebSocket channels and event names must match frontend store subscriptions.")
    if output.get("state_management_strategy"):
        points.append("Stores, cache keys, and optimistic flows must map to declared endpoints and entities.")
    if output.get("infrastructure_strategy"):
        points.append("Container, env, and proxy contracts must match generated backend/frontend services.")
    if output.get("security_strategy"):
        points.append("Security controls must be reflected in backend dependencies, frontend storage, and CI gates.")
    if output.get("testing_strategy"):
        points.append("Tests must cover declared critical routes, stores, auth flows, realtime events, and build gates.")
    if output.get("validation_strategy"):
        points.append("Compilation must follow validation readiness, blocking issues, and recommended corrections.")
    if output.get("optimization_strategy"):
        points.append("Performance, cache, async, and scaling decisions must shape generated services, stores, routes, and deployment configs.")
    if output.get("generation_strategy"):
        points.append("Generated files must follow the declared dependency graph, generation phases, and compilation batches.")
    return points[:8]


def _extract_handoff_summary(output: Mapping[str, Any]) -> List[str]:
    summary: List[str] = []
    for key in (
        "project_overview",
        "execution_strategy",
        "database_strategy",
        "backend_strategy",
        "api_strategy",
        "frontend_strategy",
        "design_system",
        "authentication_strategy",
        "realtime_strategy",
        "state_management_strategy",
        "infrastructure_strategy",
        "security_strategy",
        "testing_strategy",
        "validation_strategy",
        "optimization_strategy",
        "generation_strategy",
    ):
        value = output.get(key)
        if isinstance(value, Mapping):
            summary.append(f"{key}: {', '.join(str(k) for k in list(value.keys())[:5])}")
    if output.get("entities"):
        summary.append(f"entities: {', '.join(_names_from_items(output.get('entities'), 'entity_name')[:8])}")
    if output.get("endpoints"):
        endpoint_count = len(output.get("endpoints", []))
        summary.append(f"endpoints: {endpoint_count} route contracts")
    if output.get("pages"):
        summary.append(f"pages: {', '.join(_names_from_items(output.get('pages'), 'page_name')[:8])}")
    return summary[:8]


def enrich_agent_output(
    output: Dict[str, Any],
    agent_name: str,
    inputs: Dict[str, Any],
    role: str | None = None,
) -> Dict[str, Any]:
    """Attach one consistent Sarthi handoff contract to every agent result."""
    if not isinstance(output, dict):
        output = {"status": "success", "result": output}

    existing_handoff = output.get("agent_handoff")
    if not isinstance(existing_handoff, dict):
        existing_handoff = {}

    role_text = role or AGENT_ROLES.get(agent_name, "Sarthi architecture agent.")
    output["agent_handoff"] = {
        "agent": agent_name,
        "role": role_text,
        "upstream_agents": get_upstream_agents(agent_name),
        "downstream_agents": get_downstream_agents(agent_name),
        "input_contracts_used": summarize_inputs(inputs),
        "handoff_summary": existing_handoff.get("handoff_summary") or _extract_handoff_summary(output),
        "integration_points": existing_handoff.get("integration_points") or _extract_integration_points(output),
        "quality_gates": existing_handoff.get("quality_gates") or [
            "Preserve exact names for entities, routes, states, theme tokens, and workflows.",
            "Flag conflicts explicitly in validation or future_generation_context instead of silently changing contracts.",
            "Keep downstream generation decisions traceable to upstream agent outputs.",
        ],
    }
    return output


def build_compilation_context(agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Create a compact architecture context for the final code compiler prompt."""
    ordered_context: Dict[str, Any] = {}
    for key in (
        "requirements",
        "planning",
        "db_architecture",
        "backend_architecture",
        "api_architecture",
        "frontend_architecture",
        "theme_styling",
        "auth_architecture",
        "realtime_architecture",
        "state_management",
        "devops_architecture",
        "security_architecture",
        "testing_architecture",
        "validation_architecture",
        "optimization_architecture",
        "code_generation_plan",
        "database_model_generation",
        "backend_code_generation",
        "api_implementation",
        "frontend_code_generation",
        "ui_component_generation",
        "state_implementation",
        "integration_generation",
        "build_compilation",
        "error_correction",
        "project_export",
    ):
        value = agent_outputs.get(key)
        if value:
            ordered_context[key] = summarize_contract(value)
    return ordered_context


# ──────────────────────────────────────────────────────────────
# Dynamic Prompt Template System (Sarthi 2.0)
# ──────────────────────────────────────────────────────────────

TASK_OBJECTIVES: Dict[str, str] = {
    "RequirementAnalyzerAgent": "Identify project scope, features, core modules, and technical requirements from client idea.",
    "PlannerAgent": "Plan execution order, module dependency mapping, and assign agent scheduler schema.",
    "ResearchPlanningAgent": "Examine requirements and code structure to map proposed files alterations list.",
    "DatabaseArchitectureAgent": "Design persistence entities, primary/foreign key relations, indexes, caching layer, and data contracts.",
    "BackendArchitectureAgent": "Design internal backend modules, repositories, service patterns, and business logic execution pipelines.",
    "APIAgent": "Define REST routes, WebSocket channels, payloads, headers, auth guards, and response contracts.",
    "FrontendArchitectureAgent": "Design layout hierarchies, routing strategies, page flows, and UI component dependencies.",
    "UIUXArchitectAgent": "Define style sheets, visual typography, HSL Tailwind colors, design system tokens, and theme configurations.",
    "AuthArchitectureAgent": "Design authorization and authentication layers (sessions, JWT, tokens, cookie strategy, roles access).",
    "RealtimeArchitectureAgent": "Design realtime WebSocket subscriptions, event payloads, channels mappings, and sync states.",
    "StateManagementAgent": "Design client global state stores, slice actions, async cache invalidation, and data hydration.",
    "DevOpsArchitectureAgent": "Design deployment configurations, Dockerfiles, environments, and CI/CD pipelines.",
    "SecurityArchitectureAgent": "Design application security (CORS, Rate Limiting, sanitization, hashing, secrets management).",
    "TestingArchitectureAgent": "Design test strategies, fixtures schemas, and quality check specifications.",
}

JSON_SCHEMAS: Dict[str, str] = {
    "DatabaseArchitectureAgent": """{
  "status": "success",
  "database_strategy": {
    "primary_database": "string (e.g. 'PostgreSQL', 'MongoDB', 'SQLite')",
    "secondary_databases": ["string"],
    "cache_layer": "string (e.g. 'Redis', 'None')",
    "database_reasoning": ["string"]
  },
  "entities": [
    {
      "entity_name": "string (PascalCase)",
      "fields": [{"name": "string (snake_case)", "type": "string", "required": "boolean", "indexed": "boolean"}]
    }
  ]
}""",
    "ResearchPlanningAgent": """{
  "status": "success",
  "plan_markdown": "string (A detailed Markdown document detailing the implementation steps)",
  "proposed_changes": [
    {"path": "string", "action": "string", "description": "string"}
  ]
}"""
}

def get_role_definition(agent_role: str) -> str:
    return AGENT_ROLES.get(agent_role, "Senior software architecture agent for Sarthi pipeline.")

def get_required_state_keys(agent_role: str) -> str:
    mapping = {
        "RequirementAnalyzerAgent": "requirements",
        "PlannerAgent": "planning",
        "ResearchPlanningAgent": "implementation_plan",
        "DatabaseArchitectureAgent": "db_architecture",
        "BackendArchitectureAgent": "backend_architecture",
        "APIAgent": "api_architecture",
        "FrontendArchitectureAgent": "frontend_architecture",
        "UIUXArchitectAgent": "theme_styling",
        "AuthArchitectureAgent": "auth_architecture",
        "RealtimeArchitectureAgent": "realtime_architecture",
        "StateManagementAgent": "state_management",
        "DevOpsArchitectureAgent": "devops_architecture",
        "SecurityArchitectureAgent": "security_architecture",
        "TestingArchitectureAgent": "testing_architecture",
        "ValidationArchitectureAgent": "validation_architecture",
        "OptimizationArchitectureAgent": "optimization_strategy",
        "CodeGenerationPlannerAgent": "code_generation_plan",
        "DatabaseModelGenerationAgent": "database_model_generation",
        "BackendCodeGenerationAgent": "backend_code_generation",
        "APIImplementationAgent": "api_implementation",
        "FrontendCodeGenerationAgent": "frontend_code_generation",
        "UIComponentGenerationAgent": "ui_component_generation",
        "StateImplementationAgent": "state_implementation",
        "IntegrationGenerationAgent": "integration_generation",
        "BuildCompilationAgent": "build_compilation",
        "ErrorCorrectionAgent": "error_correction",
        "ProjectExportAgent": "project_export",
    }
    return mapping.get(agent_role, agent_role.lower())

def get_task_objective(agent_role: str) -> str:
    return TASK_OBJECTIVES.get(agent_role, f"Implement Sarthi architecture tasks for {agent_role}.")

def get_json_schema(agent_role: str) -> str:
    default_schema = """{
  "status": "success",
  "result": {},
  "agent_handoff": {
    "agent": "string",
    "role": "string",
    "upstream_agents": ["string"],
    "downstream_agents": ["string"],
    "handoff_summary": ["string"]
  }
}"""
    return JSON_SCHEMAS.get(agent_role, default_schema)

def generate_agent_prompt(agent_role: str, state: dict) -> str:
    base_template = """
    ROLE: {role_definition}
    
    UPSTREAM CONTEXT (BINDING CONTRACTS):
    - Requirements Context: {requirements_context}
    - Implementation Plan: {plan_context}
    - Active Workspace State: {active_state_context}
    
    OBJECTIVE & SCOPE:
    {task_objective}
    
    STRICT CONSTRAINTS:
    - Never write placeholders or mock codes.
    - Align database schemas with model entities exactly.
    - All JSON outputs must strictly conform to the schema outlined below.
    
    REQUIRED OUTPUT CONTRACT SCHEMA:
    {json_output_schema}
    """
    
    return base_template.format(
        role_definition=get_role_definition(agent_role),
        requirements_context=json.dumps(state.get("requirements") or {}),
        plan_context=json.dumps(state.get("implementation_plan") or {}),
        active_state_context=json.dumps(state.get(get_required_state_keys(agent_role)) or {}),
        task_objective=get_task_objective(agent_role),
        json_output_schema=get_json_schema(agent_role)
    )
