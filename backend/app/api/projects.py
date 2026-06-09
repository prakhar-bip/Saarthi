import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
import io
import zipfile
from app.models.project import ProjectResponse, ProjectCreate, CodeFileSchema, BlueprintSchema, ThemePaletteSchema
from app.db.mongodb import get_database
from app.api.auth import get_current_user
from app.core.config import settings
from app.services.ai import generate_codebase, generate_project_suggestions
from app.services.mcp_service import mcp_client
from app.services.ws_manager import manager
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
from app.agents.context import AGENT_PIPELINE, AGENT_ROLES, build_compilation_context

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = logging.getLogger(__name__)

ARCHITECTURE_CONTEXT_FIELDS = (
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
)


def build_hackathon_metadata(
    project_id: str,
    name: str,
    category: str,
    blueprint: dict | None = None,
) -> dict:
    """Create Devpost/judging metadata for Sarthi and generated projects."""
    return {
        "challenge": "Building Agents for Real-World Challenges",
        "project": name,
        "project_id": project_id,
        "category": category,
        "partner_track": settings.PARTNER_TRACK,
        "partner_bucket": settings.PARTNER_TRACK,
        "partner_mcp_server": settings.PARTNER_MCP_SERVER,
        "mcp_protocol": "Model Context Protocol",
        "mcp_integration": "MongoDB MCP tools are exposed to Sarthi planning, database, API, code generation, build, and export agents.",
        "gemini_powered": True,
        "primary_model": settings.GOOGLE_REASONING_MODEL or settings.GOOGLE_MODEL,
        "fast_model": settings.GOOGLE_FAST_MODEL or settings.GOOGLE_MODEL,
        "agent_builder_runtime": "Google Cloud Agent Builder compatible orchestration using Google ADK-style agent runners.",
        "human_oversight": [
            "User confirms blueprint before documents are generated.",
            "User reviews PRD/MRD/TRD before codebase compilation.",
            "User manually downloads or pushes the generated project.",
        ],
        "move_beyond_chat": [
            "Creates requirements documents.",
            "Runs a multi-agent software architecture pipeline.",
            "Uses MongoDB MCP tools for database context and evidence.",
            "Generates runnable project files, env templates, and submission artifacts.",
        ],
        "sub_agent_pipeline": [
            {"name": agent_name, "role": AGENT_ROLES.get(agent_name, "")}
            for agent_name in AGENT_PIPELINE
        ],
        "submission_checklist": [
            "Hosted project URL",
            "Public open-source repository URL",
            "Root LICENSE file visible to GitHub",
            "Approximately 3 minute demo video",
            "Selected partner track: MongoDB",
            "Completed Devpost submission form",
        ],
        "blueprint": blueprint or {},
    }


def extract_architecture_context(project_doc: dict) -> dict:
    return {
        field: project_doc.get(field)
        for field in ARCHITECTURE_CONTEXT_FIELDS
        if project_doc.get(field)
    }


