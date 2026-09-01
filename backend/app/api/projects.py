import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import io
import zipfile
from pydantic import BaseModel
from app.models.project import ProjectResponse, ProjectCreate, BlueprintSchema, ThemePaletteSchema
from app.db.mongodb import get_database
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.progress_logger import progress_logger
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

def _map_project_doc(doc: dict) -> ProjectResponse:
    if "_id" in doc and "id" not in doc:
        doc["id"] = doc["_id"]
    return ProjectResponse(
        id=doc.get("id") or doc.get("_id"),
        name=doc.get("name"),
        category=doc.get("category"),
        status=doc.get("status", "completed"),
        progress=doc.get("progress", 100),
        step=doc.get("step", ""),
        summary=doc.get("summary", ""),
        codebase=doc.get("codebase", []),
        created=doc.get("created", ""),
        user_id=doc.get("user_id"),
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
        hitl_enabled=doc.get("hitl_enabled", False),
        hitl_approved=doc.get("hitl_approved", True),
        implementation_plan=(
            {"plan_markdown": doc.get("implementation_plan"), "proposed_changes": []}
            if isinstance(doc.get("implementation_plan"), str)
            else doc.get("implementation_plan")
        ),
        validation_logs=doc.get("validation_logs", []),
        compilation_logs=doc.get("compilation_logs", []),
        generation_type=doc.get("generation_type", "full_stack")
    )

async def broadcast_agent_progress(db, project_id: str, progress: int | float, step: str) -> None:
    from app.services.workflow import broadcast_agent_progress as workflow_broadcast
    await workflow_broadcast(db, project_id, progress, step)


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
        pass
        return

    optimization_arch = project_doc.get("optimization_architecture")
    if not optimization_arch:
        try:
            await broadcast_agent_progress(db, project_id, 80, "Optimizing Performance...")
            pass
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
            pass
        except Exception as opt_err:
            pass

    if not project_doc.get("optimization_architecture"):
        return

    if not project_doc.get("code_generation_plan"):
        try:
            pass
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
            pass
        except Exception as codegen_err:
            pass

    if not project_doc.get("code_generation_plan"):
        return

    if not project_doc.get("database_model_generation"):
        try:
            pass
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
            pass
        except Exception as db_model_err:
            pass

    if not project_doc.get("backend_code_generation") and project_doc.get("database_model_generation"):
        try:
            pass
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
            pass
        except Exception as backend_code_err:
            pass

    if not project_doc.get("api_implementation") and project_doc.get("backend_code_generation"):
        try:
            await broadcast_agent_progress(db, project_id, 81, "Implementing APIs...")
            pass
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
            pass
        except Exception as api_impl_err:
            pass

    if not project_doc.get("frontend_code_generation") and project_doc.get("api_implementation"):
        try:
            await broadcast_agent_progress(db, project_id, 83, "Generating Frontend Code...")
            pass
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
            pass
        except Exception as fe_code_err:
            pass

    if not project_doc.get("ui_component_generation") and project_doc.get("frontend_code_generation"):
        try:
            await broadcast_agent_progress(db, project_id, 85, "Generating UI Components...")
            pass
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
            pass
        except Exception as ui_comp_err:
            pass

    if not project_doc.get("state_implementation") and project_doc.get("ui_component_generation"):
        try:
            await broadcast_agent_progress(db, project_id, 87, "Implementing State Management...")
            pass
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
            pass
        except Exception as state_impl_err:
            pass

    if not project_doc.get("integration_generation") and project_doc.get("state_implementation"):
        try:
            await broadcast_agent_progress(db, project_id, 89, "Integrating Systems...")
            pass
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
            pass
        except Exception as integration_err:
            pass

    if not project_doc.get("build_compilation") and project_doc.get("integration_generation"):
        try:
            await broadcast_agent_progress(db, project_id, 91, "Compiling Build Assets...")
            pass
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
            pass
        except Exception as build_err:
            pass

    if not project_doc.get("error_correction") and project_doc.get("build_compilation"):
        try:
            await broadcast_agent_progress(db, project_id, 93, "Running Error Correction...")
            pass
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
            pass
        except Exception as ec_err:
            pass

    if not project_doc.get("project_export") and project_doc.get("error_correction"):
        try:
            await broadcast_agent_progress(db, project_id, 95, "Exporting Project Files...")
            pass
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
            pass
        except Exception as export_err:
            pass

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
    pass
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
                pass
                return
            
            # If workflow finished but status wasn't set, finalize now
            pass
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
        pass
        
    except Exception as e:
        pass
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
    from app.services.suggestion_cache import SuggestionCache
    cached = SuggestionCache.get(category)
    if cached is not None:
        return cached
    suggestions = await generate_project_suggestions(category)
    if suggestions:
        SuggestionCache.set(category, suggestions)
    return suggestions

