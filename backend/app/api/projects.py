from loguru import logger
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import io
import zipfile
from pydantic import BaseModel
from app.models.project import ProjectResponse, ProjectCreate, BlueprintSchema, ThemePaletteSchema
from app.db.mongodb import get_database
from app.api.auth import get_current_user
from app.core.config import settings
from app.services.ai import generate_codebase, generate_project_suggestions
from app.services.mcp_service import mcp_client
from app.services.ws_manager import manager
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

async def broadcast_agent_progress(db, project_id: str, progress: int, step: str) -> None:
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"progress": progress, "step": step}}
    )
    await manager.broadcast_progress(
        project_id=project_id,
        progress=progress,
        step=step
    )
    logger.info(f"Project {project_id} compilation progress: {progress}% - {step}")


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
            await broadcast_agent_progress(db, project_id, 80, "Optimizing Performance...")
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
            await broadcast_agent_progress(db, project_id, 81, "Implementing APIs...")
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
            await broadcast_agent_progress(db, project_id, 83, "Generating Frontend Code...")
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
            await broadcast_agent_progress(db, project_id, 85, "Generating UI Components...")
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
            await broadcast_agent_progress(db, project_id, 87, "Implementing State Management...")
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
            await broadcast_agent_progress(db, project_id, 89, "Integrating Systems...")
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
            await broadcast_agent_progress(db, project_id, 91, "Compiling Build Assets...")
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
            await broadcast_agent_progress(db, project_id, 93, "Running Error Correction...")
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
            await broadcast_agent_progress(db, project_id, 95, "Exporting Project Files...")
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
    from app.core.logger import current_project_id
    current_project_id.set(project_id)
    db = get_database()
    
    try:
        # Fetch chat history for context
        chat_doc = await db.chats.find_one({"_id": chat_id, "user_id": user_id})
        
        project_doc = await db.projects.find_one({"_id": project_id}) or {}
        bp_dict = blueprint.dict() if blueprint else {
            "name": name,
            "idea": chat_doc.get("selected_project", {}).get("idea", "") if chat_doc else "",
            "features": chat_doc.get("selected_project", {}).get("features", []) if chat_doc else [],
            "tech_stack": chat_doc.get("selected_project", {}).get("tech_stack", "") if chat_doc else ""
        }
        
        if "initial_prompt" not in project_doc:
            project_doc["initial_prompt"] = bp_dict
        
        # Store hackathon metadata and MCP evidence before workflow starts
        blueprint_dict = blueprint.dict() if blueprint else project_doc.get("blueprint") or bp_dict
        hackathon_metadata = build_hackathon_metadata(
            project_id=project_id,
            name=name,
            category=category,
            blueprint=blueprint_dict,
        )
        mcp_evidence = await mcp_client.build_evidence_snapshot(project_id=project_id)
        await db.projects.update_one(
            {"_id": project_id},
            {"$set": {
                "hackathon_metadata": hackathon_metadata,
                "mcp_evidence": mcp_evidence,
            }}
        )
        
        # ── Run the full Sarthi workflow (architecture → synthesis → validation → export) ──
        # The workflow now handles EVERYTHING end-to-end:
        #   1. Requirements analysis
        #   2. Architecture design (28 agents in parallel workspaces)
        #   3. Verification guardrails
        #   4. Code synthesis (CodeSynthesizerAgent generates actual files)
        #   5. Structural validation (CodeValidatorAgent checks imports, contracts)
        #   6. Project assembly (project_assembler merges AI + deterministic files)
        #   7. Quality gates + export
        from app.services.workflow import compile_project_workflow
        await compile_project_workflow(db, project_id, project_doc)
        
        # After workflow completes, verify the project was assembled
        latest_project_doc = await db.projects.find_one({"_id": project_id, "user_id": user_id}) or {}
        
        # Store the compilation context for reference
        architecture_context = extract_architecture_context(latest_project_doc)
        if architecture_context:
            agent_context = build_compilation_context(architecture_context)
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"agent_context": agent_context}}
            )
        
        # Ensure completion state is set (workflow's finalize_project_delivery should have done this)
        if latest_project_doc.get("status") != "completed":
            # Fallback: the workflow may have been interrupted at HITL gate
            if latest_project_doc.get("status") == "waiting_approval":
                logger.info(f"Project {project_id} is waiting for HITL approval — not marking complete.")
                return
            
            # If workflow finished but status wasn't set, finalize now
            logger.warning(f"Project {project_id} workflow finished but status is '{latest_project_doc.get('status')}' — finalizing.")
            from app.services.workflow import finalize_project_delivery
            await finalize_project_delivery(db, project_id, latest_project_doc)
        
        # Append AI message indicating completion
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        codebase_count = len(latest_project_doc.get("codebase", []))
        synthesis_info = latest_project_doc.get("synthesis_validation", {})
        file_count = synthesis_info.get("total_files", codebase_count)
        
        success_msg = {
            "id": f"m-{uuid.uuid4().hex[:8]}",
            "sender": "ai",
            "text": (
                f"🎉 Your project **{name}** has been successfully generated! "
                f"Sarthi synthesized **{file_count} source files** across backend, frontend, and infrastructure. "
                f"You can explore the codebase and architecture in the projects history or the file panel on the right!"
            ),
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
        logger.info(f"Project {project_id} compilation complete! ({file_count} files synthesized)")
        
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

class SuggestBlueprintRequest(BaseModel):
    idea: str

@router.post("/suggest-blueprint")
async def suggest_blueprint(req: SuggestBlueprintRequest, current_user: dict = Depends(get_current_user)):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Project idea description is required")
    from app.services.ai import generate_single_project_suggestion
    blueprint = await generate_single_project_suggestion(req.idea.strip())
    return blueprint

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
            trd=doc.get("trd"),
            hitl_enabled=doc.get("hitl_enabled", True),
            hitl_approved=doc.get("hitl_approved", False),
            implementation_plan=doc.get("implementation_plan"),
            validation_logs=doc.get("validation_logs", [])
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
        trd=doc.get("trd"),
        hitl_enabled=doc.get("hitl_enabled", True),
        hitl_approved=doc.get("hitl_approved", False),
        implementation_plan=doc.get("implementation_plan"),
        validation_logs=doc.get("validation_logs", [])
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
        mcp_evidence=new_project["mcp_evidence"],
        hitl_enabled=new_project.get("hitl_enabled", True),
        hitl_approved=new_project.get("hitl_approved", False),
        implementation_plan=new_project.get("implementation_plan"),
        validation_logs=new_project.get("validation_logs", [])
    )

