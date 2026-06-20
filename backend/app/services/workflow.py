import inspect
import asyncio
from typing import Dict, Any, TypedDict, Optional, List
from datetime import datetime, timezone
import uuid
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from app.agents.context import (
    IncompleteJSONError,
    build_compilation_context,
    build_document_context,
    generate_agent_prompt,
)
from app.services.llm_router import current_agent_feedback

# Import all agents explicitly
from app.agents.requirement_analyzer import RequirementAnalyzerAgent
from app.agents.planner import PlannerAgent
from app.agents.research_planning_agent import ResearchPlanningAgent
from app.agents.db_architect import DatabaseArchitectureAgent
from app.agents.backend_architect import BackendArchitectureAgent
from app.agents.api_agent import APIAgent
from app.agents.frontend_architect import FrontendArchitectureAgent
from app.agents.uiux_architect import UIUXArchitectAgent
from app.agents.auth_architect import AuthArchitectureAgent
from app.agents.realtime_architect import RealtimeArchitectureAgent
from app.agents.state_architect import StateManagementAgent
from app.agents.devops_architect import DevOpsArchitectureAgent
from app.agents.security_architect import SecurityArchitectureAgent
from app.agents.testing_architect import TestingArchitectureAgent
from app.agents.validation_architect import ValidationArchitectureAgent
from app.agents.optimization_architect import OptimizationArchitectureAgent
from app.agents.code_generation_planner import CodeGenerationPlannerAgent
from app.agents.persistence_architect import DatabaseModelGenerationAgent
from app.agents.backend_code_generator import BackendCodeGenerationAgent
from app.agents.api_implementation_generator import APIImplementationAgent
from app.agents.frontend_code_generator import FrontendCodeGenerationAgent
from app.agents.ui_component_generator import UIComponentGenerationAgent
from app.agents.state_implementation_generator import StateImplementationAgent
from app.agents.integration_generator import IntegrationGenerationAgent
from app.agents.build_compiler import BuildCompilationAgent
from app.agents.error_correction import ErrorCorrectionAgent
from app.agents.project_export import ProjectExportAgent
from app.agents.verifier_agent import VerifierAgent
from app.agents.code_synthesizer import CodeSynthesizerAgent
from app.agents.code_validator import CodeValidatorAgent
from app.services.project_assembler import assemble_project_codebase

from typing import Dict, Any, TypedDict, Optional, List, Annotated

def reduce_project_doc(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not left:
        return right or {}
    if not right:
        return left
    merged = dict(left)
    for k, v in right.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = reduce_project_doc(merged[k], v)
        else:
            merged[k] = v
    return merged

def reduce_latest_output(left: Any, right: Any) -> Any:
    if right is not None:
        return right
    return left

async def broadcast_agent_progress(db: Any, project_id: str, progress: int | float, step: str) -> None:
    # Fetch project_doc to determine generation_type and calculate completed fields
    project_doc = await db.projects.find_one({"_id": project_id}) or {}
    
    gen_type = project_doc.get("generation_type", "full_stack")
    
    # Expected architecture / generation fields in database
    expected_fields = ["requirements", "planning", "code_generation_plan"]
    
    if gen_type != "frontend_only":
        expected_fields.extend([
            "db_architecture", 
            "database_model_generation",
            "backend_architecture", 
            "api_architecture", 
            "api_implementation",
            "backend_code_generation"
        ])
        
    if gen_type not in ("backend_only", "microservice"):
        expected_fields.extend([
            "frontend_architecture", 
            "theme_styling", 
            "ui_component_generation",
            "frontend_code_generation",
            "state_management", 
            "state_implementation"
        ])
        
    expected_fields.extend([
        "auth_architecture",
        "realtime_architecture",
        "devops_architecture",
        "security_architecture",
        "testing_architecture",
        "validation_architecture",
        "optimization_architecture",
        "integration_generation",
        "build_compilation",
        "error_correction",
        "project_export"
    ])
    
    # Count completed fields
    completed_fields = 0
    for field in expected_fields:
        val = project_doc.get(field)
        if val:
            if isinstance(val, list):
                if len(val) > 0:
                    completed_fields += 1
            elif isinstance(val, dict):
                if len(val) > 0:
                    completed_fields += 1
            else:
                completed_fields += 1
                
    activity_ratio = completed_fields / max(1, len(expected_fields))
    activity_progress = 5.0 + activity_ratio * 90.0
    
    # Mix passed progress with activity progress, keeping it monotonic
    base_progress = max(float(progress), activity_progress)
    
    # Generate stable decimal part based on step and project_id to avoid jitter
    import hashlib
    h = hashlib.md5((project_id + step).encode()).hexdigest()
    decimal_part = (int(h[:4], 16) % 90 + 10) / 100.0 # 0.10 to 0.99
    
    final_progress = float(int(base_progress)) + decimal_part
    
    # Cap progress appropriately
    if progress >= 100:
        final_progress = 100.0
    else:
        final_progress = min(99.95, final_progress)
        
    # Strictly monotonic check
    current_progress = project_doc.get("progress", 0)
    if current_progress is not None:
        if final_progress < current_progress:
            final_progress = current_progress
            
    # Update DB
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"progress": final_progress, "step": step}}
    )
    
    # Broadcast to websocket
    from app.services.ws_manager import manager
    await manager.broadcast_progress(
        project_id=project_id,
        progress=final_progress,
        step=step
    )
    logger.info(f"Project {project_id} progress: {final_progress}% - {step}")

class AppState(TypedDict):
    project_id: str
    project_doc: Annotated[Dict[str, Any], reduce_project_doc]
    current_index: int
    feedback: Optional[str]
    retry_count: int
    latest_output: Annotated[Any, reduce_latest_output]
    
    # Sarthi 2.0 Orchestration State
    implementation_plan: Optional[Dict[str, Any]]
    hitl_approved: bool
    hitl_enabled: bool
    active_dynamic_agents: List[str]
    validation_logs: List[Dict[str, Any]]
    quality_report: Optional[Dict[str, Any]]