async def run_optimization_and_generation_planning(
    db,
    project_id: str,
    user_id: str,
    project_context: dict
) -> None:
    """
    Runs post-validation agents that enrich final compilation with performance and deterministic generation planning.
    """
    project_doc = await db.projects.find_one({"_id": project_id, "user_id": user_id}) or {}
    required_fields = (
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
    )
    missing_fields = [field for field in required_fields if not project_doc.get(field)]
    if missing_fields:
        logger.info(
            "Skipping post-validation optimization agents for project %s. Missing: %s",
            project_id,
            ", ".join(missing_fields)
        )
        return

    optimization_arch = project_doc.get("optimization_architecture")
    if not optimization_arch:
        try:
            logger.info(f"Executing OptimizationArchitectureAgent for project {project_id}...")
            optimization_agent = OptimizationArchitectureAgent()
            optimization_arch = await optimization_agent.design(
                project_doc["requirements"],
                project_doc["planning"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["frontend_architecture"],
                project_doc["theme_styling"],
                project_doc["auth_architecture"],
                project_doc["realtime_architecture"],
                project_doc["state_management"],
                project_doc["devops_architecture"],
                project_doc["security_architecture"],
                project_doc["testing_architecture"],
                project_doc["validation_architecture"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"optimization_architecture": optimization_arch}}
            )
            project_doc["optimization_architecture"] = optimization_arch
            logger.info("OptimizationArchitectureAgent completed successfully.")
        except Exception as opt_err:
            logger.error(f"OptimizationArchitectureAgent failed: {opt_err}")

    if not project_doc.get("optimization_architecture"):
        return

    if not project_doc.get("code_generation_plan"):
        try:
            logger.info(f"Executing CodeGenerationPlannerAgent for project {project_id}...")
            codegen_planner = CodeGenerationPlannerAgent()
            code_generation_plan = await codegen_planner.design(
                project_doc["requirements"],
                project_doc["planning"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["frontend_architecture"],
                project_doc["theme_styling"],
                project_doc["auth_architecture"],
                project_doc["realtime_architecture"],
                project_doc["state_management"],
                project_doc["devops_architecture"],
                project_doc["security_architecture"],
                project_doc["testing_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"code_generation_plan": code_generation_plan}}
            )
            project_doc["code_generation_plan"] = code_generation_plan
            logger.info("CodeGenerationPlannerAgent completed successfully.")
        except Exception as codegen_err:
            logger.error(f"CodeGenerationPlannerAgent failed: {codegen_err}")

    if not project_doc.get("code_generation_plan"):
        return

    if not project_doc.get("database_model_generation"):
        try:
            logger.info(f"Executing DatabaseModelGenerationAgent for project {project_id}...")
            db_model_agent = DatabaseModelGenerationAgent()
            database_model_generation = await db_model_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"database_model_generation": database_model_generation}}
            )
            project_doc["database_model_generation"] = database_model_generation
            logger.info("DatabaseModelGenerationAgent completed successfully.")
        except Exception as db_model_err:
            logger.error(f"DatabaseModelGenerationAgent failed: {db_model_err}")

    if not project_doc.get("backend_code_generation") and project_doc.get("database_model_generation"):
        try:
            logger.info(f"Executing BackendCodeGenerationAgent for project {project_id}...")
            backend_code_agent = BackendCodeGenerationAgent()
            backend_code_generation = await backend_code_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"backend_code_generation": backend_code_generation}}
            )
            project_doc["backend_code_generation"] = backend_code_generation
            logger.info("BackendCodeGenerationAgent completed successfully.")
        except Exception as backend_code_err:
            logger.error(f"BackendCodeGenerationAgent failed: {backend_code_err}")

    if not project_doc.get("api_implementation") and project_doc.get("backend_code_generation"):
        try:
            logger.info(f"Executing APIImplementationAgent for project {project_id}...")
            api_impl_agent = APIImplementationAgent()
            api_implementation = await api_impl_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"api_implementation": api_implementation}}
            )
            project_doc["api_implementation"] = api_implementation
            logger.info("APIImplementationAgent completed successfully.")
        except Exception as api_impl_err:
            logger.error(f"APIImplementationAgent failed: {api_impl_err}")

    if not project_doc.get("frontend_code_generation") and project_doc.get("api_implementation"):
        try:
            logger.info(f"Executing FrontendCodeGenerationAgent for project {project_id}...")
            fe_code_agent = FrontendCodeGenerationAgent()
            frontend_code_generation = await fe_code_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"frontend_code_generation": frontend_code_generation}}
            )
            project_doc["frontend_code_generation"] = frontend_code_generation
            logger.info("FrontendCodeGenerationAgent completed successfully.")
        except Exception as fe_code_err:
            logger.error(f"FrontendCodeGenerationAgent failed: {fe_code_err}")

    if not project_doc.get("ui_component_generation") and project_doc.get("frontend_code_generation"):
        try:
            logger.info(f"Executing UIComponentGenerationAgent for project {project_id}...")
            ui_comp_agent = UIComponentGenerationAgent()
            ui_component_generation = await ui_comp_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"ui_component_generation": ui_component_generation}}
            )
            project_doc["ui_component_generation"] = ui_component_generation
            logger.info("UIComponentGenerationAgent completed successfully.")
        except Exception as ui_comp_err:
            logger.error(f"UIComponentGenerationAgent failed: {ui_comp_err}")

    if not project_doc.get("state_implementation") and project_doc.get("ui_component_generation"):
        try:
            logger.info(f"Executing StateImplementationAgent for project {project_id}...")
            state_impl_agent = StateImplementationAgent()
            state_implementation = await state_impl_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                project_doc["ui_component_generation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"state_implementation": state_implementation}}
            )
            project_doc["state_implementation"] = state_implementation
            logger.info("StateImplementationAgent completed successfully.")
        except Exception as state_impl_err:
            logger.error(f"StateImplementationAgent failed: {state_impl_err}")

    if not project_doc.get("integration_generation") and project_doc.get("state_implementation"):
        try:
            logger.info(f"Executing IntegrationGenerationAgent for project {project_id}...")
            integration_agent = IntegrationGenerationAgent()
            integration_generation = await integration_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                project_doc["ui_component_generation"],
                project_doc["state_implementation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"integration_generation": integration_generation}}
            )
            project_doc["integration_generation"] = integration_generation
            logger.info("IntegrationGenerationAgent completed successfully.")
        except Exception as integration_err:
            logger.error(f"IntegrationGenerationAgent failed: {integration_err}")

    if not project_doc.get("build_compilation") and project_doc.get("integration_generation"):
        try:
            logger.info(f"Executing BuildCompilationAgent for project {project_id}...")
            build_agent = BuildCompilationAgent()
            build_compilation = await build_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                project_doc["ui_component_generation"],
                project_doc["state_implementation"],
                project_doc["integration_generation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"build_compilation": build_compilation}}
            )
            project_doc["build_compilation"] = build_compilation
            logger.info("BuildCompilationAgent completed successfully.")
        except Exception as build_err:
            logger.error(f"BuildCompilationAgent failed: {build_err}")

    if not project_doc.get("error_correction") and project_doc.get("build_compilation"):
        try:
            logger.info(f"Executing ErrorCorrectionAgent for project {project_id}...")
            error_correction_agent = ErrorCorrectionAgent()
            error_correction = await error_correction_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["auth_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                project_doc["ui_component_generation"],
                project_doc["state_implementation"],
                project_doc["integration_generation"],
                project_doc["build_compilation"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"error_correction": error_correction}}
            )
            project_doc["error_correction"] = error_correction
            logger.info("ErrorCorrectionAgent completed successfully.")
        except Exception as ec_err:
            logger.error(f"ErrorCorrectionAgent failed: {ec_err}")

    if not project_doc.get("project_export") and project_doc.get("error_correction"):
        try:
            logger.info(f"Executing ProjectExportAgent for project {project_id}...")
            export_agent = ProjectExportAgent()
            project_export = await export_agent.design(
                project_doc["requirements"],
                project_doc["db_architecture"],
                project_doc["backend_architecture"],
                project_doc["api_architecture"],
                project_doc["frontend_architecture"],
                project_doc["auth_architecture"],
                project_doc["devops_architecture"],
                project_doc["validation_architecture"],
                project_doc["optimization_architecture"],
                project_doc["code_generation_plan"],
                project_doc["database_model_generation"],
                project_doc["backend_code_generation"],
                project_doc["api_implementation"],
                project_doc["frontend_code_generation"],
                project_doc["ui_component_generation"],
                project_doc["state_implementation"],
                project_doc["integration_generation"],
                project_doc["build_compilation"],
                project_doc["error_correction"],
                global_project_context=project_context
            )
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"project_export": project_export}}
            )
            project_doc["project_export"] = project_export
            logger.info("ProjectExportAgent completed successfully.")
        except Exception as export_err:
            logger.error(f"ProjectExportAgent failed: {export_err}")

    agent_context = build_compilation_context(extract_architecture_context(project_doc))
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"agent_context": agent_context}}
    )


