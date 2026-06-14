import inspect
from typing import Dict, Any, TypedDict, Optional, List
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.context import IncompleteJSONError
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

async def broadcast_agent_progress(db: Any, project_id: str, progress: int, step: str) -> None:
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"progress": progress, "step": step}}
    )
    from app.services.ws_manager import manager
    await manager.broadcast_progress(
        project_id=project_id,
        progress=progress,
        step=step
    )
    logger.info(f"Project {project_id} progress: {progress}% - {step}")

class AppState(TypedDict):
    project_id: str
    project_doc: Dict[str, Any]
    current_index: int
    feedback: Optional[str]
    retry_count: int
    latest_output: Any
    
    # Sarthi 2.0 Orchestration State
    implementation_plan: Optional[Dict[str, Any]]
    hitl_approved: bool
    hitl_enabled: bool
    active_dynamic_agents: List[str]
    validation_logs: List[Dict[str, Any]]

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

async def run_single_agent(db: Any, project_id: str, project_doc: Dict[str, Any], agent_name: str) -> Any:
    """Executes a single agent node with verification and fallback retries."""
    agent = get_agent_instance(agent_name)
    db_key = get_agent_db_key(agent_name)
    
    retry_count = 0
    feedback = None
    result = None
    
    while retry_count <= 3:
        token = current_agent_feedback.set(feedback)
        try:
            if agent_name == "RequirementAnalyzerAgent":
                result = await agent.analyze(project_doc.get("initial_prompt", ""))
            elif agent_name == "PlannerAgent":
                result = await agent.plan(project_doc.get("requirements", {}))
            elif agent_name == "ResearchPlanningAgent":
                result = await agent.generate_plan(
                    project_doc.get("requirements", {}),
                    project_doc.get("planning", {}),
                    project_doc.get("codebase", [])
                )
            else:
                result = await call_agent_design(agent_name, agent, project_doc, feedback)
        except IncompleteJSONError as e:
            logger.warning(f"LangGraph caught IncompleteJSONError for {agent_name}")
            result = e
        except Exception as e:
            logger.error(f"LangGraph caught generic error for {agent_name}: {e}")
            result = {"_error": "GenericError", "message": str(e)}
        finally:
            current_agent_feedback.reset(token)
            
        verifier = VerifierAgent()
        is_complete, new_feedback = await verifier.verify(agent_name, result)
        
        if is_complete:
            if result:
                await db.projects.update_one({"_id": project_id}, {"$set": {db_key: result}})
                project_doc[db_key] = result
            return result
        else:
            retry_count += 1
            feedback = new_feedback
            logger.warning(f"Verifier feedback for {agent_name} (retry {retry_count}): {feedback}")
            
    logger.error(f"Max retries reached for {agent_name}. Advancing anyway.")
    if result:
        await db.projects.update_one({"_id": project_id}, {"$set": {db_key: result}})
        project_doc[db_key] = result
    return result

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

