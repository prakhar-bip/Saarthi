"""
Sarthi Agents Grouping Registry.
Defines logical classifications for all AI agents inside the compilation pipeline.
Allows dynamic orchestration of active steps depending on the generation_type.
"""

AGENT_GROUPS = {
    "db": [
        "DatabaseArchitectureAgent",
        "DatabaseModelGenerationAgent"
    ],
    "backend": [
        "BackendArchitectureAgent",
        "APIAgent",
        "APIImplementationAgent",
        "BackendCodeGenerationAgent"
    ],
    "frontend": [
        "FrontendArchitectureAgent",
        "UIUXArchitectAgent",
        "UIComponentGenerationAgent",
        "StateManagementAgent",
        "StateImplementationAgent",
        "FrontendCodeGenerationAgent"
    ],
    "ops_security": [
        "AuthArchitectureAgent",
        "RealtimeArchitectureAgent",
        "DevOpsArchitectureAgent",
        "SecurityArchitectureAgent",
        "TestingArchitectureAgent",
        "ValidationArchitectureAgent",
        "OptimizationArchitectureAgent",
        "BuildCompilationAgent"
    ],
    "common": [
        "CodeGenerationPlannerAgent",
        "IntegrationGenerationAgent",
        "ErrorCorrectionAgent",
        "CodeSynthesizerAgent",
        "RuntimeVerifierAgent",
        "ProjectExportAgent"
    ]
}

def get_group_for_agent(agent_name: str) -> str:
    """Returns the logical group name (db, backend, frontend, ops_security, common) for a given agent."""
    for group, agents in AGENT_GROUPS.items():
        if agent_name in agents:
            return group
    return "common"

def should_run_agent(agent_name: str, generation_type: str) -> bool:
    """Returns True if the agent is relevant for the selected generation_type, False otherwise."""
    group = get_group_for_agent(agent_name)
    if generation_type == "frontend_only":
        if group in ("db", "backend"):
            return False
    elif generation_type in ("backend_only", "microservice"):
        if group == "frontend":
            return False
    return True