def get_agent_instance(agent_name: str):
    mapping = {
        "RequirementAnalyzerAgent": RequirementAnalyzerAgent,
        "PlannerAgent": PlannerAgent,
        "ResearchPlanningAgent": ResearchPlanningAgent,
        "DatabaseArchitectureAgent": DatabaseArchitectureAgent,
        "BackendArchitectureAgent": BackendArchitectureAgent,
        "APIAgent": APIAgent,
        "FrontendArchitectureAgent": FrontendArchitectureAgent,
        "UIUXArchitectAgent": UIUXArchitectAgent,
        "AuthArchitectureAgent": AuthArchitectureAgent,
        "RealtimeArchitectureAgent": RealtimeArchitectureAgent,
        "StateManagementAgent": StateManagementAgent,
        "DevOpsArchitectureAgent": DevOpsArchitectureAgent,
        "SecurityArchitectureAgent": SecurityArchitectureAgent,
        "TestingArchitectureAgent": TestingArchitectureAgent,
        "ValidationArchitectureAgent": ValidationArchitectureAgent,
        "OptimizationArchitectureAgent": OptimizationArchitectureAgent,
        "CodeGenerationPlannerAgent": CodeGenerationPlannerAgent,
        "DatabaseModelGenerationAgent": DatabaseModelGenerationAgent,
        "BackendCodeGenerationAgent": BackendCodeGenerationAgent,
        "APIImplementationAgent": APIImplementationAgent,
        "FrontendCodeGenerationAgent": FrontendCodeGenerationAgent,
        "UIComponentGenerationAgent": UIComponentGenerationAgent,
        "StateImplementationAgent": StateImplementationAgent,
        "IntegrationGenerationAgent": IntegrationGenerationAgent,
        "BuildCompilationAgent": BuildCompilationAgent,
        "ErrorCorrectionAgent": ErrorCorrectionAgent,
        "ProjectExportAgent": ProjectExportAgent,
    }
    return mapping[agent_name]()

def get_agent_db_key(agent_name: str) -> str:
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
        "OptimizationArchitectureAgent": "optimization_architecture",
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
    return mapping.get(agent_name, agent_name.lower())

async def call_agent_design(agent_name: str, agent: Any, project_doc: Dict[str, Any], feedback: Optional[str]) -> Any:
    """Helper to dynamically call agent methods using signature inspections."""
    method = getattr(agent, "design", None) or getattr(agent, "plan", None) or getattr(agent, "analyze", None) or getattr(agent, "generate_plan", None)
    if not method:
        raise AttributeError(f"Agent {agent_name} has no design/plan/analyze method.")
        
    sig = inspect.signature(method)
    kwargs = {}
    
    param_mapping = {
        "requirements": "requirements",
        "planning": "planning",
        "codebase": "codebase",
        "db_architecture": "db_architecture",
        "backend_architecture": "backend_architecture",
        "api_architecture": "api_architecture",
        "frontend_architecture": "frontend_architecture",
        "theme_styling": "theme_styling",
        "auth_architecture": "auth_architecture",
        "realtime_architecture": "realtime_architecture",
        "state_management": "state_management",
        "devops_architecture": "devops_architecture",
        "security_architecture": "security_architecture",
        "testing_architecture": "testing_architecture",
        "validation_architecture": "validation_architecture",
        "optimization_architecture": "optimization_architecture",
        "code_generation_plan": "code_generation_plan",
        "code_generation_planner": "code_generation_plan",
        "database_model_generation": "database_model_generation",
        "backend_code_generation": "backend_code_generation",
        "api_implementation": "api_implementation",
        "frontend_code_generation": "frontend_code_generation",
        "ui_component_generation": "ui_component_generation",
        "state_implementation": "state_implementation",
        "integration_generation": "integration_generation",
        "build_compilation": "build_compilation",
        "error_correction": "error_correction",
        "project_export": "project_export",
        "global_project_context": "agent_context",
        "implementation_plan": "implementation_plan",
        "prd": "prd",
        "trd": "trd",
        "mrd": "mrd",
    }
    
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        db_key = param_mapping.get(param_name)
        if db_key:
            # Handle list keys differently
            if db_key == "codebase":
                kwargs[param_name] = project_doc.get(db_key, []) or []
            else:
                kwargs[param_name] = project_doc.get(db_key, {}) or {}
        elif param.default == inspect.Parameter.empty:
            kwargs[param_name] = {}
            
    if inspect.iscoroutinefunction(method):
        return await method(**kwargs)
    else:
        return method(**kwargs)

