import json
from loguru import logger
from typing import Dict, Any, List

DEPENDENCY_MAP = {
    "RequirementAnalyzerAgent": [],
    "PlannerAgent": ["requirements"],
    "ResearchPlanningAgent": ["requirements", "planning"],
    "DatabaseArchitectureAgent": ["requirements", "planning"],
    "DatabaseModelGenerationAgent": ["requirements", "planning", "db_architecture"],
    "BackendArchitectureAgent": ["requirements", "planning", "db_architecture"],
    "APIAgent": ["requirements", "planning", "db_architecture", "backend_architecture"],
    "APIImplementationAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "FrontendArchitectureAgent": ["requirements", "planning", "theme_styling"],
    "UIUXArchitectAgent": ["requirements", "planning", "theme_styling"],
    "UIComponentGenerationAgent": ["requirements", "planning", "theme_styling", "frontend_architecture"],
    "StateManagementAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "frontend_architecture"],
    "StateImplementationAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "frontend_architecture", "state_management"],
    "AuthArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "RealtimeArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "DevOpsArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture"],
    "SecurityArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "auth_architecture"],
    "TestingArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "ValidationArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "OptimizationArchitectureAgent": ["requirements", "planning", "db_architecture", "backend_architecture", "api_architecture", "frontend_architecture"],
    "CodeGenerationPlannerAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "devops_architecture", "security_architecture",
        "testing_architecture", "validation_architecture", "optimization_architecture"
    ],
    "BackendCodeGenerationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "auth_architecture", "realtime_architecture", "state_management", "code_generation_plan"
    ],
    "FrontendCodeGenerationAgent": [
        "requirements", "planning", "implementation_plan", "frontend_architecture", "theme_styling",
        "state_management", "code_generation_plan"
    ],
    "IntegrationGenerationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation"
    ],
    "BuildCompilationAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation"
    ],
    "ErrorCorrectionAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation", "build_compilation"
    ],
    "ProjectExportAgent": [
        "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
        "realtime_architecture", "state_management", "code_generation_plan", "backend_code_generation",
        "api_implementation", "frontend_code_generation", "ui_component_generation", "state_implementation",
        "integration_generation", "build_compilation", "error_correction"
    ]
}