async def requirement_analyzer_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    requirements = project_doc.get("requirements")
    if requirements:
        logger.info(f"[{project_id}] RequirementAnalyzerAgent output already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "latest_output": requirements}
        
    await broadcast_agent_progress(db, project_id, 5, "Analyzing Requirements...")
    res = await run_single_agent(db, project_id, project_doc, "RequirementAnalyzerAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def planner_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    planning = project_doc.get("planning")
    if planning:
        logger.info(f"[{project_id}] PlannerAgent output already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "latest_output": planning}
        
    await broadcast_agent_progress(db, project_id, 10, "Planning Orchestration...")
    res = await run_single_agent(db, project_id, project_doc, "PlannerAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def research_planning_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    impl_plan = project_doc.get("implementation_plan")
    if impl_plan:
        logger.info(f"[{project_id}] ResearchPlanningAgent output (Implementation Plan) already exists in database. Skipping LLM execution.")
        return {"project_doc": project_doc, "implementation_plan": impl_plan, "latest_output": impl_plan}
        
    await broadcast_agent_progress(db, project_id, 12, "Creating Research & Planning Blueprint...")
    res = await run_single_agent(db, project_id, project_doc, "ResearchPlanningAgent")
    return {"project_doc": project_doc, "implementation_plan": res, "latest_output": res}

async def agent_dispatcher_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    logger.info(f"Agent dispatcher running. Spawning parallel workspaces...")
    return {}

async def db_workspace_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Database Workspace Subgraph for {project_id}...")
    await run_single_agent(db, project_id, project_doc, "DatabaseArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "DatabaseModelGenerationAgent")
    return {}

async def backend_workspace_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Backend Workspace Subgraph for {project_id}...")
    await run_single_agent(db, project_id, project_doc, "BackendArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "APIAgent")
    await run_single_agent(db, project_id, project_doc, "APIImplementationAgent")
    return {}

async def frontend_workspace_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Frontend Workspace Subgraph for {project_id}...")
    await run_single_agent(db, project_id, project_doc, "FrontendArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "UIUXArchitectAgent")
    await run_single_agent(db, project_id, project_doc, "UIComponentGenerationAgent")
    await run_single_agent(db, project_id, project_doc, "StateManagementAgent")
    await run_single_agent(db, project_id, project_doc, "StateImplementationAgent")
    return {}

async def ops_security_workspace_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info(f"Starting Operations & Security Workspace Subgraph for {project_id}...")
    await run_single_agent(db, project_id, project_doc, "AuthArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "RealtimeArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "DevOpsArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "SecurityArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "TestingArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "ValidationArchitectureAgent")
    await run_single_agent(db, project_id, project_doc, "OptimizationArchitectureAgent")
    return {}

async def join_workspaces_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info("Merging parallel workspace branches...")
    return {"project_doc": project_doc}

async def verifier_guardrail_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    logger.info("Running Verifier State Guardrails...")
    # Validate modules consistency
    validation_logs = []
    
    db_arch = project_doc.get("db_architecture", {})
    be_arch = project_doc.get("backend_architecture", {})
    fe_arch = project_doc.get("frontend_architecture", {})
    
    # Simple check for schema mismatch as a contract guardrail
    if db_arch and be_arch:
        db_entities = {e.get("entity_name") for e in db_arch.get("entities", []) if isinstance(e, dict)}
        if not db_entities:
            validation_logs.append({"module": "Database", "error": "No database entities defined in db_architecture."})
            
    # If errors exist, we log and route back to dispatcher for correction
    if validation_logs:
        logger.error(f"State guardrail failed: {validation_logs}")
        await db.projects.update_one({"_id": project_id}, {"$set": {"validation_logs": validation_logs}})
        return {"validation_logs": validation_logs, "hitl_approved": False}
        
    return {"validation_logs": [], "hitl_approved": True}

async def code_gen_planner_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 75, "Compiling Code Generation Plan...")
    res = await run_single_agent(db, project_id, project_doc, "CodeGenerationPlannerAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def integration_generator_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 80, "Integrating Workspace Components...")
    res = await run_single_agent(db, project_id, project_doc, "IntegrationGenerationAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def build_compiler_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 85, "Running Compilation Checks...")
    res = await run_single_agent(db, project_id, project_doc, "BuildCompilationAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def error_correction_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 90, "Applying Error Self-Correction...")
    res = await run_single_agent(db, project_id, project_doc, "ErrorCorrectionAgent")
    return {"project_doc": project_doc, "latest_output": res}

async def project_export_node(state: AppState, config: Any = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    await broadcast_agent_progress(db, project_id, 95, "Packaging Workspace Artifacts...")
    res = await run_single_agent(db, project_id, project_doc, "ProjectExportAgent")
    return {"project_doc": project_doc, "latest_output": res}

# ──────────────────────────────────────────────────────────────
# Routing Logic
# ──────────────────────────────────────────────────────────────

def route_after_planner(state: AppState) -> str:
    hitl_enabled = state.get("hitl_enabled", True)
    if hitl_enabled:
        return "research_planning"
    return "agent_dispatcher"

def route_dispatcher(state: AppState) -> List[str]:
    plan = state.get("implementation_plan")
    if not plan:
        return ["db_workspace", "backend_workspace", "frontend_workspace", "ops_security_workspace"]
        
    proposed_changes = plan.get("proposed_changes", [])
    if not proposed_changes:
        return ["db_workspace", "backend_workspace", "frontend_workspace", "ops_security_workspace"]
        
    branches = []
    has_db = False
    has_backend = False
    has_frontend = False
    has_ops = False
    
    for change in proposed_changes:
        path = change.get("path", "").lower()
        if "db" in path or "model" in path or "schema" in path or "persistence" in path:
            has_db = True
        elif "backend" in path or "route" in path or "api" in path or "server" in path:
            has_backend = True
        elif "frontend" in path or "ui" in path or "component" in path or "style" in path or "page" in path:
            has_frontend = True
        else:
            has_ops = True
            
    if has_db:
        branches.append("db_workspace")
    if has_backend:
        branches.append("backend_workspace")
    if has_frontend:
        branches.append("frontend_workspace")
    if has_ops or not branches:
        branches.append("ops_security_workspace")
        
    return branches

def route_after_verifier(state: AppState) -> str:
    validation_logs = state.get("validation_logs", [])
    if validation_logs:
        # Route back to dispatcher for correction loop
        return "agent_dispatcher"
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
    
    workflow.add_node("db_workspace", db_workspace_node)
    workflow.add_node("backend_workspace", backend_workspace_node)
    workflow.add_node("frontend_workspace", frontend_workspace_node)
    workflow.add_node("ops_security_workspace", ops_security_workspace_node)
    
    workflow.add_node("join_workspaces", join_workspaces_node)
    workflow.add_node("verifier_guardrail", verifier_guardrail_node)
    
    workflow.add_node("code_gen_planner", code_gen_planner_node)
    workflow.add_node("integration_generator", integration_generator_node)
    workflow.add_node("build_compiler", build_compiler_node)
    workflow.add_node("error_correction", error_correction_node)
    workflow.add_node("project_export", project_export_node)
    
    # Edges
    workflow.set_entry_point("requirement_analyzer")
    workflow.add_edge("requirement_analyzer", "planner")
    
    workflow.add_conditional_edges("planner", route_after_planner, {
        "research_planning": "research_planning",
        "agent_dispatcher": "agent_dispatcher"
    })
    
    workflow.add_edge("research_planning", "agent_dispatcher")
    
    # Parallel dispatching
    workflow.add_conditional_edges("agent_dispatcher", route_dispatcher, {
        "db_workspace": "db_workspace",
        "backend_workspace": "backend_workspace",
        "frontend_workspace": "frontend_workspace",
        "ops_security_workspace": "ops_security_workspace",
    })
    
    # Joins
    workflow.add_edge("db_workspace", "join_workspaces")
    workflow.add_edge("backend_workspace", "join_workspaces")
    workflow.add_edge("frontend_workspace", "join_workspaces")
    workflow.add_edge("ops_security_workspace", "join_workspaces")
    
    workflow.add_edge("join_workspaces", "verifier_guardrail")
    
    workflow.add_conditional_edges("verifier_guardrail", route_after_verifier, {
        "code_gen_planner": "code_gen_planner",
        "agent_dispatcher": "agent_dispatcher"
    })
    
    # Final sequential chain
    workflow.add_edge("code_gen_planner", "integration_generator")
    workflow.add_edge("integration_generator", "build_compiler")
    workflow.add_edge("build_compiler", "error_correction")
    workflow.add_edge("error_correction", "project_export")
    workflow.add_edge("project_export", END)
    
    # Compile graph with interruption before dispatcher node
    return workflow.compile(
        checkpointer=memory_saver,
        interrupt_before=["agent_dispatcher"]
    )

async def compile_project_workflow(db: Any, project_id: str, project_doc: Dict[str, Any]):
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
        "validation_logs": project_doc.get("validation_logs", [])
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

async def resume_project_workflow(db: Any, project_id: str, plan_edits: Optional[Dict[str, Any]] = None):
    app = build_graph()
    config = {"configurable": {"thread_id": project_id, "db": db}}
    
    state_info = await app.aget_state(config)
    if not state_info.next:
        logger.error(f"Cannot resume: thread {project_id} has no suspended state.")
        return
        
    updates = {"hitl_approved": True}
    if plan_edits:
        updates["implementation_plan"] = plan_edits
        
    await app.aupdate_state(config, updates)
    
    # Set status to generating and store approval details
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
    
    # Fetch latest doc and resume
    latest_proj = await db.projects.find_one({"_id": project_id})
    await compile_project_workflow(db, project_id, latest_proj)