def enrich_project_doc_context(project_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Attach PRD/TRD/MRD and compilation context so every agent shares the same source of truth."""
    project_doc["prd"] = project_doc.get("prd", "") or ""
    project_doc["trd"] = project_doc.get("trd", "") or ""
    project_doc["mrd"] = project_doc.get("mrd", "") or ""
    project_doc["_document_context"] = build_document_context(project_doc)
    if not project_doc.get("agent_context"):
        arch_keys = (
            "requirements", "planning", "db_architecture", "backend_architecture",
            "api_architecture", "frontend_architecture", "theme_styling",
            "auth_architecture", "realtime_architecture", "state_management",
            "devops_architecture", "security_architecture", "testing_architecture",
            "validation_architecture", "optimization_architecture",
            "implementation_plan", "code_generation_plan",
        )
        project_doc["agent_context"] = build_compilation_context(
            {k: project_doc.get(k) for k in arch_keys if project_doc.get(k)}
        )
    return project_doc


async def run_single_agent(db: Any, project_id: str, project_doc: Dict[str, Any], agent_name: str) -> Any:
    """Executes a single agent node with verification and fallback retries."""
    from app.agents.registry import should_run_agent, get_group_for_agent
    gen_type = project_doc.get("generation_type", "full_stack")
    if not should_run_agent(agent_name, gen_type):
        logger.info(f"[{project_id}] Skipping agent {agent_name} (Group: {get_group_for_agent(agent_name)}) based on generation type {gen_type}.")
        return None

    agent = get_agent_instance(agent_name)
    db_key = get_agent_db_key(agent_name)
    project_doc = enrich_project_doc_context(project_doc)
    
    # Set tech stack and theme context variables for dynamic prompt adaptation
    from app.services.llm_router import current_tech_stack, current_theme_palette, current_generation_type
    tech_stack = project_doc.get("blueprint", {}).get("tech_stack") or project_doc.get("tech_stack")
    theme_palette = project_doc.get("theme_palette")
    
    token_tech = current_tech_stack.set(tech_stack)
    token_theme = current_theme_palette.set(theme_palette)
    token_gen_type = current_generation_type.set(gen_type)
    
    retry_count = 0
    feedback_history = []
    result = None
    
    try:
        while retry_count <= 3:
            if feedback_history:
                cumulative_feedback = "\n\n".join([f"Attempt {i+1} Issue:\n{fb}" for i, fb in enumerate(feedback_history)])
            else:
                cumulative_feedback = None
                
            token = current_agent_feedback.set(cumulative_feedback)
            try:
                if agent_name == "RequirementAnalyzerAgent":
                    blueprint = project_doc.get("blueprint") or project_doc.get("initial_prompt", {}) or {}
                    result = await agent.analyze(blueprint, project_doc.get("theme"), gen_type)
                elif agent_name == "PlannerAgent":
                    result = await agent.plan(project_doc.get("requirements", {}))
                elif agent_name == "ResearchPlanningAgent":
                    result = await agent.generate_plan(
                        project_doc.get("requirements", {}),
                        project_doc.get("planning", {}),
                        project_doc.get("codebase", []),
                        gen_type
                    )
                else:
                    result = await call_agent_design(agent_name, agent, project_doc, cumulative_feedback)
            except IncompleteJSONError as e:
                logger.warning(f"LangGraph caught IncompleteJSONError for {agent_name}")
                result = e
            except Exception as e:
                logger.error(f"LangGraph caught generic error for {agent_name}: {e}")
                result = {"_error": "GenericError", "message": str(e)}
            finally:
                current_agent_feedback.reset(token)
                
            verifier = VerifierAgent()
            is_complete, new_feedback = await verifier.verify(agent_name, block_err := result)
            
            if is_complete:
                if result:
                    await db.projects.update_one({"_id": project_id}, {"$set": {db_key: result}})
                    project_doc[db_key] = result
                return result
            else:
                retry_count += 1
                feedback_history.append(new_feedback)
                logger.warning(f"Verifier feedback for {agent_name} (retry {retry_count}): {new_feedback}")
                
        logger.error(f"Max retries reached for {agent_name}. Advancing anyway.")
        if result:
            await db.projects.update_one({"_id": project_id}, {"$set": {db_key: result}})
            project_doc[db_key] = result
        return result
    finally:
        current_tech_stack.reset(token_tech)
        current_theme_palette.reset(token_theme)
        current_generation_type.reset(token_gen_type)

def get_db(state: AppState, config: Any = None) -> Any:
    if config and hasattr(config, "get") and config.get("configurable"):
        db = config.get("configurable", {}).get("db")
        if db is not None:
            return db
    elif config and hasattr(config, "configurable"):
        db = getattr(config, "configurable", {}).get("db")
        if db is not None:
            return db
    from app.db.mongodb import get_database
    return get_database()

# ──────────────────────────────────────────────────────────────
# Graph Nodes
# ──────────────────────────────────────────────────────────────

async def requirement_analyzer_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    requirements = project_doc.get("requirements")
    if requirements:
        logger.info(f"[{project_id}] RequirementAnalyzerAgent output already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "latest_output": requirements}
        
    await broadcast_agent_progress(db, project_id, 3, "Analyzing Requirements...")
    res = await run_single_agent(db, project_id, project_doc, "RequirementAnalyzerAgent")
    await broadcast_agent_progress(db, project_id, 5, "Requirements Analysis Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def planner_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    planning = project_doc.get("planning")
    if planning:
        logger.info(f"[{project_id}] PlannerAgent output already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "latest_output": planning}
        
    await broadcast_agent_progress(db, project_id, 6, "Planning Orchestration...")
    res = await run_single_agent(db, project_id, project_doc, "PlannerAgent")
    await broadcast_agent_progress(db, project_id, 10, "Planning Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def research_planning_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    impl_plan = project_doc.get("implementation_plan")
    if impl_plan:
        logger.info(f"[{project_id}] ResearchPlanningAgent output (Implementation Plan) already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "implementation_plan": impl_plan, "latest_output": impl_plan}
        
    await broadcast_agent_progress(db, project_id, 11, "Creating Research & Planning Blueprint...")
    res = await run_single_agent(db, project_id, project_doc, "ResearchPlanningAgent")
    await broadcast_agent_progress(db, project_id, 14, "Research & Planning Complete.")
    return {"project_doc": project_doc, "implementation_plan": res, "latest_output": res}

ARCHITECTURE_RESET_FIELDS = (
    "db_architecture", "database_model_generation",
    "backend_architecture", "api_architecture", "api_implementation",
    "frontend_architecture", "theme_styling", "ui_component_generation",
    "state_management", "state_implementation",
    "auth_architecture", "realtime_architecture", "devops_architecture",
    "security_architecture", "testing_architecture", "validation_architecture",
    "optimization_architecture", "code_generation_plan",
    "backend_code_generation", "frontend_code_generation",
    "integration_generation", "build_compilation", "error_correction", "project_export",
    "synthesized_codebase", "codebase",
)


async def reset_architecture_outputs(db: Any, project_id: str) -> None:
    """Clear cached architecture/codegen outputs so correction loops re-execute agents."""
    unset_fields = {field: "" for field in ARCHITECTURE_RESET_FIELDS}
    await db.projects.update_one({"_id": project_id}, {"$unset": unset_fields})
    logger.warning(f"[{project_id}] Cleared architecture outputs for correction loop retry.")


async def agent_dispatcher_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    retry_count = state.get("retry_count", 0)
    if retry_count > 0 and state.get("validation_logs"):
        await reset_architecture_outputs(db, project_id)
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "agent_context": project_doc.get("agent_context", {}),
            "workflow_phase": "architecture",
        }},
    )
    logger.info(f"Agent dispatcher running. Starting sequential architecture workspaces for {project_id}...")
    return {"project_doc": project_doc}

async def db_workspace_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Database Workspace Subgraph for {project_id}...")
    await broadcast_agent_progress(db, project_id, 15, "Designing Database Architecture...")
    await run_single_agent(db, project_id, project_doc, "DatabaseArchitectureAgent")
    # Re-fetch after each agent so next agent sees fresh data
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 20, "Generating Database Models...")
    await run_single_agent(db, project_id, project_doc, "DatabaseModelGenerationAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 25, "Database Workspace Complete.")
    return {"project_doc": project_doc}

async def backend_workspace_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Backend Workspace Subgraph for {project_id}...")
    await broadcast_agent_progress(db, project_id, 26, "Designing Backend Architecture...")
    await run_single_agent(db, project_id, project_doc, "BackendArchitectureAgent")
    # Re-fetch after each agent so next agent sees fresh data
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 31, "Designing API Architecture...")
    await run_single_agent(db, project_id, project_doc, "APIAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 36, "Generating API Implementation...")
    await run_single_agent(db, project_id, project_doc, "APIImplementationAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 40, "Backend Workspace Complete.")
    return {"project_doc": project_doc}

async def frontend_workspace_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Frontend Workspace Subgraph for {project_id}...")
    await broadcast_agent_progress(db, project_id, 41, "Designing Frontend Architecture...")
    await run_single_agent(db, project_id, project_doc, "FrontendArchitectureAgent")
    # Re-fetch after each agent so next agent sees fresh data
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 44, "Designing UI/UX Theme & Styling...")
    await run_single_agent(db, project_id, project_doc, "UIUXArchitectAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 47, "Generating UI Components...")
    await run_single_agent(db, project_id, project_doc, "UIComponentGenerationAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 50, "Designing State Management...")
    await run_single_agent(db, project_id, project_doc, "StateManagementAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 53, "Generating State Implementation...")
    await run_single_agent(db, project_id, project_doc, "StateImplementationAgent")
    await broadcast_agent_progress(db, project_id, 55, "Frontend Workspace Complete.")
    return {"project_doc": project_doc}

async def architecture_design_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    gen_type = project_doc.get("generation_type", "full_stack")
    logger.info(f"[{project_id}] Running concurrent architecture design workspaces for generation_type: {gen_type}...")
    
    tasks = []
    
    if gen_type != "frontend_only":
        async def run_db_backend():
            # Run DB workspace sequentially
            doc = await db.projects.find_one({"_id": project_id}) or project_doc
            res_db = await db_workspace_node({"project_id": project_id, "project_doc": doc}, config)
            
            # Run Backend workspace sequentially after DB workspace
            doc_next = await db.projects.find_one({"_id": project_id}) or res_db.get("project_doc") or project_doc
            res_be = await backend_workspace_node({"project_id": project_id, "project_doc": doc_next}, config)
            return res_be
            
        tasks.append(run_db_backend())
        
    if gen_type not in ("backend_only", "microservice"):
        async def run_frontend():
            doc = await db.projects.find_one({"_id": project_id}) or project_doc
            return await frontend_workspace_node({"project_id": project_id, "project_doc": doc}, config)
            
        tasks.append(run_frontend())
        
    if tasks:
        await asyncio.gather(*tasks)
        
    # Re-fetch the fully updated project document after parallel workspaces complete
    final_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    return {"project_doc": final_doc}

async def ops_security_workspace_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Operations & Security Workspace Subgraph for {project_id}...")
    await broadcast_agent_progress(db, project_id, 56, "Designing Auth Architecture...")
    await run_single_agent(db, project_id, project_doc, "AuthArchitectureAgent")
    # Re-fetch after each agent so next agent sees fresh data
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 58, "Designing Realtime Architecture...")
    await run_single_agent(db, project_id, project_doc, "RealtimeArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 60, "Designing DevOps Architecture...")
    await run_single_agent(db, project_id, project_doc, "DevOpsArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 62, "Designing Security Architecture...")
    await run_single_agent(db, project_id, project_doc, "SecurityArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 64, "Designing Testing Architecture...")
    await run_single_agent(db, project_id, project_doc, "TestingArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 66, "Designing Validation Architecture...")
    await run_single_agent(db, project_id, project_doc, "ValidationArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 68, "Designing Optimization Architecture...")
    await run_single_agent(db, project_id, project_doc, "OptimizationArchitectureAgent")
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 70, "Ops & Security Workspace Complete.")
    return {"project_doc": project_doc}

async def join_workspaces_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    # Log workspace completion status
    workspace_status = {
        "db": bool(project_doc.get("db_architecture") and project_doc.get("database_model_generation")),
        "backend": bool(project_doc.get("backend_architecture") and project_doc.get("api_architecture")),
        "frontend": bool(project_doc.get("frontend_architecture") and project_doc.get("theme_styling")),
        "ops_security": bool(project_doc.get("auth_architecture") and project_doc.get("security_architecture")),
    }
    logger.info(f"Workspace merge status for {project_id}: {workspace_status}")
    
    gen_type = project_doc.get("generation_type", "full_stack")
    expected_workspaces = ["ops_security"]
    if gen_type != "frontend_only":
        expected_workspaces.extend(["db", "backend"])
    if gen_type not in ("backend_only", "microservice"):
        expected_workspaces.append("frontend")
        
    missing = [k for k in expected_workspaces if not workspace_status[k]]
    if missing:
        logger.warning(f"Incomplete workspaces detected: {missing}")
    
    project_doc = enrich_project_doc_context(project_doc)
    agent_context = build_compilation_context({
        k: project_doc.get(k) for k in (
            "requirements", "planning", "db_architecture", "backend_architecture",
            "api_architecture", "frontend_architecture", "theme_styling",
            "auth_architecture", "realtime_architecture", "state_management",
            "devops_architecture", "security_architecture", "testing_architecture",
            "validation_architecture", "optimization_architecture",
            "code_generation_plan", "database_model_generation",
            "backend_code_generation", "api_implementation", "frontend_code_generation",
            "ui_component_generation", "state_implementation",
            "integration_generation", "build_compilation", "error_correction",
            "project_export", "implementation_plan",
        ) if project_doc.get(k)
    })
    project_doc["agent_context"] = agent_context
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"agent_context": agent_context, "workflow_phase": "codegen"}},
    )
    
    await broadcast_agent_progress(db, project_id, 71, "Merging Sequential Workspace Results...")
    return {"project_doc": project_doc}

async def verifier_guardrail_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 71, "Running Verifier State Guardrails...")
    logger.info("Running Enhanced Verifier State Guardrails...")
    validation_logs = []
    
    db_arch = project_doc.get("db_architecture", {}) or {}
    be_arch = project_doc.get("backend_architecture", {}) or {}
    fe_arch = project_doc.get("frontend_architecture", {}) or {}
    api_arch = project_doc.get("api_architecture", {}) or {}
    auth_arch = project_doc.get("auth_architecture", {}) or {}
    requirements = project_doc.get("requirements", {}) or {}
    theme_styling = project_doc.get("theme_styling", {}) or {}
    state_mgmt = project_doc.get("state_management", {}) or {}
    impl_plan = project_doc.get("implementation_plan", {}) or {}
    security_arch = project_doc.get("security_architecture", {}) or {}
    
    gen_type = project_doc.get("generation_type", "full_stack")
    
    # 1. Entity existence check (Only if not frontend_only)
    db_entities = set()
    for e in db_arch.get("entities", []):
        if isinstance(e, dict) and e.get("entity_name"):
            db_entities.add(e["entity_name"])
        elif isinstance(e, str):
            db_entities.add(e)
    if gen_type != "frontend_only":
        if not db_entities:
            validation_logs.append({"module": "Database", "error": "No entities defined in db_architecture."})
    
    # 2. API endpoints exist for entities (Only if not frontend_only)
    api_endpoints = api_arch.get("endpoints", [])
    if gen_type != "frontend_only":
        if db_entities and not api_endpoints:
            validation_logs.append({"module": "API", "error": "No API endpoints defined despite having entities."})
    
    # 3. Frontend pages exist (Only if not backend_only or microservice)
    fe_pages = fe_arch.get("pages", [])
    if gen_type not in ("backend_only", "microservice"):
        if not fe_pages and not fe_arch.get("structure"):
            validation_logs.append({"module": "Frontend", "error": "No frontend pages defined."})
    
    # 4. Auth architecture exists if auth is needed (Only if not frontend_only)
    has_auth_endpoints = any(
        (ep.get("requires_auth") if isinstance(ep, dict) else False)
        for ep in api_endpoints
    )
    if gen_type != "frontend_only":
        if has_auth_endpoints and not auth_arch:
            validation_logs.append({"module": "Auth", "error": "Endpoints require auth but no auth_architecture defined."})
    
    # 5. Minimum feature scope from PRD/requirements (Applies to all)
    features = requirements.get("features", []) if isinstance(requirements, dict) else []
    if isinstance(features, list) and len(features) < 5:
        validation_logs.append({
            "module": "Requirements",
            "error": f"Only {len(features)} features defined — production projects require at least 5 interconnected features.",
        })

    # 6. Minimum page scope (Only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice"):
        if fe_pages and len(fe_pages) < 5:
            validation_logs.append({
                "module": "Frontend",
                "severity": "warning",
                "error": f"Only {len(fe_pages)} frontend pages — production apps need at least 5 pages/modules.",
            })

    # 7. PRD/TRD/MRD must exist as generation source of truth (Applies to all)
    if not project_doc.get("prd") or not project_doc.get("trd"):
        validation_logs.append({
            "module": "Documents",
            "error": "PRD and TRD must be present before architecture compilation.",
        })

    # 8. Implementation plan must exist (Applies to all)
    if not impl_plan:
        validation_logs.append({"module": "ImplementationPlan", "error": "No implementation_plan defined."})
        
    # 9. Backend architecture exists (warning, only if not frontend_only)
    if gen_type != "frontend_only":
        if not be_arch:
            validation_logs.append({"module": "Backend", "severity": "warning", "error": "No backend_architecture defined."})
    
    # 10. Theme/styling exists (warning, only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice"):
        if not theme_styling:
            validation_logs.append({"module": "ThemeStyling", "severity": "warning", "error": "No theme_styling defined."})
    
    # 11. State management exists (warning, only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice"):
        if not state_mgmt:
            validation_logs.append({"module": "StateManagement", "severity": "warning", "error": "No state_management defined."})
            
    # 12. Cross-reference: entities in db_architecture should have corresponding API endpoints (Only if not frontend_only)
    if gen_type != "frontend_only" and db_entities and api_endpoints:
        endpoint_paths = set()
        for ep in api_endpoints:
            if isinstance(ep, dict):
                endpoint_paths.add(ep.get("path", "").lower())
                endpoint_paths.add(ep.get("resource", "").lower())
        uncovered_entities = []
        for entity in db_entities:
            entity_lower = entity.lower().replace("_", "").replace("-", "")
            has_endpoint = any(entity_lower in p.lower().replace("_", "").replace("-", "") for p in endpoint_paths if p)
            if not has_endpoint:
                uncovered_entities.append(entity)
        if uncovered_entities:
            validation_logs.append({
                "module": "CrossRef-API",
                "severity": "warning",
                "error": f"Entities without matching API endpoints: {uncovered_entities}",
            })
    
    # 13. Cross-reference: pages in frontend_architecture should have routes (Only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice") and fe_pages:
        pages_without_routes = []
        for page in fe_pages:
            if isinstance(page, dict):
                has_route = page.get("route") or page.get("path") or page.get("url")
                if not has_route:
                    page_name = page.get("name") or page.get("page_name") or str(page)
                    pages_without_routes.append(page_name)
        if pages_without_routes:
            validation_logs.append({
                "module": "CrossRef-Routes",
                "severity": "warning",
                "error": f"Frontend pages without routes: {pages_without_routes}",
            })
    
    # 13. Cross-reference: pages in frontend_architecture should have routes
    if validation_logs:
        logger.warning(f"Verifier guardrail found {len(validation_logs)} issues: {validation_logs}")
        critical_modules = ("Database", "Requirements", "Documents", "ImplementationPlan", "API", "Frontend", "Auth")
        critical = [
            v for v in validation_logs
            if v.get("module") in critical_modules and v.get("severity") != "warning"
        ]
        await db.projects.update_one({"_id": project_id}, {"$set": {"validation_logs": validation_logs}})
        if critical:
            retry_count = state.get("retry_count", 0) + 1
            return {
                "validation_logs": validation_logs,
                "hitl_approved": False,
                "retry_count": retry_count,
            }
    
    await broadcast_agent_progress(db, project_id, 73, "Verifier Guardrail Complete.")
    logger.info("Verifier guardrail passed — all critical checks OK")
    return {"validation_logs": [], "hitl_approved": True, "retry_count": state.get("retry_count", 0)}

async def code_gen_planner_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 74, "Compiling Code Generation Plan...")
    res = await run_single_agent(db, project_id, project_doc, "CodeGenerationPlannerAgent")
    await broadcast_agent_progress(db, project_id, 76, "Code Generation Plan Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def backend_code_generation_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    gen_type = project_doc.get("generation_type", "full_stack")
    if gen_type == "frontend_only":
        logger.info(f"[{project_id}] Skipping Backend Code Generation for frontend_only project.")
        return {"project_doc": project_doc}
        
    await broadcast_agent_progress(db, project_id, 77, "Generating Backend Code Contracts...")
    res = await run_single_agent(db, project_id, project_doc, "BackendCodeGenerationAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def frontend_code_generation_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    gen_type = project_doc.get("generation_type", "full_stack")
    if gen_type in ("backend_only", "microservice"):
        logger.info(f"[{project_id}] Skipping Frontend Code Generation for backend_only or microservice project.")
        return {"project_doc": project_doc}
        
    await broadcast_agent_progress(db, project_id, 78, "Generating Frontend Code Contracts...")
    res = await run_single_agent(db, project_id, project_doc, "FrontendCodeGenerationAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def integration_generator_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 79, "Integrating Workspace Components...")
    res = await run_single_agent(db, project_id, project_doc, "IntegrationGenerationAgent")
    await broadcast_agent_progress(db, project_id, 80, "Integration Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def build_compiler_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 80, "Running Compilation Checks...")
    res = await run_single_agent(db, project_id, project_doc, "BuildCompilationAgent")
    await broadcast_agent_progress(db, project_id, 82, "Compilation Checks Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def error_correction_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 83, "Applying Error Self-Correction...")
    res = await run_single_agent(db, project_id, project_doc, "ErrorCorrectionAgent")
    await broadcast_agent_progress(db, project_id, 85, "Error Correction Complete.")
    return {"project_doc": project_doc, "latest_output": res}

async def finalize_project_delivery(
    db: Any,
    project_id: str,
    project_doc: Optional[Dict[str, Any]] = None,
    synthesized_codebase: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Assemble the final connected file tree and persist completion state."""
    latest_project_doc = project_doc or await db.projects.find_one({"_id": project_id}) or {}
    if latest_project_doc.get("status") == "completed" and latest_project_doc.get("codebase"):
        return latest_project_doc

    # Use synthesized codebase (from CodeSynthesizerAgent) as the AI-generated files
    ai_codebase = synthesized_codebase or latest_project_doc.get("synthesized_codebase", [])
    assembly = assemble_project_codebase(latest_project_doc, ai_codebase=ai_codebase if ai_codebase else None)
    quality_report = assembly["quality_report"]
    quality_status = quality_report.get("status", "passed")
    final_status = "completed" if quality_status != "failed" else "completed_with_issues"
    await db.projects.update_one(
        {"_id": project_id},
        {
            "$set": {
                "progress": 100,
                "status": final_status,
                "step": "Project Ready" if final_status == "completed" else "Project Ready (Quality Review Recommended)",
                "summary": assembly["summary"],
                "codebase": assembly["codebase"],
                "quality_report": quality_report,
                "generated_project_contract": assembly["generated_project_contract"],
                "completion_notified": True,
            }
        },
    )

    chat_id = latest_project_doc.get("chat_id")
    if chat_id and not latest_project_doc.get("completion_notified"):
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        await db.chats.update_one(
            {"_id": chat_id},
            {
                "$push": {
                    "messages": {
                        "id": f"m-{uuid.uuid4().hex[:8]}",
                        "sender": "ai",
                        "text": (
                            f"Your project **{latest_project_doc.get('name', 'Sarthi Project')}** is ready. "
                            "Sarthi assembled the connected codebase, ran quality gates, and packaged it for download."
                        ),
                        "timestamp": time_str,
                    }
                },
                "$set": {"completion_notified": True},
            },
        )

    from app.services.ws_manager import manager
    await manager.broadcast_progress(
        project_id=project_id,
        progress=100,
        step="Project Ready",
        status="completed",
    )
    return await db.projects.find_one({"_id": project_id}) or latest_project_doc

async def code_synthesis_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Multi-phase code synthesis — generates actual source code files from architecture."""
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    existing_codebase = project_doc.get("synthesized_codebase")
    if existing_codebase and len(existing_codebase) > 15:
        logger.info(f"[{project_id}] Code already synthesized ({len(existing_codebase)} files). Skipping.")
        return {"project_doc": project_doc}
    
    await broadcast_agent_progress(db, project_id, 86, "🚀 Starting Multi-Phase Code Synthesis...")
    
    synthesizer = CodeSynthesizerAgent()
    validator = CodeValidatorAgent()
    arch_context = {
        "db_architecture": project_doc.get("db_architecture", {}),
        "api_architecture": project_doc.get("api_architecture", {}),
        "frontend_architecture": project_doc.get("frontend_architecture", {}),
        "implementation_plan": project_doc.get("implementation_plan", {}),
        "requirements": project_doc.get("requirements", {}),
        "blueprint": project_doc.get("blueprint", {}) or project_doc.get("initial_prompt", {}),
        "generation_type": project_doc.get("generation_type", "full_stack"),
    }
    
    codebase: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    max_synthesis_attempts = 3
    for attempt in range(1, max_synthesis_attempts + 1):
        if attempt > 1:
            await broadcast_agent_progress(
                db, project_id, 88,
                f"🔁 Re-synthesizing & healing code (attempt {attempt}/{max_synthesis_attempts})..."
            )
            project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
            critical_issues = [i for i in issues if i.get("severity") == "error"]
            codebase = await synthesizer.synthesize(
                project_doc, db, project_id,
                validation_errors=critical_issues,
                existing_codebase=codebase
            )
        else:
            codebase = await synthesizer.synthesize(project_doc, db, project_id)
            
        issues = validator.validate(codebase, arch_context)
        critical_issues = [i for i in issues if i.get("severity") == "error"]
        if not critical_issues or attempt == max_synthesis_attempts:
            break
        logger.warning(
            f"[{project_id}] Synthesis attempt {attempt} produced {len(critical_issues)} critical issues — triggering self-healing loop."
        )
        await db.projects.update_one(
            {"_id": project_id},
            {"$unset": {"synthesized_codebase": ""}},
        )
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "synthesized_codebase": codebase,
            "synthesis_validation": {
                "total_files": len(codebase),
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.get("severity") == "error"]),
                "issues": issues[:50],
            },
        }}
    )
    project_doc["synthesized_codebase"] = codebase
    
    logger.info(f"[{project_id}] Code synthesis complete: {len(codebase)} files, {len(issues)} issues")
    return {"project_doc": project_doc}

async def project_export_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 95, "Packaging Workspace Artifacts...")
    res = await run_single_agent(db, project_id, project_doc, "ProjectExportAgent")
    project_doc["project_export"] = res

    await broadcast_agent_progress(db, project_id, 99, "Assembling Connected Codebase...")
    latest_project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    latest_project_doc["project_export"] = latest_project_doc.get("project_export") or res
    
    # Feed synthesized code to the assembler for final merge + validation
    synthesized_codebase = latest_project_doc.get("synthesized_codebase", [])
    updated_doc = await finalize_project_delivery(db, project_id, latest_project_doc, synthesized_codebase)
    return {
        "project_doc": updated_doc,
        "latest_output": res,
        "quality_report": updated_doc.get("quality_report"),
    }

async def runtime_compilation_verifier_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 91, "🔍 Running Runtime Verification & Compile-Checks...")
    
    from app.agents.runtime_verifier import RuntimeVerifierAgent
    verifier = RuntimeVerifierAgent()
    updated_doc = await verifier.verify_and_heal(project_doc, db, project_id)
    
    await broadcast_agent_progress(db, project_id, 94, "✅ Runtime Verification & Auto-Healing Complete!")
    return {"project_doc": updated_doc}

# ──────────────────────────────────────────────────────────────
# Routing Logic
# ──────────────────────────────────────────────────────────────

def route_after_planner(state: AppState) -> str:
    hitl_enabled = state.get("hitl_enabled", True)
    if hitl_enabled:
        return "research_planning"
    return "agent_dispatcher"

def route_dispatcher(state: AppState) -> List[str]:
    """Dynamically route and branch workspaces in parallel depending on generation_type."""
    project_doc = state.get("project_doc", {}) or {}
    gen_type = project_doc.get("generation_type", "full_stack")
    
    if gen_type == "frontend_only":
        return ["frontend_workspace"]
    elif gen_type in ("backend_only", "microservice"):
        return ["db_workspace"]
    else:
        # full_stack: execute DB/Backend branch and Frontend branch in parallel
        return ["db_workspace", "frontend_workspace"]

def route_after_verifier(state: AppState) -> str:
    from app.agents.context import MAX_CORRECTION_LOOPS
    validation_logs = state.get("validation_logs", [])
    retry_count = state.get("retry_count", 0)
    
    if validation_logs and retry_count < MAX_CORRECTION_LOOPS:
        # Route back to dispatcher for correction loop (with limit)
        logger.warning(f"Verifier found issues (attempt {retry_count + 1}/{MAX_CORRECTION_LOOPS}). Routing to correction loop.")
        return "agent_dispatcher"
    elif validation_logs:
        # Max correction loops reached — force proceed to avoid infinite loop
        logger.warning(f"Max correction loops ({MAX_CORRECTION_LOOPS}) reached. Proceeding to code generation despite {len(validation_logs)} validation issues.")
    return "code_gen_planner"

# ──────────────────────────────────────────────────────────────
# Graph Builder
# ──────────────────────────────────────────────────────────────

memory_saver = MemorySaver()

def build_graph() -> StateGraph:
    workflow = StateGraph(AppState)
    
    # Register all nodes
    workflow.add_node("requirement_analyzer", requirement_analyzer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research_planning", research_planning_node)
    workflow.add_node("agent_dispatcher", agent_dispatcher_node)
    
    workflow.add_node("architecture_design", architecture_design_node)
    workflow.add_node("ops_security_workspace", ops_security_workspace_node)
    
    workflow.add_node("join_workspaces", join_workspaces_node)
    workflow.add_node("verifier_guardrail", verifier_guardrail_node)
    
    workflow.add_node("code_gen_planner", code_gen_planner_node)
    workflow.add_node("backend_code_generation", backend_code_generation_node)
    workflow.add_node("frontend_code_generation", frontend_code_generation_node)
    workflow.add_node("integration_generator", integration_generator_node)
    workflow.add_node("build_compiler", build_compiler_node)
    workflow.add_node("error_correction", error_correction_node)
    workflow.add_node("code_synthesis", code_synthesis_node)
    workflow.add_node("runtime_compilation_verifier", runtime_compilation_verifier_node)
    workflow.add_node("project_export", project_export_node)
    
    # Edges
    workflow.set_entry_point("requirement_analyzer")
    workflow.add_edge("requirement_analyzer", "planner")
    
    workflow.add_conditional_edges("planner", route_after_planner, {
        "research_planning": "research_planning",
        "agent_dispatcher": "agent_dispatcher"
    })
    
    workflow.add_edge("research_planning", "agent_dispatcher")
    
    # Sequential architecture workspaces — downstream agents always see upstream contracts
    workflow.add_edge("agent_dispatcher", "architecture_design")
    workflow.add_edge("architecture_design", "join_workspaces")
    workflow.add_edge("join_workspaces", "ops_security_workspace")
    workflow.add_edge("ops_security_workspace", "verifier_guardrail")
    
    workflow.add_conditional_edges("verifier_guardrail", route_after_verifier, {
        "code_gen_planner": "code_gen_planner",
        "agent_dispatcher": "agent_dispatcher"
    })
    
    # Codegen chain — TRD/Implementation Plan drive synthesis contracts
    workflow.add_edge("code_gen_planner", "backend_code_generation")
    workflow.add_edge("backend_code_generation", "frontend_code_generation")
    workflow.add_edge("frontend_code_generation", "integration_generator")
    workflow.add_edge("integration_generator", "build_compiler")
    workflow.add_edge("build_compiler", "error_correction")
    workflow.add_edge("error_correction", "code_synthesis")
    workflow.add_edge("code_synthesis", "runtime_compilation_verifier")
    workflow.add_edge("runtime_compilation_verifier", "project_export")
    workflow.add_edge("project_export", END)
    
    # Compile graph with interruption before dispatcher node
    return workflow.compile(
        checkpointer=memory_saver,
        interrupt_before=["agent_dispatcher"]
    )

async def compile_project_workflow(db: Any, project_id: str, project_doc: Dict[str, Any]):
    from app.core.logger import current_project_id
    current_project_id.set(project_id)
    app = build_graph()
    config = {"configurable": {"thread_id": project_id, "db": db}}
    
    initial_state = {
        "project_id": project_id,
        "project_doc": project_doc,
        "current_index": 0,
        "feedback": None,
        "retry_count": 0,
        "latest_output": None,
        "implementation_plan": project_doc.get("implementation_plan"),
        "hitl_approved": project_doc.get("hitl_approved", False),
        "hitl_enabled": project_doc.get("hitl_enabled", True),
        "active_dynamic_agents": project_doc.get("active_dynamic_agents", []),
        "validation_logs": project_doc.get("validation_logs", []),
        "quality_report": project_doc.get("quality_report")
    }
    
    # Run the graph
    state_info = await app.aget_state(config)
    if not state_info.next:
        await app.ainvoke(initial_state, config)
        
    while True:
        state_info = await app.aget_state(config)
        if not state_info.next:
            break
            
        if "agent_dispatcher" in state_info.next:
            latest_proj = await db.projects.find_one({"_id": project_id})
            hitl_enabled = latest_proj.get("hitl_enabled", True)
            hitl_approved = latest_proj.get("hitl_approved", False)
            
            if hitl_enabled and not hitl_approved:
                # Suspend and wait for user approval
                impl_plan = state_info.values.get("implementation_plan")
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$set": {
                        "status": "waiting_approval",
                        "step": "Awaiting Implementation Plan Approval",
                        "progress": 15,
                        "implementation_plan": impl_plan
                    }}
                )
                from app.services.ws_manager import manager
                await manager.broadcast_progress(
                    project_id=project_id,
                    progress=15,
                    step="Awaiting Implementation Plan Approval",
                    status="waiting_approval"
                )
                logger.info(f"Graph execution suspended for project {project_id}. Awaiting HITL approval.")
                return
            else:
                # Resume execution
                logger.info(f"Resuming project {project_id} past the dispatcher gate...")
                await app.ainvoke(None, config)
        else:
            await app.ainvoke(None, config)

    latest_proj = await db.projects.find_one({"_id": project_id})
    if latest_proj and latest_proj.get("project_export") and latest_proj.get("status") != "completed":
        await broadcast_agent_progress(db, project_id, 100, "Finalizing Project Delivery...")
        await finalize_project_delivery(db, project_id, latest_proj)

async def resume_project_workflow(db: Any, project_id: str, plan_edits: Optional[Dict[str, Any]] = None):
    """Resume a suspended workflow or start fresh if no checkpoint exists.
    
    There are two scenarios:
    1. The workflow was started via compile_project_workflow and paused at the
       agent_dispatcher interrupt gate → we resume the LangGraph checkpoint.
    2. The project was created with synchronous HITL (req + plan + research ran
       outside the graph) → no checkpoint exists → we start the full workflow.
    """
    from app.core.logger import current_project_id
    current_project_id.set(project_id)
    
    try:
        app = build_graph()
        config = {"configurable": {"thread_id": project_id, "db": db}}
        
        state_info = await app.aget_state(config)
        has_checkpoint = bool(state_info.next)
        
        # Apply plan edits to DB first
        db_updates = {
            "status": "generating",
            "progress": 20,
            "step": "Resuming codebase compilation...",
            "hitl_approved": True
        }
        if plan_edits:
            db_updates["implementation_plan"] = plan_edits

        await db.projects.update_one(
            {"_id": project_id},
            {"$set": db_updates}
        )
        
        from app.services.ws_manager import manager
        await manager.broadcast_progress(
            project_id=project_id,
            progress=20,
            step="Resuming codebase compilation..."
        )
        
        if has_checkpoint:
            # Scenario 1: Graph was suspended at interrupt → resume it
            logger.info(f"[{project_id}] Found suspended checkpoint at {state_info.next}. Resuming graph...")
            updates = {"hitl_approved": True}
            if plan_edits:
                updates["implementation_plan"] = plan_edits
            await app.aupdate_state(config, updates)
            
            # Continue the graph from where it was suspended
            latest_proj = await db.projects.find_one({"_id": project_id})
            await compile_project_workflow(db, project_id, latest_proj)
        else:
            # Scenario 2: No checkpoint — HITL ran synchronously during project creation
            # Start the full workflow from scratch (it will skip already-computed phases)
            logger.info(f"[{project_id}] No suspended checkpoint found. Starting full workflow from scratch (HITL sync path).")
            latest_proj = await db.projects.find_one({"_id": project_id})
            if not latest_proj:
                logger.error(f"[{project_id}] Project not found in database!")
                return
            
            # Ensure the project has the initial_prompt set
            if not latest_proj.get("initial_prompt"):
                latest_proj["initial_prompt"] = latest_proj.get("blueprint", {}) or {
                    "name": latest_proj.get("name", ""),
                    "idea": latest_proj.get("summary", ""),
                    "features": [],
                }
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$set": {"initial_prompt": latest_proj["initial_prompt"]}}
                )
            
            await compile_project_workflow(db, project_id, latest_proj)
            
    except Exception as e:
        logger.error(f"[{project_id}] resume_project_workflow FAILED: {e}", exc_info=True)
        await db.projects.update_one(
            {"_id": project_id},
            {"$set": {
                "status": "failed",
                "step": f"Compilation Error: {str(e)}",
                "progress": 100
            }}
        )
        from app.services.ws_manager import manager
        await manager.broadcast_progress(
            project_id=project_id,
            progress=100,
            step=f"Compilation Error: {str(e)}",
            status="failed"
        )