@router.post("", response_model=ProjectResponse)
async def compile_project(
    payload: ProjectCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    from app.core.logger import current_project_id
    current_project_id.set(project_id)
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
        
    requirements = None
    planning = None
    impl_plan = None
    
    # Always generate requirements, planning, and implementation plan as workflow source of truth
    try:
        logger.info("Generating requirements, planning, and implementation plan during project creation...")
        from app.agents.requirement_analyzer import RequirementAnalyzerAgent
        from app.agents.planner import PlannerAgent
        from app.agents.research_planning_agent import ResearchPlanningAgent
        
        analyzer = RequirementAnalyzerAgent()
        requirements = await analyzer.analyze(blueprint_payload or {}, payload.theme)
        
        planner = PlannerAgent()
        planning = await planner.plan(requirements)
        
        researcher = ResearchPlanningAgent()
        impl_plan = await researcher.generate_plan(requirements, planning, [])
        
        logger.info("Successfully generated PRD/TRD/MRD-aligned implementation plan during project creation.")
    except Exception as plan_err:
        logger.error(f"Failed to generate implementation plan during project creation: {plan_err}")
        impl_plan = {
            "plan_markdown": f"# Implementation Plan\nFailed to generate plan: {str(plan_err)}",
            "proposed_changes": [],
        }

    new_project = {
        "_id": project_id,
        "name": payload.name,
        "category": detected_category,
        "status": "waiting_approval" if payload.hitl_enabled else "documents_ready",
        "progress": 15 if payload.hitl_enabled else 100,
        "step": "Awaiting Implementation Plan Approval" if payload.hitl_enabled else "Documents Generated",
        "summary": (
            "PRD, MRD, TRD, and Implementation Plan compiled successfully. "
            "Review and approve to start production codebase generation."
            if payload.hitl_enabled
            else "PRD, MRD, TRD, and Implementation Plan compiled successfully. Review specs, then proceed to build."
        ),
        "codebase": [],
        "created": created_str,
        "created_at_dt": datetime.now(timezone.utc),
        "user_id": current_user["id"],
        "chat_id": payload.chat_id,
        "theme": payload.theme,
        "blueprint": blueprint_payload,
        "initial_prompt": blueprint_payload,
        "theme_palette": payload.theme_palette.dict() if payload.theme_palette else None,
        "prd": docs.get("prd", ""),
        "mrd": docs.get("mrd", ""),
        "trd": docs.get("trd", ""),
        "hackathon_metadata": hackathon_metadata,
        "mcp_evidence": mcp_evidence,
        "hitl_enabled": payload.hitl_enabled if payload.hitl_enabled is not None else True,
        "hitl_approved": False,
        "requirements": requirements,
        "planning": planning,
        "implementation_plan": impl_plan,
        "validation_logs": [],
    }
    
    await db.projects.insert_one(new_project)
    
    # Mark chat session as confirmed, link project_id and update category
    await db.chats.update_one(
        {"_id": payload.chat_id, "user_id": current_user["id"]},
        {"$set": {"is_confirmed": True, "project_id": project_id, "category": detected_category}}
    )
    
    # Notify chat that documents were generated
    time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    if payload.hitl_enabled:
        text_msg = (
            f"Sarthi generated **PRD**, **MRD**, **TRD**, and a detailed **Implementation Plan** "
            f"for **{payload.name}**. Review them in the right pane, edit the plan if needed, "
            f"then approve to start production codebase generation."
        )
    else:
        text_msg = (
            f"Sarthi generated **PRD**, **MRD**, **TRD**, and an **Implementation Plan** "
            f"for **{payload.name}**. Review the specifications in the right pane, "
            f"then click Proceed to Build to compile the production-ready codebase."
        )
        
    start_msg = {
        "id": f"m-{uuid.uuid4().hex[:8]}",
        "sender": "ai",
        "text": text_msg,
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
        mcp_evidence=new_project["mcp_evidence"],
        hitl_enabled=new_project["hitl_enabled"],
        hitl_approved=new_project["hitl_approved"],
        implementation_plan=new_project["implementation_plan"],
        validation_logs=new_project["validation_logs"]
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
            "text": f"Sarthi is now compiling your production-ready FastAPI + React codebase for project **{project['name']}** in the background...",
            "timestamp": time_str
        }
        await db.chats.update_one(
            {"_id": chat_id},
            {"$push": {"messages": comp_msg}}
        )
        
    # Parse models from dict
    from app.models.project import BlueprintSchema, ThemePaletteSchema
    blueprint_dict = project.get("blueprint")
    blueprint = None
    if blueprint_dict:
        blueprint = BlueprintSchema(**blueprint_dict)
        
    theme_palette_dict = project.get("theme_palette")
    theme_palette = None
    if theme_palette_dict:
        theme_palette = ThemePaletteSchema(**theme_palette_dict)

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
        mcp_evidence=updated_project.get("mcp_evidence"),
        hitl_enabled=updated_project.get("hitl_enabled", True),
        hitl_approved=updated_project.get("hitl_approved", False),
        implementation_plan=updated_project.get("implementation_plan"),
        validation_logs=updated_project.get("validation_logs", [])
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
    if "hitl_enabled" in payload:
        updates["hitl_enabled"] = bool(payload["hitl_enabled"])
        
    if updates:
        await db.projects.update_one({"_id": project_id}, {"$set": updates})
        
    return {"status": "success", "updates": updates}

@router.post("/{project_id}/approve", response_model=ProjectResponse)
async def approve_project_plan(
    project_id: str,
    payload: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    plan_edits = payload.get("implementation_plan")
    
    # Persist plan edits to MongoDB BEFORE resuming workflow so agents read edited plan
    update_fields = {
        "hitl_approved": True,
        "status": "generating",
        "progress": 20,
        "step": "Resuming codebase compilation..."
    }
    if plan_edits:
        update_fields["implementation_plan"] = plan_edits
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": update_fields}
    )
    
    from app.services.workflow import resume_project_workflow
    background_tasks.add_task(
        resume_project_workflow,
        db,
        project_id,
        plan_edits
    )
    
    updated_project = await db.projects.find_one({"_id": project_id})
    from app.models.project import BlueprintSchema, ThemePaletteSchema
    blueprint_dict = updated_project.get("blueprint")
    blueprint = BlueprintSchema(**blueprint_dict) if blueprint_dict else None
    
    theme_palette_dict = updated_project.get("theme_palette")
    theme_palette = ThemePaletteSchema(**theme_palette_dict) if theme_palette_dict else None
    
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
        mcp_evidence=updated_project.get("mcp_evidence"),
        hitl_enabled=updated_project.get("hitl_enabled", True),
        hitl_approved=updated_project.get("hitl_approved", False),
        implementation_plan=updated_project.get("implementation_plan"),
        validation_logs=updated_project.get("validation_logs", [])
    )

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Restore the chat session to active state (is_confirmed=False, project_id=None)
    await db.chats.update_one(
        {"project_id": project_id, "user_id": current_user["id"]},
        {"$set": {"is_confirmed": False, "project_id": None}}
    )
    
    result = await db.projects.delete_one({"_id": project_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": "Project deleted successfully"}


@router.post("/{project_id}/regenerate-documents")
async def regenerate_project_documents(
    project_id: str,
    payload: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Regenerate PRD/MRD/TRD documents for an existing project."""
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.get("status") == "generating":
        raise HTTPException(status_code=400, detail="Cannot regenerate documents while project is compiling")
    
    from app.services.ai import generate_prd_mrd_trd
    
    blueprint = project.get("blueprint", {}) or {}
    idea = blueprint.get("idea", "")
    features = blueprint.get("features", [])
    tech_stack = blueprint.get("tech_stack", "")
    features_str = ", ".join(features) if features else ""
    
    custom_prompt = ""
    if payload and payload.get("custom_prompt"):
        custom_prompt = f"\nAdditional instructions: {payload['custom_prompt']}"
    
    prompt_for_docs = f"Project Idea: {idea}\nFeatures: {features_str}\nTech Stack: {tech_stack}{custom_prompt}"
    
    try:
        docs = await generate_prd_mrd_trd(project["name"], prompt_for_docs)
    except Exception as e:
        logger.error(f"Failed to regenerate documents for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Document regeneration failed: {str(e)}")
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "prd": docs.get("prd", ""),
            "mrd": docs.get("mrd", ""),
            "trd": docs.get("trd", ""),
            "status": "documents_ready" if not project.get("hitl_enabled") else "waiting_approval",
        }}
    )
    
    return {"status": "success", "message": "Documents regenerated successfully"}


@router.post("/{project_id}/cancel")
async def cancel_project_compilation(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an in-progress project compilation."""
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.get("status") != "generating":
        raise HTTPException(status_code=400, detail="Project is not currently generating")
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "status": "cancelled",
            "step": "Compilation cancelled by user",
            "progress": project.get("progress", 0),
        }}
    )
    
    # Notify via WebSocket
    from app.services.ws_manager import manager
    await manager.broadcast_progress(project_id, {
        "type": "progress",
        "project_id": project_id,
        "progress": project.get("progress", 0),
        "step": "Compilation cancelled by user",
        "status": "cancelled"
    })
    
    return {"status": "success", "message": "Compilation cancelled"}