async def run_project_compilation(
    project_id: str, 
    chat_id: str, 
    name: str, 
    category: str, 
    user_id: str, 
    theme: str = None,
    blueprint: BlueprintSchema = None,
    theme_palette: ThemePaletteSchema = None
):
    """Background task to simulate stages, call Nvidia NIM to write code, and update DB."""
    db = get_database()
    
    stages = [
        {"progress": 15, "step": "Gemini agent planning and user oversight checkpoint", "delay": 1.5},
        {"progress": 35, "step": "MongoDB MCP context plus requirements/data-flow architecture", "delay": 2.0},
        {"progress": 60, "step": "Sub-agent UI, API, auth, realtime, state, security, and testing design", "delay": 2.5},
        {"progress": 85, "step": "Build, correction, export, and hackathon packaging agents", "delay": 2.0},
    ]
    
    try:
        # Fetch chat history to feed Nvidia NIM for relevant context
        chat_doc = await db.chats.find_one({"_id": chat_id, "user_id": user_id})
        chat_history = chat_doc.get("messages", []) if chat_doc else []
        
        # Loop through visual stages
        for stage in stages:
            await asyncio.sleep(stage["delay"])
            
            if stage["progress"] == 35:
                # Run the Requirement Analyzer Agent
                requirements = None
                try:
                    logger.info(f"Executing RequirementAnalyzerAgent for project {project_id}...")
                    agent = RequirementAnalyzerAgent()
                    bp_data = blueprint.dict() if blueprint else {
                        "name": name,
                        "idea": chat_doc.get("selected_project", {}).get("idea", "") if chat_doc else "",
                        "features": chat_doc.get("selected_project", {}).get("features", []) if chat_doc else [],
                        "tech_stack": chat_doc.get("selected_project", {}).get("tech_stack", "") if chat_doc else ""
                    }
                    requirements = await agent.analyze(bp_data, theme)
                    logger.info(f"RequirementAnalyzerAgent completed successfully.")
                    
                    # Store requirements in the project document
                    await db.projects.update_one(
                        {"_id": project_id},
                        {"$set": {"requirements": requirements}}
                    )
                except Exception as agent_err:
                    logger.error(f"RequirementAnalyzerAgent failed: {agent_err}")

                if requirements:
                    planning = None
                    try:
                        logger.info(f"Executing PlannerAgent for project {project_id}...")
                        planner = PlannerAgent()
                        planning = await planner.plan(requirements)
                        logger.info(f"PlannerAgent completed successfully.")
                        
                        # Store planning in the project document
                        await db.projects.update_one(
                            {"_id": project_id},
                            {"$set": {"planning": planning}}
                        )
                    except Exception as planner_err:
                        logger.error(f"PlannerAgent failed: {planner_err}")

                    if planning:
                        db_arch = None
                        try:
                            logger.info(f"Executing DatabaseArchitectureAgent for project {project_id}...")
                            db_agent = DatabaseArchitectureAgent()
                            db_arch = await db_agent.design(requirements, planning)
                            logger.info(f"DatabaseArchitectureAgent completed successfully.")
                            
                            # Store db_architecture in the project document
                            await db.projects.update_one(
                                {"_id": project_id},
                                {"$set": {"db_architecture": db_arch}}
                            )
                        except Exception as db_err:
                            logger.error(f"DatabaseArchitectureAgent failed: {db_err}")

                        if db_arch:
                            try:
                                logger.info(f"Executing BackendArchitectureAgent for project {project_id}...")
                                be_agent = BackendArchitectureAgent()
                                be_arch = await be_agent.design(requirements, planning, db_arch)
                                logger.info(f"BackendArchitectureAgent completed successfully.")
                                
                                # Store backend_architecture in the project document
                                await db.projects.update_one(
                                    {"_id": project_id},
                                    {"$set": {"backend_architecture": be_arch}}
                                )

                                if be_arch:
                                    try:
                                        logger.info(f"Executing APIAgent for project {project_id}...")
                                        api_agent = APIAgent()
                                        api_arch = await api_agent.design(requirements, planning, db_arch, be_arch)
                                        logger.info(f"APIAgent completed successfully.")
                                        
                                        # Store api_architecture in the project document
                                        await db.projects.update_one(
                                            {"_id": project_id},
                                            {"$set": {"api_architecture": api_arch}}
                                        )

                                        if api_arch:
                                            try:
                                                logger.info(f"Executing FrontendArchitectureAgent for project {project_id}...")
                                                fe_agent = FrontendArchitectureAgent()
                                                fe_arch = await fe_agent.design(requirements, planning, db_arch, be_arch, api_arch)
                                                logger.info(f"FrontendArchitectureAgent completed successfully.")
                                                
                                                # Store frontend_architecture in the project document
                                                await db.projects.update_one(
                                                    {"_id": project_id},
                                                    {"$set": {"frontend_architecture": fe_arch}}
                                                )

                                                if fe_arch:
                                                    try:
                                                        logger.info(f"Executing UIUXArchitectAgent for project {project_id}...")
                                                        uiux_agent = UIUXArchitectAgent()
                                                        uiux_style = await uiux_agent.design(requirements, planning, db_arch, be_arch, api_arch, fe_arch)
                                                        logger.info(f"UIUXArchitectAgent completed successfully.")
                                                        
                                                        # Store theme_styling in the project document
                                                        await db.projects.update_one(
                                                            {"_id": project_id},
                                                            {"$set": {"theme_styling": uiux_style}}
                                                        )

                                                        if uiux_style:
                                                            try:
                                                                logger.info(f"Executing AuthArchitectureAgent for project {project_id}...")
                                                                auth_agent = AuthArchitectureAgent()
                                                                auth_arch = await auth_agent.design(requirements, planning, db_arch, be_arch, api_arch, fe_arch, uiux_style)
                                                                logger.info(f"AuthArchitectureAgent completed successfully.")

                                                                # Store auth_architecture in the project document
                                                                await db.projects.update_one(
                                                                    {"_id": project_id},
                                                                    {"$set": {"auth_architecture": auth_arch}}
                                                                )

                                                                if auth_arch:
                                                                    try:
                                                                        logger.info(f"Executing RealtimeArchitectureAgent for project {project_id}...")
                                                                        realtime_agent = RealtimeArchitectureAgent()
                                                                        realtime_arch = await realtime_agent.design(requirements, planning, db_arch, be_arch, api_arch, fe_arch, uiux_style, auth_arch)
                                                                        logger.info(f"RealtimeArchitectureAgent completed successfully.")

                                                                        # Store realtime_architecture in the project document
                                                                        await db.projects.update_one(
                                                                            {"_id": project_id},
                                                                            {"$set": {"realtime_architecture": realtime_arch}}
                                                                        )

                                                                        if realtime_arch:
                                                                            try:
                                                                                logger.info(f"Executing StateManagementAgent for project {project_id}...")
                                                                                state_agent = StateManagementAgent()
                                                                                state_mgmt = await state_agent.design(
                                                                                    requirements,
                                                                                    planning,
                                                                                    db_arch,
                                                                                    be_arch,
                                                                                    api_arch,
                                                                                    fe_arch,
                                                                                    uiux_style,
                                                                                    auth_arch,
                                                                                    realtime_arch
                                                                                )
                                                                                logger.info(f"StateManagementAgent completed successfully.")

                                                                                # Store state_management in the project document
                                                                                await db.projects.update_one(
                                                                                    {"_id": project_id},
                                                                                    {"$set": {"state_management": state_mgmt}}
                                                                                )
                                                                                if state_mgmt:
                                                                                    try:
                                                                                        logger.info(f"Executing DevOpsArchitectureAgent for project {project_id}...")
                                                                                        devops_agent = DevOpsArchitectureAgent()
                                                                                        devops_arch = await devops_agent.design(
                                                                                            requirements,
                                                                                            planning,
                                                                                            db_arch,
                                                                                            be_arch,
                                                                                            api_arch,
                                                                                            fe_arch,
                                                                                            uiux_style,
                                                                                            auth_arch,
                                                                                            realtime_arch,
                                                                                            state_mgmt
                                                                                        )
                                                                                        logger.info(f"DevOpsArchitectureAgent completed successfully.")
                                                                                        
                                                                                        # Store devops_architecture in the project document
                                                                                        await db.projects.update_one(
                                                                                            {"_id": project_id},
                                                                                            {"$set": {"devops_architecture": devops_arch}}
                                                                                        )

                                                                                        if devops_arch:
                                                                                            try:
                                                                                                logger.info(f"Executing SecurityArchitectureAgent for project {project_id}...")
                                                                                                security_agent = SecurityArchitectureAgent()
                                                                                                security_arch = await security_agent.design(
                                                                                                    requirements,
                                                                                                    planning,
                                                                                                    db_arch,
                                                                                                    be_arch,
                                                                                                    api_arch,
                                                                                                    fe_arch,
                                                                                                    uiux_style,
                                                                                                    auth_arch,
                                                                                                    realtime_arch,
                                                                                                    state_mgmt,
                                                                                                    devops_arch
                                                                                                )
                                                                                                logger.info(f"SecurityArchitectureAgent completed successfully.")

                                                                                                # Store security_architecture in the project document
                                                                                                await db.projects.update_one(
                                                                                                    {"_id": project_id},
                                                                                                    {"$set": {"security_architecture": security_arch}}
                                                                                                )

                                                                                                if security_arch:
                                                                                                    try:
                                                                                                        logger.info(f"Executing TestingArchitectureAgent for project {project_id}...")
                                                                                                        testing_agent = TestingArchitectureAgent()
                                                                                                        testing_arch = await testing_agent.design(
                                                                                                            requirements,
                                                                                                            planning,
                                                                                                            db_arch,
                                                                                                            be_arch,
                                                                                                            api_arch,
                                                                                                            fe_arch,
                                                                                                            uiux_style,
                                                                                                            auth_arch,
                                                                                                            realtime_arch,
                                                                                                            state_mgmt,
                                                                                                            devops_arch,
                                                                                                            security_arch
                                                                                                        )
                                                                                                        logger.info(f"TestingArchitectureAgent completed successfully.")

                                                                                                        # Store testing_architecture in the project document
                                                                                                        await db.projects.update_one(
                                                                                                            {"_id": project_id},
                                                                                                            {"$set": {"testing_architecture": testing_arch}}
                                                                                                        )

                                                                                                        if testing_arch:
                                                                                                            try:
                                                                                                                logger.info(f"Executing ValidationArchitectureAgent for project {project_id}...")
                                                                                                                validation_agent = ValidationArchitectureAgent()
                                                                                                                validation_arch = await validation_agent.design(
                                                                                                                    requirements,
                                                                                                                    planning,
                                                                                                                    db_arch,
                                                                                                                    be_arch,
                                                                                                                    api_arch,
                                                                                                                    fe_arch,
                                                                                                                    uiux_style,
                                                                                                                    auth_arch,
                                                                                                                    realtime_arch,
                                                                                                                    state_mgmt,
                                                                                                                    devops_arch,
                                                                                                                    security_arch,
                                                                                                                    testing_arch
                                                                                                                )
                                                                                                                logger.info(f"ValidationArchitectureAgent completed successfully.")

                                                                                                                # Store validation_architecture in the project document
                                                                                                                await db.projects.update_one(
                                                                                                                    {"_id": project_id},
                                                                                                                    {"$set": {"validation_architecture": validation_arch}}
                                                                                                                )
                                                                                                            except Exception as val_err:
                                                                                                                logger.error(f"ValidationArchitectureAgent failed: {val_err}")
                                                                                                    except Exception as test_err:
                                                                                                        logger.error(f"TestingArchitectureAgent failed: {test_err}")
                                                                                            except Exception as sec_err:
                                                                                                logger.error(f"SecurityArchitectureAgent failed: {sec_err}")
                                                                                    except Exception as devops_err:
                                                                                        logger.error(f"DevOpsArchitectureAgent failed: {devops_err}")
                                                                            except Exception as state_err:
                                                                                logger.error(f"StateManagementAgent failed: {state_err}")
                                                                    except Exception as realtime_err:
                                                                        logger.error(f"RealtimeArchitectureAgent failed: {realtime_err}")
                                                            except Exception as auth_err:
                                                                logger.error(f"AuthArchitectureAgent failed: {auth_err}")
                                                    except Exception as uiux_err:
                                                        logger.error(f"UIUXArchitectAgent failed: {uiux_err}")
                                            except Exception as fe_err:
                                                logger.error(f"FrontendArchitectureAgent failed: {fe_err}")
                                    except Exception as api_err:
                                        logger.error(f"APIAgent failed: {api_err}")
                            except Exception as be_err:
                                logger.error(f"BackendArchitectureAgent failed: {be_err}")

                await run_optimization_and_generation_planning(
                    db,
                    project_id,
                    user_id,
                    {
                        "project_id": project_id,
                        "chat_id": chat_id,
                        "name": name,
                        "category": category,
                        "theme": theme,
                        "blueprint": blueprint.dict() if blueprint else None,
                        "theme_palette": theme_palette.dict() if theme_palette else None,
                        "chat_message_count": len(chat_history),
                    }
                )

            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"progress": stage["progress"], "step": stage["step"]}}
            )
            
            # Broadcast real-time progress to frontend
            await manager.broadcast_progress(
                project_id=project_id,
                progress=stage["progress"],
                step=stage["step"]
            )
            logger.info(f"Project {project_id} compilation progress: {stage['progress']}% - {stage['step']}")
            
        # Call Nvidia NIM Service to compile codebase
        logger.info(f"Requesting AI codebase generation for project {name} ({category}) with theme {theme}")
        latest_project_doc = await db.projects.find_one({"_id": project_id, "user_id": user_id}) or {}
        architecture_context = extract_architecture_context(latest_project_doc)
        blueprint_dict = blueprint.dict() if blueprint else latest_project_doc.get("blueprint")
        hackathon_metadata = build_hackathon_metadata(
            project_id=project_id,
            name=name,
            category=category,
            blueprint=blueprint_dict,
        )
        mcp_evidence = await mcp_client.build_evidence_snapshot(project_id=project_id)
        if architecture_context:
            await db.projects.update_one(
                {"_id": project_id},
                {
                    "$set": {
                        "agent_context": build_compilation_context(architecture_context),
                        "hackathon_metadata": hackathon_metadata,
                        "mcp_evidence": mcp_evidence,
                    }
                }
            )
        ai_data = await generate_codebase(
            name, 
            category, 
            chat_history, 
            theme,
            blueprint_dict,
            theme_palette.dict() if theme_palette else None,
            architecture_context=architecture_context,
            hackathon_metadata=hackathon_metadata,
            mcp_evidence=mcp_evidence,
        )
        
        summary = ai_data.get("summary", "Complete hackathon-ready Flask codebase compiled successfully.")
        codebase_list = ai_data.get("codebase", [])
        
        # Parse CodeFiles
        codefiles_db = []
        for file in codebase_list:
            codefiles_db.append({
                "name": file.get("name", ""),
                "path": file.get("path", ""),
                "content": file.get("content", ""),
                "language": file.get("language", "typescript")
            })
            
        # Complete stage
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "progress": 100,
                    "status": "completed",
                    "step": "Deployment Complete",
                    "summary": summary,
                    "codebase": codefiles_db,
                    "hackathon_metadata": hackathon_metadata,
                    "mcp_evidence": mcp_evidence,
                }
            }
        )
        
        # Append AI message indicating completion
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        success_msg = {
            "id": f"m-{uuid.uuid4().hex[:8]}",
            "sender": "ai",
            "text": f"🎉 Amazing news! Your project **{name}** has been successfully generated. You can explore the codebase and architecture in the projects history or the file panel on the right!",
            "timestamp": time_str
        }
        await db.chats.update_one(
            {"_id": chat_id},
            {"$push": {"messages": success_msg}}
        )
        
        # Broadcast success state
        await manager.broadcast_progress(
            project_id=project_id,
            progress=100,
            step="Deployment Complete",
            status="completed"
        )
        logger.info(f"Project {project_id} compilation complete!")
        
    except Exception as e:
        logger.error(f"Project compilation failed for {project_id}: {e}")
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "status": "failed",
                    "step": f"Compilation Error: {str(e)}",
                    "progress": 100
                }
            }
        )
        # Broadcast failure
        await manager.broadcast_progress(
            project_id=project_id,
            progress=100,
            step=f"Compilation Error: {str(e)}",
            status="failed"
        )


