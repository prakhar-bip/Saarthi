import asyncio
from typing import Dict, Any, TypedDict, Optional, List
from loguru import logger
from langgraph.graph import StateGraph, END
import time

from app.core.config import settings
from app.api.websockets import broadcast_agent_progress
from app.agents.context import AGENT_PIPELINE, IncompleteJSONError
from app.services.llm_router import current_agent_feedback

# Import all agents dynamically or explicitly
from app.agents.requirement_analyzer import RequirementAnalyzerAgent
from app.agents.planner import PlannerAgent
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

class AppState(TypedDict):
    project_id: str
    db: Any
    project_doc: Dict[str, Any]
    current_index: int
    feedback: Optional[str]
    retry_count: int
    latest_output: Any

def get_agent_instance(agent_name: str):
    mapping = {
        "RequirementAnalyzerAgent": RequirementAnalyzerAgent,
        "PlannerAgent": PlannerAgent,
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

async def execute_agent_node(state: AppState) -> AppState:
    idx = state["current_index"]
    agent_name = AGENT_PIPELINE[idx]
    project_doc = state["project_doc"]
    db = state["db"]
    project_id = state["project_id"]
    feedback = state.get("feedback")
    
    agent = get_agent_instance(agent_name)
    logger.info(f"LangGraph: Executing {agent_name} for project {project_id} (Retry: {state['retry_count']})")
    
    progress_percent = min(10 + int((idx / len(AGENT_PIPELINE)) * 85), 95)
    await broadcast_agent_progress(db, project_id, progress_percent, f"Executing {agent_name}...")
    
    # Inject feedback context
    token = current_agent_feedback.set(feedback)
    
    try:
        if agent_name == "RequirementAnalyzerAgent":
            result = await agent.analyze(project_doc.get("initial_prompt", ""))
        elif agent_name == "PlannerAgent":
            result = await agent.plan(project_doc.get("requirements", {}))
        elif agent_name == "DatabaseArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}))
        elif agent_name == "BackendArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}))
        elif agent_name == "APIAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}))
        elif agent_name == "FrontendArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}))
        elif agent_name == "UIUXArchitectAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}))
        elif agent_name == "AuthArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}))
        elif agent_name == "RealtimeArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}))
        elif agent_name == "StateManagementAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}))
        elif agent_name == "DevOpsArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}))
        elif agent_name == "SecurityArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}), project_doc.get("devops_architecture", {}))
        elif agent_name == "TestingArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}), project_doc.get("devops_architecture", {}), project_doc.get("security_architecture", {}))
        elif agent_name == "ValidationArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}), project_doc.get("devops_architecture", {}), project_doc.get("security_architecture", {}), project_doc.get("testing_architecture", {}))
        elif agent_name == "OptimizationArchitectureAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("planning", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}), project_doc.get("devops_architecture", {}), project_doc.get("security_architecture", {}), project_doc.get("testing_architecture", {}), project_doc.get("validation_architecture", {}))
        elif agent_name == "CodeGenerationPlannerAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("theme_styling", {}), project_doc.get("auth_architecture", {}), project_doc.get("realtime_architecture", {}), project_doc.get("state_management", {}), project_doc.get("devops_architecture", {}), project_doc.get("security_architecture", {}), project_doc.get("testing_architecture", {}), project_doc.get("validation_architecture", {}), project_doc.get("optimization_architecture", {}))
        elif agent_name == "DatabaseModelGenerationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("code_generation_plan", {}))
        elif agent_name == "BackendCodeGenerationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}))
        elif agent_name == "APIImplementationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}), project_doc.get("backend_code_generation", {}))
        elif agent_name == "FrontendCodeGenerationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("frontend_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("api_implementation", {}))
        elif agent_name == "UIComponentGenerationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("theme_styling", {}), project_doc.get("frontend_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("frontend_code_generation", {}))
        elif agent_name == "StateImplementationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("state_management", {}), project_doc.get("frontend_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("frontend_code_generation", {}), project_doc.get("ui_component_generation", {}))
        elif agent_name == "IntegrationGenerationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("auth_architecture", {}), project_doc.get("devops_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}), project_doc.get("backend_code_generation", {}), project_doc.get("api_implementation", {}), project_doc.get("frontend_code_generation", {}), project_doc.get("ui_component_generation", {}), project_doc.get("state_implementation", {}))
        elif agent_name == "BuildCompilationAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("devops_architecture", {}), project_doc.get("validation_architecture", {}), project_doc.get("optimization_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}), project_doc.get("backend_code_generation", {}), project_doc.get("api_implementation", {}), project_doc.get("frontend_code_generation", {}), project_doc.get("ui_component_generation", {}), project_doc.get("state_implementation", {}), project_doc.get("integration_generation", {}))
        elif agent_name == "ErrorCorrectionAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("auth_architecture", {}), project_doc.get("devops_architecture", {}), project_doc.get("validation_architecture", {}), project_doc.get("optimization_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}), project_doc.get("backend_code_generation", {}), project_doc.get("api_implementation", {}), project_doc.get("frontend_code_generation", {}), project_doc.get("ui_component_generation", {}), project_doc.get("state_implementation", {}), project_doc.get("integration_generation", {}), project_doc.get("build_compilation", {}))
        elif agent_name == "ProjectExportAgent":
            result = await agent.design(project_doc.get("requirements", {}), project_doc.get("db_architecture", {}), project_doc.get("backend_architecture", {}), project_doc.get("api_architecture", {}), project_doc.get("frontend_architecture", {}), project_doc.get("auth_architecture", {}), project_doc.get("devops_architecture", {}), project_doc.get("validation_architecture", {}), project_doc.get("optimization_architecture", {}), project_doc.get("code_generation_plan", {}), project_doc.get("database_model_generation", {}), project_doc.get("backend_code_generation", {}), project_doc.get("api_implementation", {}), project_doc.get("frontend_code_generation", {}), project_doc.get("ui_component_generation", {}), project_doc.get("state_implementation", {}), project_doc.get("integration_generation", {}), project_doc.get("build_compilation", {}), project_doc.get("error_correction", {}))
        else:
            result = None
    except IncompleteJSONError as e:
        logger.warning(f"LangGraph caught IncompleteJSONError for {agent_name}")
        result = e
    except Exception as e:
        logger.error(f"LangGraph caught generic error for {agent_name}: {e}")
        # If the agent's internal except block failed, or something else crashed, we fall back to it
        result = {"_error": "GenericError", "message": str(e)}
    finally:
        current_agent_feedback.reset(token)

    return {**state, "latest_output": result}