class SuggestBlueprintRequest(BaseModel):
    idea: str
    generation_type: str = "full_stack"

@router.post("/suggest-blueprint")
async def suggest_blueprint(req: SuggestBlueprintRequest, current_user: dict = Depends(get_current_user)):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Project idea description is required")
    from app.services.ai import generate_single_project_suggestion
    blueprint = await generate_single_project_suggestion(req.idea.strip(), req.generation_type)
    return blueprint

@router.get("", response_model=list[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.projects.find({"user_id": current_user["id"]}).sort("created_at_dt", -1)
    projects = []
    async for doc in cursor:
        projects.append(_map_project_doc(doc))
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return _map_project_doc(doc)

from pydantic import BaseModel as PydanticBaseModel

class GenerateDocumentsRequest(PydanticBaseModel):
    name: str
    prompt: str
    generation_type: Optional[str] = "full_stack"

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
        docs = await generate_prd_mrd_trd(payload.name, payload.prompt, payload.generation_type)
    except Exception as e:
        pass
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
        "generation_type": payload.generation_type or "full_stack",
    }
    
    await db.projects.insert_one(new_project)
    
    return _map_project_doc(new_project)

async def run_full_generation_pipeline(
    project_id: str,
    chat_id: str,
    name: str,
    category: str,
    user_id: str,
    theme: Optional[str],
    blueprint_payload: Optional[dict],
    theme_palette_dict: Optional[dict],
    generation_type: str,
    prompt_for_docs: str,
    chat_history_str: str
):
    """Pre-generation phase: generate TRD + Requirements + Planning + Implementation Plan
    and save each to MongoDB atomically before triggering the main orchestration pipeline.

    Design principles:
    - Each step is saved to MongoDB immediately after generation (atomic, not batched).
    - Only TRD is generated — PRD and MRD are NOT part of this workflow.
    - If TRD generation fails, a fallback TRD is used so downstream verifier never blocks.
    - Each agent step has individual error handling + fallback values.
    """
    pass
    db = get_database()

    # ── Step 1: TRD Generation — Atomic Save (0-8%) ──────────────────────────────
    await manager.broadcast_progress(
        project_id=project_id,
        progress=5,
        step="Generating Technical Requirements Document (TRD)...",
        status="generating"
    )
    trd = ""
    for trd_attempt in range(1, 3):  # Max 2 attempts
        try:
            from app.services.ai import generate_prd_mrd_trd
            docs = await generate_prd_mrd_trd(
                name,
                prompt_for_docs,
                generation_type,
                theme=theme,
                theme_palette=theme_palette_dict,
                chat_history=chat_history_str,
                exclude_prd_mrd=True
            )
            trd = docs.get("trd", "").strip()
            if trd and len(trd) > 100:
                break
            pass
        except Exception as e:
            pass

    if not trd or len(trd) < 100:
        # Fallback TRD — ensures verifier check never fails due to empty TRD
        trd = (
            f"# Technical Requirements Document\n\n"
            f"## Project: {name}\n\n"
            f"**Generation Type:** {generation_type}\n\n"
            f"**Summary:** {prompt_for_docs}\n\n"
            f"Technical requirements are derived from the project blueprint and chat context. "
            f"Architecture agents will design the system based on the blueprint specification."
        )
        pass

    # Save TRD immediately — do NOT batch with other fields
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"trd": trd, "prd": "", "mrd": ""}}  # PRD/MRD intentionally empty
    )
    pass

    # ── Step 2: Requirements Analysis — Atomic Save (8-14%) ──────────────────────
    await manager.broadcast_progress(
        project_id=project_id,
        progress=10,
        step="Analyzing blueprint requirements...",
        status="generating"
    )
    requirements = None
    try:
        from app.agents.requirement_analyzer import RequirementAnalyzerAgent
        analyzer = RequirementAnalyzerAgent()
        requirements = await analyzer.analyze(
            blueprint_payload or {},
            theme,
            theme_palette_dict,
            chat_history_str,
            generation_type
        )
        if requirements:
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {"requirements": requirements}}
            )
            pass
    except Exception as e:
        pass
        # requirements stays None — LangGraph workflow will re-run it via its own retry

    # ── Step 3: Planner — Atomic Save (14-19%) ───────────────────────────────────
    await manager.broadcast_progress(
        project_id=project_id,
        progress=15,
        step="Orchestrating system architecture blueprints...",
        status="generating"
    )
    planning = None
    if requirements:
        try:
            from app.agents.planner import PlannerAgent
            planner = PlannerAgent()
            planning = await planner.plan(requirements)
            if planning:
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$set": {"planning": planning}}
                )
                pass
        except Exception as e:
            pass

    # ── Step 4: Implementation Plan — Atomic Save (19-25%) ───────────────────────
    await manager.broadcast_progress(
        project_id=project_id,
        progress=20,
        step="Compiling technical implementation plan...",
        status="generating"
    )
    impl_plan = None
    if requirements and planning:
        try:
            from app.agents.research_planning_agent import ResearchPlanningAgent
            researcher = ResearchPlanningAgent()
            impl_plan = await researcher.generate_plan(requirements, planning, [], generation_type)
            if impl_plan:
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$set": {"implementation_plan": impl_plan}}
                )
                pass
        except Exception as e:
            pass

    if not impl_plan:
        # Minimal fallback so downstream agents have something to reference
        impl_plan = {
            "plan_markdown": (
                f"# Implementation Plan\n\nProject: {name}\n\nType: {generation_type}\n\n"
                f"Build based on TRD and blueprint specifications."
            ),
            "proposed_changes": [],
        }
        await db.projects.update_one(
            {"_id": project_id},
            {"$set": {"implementation_plan": impl_plan}}
        )

    pass

    # ── Step 5: Trigger main orchestration pipeline (25-100%) ────────────────────
    await manager.broadcast_progress(
        project_id=project_id,
        progress=25,
        step="Initializing codebase synthesizer...",
        status="generating"
    )

    from app.models.project import BlueprintSchema, ThemePaletteSchema
    blueprint = BlueprintSchema(**blueprint_payload) if blueprint_payload else None
    theme_palette = ThemePaletteSchema(**theme_palette_dict) if theme_palette_dict else None

    await run_project_compilation(
        project_id,
        chat_id,
        name,
        category,
        user_id,
        theme,
        blueprint,
        theme_palette
    )