@router.get("/{project_id}/download")
async def download_project_zip(project_id: str, current_user: dict = Depends(get_current_user)):
    """Downloads the generated project codebase as a valid ZIP file."""
    db = get_database()
    doc = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
        
    codebase = doc.get("codebase", [])
    
    # Auto-heal: If codebase is empty but we have requirements or a compiled status,
    # run finalize_project_delivery on-the-fly to compile/assemble the workspace ZIP.
    if not codebase and (doc.get("status") in ("completed", "completed_with_issues", "generating", "failed", "waiting_approval") or doc.get("synthesized_codebase")):
        logger.info(f"Project {project_id} download requested but codebase is empty. Running on-the-fly export/assembly...")
        try:
            from app.services.workflow import finalize_project_delivery
            updated_doc = await finalize_project_delivery(db, project_id, doc)
            if updated_doc:
                doc = updated_doc
                codebase = doc.get("codebase", [])
        except Exception as e:
            logger.error(f"On-the-fly codebase assembly failed for project {project_id}: {e}")

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


@router.post("/{project_id}/export", response_model=ProjectResponse)
async def force_export_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Force re-assembles, validates and exports the project's codebase."""
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    from app.services.workflow import finalize_project_delivery
    
    # We want to force re-assembly, so we clear the old codebase to force assembly
    if project.get("codebase"):
        await db.projects.update_one({"_id": project_id}, {"$set": {"codebase": []}})
        project["codebase"] = []
        
    updated_project = await finalize_project_delivery(db, project_id, project)
    
    from app.models.project import BlueprintSchema, ThemePaletteSchema
    blueprint_dict = updated_project.get("blueprint")
    blueprint = BlueprintSchema(**blueprint_dict) if blueprint_dict else None
    theme_palette_dict = updated_project.get("theme_palette")
    theme_palette = ThemePaletteSchema(**theme_palette_dict) if theme_palette_dict else None
    
    return ProjectResponse(
        id=updated_project["_id"],
        name=updated_project["name"],
        category=updated_project["category"],
        status=updated_project["status"],
        progress=updated_project["progress"],
        step=updated_project["step"],
        summary=updated_project["summary"],
        codebase=[],  # Omit in response to prevent bloated payloads
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
        mcp_evidence=updated_project.get("mcp_evidence"),
        hitl_enabled=updated_project.get("hitl_enabled", True),
        hitl_approved=updated_project.get("hitl_approved", False),
        implementation_plan=updated_project.get("implementation_plan"),
        validation_logs=updated_project.get("validation_logs", [])
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