async def verify_output_node(state: AppState) -> AppState:
    idx = state["current_index"]
    agent_name = AGENT_PIPELINE[idx]
    output = state["latest_output"]
    db = state["db"]
    project_id = state["project_id"]
    
    verifier = VerifierAgent()
    is_complete, feedback = await verifier.verify(agent_name, output)
    
    if is_complete:
        db_key = get_agent_db_key(agent_name)
        # Only save valid output
        if output:
            await db.projects.update_one({"_id": project_id}, {"$set": {db_key: output}})
            state["project_doc"][db_key] = output
        
        return {
            **state,
            "current_index": idx + 1,
            "feedback": None,
            "retry_count": 0,
            "latest_output": None
        }
    else:
        retry_count = state["retry_count"] + 1
        if retry_count > 3:
            logger.error(f"Max retries reached for {agent_name}. Advancing anyway.")
            return {
                **state,
                "current_index": idx + 1,
                "feedback": None,
                "retry_count": 0,
                "latest_output": None
            }
        
        return {
            **state,
            "feedback": feedback,
            "retry_count": retry_count
        }


def should_continue(state: AppState) -> str:
    if state["current_index"] >= len(AGENT_PIPELINE):
        return END
    return "execute_agent"


def build_graph() -> StateGraph:
    workflow = StateGraph(AppState)
    workflow.add_node("execute_agent", execute_agent_node)
    workflow.add_node("verify_output", verify_output_node)
    
    workflow.set_entry_point("execute_agent")
    workflow.add_edge("execute_agent", "verify_output")
    workflow.add_conditional_edges("verify_output", should_continue, {END: END, "execute_agent": "execute_agent"})
    
    return workflow.compile()


async def compile_project_workflow(db: Any, project_id: str, project_doc: Dict[str, Any]):
    app = build_graph()
    
    initial_state = {
        "project_id": project_id,
        "db": db,
        "project_doc": project_doc,
        "current_index": 0,
        "feedback": None,
        "retry_count": 0,
        "latest_output": None
    }
    
    # Fast forward if we already compiled partially
    # By checking which keys exist in project_doc
    for idx, agent_name in enumerate(AGENT_PIPELINE):
        key = get_agent_db_key(agent_name)
        if key not in project_doc or not project_doc[key]:
            initial_state["current_index"] = idx
            break
            
    if initial_state["current_index"] >= len(AGENT_PIPELINE):
        logger.info(f"Project {project_id} is already fully compiled.")
        return
        
    logger.info(f"Starting LangGraph execution for {project_id} from index {initial_state['current_index']}")
    await app.ainvoke(initial_state)