@router.get("/suggestions")
async def get_suggestions(category: str, current_user: dict = Depends(get_current_user)):
    if not category:
        raise HTTPException(status_code=400, detail="Category parameter is required")
    suggestions = await generate_project_suggestions(category)
    return suggestions

@router.get("", response_model=list[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.projects.find({"user_id": current_user["id"]}).sort("created_at_dt", -1)
    projects = []
    async for doc in cursor:
        projects.append(ProjectResponse(
            id=doc["_id"],
            name=doc["name"],
            category=doc["category"],
            status=doc.get("status", "completed"),
            progress=doc.get("progress", 100),
            step=doc.get("step", ""),
            summary=doc.get("summary", ""),
            codebase=doc.get("codebase", []),
            created=doc.get("created", ""),
            user_id=doc["user_id"],
            chat_id=doc.get("chat_id", ""),
            theme=doc.get("theme"),
            blueprint=doc.get("blueprint"),
            theme_palette=doc.get("theme_palette"),
            requirements=doc.get("requirements"),
            planning=doc.get("planning"),
            db_architecture=doc.get("db_architecture"),
            backend_architecture=doc.get("backend_architecture"),
            api_architecture=doc.get("api_architecture"),
            frontend_architecture=doc.get("frontend_architecture"),
            theme_styling=doc.get("theme_styling"),
            auth_architecture=doc.get("auth_architecture"),
            realtime_architecture=doc.get("realtime_architecture"),
            state_management=doc.get("state_management"),
            devops_architecture=doc.get("devops_architecture"),
            security_architecture=doc.get("security_architecture"),
            testing_architecture=doc.get("testing_architecture"),
            validation_architecture=doc.get("validation_architecture"),
            optimization_architecture=doc.get("optimization_architecture"),
            code_generation_plan=doc.get("code_generation_plan"),
            database_model_generation=doc.get("database_model_generation"),
            backend_code_generation=doc.get("backend_code_generation"),
            api_implementation=doc.get("api_implementation"),
            frontend_code_generation=doc.get("frontend_code_generation"),
            ui_component_generation=doc.get("ui_component_generation"),
            state_implementation=doc.get("state_implementation"),
            integration_generation=doc.get("integration_generation"),
            build_compilation=doc.get("build_compilation"),
            error_correction=doc.get("error_correction"),
            project_export=doc.get("project_export"),
            agent_context=doc.get("agent_context"),
            hackathon_metadata=doc.get("hackathon_metadata"),
            mcp_evidence=doc.get("mcp_evidence"),
            prd=doc.get("prd"),
            mrd=doc.get("mrd"),
            trd=doc.get("trd")
        ))
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=doc["_id"],
        name=doc["name"],
        category=doc["category"],
        status=doc.get("status", "completed"),
        progress=doc.get("progress", 100),
        step=doc.get("step", ""),
        summary=doc.get("summary", ""),
        codebase=doc.get("codebase", []),
        created=doc.get("created", ""),
        user_id=doc["user_id"],
        chat_id=doc.get("chat_id", ""),
        theme=doc.get("theme"),
        blueprint=doc.get("blueprint"),
        theme_palette=doc.get("theme_palette"),
        requirements=doc.get("requirements"),
        planning=doc.get("planning"),
        db_architecture=doc.get("db_architecture"),
        backend_architecture=doc.get("backend_architecture"),
        api_architecture=doc.get("api_architecture"),
        frontend_architecture=doc.get("frontend_architecture"),
        theme_styling=doc.get("theme_styling"),
        auth_architecture=doc.get("auth_architecture"),
        realtime_architecture=doc.get("realtime_architecture"),
        state_management=doc.get("state_management"),
        devops_architecture=doc.get("devops_architecture"),
        security_architecture=doc.get("security_architecture"),
        testing_architecture=doc.get("testing_architecture"),
        validation_architecture=doc.get("validation_architecture"),
        optimization_architecture=doc.get("optimization_architecture"),
        code_generation_plan=doc.get("code_generation_plan"),
        database_model_generation=doc.get("database_model_generation"),
        backend_code_generation=doc.get("backend_code_generation"),
        api_implementation=doc.get("api_implementation"),
        frontend_code_generation=doc.get("frontend_code_generation"),
        ui_component_generation=doc.get("ui_component_generation"),
        state_implementation=doc.get("state_implementation"),
        integration_generation=doc.get("integration_generation"),
        build_compilation=doc.get("build_compilation"),
        error_correction=doc.get("error_correction"),
        project_export=doc.get("project_export"),
        agent_context=doc.get("agent_context"),
        hackathon_metadata=doc.get("hackathon_metadata"),
        mcp_evidence=doc.get("mcp_evidence"),
        prd=doc.get("prd"),
        mrd=doc.get("mrd"),
        trd=doc.get("trd")
    )

from pydantic import BaseModel as PydanticBaseModel

class GenerateDocumentsRequest(PydanticBaseModel):
    name: str
    prompt: str

@router.post("/generate-documents", response_model=ProjectResponse)
async def generate_documents_endpoint(
    payload: GenerateDocumentsRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    created_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    hackathon_metadata = build_hackathon_metadata(
        project_id=project_id,
        name=payload.name,
        category="documents",
        blueprint={"name": payload.name, "idea": payload.prompt},
    )
    mcp_evidence = await mcp_client.build_evidence_snapshot(project_id=project_id)
    
    # Import generating service function
    from app.services.ai import generate_prd_mrd_trd
    
    try:
        docs = await generate_prd_mrd_trd(payload.name, payload.prompt)
    except Exception as e:
        logger.error(f"Failed to generate documents for project {payload.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")
        
    new_project = {
        "_id": project_id,
        "name": payload.name,
        "category": "documents",
        "status": "completed",
        "progress": 100,
        "step": "Documents Generated",
        "summary": "Product Requirements Document (PRD), Market Requirements Document (MRD), and Technical Requirements Document (TRD) compiled successfully.",
        "codebase": [],
        "created": created_str,
        "created_at_dt": datetime.now(timezone.utc),
        "user_id": current_user["id"],
        "chat_id": "",
        "theme": None,
        "blueprint": None,
        "theme_palette": None,
        "prd": docs.get("prd", ""),
        "mrd": docs.get("mrd", ""),
        "trd": docs.get("trd", ""),
        "hackathon_metadata": hackathon_metadata,
        "mcp_evidence": mcp_evidence,
    }
    
    await db.projects.insert_one(new_project)
    
    return ProjectResponse(
        id=project_id,
        name=new_project["name"],
        category=new_project["category"],
        status=new_project["status"],
        progress=new_project["progress"],
        step=new_project["step"],
        summary=new_project["summary"],
        codebase=[],
        created=new_project["created"],
        user_id=new_project["user_id"],
        chat_id=new_project["chat_id"],
        theme=None,
        blueprint=None,
        theme_palette=None,
        prd=new_project["prd"],
        mrd=new_project["mrd"],
        trd=new_project["trd"],
        hackathon_metadata=new_project["hackathon_metadata"],
        mcp_evidence=new_project["mcp_evidence"]
    )

@router.post("", response_model=ProjectResponse)
async def compile_project(
    payload: ProjectCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    created_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    
    # Check if chat exists
    chat_exists = await db.chats.find_one({"_id": payload.chat_id, "user_id": current_user["id"]})
    if not chat_exists:
        raise HTTPException(status_code=400, detail="Invalid chat_id specified")
        
    # Auto-identify category on the basis of conversation and user's idea
    from app.services.ai import auto_identify_category
    bp_dict = payload.blueprint.dict() if payload.blueprint else {}
    detected_category = await auto_identify_category(bp_dict, chat_exists.get("messages", []))
    logger.info(f"Project category auto-identified as: {detected_category}")

    # Generate PRD, MRD, TRD documents first
    from app.services.ai import generate_prd_mrd_trd
    
    idea = payload.blueprint.idea if payload.blueprint else ""
    features = payload.blueprint.features if payload.blueprint else []
    tech_stack = payload.blueprint.tech_stack if payload.blueprint else ""
    features_str = ", ".join(features) if features else ""
    prompt_for_docs = f"Project Idea: {idea}\nFeatures: {features_str}\nTech Stack: {tech_stack}"
    blueprint_payload = payload.blueprint.dict() if payload.blueprint else None
    hackathon_metadata = build_hackathon_metadata(
        project_id=project_id,
        name=payload.name,
        category=detected_category,
        blueprint=blueprint_payload,
    )
    mcp_evidence = await mcp_client.build_evidence_snapshot(project_id=project_id)
    
    try:
        logger.info(f"Generating documents for project {payload.name} first...")
        docs = await generate_prd_mrd_trd(payload.name, prompt_for_docs)
    except Exception as e:
        logger.error(f"Failed to generate documents during project init: {e}")
        docs = {"prd": f"# PRD\nFailed to generate documents: {str(e)}", "mrd": "", "trd": ""}
        
    new_project = {
        "_id": project_id,
        "name": payload.name,
        "category": detected_category,
        "status": "documents_ready",
        "progress": 100,
        "step": "Documents Generated",
        "summary": "Product Requirements Document (PRD), Market Requirements Document (MRD), and Technical Requirements Document (TRD) compiled successfully.",
        "codebase": [],
        "created": created_str,
        "created_at_dt": datetime.now(timezone.utc),
        "user_id": current_user["id"],
        "chat_id": payload.chat_id,
        "theme": payload.theme,
        "blueprint": blueprint_payload,
        "theme_palette": payload.theme_palette.dict() if payload.theme_palette else None,
        "prd": docs.get("prd", ""),
        "mrd": docs.get("mrd", ""),
        "trd": docs.get("trd", ""),
        "hackathon_metadata": hackathon_metadata,
        "mcp_evidence": mcp_evidence,
    }
    
    await db.projects.insert_one(new_project)
    
    # Mark chat session as confirmed, link project_id and update category
    await db.chats.update_one(
        {"_id": payload.chat_id, "user_id": current_user["id"]},
        {"$set": {"is_confirmed": True, "project_id": project_id, "category": detected_category}}
    )
    
    # Notify chat that documents were generated
    time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    start_msg = {
        "id": f"m-{uuid.uuid4().hex[:8]}",
        "sender": "ai",
        "text": f"Sarthi has generated the Product, Market, and Technical specifications (PRD/MRD/TRD) for your hackathon project **{payload.name}**! You can review and download them in the right pane, then proceed to build the codebase.",
        "timestamp": time_str
    }
    await db.chats.update_one(
        {"_id": payload.chat_id},
        {"$push": {"messages": start_msg}}
    )
    
    return ProjectResponse(
        id=project_id,
        name=new_project["name"],
        category=new_project["category"],
        status=new_project["status"],
        progress=new_project["progress"],
        step=new_project["step"],
        summary=new_project["summary"],
        codebase=[],
        created=new_project["created"],
        user_id=new_project["user_id"],
        chat_id=new_project["chat_id"],
        theme=new_project["theme"],
        blueprint=payload.blueprint,
        theme_palette=payload.theme_palette,
        prd=new_project["prd"],
        mrd=new_project["mrd"],
        trd=new_project["trd"],
        hackathon_metadata=new_project["hackathon_metadata"],
        mcp_evidence=new_project["mcp_evidence"]
    )

@router.post("/{project_id}/compile", response_model=ProjectResponse)
async def compile_project_codebase(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Set project status to generating
    await db.projects.update_one(
        {"_id": project_id},
        {
            "$set": {
                "status": "generating",
                "progress": 5,
                "step": "Initializing Sarthi AI engine...",
                "codebase": []
            }
        }
    )
    
    # Notify chat that codebase compilation started
    chat_id = project.get("chat_id")
    if chat_id:
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        comp_msg = {
            "id": f"m-{uuid.uuid4().hex[:8]}",
            "sender": "ai",
            "text": f"Sarthi is now compiling your Flask codebase for project **{project['name']}** in the background...",
            "timestamp": time_str
        }
        await db.chats.update_one(
            {"_id": chat_id},
            {"$push": {"messages": comp_msg}}
        )
        
    # Parse models from dict
    from app.models.project import ProjectBlueprint, ThemePalette
    blueprint_dict = project.get("blueprint")
    blueprint = None
    if blueprint_dict:
        blueprint = ProjectBlueprint(**blueprint_dict)
        
    theme_palette_dict = project.get("theme_palette")
    theme_palette = None
    if theme_palette_dict:
        theme_palette = ThemePalette(**theme_palette_dict)

    background_tasks.add_task(
        run_project_compilation,
        project_id,
        chat_id,
        project["name"],
        project["category"],
        current_user["id"],
        project.get("theme"),
        blueprint,
        theme_palette
    )
    
    # Return updated project dict mapped to ProjectResponse
    updated_project = await db.projects.find_one({"_id": project_id})
    return ProjectResponse(
        id=updated_project["_id"],
        name=updated_project["name"],
        category=updated_project["category"],
        status=updated_project["status"],
        progress=updated_project["progress"],
        step=updated_project["step"],
        summary=updated_project["summary"],
        codebase=[],
        created=updated_project["created"],
        user_id=updated_project["user_id"],
        chat_id=updated_project["chat_id"],
        theme=updated_project.get("theme"),
        blueprint=blueprint,
        theme_palette=theme_palette,
        prd=updated_project.get("prd", ""),
        mrd=updated_project.get("mrd", ""),
        trd=updated_project.get("trd", ""),
        hackathon_metadata=updated_project.get("hackathon_metadata"),
        mcp_evidence=updated_project.get("mcp_evidence")
    )

@router.put("/{project_id}")
async def update_project(project_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    updates = {}
    if "title" in payload:
        updates["name"] = payload["title"]  # Project schema uses 'name' for title
    if "name" in payload:
        updates["name"] = payload["name"]
        
    if updates:
        await db.projects.update_one({"_id": project_id}, {"$set": updates})
        
    return {"status": "success", "updates": updates}

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    result = await db.projects.delete_one({"_id": project_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": "Project deleted successfully"}


@router.get("/{project_id}/download")
async def download_project_zip(project_id: str, current_user: dict = Depends(get_current_user)):
    """Downloads the generated project codebase as a valid ZIP file."""
    db = get_database()
    doc = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    codebase = doc.get("codebase", [])
    has_docs = any(doc.get(f) for f in ("prd", "mrd", "trd"))
    if not codebase and not has_docs:
        raise HTTPException(status_code=400, detail="No codebase or requirements documents have been generated yet for this project.")
        
    # Create in-memory zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        written_paths = set()
        if codebase:
            for file in codebase:
                path = file.get("path", file.get("name", "unnamed.txt"))
                if path not in written_paths:
                    zf.writestr(path, file.get("content", ""))
                    written_paths.add(path)
        
        if doc.get("prd") and "PRD.md" not in written_paths:
            zf.writestr("PRD.md", doc["prd"])
            written_paths.add("PRD.md")
        if doc.get("mrd") and "MRD.md" not in written_paths:
            zf.writestr("MRD.md", doc["mrd"])
            written_paths.add("MRD.md")
        if doc.get("trd") and "TRD.md" not in written_paths:
            zf.writestr("TRD.md", doc["trd"])
            written_paths.add("TRD.md")

        from app.services.hackathon import build_hackathon_files
        for artifact in build_hackathon_files(
            doc.get("name", "Sarthi Project"),
            doc.get("hackathon_metadata") or {},
            doc.get("mcp_evidence") or {},
        ):
            if artifact["path"] not in written_paths:
                zf.writestr(artifact["path"], artifact["content"])
                written_paths.add(artifact["path"])
            
        # If ProjectExportAgent provided env templates, include an .env.example
        project_export = doc.get("project_export", {})
        if project_export:
            env_templates = project_export.get("environment_generation", {}).get("env_templates", [])
            if env_templates and ".env.example" not in written_paths:
                zf.writestr(".env.example", "\n".join(env_templates))
    
    zip_buffer.seek(0)
    slug = doc.get("name", "sarthi-project").lower().replace(" ", "-")
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={slug}.zip"}
    )


@router.post("/{project_id}/github-push")
async def push_project_to_github(project_id: str, current_user: dict = Depends(get_current_user)):
    """Pushes the compiled project to a new GitHub repository."""
    from app.core.config import settings
    
    if not settings.GITHUB_TOKEN:
        raise HTTPException(status_code=400, detail="GITHUB_TOKEN is not configured in environment settings.")
        
    db = get_database()
    doc = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    codebase = doc.get("codebase", [])
    if not codebase:
        raise HTTPException(status_code=400, detail="No codebase generated yet.")
        
    try:
        from github import Github
        import github
    except ImportError:
        raise HTTPException(status_code=500, detail="PyGithub package is not installed.")
        
    try:
        g = Github(settings.GITHUB_TOKEN)
        user = g.get_user()
        
        repo_name = f"sarthi-{doc.get('name', 'project').lower().replace(' ', '-')}-{uuid.uuid4().hex[:4]}"
        
        # Create private repo
        repo = user.create_repo(
            name=repo_name,
            description=f"Generated by Sarthi AI - {doc.get('category', 'Project')}",
            private=True,
            auto_init=False
        )
        
        # Push files
        for file in codebase:
            path = file.get("path", file.get("name", "unnamed.txt"))
            content = file.get("content", "")
            try:
                repo.create_file(path, f"Sarthi auto-commit: generate {path}", content, branch="main")
            except github.GithubException as e:
                # If main doesn't exist yet, PyGithub creates it on first commit implicitly for some API versions, 
                # but if we get an error we might need to handle branch creation.
                # However, create_file handles it natively if auto_init is false and this is the first commit.
                logger.error(f"Failed to push {path}: {e}")
                
        # Push .env.example if we have export intelligence
        project_export = doc.get("project_export", {})
        if project_export:
            env_templates = project_export.get("environment_generation", {}).get("env_templates", [])
            if env_templates:
                try:
                    repo.create_file(".env.example", "Sarthi auto-commit: add environment template", "\n".join(env_templates), branch="main")
                except Exception as e:
                    logger.error(f"Failed to push .env.example: {e}")
                    
        return {
            "status": "success", 
            "message": f"Successfully pushed to GitHub repository: {repo.html_url}",
            "repo_url": repo.html_url
        }
    except Exception as e:
        logger.error(f"GitHub Push failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to push to GitHub: {str(e)}")