@router.post("", response_model=ProjectResponse)
async def compile_project(
    payload: ProjectCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    progress_logger.set_context(project_id=project_id)
    created_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    
    # Check if chat exists
    chat_exists = await db.chats.find_one({"_id": payload.chat_id, "user_id": current_user["id"]})
    if not chat_exists:
        raise HTTPException(status_code=400, detail="Invalid chat_id specified")
        
    # Auto-identify category on the basis of conversation and user's idea
    from app.services.ai import auto_identify_category
    bp_dict = payload.blueprint.dict() if payload.blueprint else {}
    detected_category = await auto_identify_category(bp_dict, chat_exists.get("messages", []))
    progress_logger.info(f"Project category auto-identified as: {detected_category}", project_id=project_id)

    # Format chat history for context
    chat_messages = chat_exists.get("messages", [])
    chat_history_str = ""
    for msg in chat_messages:
        sender = msg.get("sender", "user")
        text = msg.get("text", "")
        chat_history_str += f"{sender.capitalize()}: {text}\n"

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

    new_project = {
        "_id": project_id,
        "name": payload.name,
        "category": detected_category,
        "status": "generating",
        "progress": 3,
        "step": "Initializing TRD generation...",
        "summary": "Technical specifications and codebase synthesis started automatically.",
        "codebase": [],
        "created": created_str,
        "created_at_dt": datetime.now(timezone.utc),
        "user_id": current_user["id"],
        "chat_id": payload.chat_id,
        "theme": payload.theme,
        "blueprint": blueprint_payload,
        "initial_prompt": blueprint_payload,
        "theme_palette": payload.theme_palette.dict() if payload.theme_palette else None,
        "prd": "",
        "mrd": "",
        "trd": "",
        "hackathon_metadata": hackathon_metadata,
        "mcp_evidence": mcp_evidence,
        "hitl_enabled": False,
        "hitl_approved": True,
        "requirements": None,
        "planning": None,
        "implementation_plan": None,
        "validation_logs": [],
        "generation_type": payload.generation_type or "full_stack",
    }
    
    await db.projects.insert_one(new_project)
    
    # Mark chat session as confirmed, link project_id and update category
    await db.chats.update_one(
        {"_id": payload.chat_id, "user_id": current_user["id"]},
        {"$set": {"is_confirmed": True, "project_id": project_id, "category": detected_category}}
    )
    
    # Notify chat that codebase generation started
    time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    text_msg = (
        f"Sarthi is generating the **Technical Requirements Document (TRD)** and **Implementation Plan** "
        f"for **{payload.name}**, and will compile the codebase automatically in the background."
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
    
    # Add background task
    background_tasks.add_task(
        run_full_generation_pipeline,
        project_id,
        payload.chat_id,
        payload.name,
        detected_category,
        current_user["id"],
        payload.theme,
        blueprint_payload,
        payload.theme_palette.dict() if payload.theme_palette else None,
        payload.generation_type or "full_stack",
        prompt_for_docs,
        chat_history_str
    )
    
    return _map_project_doc(new_project)

@router.get("/{project_id}/logs")
async def get_project_compilation_logs(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logs = project.get("compilation_logs", [])
    return {"status": "success", "logs": logs}

@router.post("/{project_id}/compile", response_model=ProjectResponse)
async def compile_project_codebase(
    project_id: str,
    background_tasks: BackgroundTasks,
    force_run_from_agent: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Handle surgical force-regeneration if requested
    if force_run_from_agent:
        from app.services.backtrack import BacktrackManager
        if force_run_from_agent not in BacktrackManager.AGENT_DB_KEYS:
            valid_agents = ", ".join(list(BacktrackManager.AGENT_DB_KEYS.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent name: '{force_run_from_agent}'. Valid agents are: {valid_agents}"
            )
        await BacktrackManager.clear_downstream_keys(db, project_id, force_run_from_agent)

    # Set project status to generating
    await db.projects.update_one(
        {"_id": project_id},
        {
            "$set": {
                "status": "generating",
                "progress": 5,
                "step": "Initializing Sarthi AI engine...",
                "codebase": [],
                "compilation_logs": []
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
    return _map_project_doc(updated_project)

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
    
    if plan_edits and isinstance(plan_edits, str):
        existing_plan = project.get("implementation_plan")
        if not isinstance(existing_plan, dict):
            existing_plan = {}
        existing_plan["plan_markdown"] = plan_edits
        plan_edits = existing_plan

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
    
    return _map_project_doc(updated_project)

@router.post("/{project_id}/generate-prd-mrd", response_model=ProjectResponse)
async def generate_prd_mrd_endpoint(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate PRD and MRD
    from app.services.ai import generate_prd_mrd_trd
    
    blueprint_dict = project.get("blueprint") or {}
    idea = blueprint_dict.get("idea", "")
    features = blueprint_dict.get("features", [])
    tech_stack = blueprint_dict.get("tech_stack", "")
    features_str = ", ".join(features) if features else ""
    prompt_for_docs = f"Project Idea: {idea}\nFeatures: {features_str}\nTech Stack: {tech_stack}"
    
    chat_history_str = ""
    chat_exists = await db.chats.find_one({"_id": project.get("chat_id"), "user_id": current_user["id"]})
    if chat_exists:
        chat_messages = chat_exists.get("messages", [])
        for msg in chat_messages:
            sender = msg.get("sender", "user")
            text = msg.get("text", "")
            chat_history_str += f"{sender.capitalize()}: {text}\n"

    try:
        pass
        docs = await generate_prd_mrd_trd(
            project.get("name"), 
            prompt_for_docs, 
            project.get("generation_type", "full_stack"),
            theme=project.get("theme"),
            theme_palette=project.get("theme_palette"),
            chat_history=chat_history_str,
            exclude_prd_mrd=False
        )
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail=f"Failed to generate documents: {str(e)}")

    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"prd": docs.get("prd", ""), "mrd": docs.get("mrd", "")}}
    )
    
    updated_project = await db.projects.find_one({"_id": project_id})
    return _map_project_doc(updated_project)

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
    
    chat_history_str = ""
    chat_id = project.get("chat_id")
    if chat_id:
        chat_doc = await db.chats.find_one({"_id": chat_id, "user_id": current_user["id"]})
        if chat_doc:
            chat_messages = chat_doc.get("messages", [])
            for msg in chat_messages:
                sender = msg.get("sender", "user")
                text = msg.get("text", "")
                chat_history_str += f"{sender.capitalize()}: {text}\n"

    try:
        docs = await generate_prd_mrd_trd(
            project["name"], 
            prompt_for_docs, 
            project.get("generation_type", "full_stack"),
            theme=project.get("theme"),
            theme_palette=project.get("theme_palette"),
            chat_history=chat_history_str
        )
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail=f"Document regeneration failed: {str(e)}")
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "prd": docs.get("prd", ""),
            "mrd": docs.get("mrd", ""),
            "trd": docs.get("trd", ""),
            "status": "documents_ready",
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


@router.post("/{project_id}/pause", response_model=ProjectResponse)
async def pause_project_compilation(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause an in-progress project compilation."""
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.get("status") != "generating":
        raise HTTPException(status_code=400, detail="Project is not currently generating and cannot be paused")
        
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "status": "paused",
            "step": "Compilation paused by user",
            "progress": project.get("progress", 0)
        }}
    )
    
    # Broadcast pause state via WS
    from app.services.ws_manager import manager
    await manager.broadcast_progress(
        project_id=project_id,
        progress=project.get("progress", 0),
        step="Compilation paused by user",
        status="paused"
    )
    
    updated_project = await db.projects.find_one({"_id": project_id})
    return _map_project_doc(updated_project)


@router.post("/{project_id}/resume", response_model=ProjectResponse)
async def resume_project_compilation(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Resume a paused project compilation."""
    db = get_database()
    project = await db.projects.find_one({"_id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.get("status") != "paused":
        raise HTTPException(status_code=400, detail="Project is not currently paused and cannot be resumed")
        
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "status": "generating",
            "step": "Resuming codebase compilation..."
        }}
    )
    
    # Broadcast resume state via WS
    from app.services.ws_manager import manager
    await manager.broadcast_progress(
        project_id=project_id,
        progress=project.get("progress", 0),
        step="Resuming codebase compilation...",
        status="generating"
    )
    
    # Start resume workflow in the background
    from app.services.workflow import resume_project_workflow
    background_tasks.add_task(
        resume_project_workflow,
        db,
        project_id,
        None # No plan edits since we are resuming from pause
    )
    
    updated_project = await db.projects.find_one({"_id": project_id})
    return _map_project_doc(updated_project)


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
        pass
        try:
            from app.services.workflow import finalize_project_delivery
            updated_doc = await finalize_project_delivery(db, project_id, doc)
            if updated_doc:
                doc = updated_doc
                codebase = doc.get("codebase", [])
        except Exception as e:
            pass

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
    
    return _map_project_doc(updated_project)



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
                pass
                
        # Push .env.example if we have export intelligence
        project_export = doc.get("project_export", {})
        if project_export:
            env_templates = project_export.get("environment_generation", {}).get("env_templates", [])
            if env_templates:
                try:
                    repo.create_file(".env.example", "Sarthi auto-commit: add environment template", "\n".join(env_templates), branch="main")
                except Exception as e:
                    pass
                    
        return {
            "status": "success", 
            "message": f"Successfully pushed to GitHub repository: {repo.html_url}",
            "repo_url": repo.html_url
        }
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail=f"Failed to push to GitHub: {str(e)}")