def estimate_tokens(text: str) -> int:
    """Fast character-to-token ratio estimation helper (~4 characters per token)."""
    return max(1, len(text) // 4)

def wrap_degraded_context(dep_key: str, summary_str: str, original_val: Any, level_name: str, contracts_dict: dict = None) -> dict:
    """Wraps summary text/contracts inside a Dict model supporting backward compatible fallback code accesses."""
    if not isinstance(original_val, dict):
        return {
            "summary": summary_str,
            "is_degraded": True,
            "context_level": level_name,
            "contracts": contracts_dict or {}
        }
        
    wrapper = {
        "summary": summary_str,
        "is_degraded": True,
        "context_level": level_name
    }
    
    if contracts_dict:
        wrapper.update(contracts_dict)
        
    # Include key top-level keys to satisfy agent Python fallback/parsing code without actual bloat
    if dep_key == "requirements":
        wrapper.update({
            "project_overview": original_val.get("project_overview", {}),
            "tech_stack": original_val.get("tech_stack", []),
            "features": original_val.get("features", []),
            "core_modules": original_val.get("core_modules", []),
            "authentication": original_val.get("authentication", {}),
            "database_requirements": original_val.get("database_requirements", {}),
            "theme": original_val.get("theme", {})
        })
    elif dep_key == "db_architecture":
        wrapper.update({
            "entities": original_val.get("entities", []),
            "relationships": original_val.get("relationships", []),
            "database_strategy": original_val.get("database_strategy", {})
        })
    elif dep_key == "backend_architecture":
        wrapper.update({
            "service_architecture": original_val.get("service_architecture", [])
        })
    elif dep_key == "api_architecture":
        wrapper.update({
            "endpoints": original_val.get("endpoints", [])
        })
    elif dep_key == "frontend_architecture":
        wrapper.update({
            "pages": original_val.get("pages", []),
            "components": original_val.get("components", [])
        })
        
    return wrapper

def build_context_for_level(agent_name: str, project_doc: dict, level_name: str, selected_keys: list) -> dict:
    """Constructs the pruned/summarized dictionary context for a given degradation level."""
    context = {}
    
    # Start with a copy of all metadata / execution-routing parameters to avoid losing state machine controls
    arch_keys = {
        "requirements", "planning", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling",
        "auth_architecture", "realtime_architecture", "state_management",
        "devops_architecture", "security_architecture", "testing_architecture",
        "validation_architecture", "optimization_architecture",
        "implementation_plan", "code_generation_plan", "database_model_generation",
        "backend_code_generation", "api_implementation", "frontend_code_generation",
        "ui_component_generation", "state_implementation", "integration_generation",
        "build_compilation", "error_correction", "project_export"
    }
    
    for k, v in project_doc.items():
        if k not in arch_keys and not k.endswith("_full") and not k.endswith("_summary") and not k.endswith("_compressed") and not k.endswith("_contracts"):
            context[k] = v
            
    # Populate selected keys based on chosen degradation tier
    for dep_key in selected_keys:
        original_val = project_doc.get(dep_key)
        if not original_val:
            continue
            
        if level_name == "FULL":
            context[dep_key] = project_doc.get(f"{dep_key}_full") or original_val
        elif level_name == "SUMMARY":
            summary_str = project_doc.get(f"{dep_key}_summary")
            if summary_str:
                context[dep_key] = wrap_degraded_context(dep_key, summary_str, original_val, "SUMMARY")
            else:
                context[dep_key] = project_doc.get(f"{dep_key}_full") or original_val
        elif level_name == "COMPRESSED":
            compressed_str = project_doc.get(f"{dep_key}_compressed")
            if compressed_str:
                context[dep_key] = wrap_degraded_context(dep_key, compressed_str, original_val, "COMPRESSED")
            else:
                summary_str = project_doc.get(f"{dep_key}_summary") or ""
                context[dep_key] = wrap_degraded_context(dep_key, summary_str, original_val, "COMPRESSED")
        elif level_name == "CONTRACTS":
            contracts_dict = project_doc.get(f"{dep_key}_contracts")
            if contracts_dict:
                context[dep_key] = wrap_degraded_context(dep_key, "", original_val, "CONTRACTS", contracts_dict)
            else:
                compressed_str = project_doc.get(f"{dep_key}_compressed") or ""
                context[dep_key] = wrap_degraded_context(dep_key, compressed_str, original_val, "CONTRACTS")
                
    return context

def build_context(agent_name: str, project_doc: dict) -> dict:
    """
    Intelligent Context Builder:
    Filters the project document to include only dependencies matching the agent profile.
    Estimates token bounds and automatically degrades details to stay below strict context limits.
    """
    arch_keys = [
        "requirements", "planning", "db_architecture", "backend_architecture",
        "api_architecture", "frontend_architecture", "theme_styling",
        "auth_architecture", "realtime_architecture", "state_management",
        "devops_architecture", "security_architecture", "testing_architecture",
        "validation_architecture", "optimization_architecture",
        "implementation_plan", "code_generation_plan", "database_model_generation",
        "backend_code_generation", "api_implementation", "frontend_code_generation",
        "ui_component_generation", "state_implementation", "integration_generation",
        "build_compilation", "error_correction", "project_export"
    ]
    
    # 1. Resolve selected keys and removed non-dependency keys
    if agent_name in DEPENDENCY_MAP:
        deps = DEPENDENCY_MAP[agent_name]
        selected_keys = [k for k in deps if k in project_doc]
        removed_keys = [k for k in arch_keys if k in project_doc and k not in deps]
    else:
        selected_keys = [k for k in arch_keys if k in project_doc]
        removed_keys = []
        
    WARNING_THRESHOLD = 80000
    HARD_LIMIT = 100000
    
    levels = ["FULL", "SUMMARY", "COMPRESSED", "CONTRACTS"]
    selected_level = "FULL"
    final_context = {}
    estimated_tokens = 0
    
    # 2. Iterate through levels to find the highest-detail format under token limits
    for level in levels:
        context_candidate = build_context_for_level(agent_name, project_doc, level, selected_keys)
        tokens = estimate_tokens(json.dumps(context_candidate, default=str))
        
        if tokens <= WARNING_THRESHOLD:
            selected_level = level
            final_context = context_candidate
            estimated_tokens = tokens
            break
        elif tokens <= HARD_LIMIT:
            selected_level = level
            final_context = context_candidate
            estimated_tokens = tokens
        else:
            selected_level = level
            final_context = context_candidate
            estimated_tokens = tokens
            
    # Print/Log exact required fields for [ContextBuilder]
    logger.info(
        f"\n"
        f"[ContextBuilder]\n"
        f"Agent: {agent_name}\n"
        f"Selected Keys: {selected_keys}\n"
        f"Removed Keys: {removed_keys}\n"
        f"Estimated Tokens: {estimated_tokens}\n"
        f"Selected Context Level: {selected_level}\n"
    )
    
    return final_context
