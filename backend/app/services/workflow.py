import inspect
import asyncio
from typing import Dict, Any, TypedDict, Optional, List
from datetime import datetime, timezone
import uuid
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from app.agents.context import (
    IncompleteJSONError,
    build_compilation_context,
    build_document_context,
    generate_agent_prompt,
)
from app.core.progress_logger import progress_logger
from app.services.llm_router import current_agent_feedback
from app.services.contract_auditor import ContractAuditor
from app.services.surgical_gap_filler import SurgicalGapFiller
from app.services.state_merger import StateMerger
from app.services.api_contracts import (
    endpoint_matches_entity,
    ensure_entity_crud_endpoints,
    get_entity_name,
    is_internal_system_entity,
)

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
from app.agents.entity_discovery import EntityDiscoveryAgent
from app.agents.entity_generation_planner import EntityGenerationPlannerAgent
from app.agents.entity_generators import BackendEntityGenerator, FrontendEntityGenerator
from app.services.module_assembler import ModuleAssembler
from app.services.project_assembler import assemble_project_codebase, detect_tech_stack
from app.agents.customization_agent import DynamicCustomizationAgent
import time
import re
import json

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
        step=step,
        active_healing_context=project_doc.get("active_healing_context"),
        backtrack_history=project_doc.get("backtrack_history", [])
    )
    progress_logger.info(f"Project progress: {final_progress}% - {step}", project_id=project_id, step=step)

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
    backtrack_depth: int
    agent_retries: Dict[str, int]
    active_healing_context: Optional[Dict[str, Any]]
    backtrack_target: Optional[str]
    
    # Entity-Level Generation State
    entity_discovery: Optional[Dict[str, Any]]
    entity_generation_plan: Optional[Dict[str, Any]]
    synthesized_modules: Annotated[Dict[str, Any], reduce_project_doc]
    entity_generation_metrics: Annotated[Dict[str, Any], reduce_project_doc]

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
        "EntityDiscoveryAgent": EntityDiscoveryAgent,
        "EntityGenerationPlannerAgent": EntityGenerationPlannerAgent,
        "BackendEntityGenerator": BackendEntityGenerator,
        "FrontendEntityGenerator": FrontendEntityGenerator,
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
        "EntityDiscoveryAgent": "entity_discovery",
        "EntityGenerationPlannerAgent": "entity_generation_plan",
        "BackendEntityGenerator": "backend_entity_generation",
        "FrontendEntityGenerator": "frontend_entity_generation",
    }
    return mapping.get(agent_name, agent_name.lower())


def normalize_agent_output_for_contracts(agent_name: str, result: Any, project_doc: Dict[str, Any]) -> Any:
    """Apply deterministic contract repairs before cache/idempotency/validation handoff."""
    if agent_name != "APIAgent" or not isinstance(result, dict):
        return result

    requirements = project_doc.get("requirements", {}) or {}
    auth_required = requirements.get("authentication", {}).get("required", True)
    return ensure_entity_crud_endpoints(
        result,
        project_doc.get("db_architecture", {}) or {},
        bool(auth_required),
    )


async def validate_agent_output_contracts(
    agent_name: str,
    result: Any,
    project_doc: Dict[str, Any],
) -> tuple[bool, str, List[Dict[str, Any]]]:
    verifier = VerifierAgent()
    is_complete, feedback = await verifier.verify(agent_name, result)
    if not is_complete:
        return False, feedback, []

    try:
        is_incr_valid, incr_feedback, incr_logs = await verifier.verify_incremental(agent_name, result, project_doc)
    except Exception:
        return True, "", []
    return is_incr_valid, incr_feedback, incr_logs

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
        # Codebase keys — passed as lists
        "synthesized_codebase": "synthesized_codebase",
        "assembled_codebase": "assembled_codebase",
    }
    
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        db_key = param_mapping.get(param_name)
        if db_key:
            # Handle list keys — these are lists not dicts
            if db_key in ("codebase", "synthesized_codebase", "assembled_codebase"):
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
    """Attach TRD and compilation context so every agent shares the same source of truth.
    PRD and MRD are intentionally set to empty — this workflow does not generate them."""
    project_doc["trd"] = project_doc.get("trd", "") or ""
    project_doc["prd"] = ""  # Intentionally empty — not generated in this workflow
    project_doc["mrd"] = ""  # Intentionally empty — not generated in this workflow
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
    """Executes a single agent node with verification and fallback retries.
    
    Key behaviors:
    - Idempotency: If the agent's DB key already has valid data, skip execution.
    - IncompleteJSONError is treated as a retryable failure (result=None), not a valid result.
    - After max retries, saves whatever partial result exists and advances (no pipeline restart).
    """
    from app.agents.registry import should_run_agent, get_group_for_agent
    gen_type = project_doc.get("generation_type", "full_stack")
    if not should_run_agent(agent_name, gen_type):
        pass
        return None

    db_key = get_agent_db_key(agent_name)

    # —— Deterministic Artifact Cache Check ——
    from app.services.artifact_cache import ArtifactCache
    from app.services.dependency_dag import DependencyDAG, AGENT_TO_ARTIFACT

    art_type = AGENT_TO_ARTIFACT.get(agent_name, agent_name.lower())
    input_hash = ArtifactCache.compute_input_hash(project_doc.get("blueprint") or project_doc.get("initial_prompt") or {})
    dep_hash = DependencyDAG.compute_dependency_hash(project_doc, art_type)
    cache_key = ArtifactCache.compute_cache_key(project_id, agent_name, input_hash=input_hash, dependency_hash=dep_hash)

    cached_content = await ArtifactCache.get(db, project_id, agent_name, cache_key)
    if cached_content and isinstance(cached_content, dict) and len(cached_content) > 0:
        cached_content = normalize_agent_output_for_contracts(agent_name, cached_content, project_doc)
        is_cached_valid, cached_feedback, cached_logs = await validate_agent_output_contracts(agent_name, cached_content, project_doc)
        if not is_cached_valid:
            if cached_logs and db is not None:
                await db.projects.update_one(
                    {"_id": project_id},
                    {"$push": {"incremental_validation_logs": {"$each": cached_logs}}}
                )
            progress_logger.info(
                f"Cached {agent_name} artifact failed contract validation; regenerating. {cached_feedback}",
                project_id=project_id,
                step="cache_contract_validation",
            )
        else:
            if agent_name == "APIAgent":
                await ArtifactCache.set(
                    db=db,
                    project_id=project_id,
                    agent_name=agent_name,
                    cache_key=cache_key,
                    content=cached_content,
                    input_hash=input_hash,
                    dependency_hash=dep_hash,
                )
            progress_logger.agent_success(agent_name, f"Cache HIT (0s, 0 tokens) -> Reusing verified artifact", project_id=project_id)
            project_doc[db_key] = cached_content
            return cached_content

    # —— Idempotency check: skip if this agent already produced valid output in project_doc ——
    existing = project_doc.get(db_key)
    if existing and isinstance(existing, dict) and len(existing) > 0:
        existing = normalize_agent_output_for_contracts(agent_name, existing, project_doc)
        is_existing_valid, existing_feedback, existing_logs = await validate_agent_output_contracts(agent_name, existing, project_doc)
        if is_existing_valid:
            if existing is not project_doc.get(db_key):
                project_doc[db_key] = existing
                if agent_name == "APIAgent" and db is not None:
                    await db.projects.update_one({"_id": project_id}, {"$set": {db_key: existing, f"{db_key}_full": existing}})
            return existing
        if existing_logs and db is not None:
            await db.projects.update_one(
                {"_id": project_id},
                {"$push": {"incremental_validation_logs": {"$each": existing_logs}}}
            )
        progress_logger.info(
            f"Existing {agent_name} artifact failed contract validation; regenerating. {existing_feedback}",
            project_id=project_id,
            step="existing_contract_validation",
        )

    agent = get_agent_instance(agent_name)
    project_doc = enrich_project_doc_context(project_doc)
    progress_logger.agent_start(agent_name, f"Executing architecture generation ({gen_type})", project_id=project_id)
    
    # Prune/Filter project document: on backtrack re-runs use precision DAG context windowing
    from app.services.graph_store import GraphStore
    from app.services.dependency_dag import DependencyDAG
    is_backtrack_run = bool(project_doc.get("active_healing_context") or project_doc.get("backtrack_depth", 0) > 0)
    if is_backtrack_run:
        pruned_project_doc = DependencyDAG.get_pruned_context_for_agent(agent_name, project_doc, is_backtrack=True)
    else:
        pruned_project_doc = GraphStore.get_pruned_context(project_doc, agent_name)
    
    # Set tech stack and theme context variables for dynamic prompt adaptation
    from app.services.llm_router import current_tech_stack, current_theme_palette, current_generation_type
    tech_stack = pruned_project_doc.get("blueprint", {}).get("tech_stack") or pruned_project_doc.get("tech_stack")
    theme_palette = pruned_project_doc.get("theme_palette")
    
    token_tech = current_tech_stack.set(tech_stack)
    token_theme = current_theme_palette.set(theme_palette)
    token_gen_type = current_generation_type.set(gen_type)
    
    retry_count = 0
    feedback_history = []
    result = None
    
    # In dev mode: cap retries at 2 and enforce a 5-min wall-clock limit per agent
    from app.core.config import settings as _settings
    max_retries = 2 if _settings.ENVIRONMENT == "development" else 3
    MAX_AGENT_WALL_SECONDS = 300 if _settings.ENVIRONMENT == "development" else 600
    
    try:
      async with asyncio.timeout(MAX_AGENT_WALL_SECONDS):
        while retry_count <= max_retries:
            if feedback_history:
                cumulative_feedback = "\n\n".join([f"Attempt {i+1} Issue:\n{fb}" for i, fb in enumerate(feedback_history)])
            else:
                cumulative_feedback = None
                
            token = current_agent_feedback.set(cumulative_feedback)
            try:
                if agent_name == "RequirementAnalyzerAgent":
                    blueprint = pruned_project_doc.get("blueprint") or pruned_project_doc.get("initial_prompt", {}) or {}
                    result = await agent.analyze(blueprint, pruned_project_doc.get("theme"), gen_type)
                elif agent_name == "PlannerAgent":
                    result = await agent.plan(pruned_project_doc.get("requirements", {}))
                elif agent_name == "ResearchPlanningAgent":
                    result = await agent.generate_plan(
                        pruned_project_doc.get("requirements", {}),
                        pruned_project_doc.get("planning", {}),
                        pruned_project_doc.get("codebase", []),
                        gen_type
                    )
                else:
                    result = await call_agent_design(agent_name, agent, pruned_project_doc, cumulative_feedback)
            except IncompleteJSONError as e:
                # IncompleteJSONError = LLM truncated its JSON output mid-way.
                # Do NOT assign the exception as result — treat as retryable failure.
                pass
                result = None
                retry_count += 1
                feedback_history.append(
                    "Your previous JSON response was truncated/incomplete. "
                    "You MUST return a complete, valid JSON object. "
                    "Reduce verbosity if needed to stay within token limits."
                )
                current_agent_feedback.reset(token)
                continue
            except Exception as e:
                pass
                result = None
                retry_count += 1
                feedback_history.append(f"Error on previous attempt: {str(e)[:300]}. Please retry with a complete response.")
                current_agent_feedback.reset(token)
                continue
            finally:
                try:
                    current_agent_feedback.reset(token)
                except Exception:
                    pass

            # Skip verifier if result is empty/None
            if result is None or isinstance(result, Exception):
                retry_count += 1
                feedback_history.append("Agent returned no valid output. Please provide a complete JSON response.")
                continue

            result = normalize_agent_output_for_contracts(agent_name, result, project_doc)
            is_complete, new_feedback, validation_logs = await validate_agent_output_contracts(agent_name, result, project_doc)
            
            if is_complete:
                if validation_logs and db is not None:
                    await db.projects.update_one(
                        {"_id": project_id},
                        {"$push": {"incremental_validation_logs": {"$each": validation_logs}}}
                    )

                # ──────────────────────────────────────────────────────
                # Contract Auditor: Cross-check against Master TRD/Reqs
                # ──────────────────────────────────────────────────────
                try:
                    gaps = ContractAuditor.audit(agent_name, result, project_doc)
                    if gaps:
                        pass
                        # Surgical Gap Filler: Generate only the missing delta
                        max_gap_retries = 2
                        for gap_attempt in range(max_gap_retries):
                            delta = await SurgicalGapFiller.fill_gaps(
                                agent_name, gaps, result, project_doc
                            )
                            if delta and isinstance(delta, dict) and len(delta) > 0:
                                # State Merger: Merge delta into result and persist
                                result = await StateMerger.merge_and_persist(
                                    agent_name, result, delta, project_doc, db
                                )
                                pass
                                # Re-audit to confirm all gaps are now filled
                                remaining_gaps = ContractAuditor.audit(agent_name, result, project_doc)
                                if not remaining_gaps:
                                    pass
                                    break
                                else:
                                    gaps = remaining_gaps
                                    pass
                            else:
                                pass
                                break
                    else:
                        pass
                except Exception as audit_err:
                    pass

                # Generate summaries if this is a design/architecture phase
                target_keys = {
                    "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
                    "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
                    "realtime_architecture", "state_management", "devops_architecture", "security_architecture",
                    "testing_architecture", "validation_architecture", "optimization_architecture"
                }
                
                if db_key in target_keys:
                    try:
                        from app.agents.summary_agent import SummaryAgent
                        summary_agent = SummaryAgent()
                        summary_results = await summary_agent.summarize(agent_name, result)
                        summary_data = {
                            db_key: result,
                            f"{db_key}_full": result,
                            f"{db_key}_summary": summary_results["summary_output"],
                            f"{db_key}_compressed": summary_results["compressed_output"],
                            f"{db_key}_contracts": summary_results["critical_contracts"]
                        }
                    except Exception as e:
                        pass
                        summary_data = {
                            db_key: result,
                            f"{db_key}_full": result,
                            f"{db_key}_summary": "",
                            f"{db_key}_compressed": "",
                            f"{db_key}_contracts": {}
                        }
                else:
                    summary_data = {
                        db_key: result,
                        f"{db_key}_full": result
                    }
                
                # Ingest output into Knowledge Graph
                from app.services.graph_store import GraphStore
                fresh_doc = await db.projects.find_one({"_id": project_id}) or project_doc
                updated_graph = GraphStore.ingest_agent_output(fresh_doc, agent_name, result)
                summary_data["knowledge_graph"] = updated_graph
                summary_data["knowledge_base"] = fresh_doc.get("knowledge_base", {})

                await db.projects.update_one({"_id": project_id}, {"$set": summary_data})
                for k, v in summary_data.items():
                    project_doc[k] = v

                # Store into deterministic artifact cache
                try:
                    await ArtifactCache.set(
                        db=db,
                        project_id=project_id,
                        agent_name=agent_name,
                        cache_key=cache_key,
                        content=result,
                        input_hash=input_hash,
                        dependency_hash=dep_hash,
                        summary=summary_results.get("summary_output", "") if "summary_results" in locals() else ""
                    )
                except Exception:
                    pass

                progress_logger.agent_success(agent_name, f"Completed successfully and saved to DB (key={db_key})", project_id=project_id)
                return result
            else:
                if validation_logs and db is not None:
                    await db.projects.update_one(
                        {"_id": project_id},
                        {"$push": {"incremental_validation_logs": {"$each": validation_logs}}}
                    )
                retry_count += 1
                feedback_history.append(new_feedback)
                pass
                
        pass
        if result and not isinstance(result, Exception):
            target_keys = {
                "requirements", "planning", "implementation_plan", "db_architecture", "backend_architecture",
                "api_architecture", "frontend_architecture", "theme_styling", "auth_architecture",
                "realtime_architecture", "state_management", "devops_architecture", "security_architecture",
                "testing_architecture", "validation_architecture", "optimization_architecture"
            }
            if db_key in target_keys:
                try:
                    from app.agents.summary_agent import SummaryAgent
                    summary_agent = SummaryAgent()
                    summary_results = await summary_agent.summarize(agent_name, result)
                    summary_data = {
                        db_key: result,
                        f"{db_key}_full": result,
                        f"{db_key}_summary": summary_results["summary_output"],
                        f"{db_key}_compressed": summary_results["compressed_output"],
                        f"{db_key}_contracts": summary_results["critical_contracts"]
                    }
                except Exception as e:
                    pass
                    summary_data = {
                        db_key: result,
                        f"{db_key}_full": result,
                        f"{db_key}_summary": "",
                        f"{db_key}_compressed": "",
                        f"{db_key}_contracts": {}
                    }
            else:
                summary_data = {
                    db_key: result,
                    f"{db_key}_full": result
                }
            
            # Ingest output into Knowledge Graph
            from app.services.graph_store import GraphStore
            fresh_doc = await db.projects.find_one({"_id": project_id}) or project_doc
            updated_graph = GraphStore.ingest_agent_output(fresh_doc, agent_name, result)
            summary_data["knowledge_graph"] = updated_graph
            summary_data["knowledge_base"] = fresh_doc.get("knowledge_base", {})

            await db.projects.update_one({"_id": project_id}, {"$set": summary_data})
            for k, v in summary_data.items():
                project_doc[k] = v
        return result
    except asyncio.TimeoutError:
        pass
        if result and not isinstance(result, Exception):
            await db.projects.update_one({"_id": project_id}, {"$set": {db_key: result}})
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
        pass
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
        pass
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
        pass
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
    pass


async def agent_dispatcher_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    # Correction loop is DISABLED: we never reset architecture outputs.
    # Each agent has its own retry loop and idempotency check.
    # If an agent already produced output, it will be skipped automatically.
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "agent_context": project_doc.get("agent_context", {}),
            "workflow_phase": "architecture",
        }},
    )
    pass
    return {"project_doc": project_doc}

async def db_backend_workspace(db: Any, project_id: str, project_doc: Dict[str, Any], config: Any) -> Dict[str, Any]:
    pass
    
    # 1. Database Architecture Design
    await broadcast_agent_progress(db, project_id, 15, "Designing Database Architecture...")
    await run_single_agent(db, project_id, project_doc, "DatabaseArchitectureAgent")
    
    # Re-fetch project doc so downstream agents see database architecture contracts
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    
    # 2. Parallel Model Generation & Backend Architecture Structure
    await broadcast_agent_progress(db, project_id, 23, "Generating Database Models & Backend Structure...")
    
    async def run_models():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "DatabaseModelGenerationAgent")
        
    async def run_backend_structure():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "BackendArchitectureAgent")
        
    await asyncio.gather(run_models(), run_backend_structure())
    
    # Re-fetch project doc so API spec agent sees models and backend layout
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    
    # 3. API Specs Architecture
    await broadcast_agent_progress(db, project_id, 31, "Designing API Architecture...")
    await run_single_agent(db, project_id, project_doc, "APIAgent")
    
    # Re-fetch project doc
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    
    # 4. API Implementation Generator
    await broadcast_agent_progress(db, project_id, 36, "Generating API Implementation Specs...")
    await run_single_agent(db, project_id, project_doc, "APIImplementationAgent")
    
    # Final fetch
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 40, "Database & Backend Workspace Complete.")
    return {"project_doc": project_doc}

async def frontend_workspace_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    pass
    
    # 1. Parallel Frontend Layout & UI/UX Styling
    await broadcast_agent_progress(db, project_id, 41, "Designing Frontend Structure & UI/UX Theme...")
    
    async def run_fe_arch():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "FrontendArchitectureAgent")
        
    async def run_uiux_styling():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "UIUXArchitectAgent")
        
    await asyncio.gather(run_fe_arch(), run_uiux_styling())
    
    # Re-fetch project doc so component/state agents see layout and styles
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    
    # 2. Parallel UI Component Generation & State Management Design
    await broadcast_agent_progress(db, project_id, 47, "Generating UI Components & Designing State Management...")
    
    async def run_ui_components():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "UIComponentGenerationAgent")
        
    async def run_state_mgmt():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "StateManagementAgent")
        
    await asyncio.gather(run_ui_components(), run_state_mgmt())
    
    # Re-fetch project doc so state implementation agent sees stores design and components
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    
    # 3. State Implementation Generation
    await broadcast_agent_progress(db, project_id, 53, "Generating State Implementation...")
    await run_single_agent(db, project_id, project_doc, "StateImplementationAgent")
    
    # Final fetch
    project_doc = await db.projects.find_one({"_id": project_id}) or project_doc
    await broadcast_agent_progress(db, project_id, 55, "Frontend Workspace Complete.")
    return {"project_doc": project_doc}

async def architecture_design_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    gen_type = project_doc.get("generation_type", "full_stack")
    pass
    
    tasks = []
    
    if gen_type != "frontend_only":
        async def run_db_backend():
            doc = await db.projects.find_one({"_id": project_id}) or project_doc
            return await db_backend_workspace(db, project_id, doc, config)
            
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
    
    pass
    await broadcast_agent_progress(db, project_id, 56, "Designing Operations, Security, and Testing Architecture...")
    
    # In development, limit concurrency to 2 to prevent GPU cluster queue timeouts.
    # In production with Vertex AI, allow 4 concurrent pipelines.
    from app.core.config import settings
    max_concurrency = 4 if settings.ENVIRONMENT == "production" else 2
    sem = asyncio.Semaphore(max_concurrency)

    async def with_sem(coro_fn):
        async with sem:
            return await coro_fn()

    async def run_auth_security():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "AuthArchitectureAgent")
        doc_next = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc_next, "SecurityArchitectureAgent")
        
    async def run_realtime():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "RealtimeArchitectureAgent")
        
    async def run_devops():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "DevOpsArchitectureAgent")
        
    async def run_testing():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "TestingArchitectureAgent")
        
    async def run_validation():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "ValidationArchitectureAgent")
        
    async def run_optimization():
        doc = await db.projects.find_one({"_id": project_id}) or project_doc
        await run_single_agent(db, project_id, doc, "OptimizationArchitectureAgent")
        
    await asyncio.gather(
        with_sem(run_auth_security),
        with_sem(run_realtime),
        with_sem(run_devops),
        with_sem(run_testing),
        with_sem(run_validation),
        with_sem(run_optimization)
    )
    
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
    pass
    
    gen_type = project_doc.get("generation_type", "full_stack")
    expected_workspaces = ["ops_security"]
    if gen_type != "frontend_only":
        expected_workspaces.extend(["db", "backend"])
    if gen_type not in ("backend_only", "microservice"):
        expected_workspaces.append("frontend")
        
    missing = [k for k in expected_workspaces if not workspace_status[k]]
    if missing:
        pass
    
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
    pass
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
    
    gen_type = project_doc.get("generation_type", "full_stack")
    
    # 1. Entity existence check (Only if not frontend_only)
    db_entities = set()
    for e in db_arch.get("entities", []):
        entity_name = get_entity_name(e)
        if entity_name:
            db_entities.add(entity_name)
    if gen_type != "frontend_only":
        if not db_entities:
            validation_logs.append({"module": "Database", "severity": "error", "error": "No entities defined in db_architecture."})
    
    # 2. API endpoints exist for entities (Only if not frontend_only)
    api_endpoints = api_arch.get("endpoints", [])
    if gen_type != "frontend_only":
        if db_entities and not api_endpoints:
            validation_logs.append({"module": "API", "severity": "error", "error": "No API endpoints defined despite having entities."})
    
    # 3. Frontend pages exist (Only if not backend_only or microservice)
    fe_pages = fe_arch.get("pages", [])
    if gen_type not in ("backend_only", "microservice"):
        if not fe_pages and not fe_arch.get("structure"):
            validation_logs.append({"module": "Frontend", "severity": "error", "error": "No frontend pages defined."})
    
    # 4. Auth architecture exists if auth is needed (Only if not frontend_only)
    has_auth_endpoints = any(
        (ep.get("requires_auth") if isinstance(ep, dict) else False)
        for ep in api_endpoints
    )
    if gen_type != "frontend_only":
        if has_auth_endpoints and not auth_arch:
            validation_logs.append({"module": "Auth", "severity": "error", "error": "Endpoints require auth but no auth_architecture defined."})
    
    # 5. Minimum feature scope from requirements
    features = requirements.get("features", []) if isinstance(requirements, dict) else []
    if isinstance(features, list) and len(features) < 5:
        validation_logs.append({
            "module": "Requirements",
            "severity": "warning",
            "error": f"Only {len(features)} features defined — consider at least 5 interconnected features.",
        })

    # 6. Minimum page scope (warning only)
    if gen_type not in ("backend_only", "microservice"):
        if fe_pages and len(fe_pages) < 5:
            validation_logs.append({
                "module": "Frontend",
                "severity": "warning",
                "error": f"Only {len(fe_pages)} frontend pages — production apps typically need 5+ pages.",
            })

    # 7. TRD must exist as generation source of truth (PRD/MRD are not generated in this workflow)
    if not project_doc.get("trd"):
        validation_logs.append({
            "module": "Documents",
            "severity": "warning",
            "error": "TRD is missing. Architecture was generated without a Technical Requirements Document.",
        })

    # 8. Implementation plan existence (warning only)
    if not impl_plan:
        validation_logs.append({"module": "ImplementationPlan", "severity": "warning", "error": "No implementation_plan defined."})
        
    # 9. Backend architecture exists (only if not frontend_only)
    if gen_type != "frontend_only":
        if not be_arch:
            validation_logs.append({"module": "Backend", "severity": "error", "error": "No backend_architecture defined."})
    
    # 10. Theme/styling exists (only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice"):
        if not theme_styling:
            validation_logs.append({"module": "ThemeStyling", "severity": "error", "error": "No theme_styling defined."})
    
    # 11. State management exists (only if not backend_only or microservice)
    if gen_type not in ("backend_only", "microservice"):
        if not state_mgmt:
            validation_logs.append({"module": "StateManagement", "severity": "error", "error": "No state_management defined."})
            
    # 12. Cross-reference: entities vs API endpoints
    if gen_type != "frontend_only" and db_entities and api_endpoints:
        uncovered_domain_entities = []
        internal_entities_acknowledged = []

        for entity in db_entities:
            has_endpoint = any(
                endpoint_matches_entity(ep, entity)
                for ep in api_endpoints
                if isinstance(ep, dict)
            )
            if not has_endpoint:
                if is_internal_system_entity(entity):
                    internal_entities_acknowledged.append(entity)
                else:
                    uncovered_domain_entities.append(entity)

        if internal_entities_acknowledged:
            pass

        if uncovered_domain_entities:
            validation_logs.append({
                "module": "CrossRef-API",
                "severity": "error",
                "error": f"Domain entities without matching API endpoints: {uncovered_domain_entities}. "
                         f"APIAgent must provide CRUD routes for these core business entities.",
            })
    
    # 13. Cross-reference: pages vs routes
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
                "severity": "error",
                "error": f"Frontend pages without routes: {pages_without_routes}. FrontendArchitectureAgent must assign route paths.",
            })
    
    # Save validation logs to project document
    if validation_logs:
        await db.projects.update_one({"_id": project_id}, {"$set": {"validation_logs": validation_logs}})
        
    # If the workflow has previously backtracked and now has zero errors, log success!
    errors = [log for log in validation_logs if log.get("severity") == "error"]
    if not errors and state.get("backtrack_depth", 0) > 0:
        pass
        from app.services.backtrack import BacktrackManager
        manager = BacktrackManager(db, project_id)
        await manager.record_regeneration_success()
    elif not errors:
        pass
    else:
        pass
    
    await broadcast_agent_progress(db, project_id, 73, "Verifier Guardrail Complete.")
    pass
    return {"validation_logs": validation_logs, "hitl_approved": True}

async def backtrack_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    
    validation_logs = state.get("validation_logs", []) or project_doc.get("validation_logs", [])
    
    from app.services.backtrack import ValidationFailureAnalyzer, BacktrackManager
    analyzer_result = ValidationFailureAnalyzer.analyze(validation_logs, "verifier_guardrail", state)
    
    manager = BacktrackManager(db, project_id)
    backtrack_res = await manager.backtrack(
        project_doc=project_doc,
        validation_logs=validation_logs,
        analyzer_result=analyzer_result,
        state=state
    )
    
    if backtrack_res.get("status") == "FAILED_REQUIRES_HUMAN_REVIEW":
        await db.projects.update_one(
            {"_id": project_id},
            {"$set": {
                "status": "FAILED_REQUIRES_HUMAN_REVIEW",
                "step": "Failing: Needs Human Review",
                "error": "Exceeded maximum backtrack depth or retries."
            }}
        )
        from app.services.ws_manager import manager as ws_mgr
        await ws_mgr.broadcast_progress(
            project_id=project_id,
            progress=100,
            step="Needs Human Review — Generation Terminated",
            status="FAILED_REQUIRES_HUMAN_REVIEW"
        )
        raise ValueError("Project generation failed: MAX_BACKTRACK_DEPTH or MAX_AGENT_RETRIES exceeded. Status marked FAILED_REQUIRES_HUMAN_REVIEW.")
        
    # Broadcast backtrack diagnostic event and healing context
    from app.services.ws_manager import manager as ws_mgr
    active_healing = backtrack_res["project_doc"].get("active_healing_context")
    await ws_mgr.broadcast_progress(
        project_id=project_id,
        progress=project_doc.get("progress", 73),
        step=f"Backtrack Depth {backtrack_res['backtrack_depth']}: Re-entering {backtrack_res.get('backtrack_target', 'architecture_design')} for {analyzer_result.get('responsible_agent')}",
        active_healing_context=active_healing,
        backtrack_history=backtrack_res["project_doc"].get("backtrack_history", [])
    )

    return {
        "project_doc": backtrack_res["project_doc"],
        "validation_logs": [],
        "backtrack_depth": backtrack_res["backtrack_depth"],
        "agent_retries": backtrack_res["agent_retries"],
        "active_healing_context": backtrack_res["project_doc"].get("active_healing_context"),
        "backtrack_target": backtrack_res.get("backtrack_target", "architecture_design")
    }

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
        pass
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
        pass
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
    """Multi-phase code synthesis — generates actual source code files from architecture.
    
    Runs AFTER module_assembler (which saves to 'assembled_codebase').
    After synthesis completes, merges assembled_codebase + synthesized output → 'synthesized_codebase'.
    Downstream nodes (dynamic_customization, runtime_verifier, project_export) all read 'synthesized_codebase'.
    """
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    # Guard: skip only if THIS node already ran (check synthesis_validation, not synthesized_codebase)
    # synthesized_codebase is the merged output — checking it would false-positive due to module_assembler
    already_ran = project_doc.get("synthesis_validation", {})
    if already_ran and already_ran.get("total_files", 0) > 15:
        pass
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
        pass
        await db.projects.update_one(
            {"_id": project_id},
            {"$unset": {"synthesis_validation": ""}},
        )
    
    # Merge with assembled_codebase from module_assembler — prefer synthesizer files on path collision
    assembled_codebase = project_doc.get("assembled_codebase") or []
    if assembled_codebase:
        synthesized_paths = {f.get("path") for f in codebase if f.get("path")}
        # Add assembled files that code_synthesizer didn't re-generate
        merged_codebase = list(codebase) + [
            f for f in assembled_codebase if f.get("path") not in synthesized_paths
        ]
        pass
    else:
        merged_codebase = codebase
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "synthesized_codebase": merged_codebase,
            "synthesis_validation": {
                "total_files": len(merged_codebase),
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.get("severity") == "error"]),
                "issues": issues[:50],
            },
        }}
    )
    project_doc["synthesized_codebase"] = merged_codebase
    
    pass
    return {"project_doc": project_doc}

async def validate_and_heal_entity(
    db: Any,
    project_id: str,
    entity_name: str,
    files: List[Dict[str, Any]],
    tech_stack: Any,
    error_correction_agent: Any
) -> List[Dict[str, Any]]:
    """Incremental compiler check & targeted healing loop."""
    pass
    
    if isinstance(tech_stack, dict):
        backend = tech_stack.get("backend", "fastapi")
        frontend = tech_stack.get("frontend", "nextjs")
        database = tech_stack.get("database", "mongodb")
    else:
        backend = str(tech_stack or "fastapi")
        frontend = "nextjs"
        database = "mongodb"
        
    attempts = 0
    max_attempts = 3
    healed_files = list(files)
    
    while attempts < max_attempts:
        errors = []
        for file in healed_files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            # Simple syntax AST parse
            if path.endswith(".py"):
                try:
                    compile(content, path, "exec")
                except SyntaxError as e:
                    errors.append({
                        "file_path": path,
                        "error_log": f"SyntaxError: {str(e)} on line {e.lineno}",
                        "file_content": content
                    })
            # Add lightweight JS/TS bracket checking/regex imports validation
            elif path.endswith((".ts", ".tsx", ".js", ".jsx")):
                if content.count("{") != content.count("}"):
                    errors.append({
                        "file_path": path,
                        "error_log": f"Bracket Mismatch: Open braces count ({content.count('{')}) does not match closing braces count ({content.count('}')}).",
                        "file_content": content
                    })
                elif "import {" in content and "from" not in content:
                    errors.append({
                        "file_path": path,
                        "error_log": "Import Error: Malformed ES6 import syntax (found 'import {' without matching 'from').",
                        "file_content": content
                    })

        if not errors:
            pass
            return healed_files
            
        pass
        attempts += 1
        
        # Heal files surgically
        for err in errors:
            pass
            healed = await error_correction_agent.heal(
                file_path=err["file_path"],
                error_log=err["error_log"],
                file_content=err["file_content"],
                backend=backend,
                frontend=frontend,
                database=database
            )
            # Update content
            corrected_content = healed.get("corrected_code") or healed.get("replacement_code")
            if corrected_content:
                for file_rec in healed_files:
                    if file_rec["path"] == err["file_path"]:
                        file_rec["content"] = corrected_content
                    
    pass
    return healed_files

async def entity_discovery_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    await broadcast_agent_progress(db, project_id, 74, "Running Entity Discovery...")
    
    discovery = EntityDiscoveryAgent()
    res = await discovery.discover(
        requirements=project_doc.get("requirements", {}),
        db_architecture=project_doc.get("db_architecture", {}),
        api_architecture=project_doc.get("api_architecture", {}),
        frontend_architecture=project_doc.get("frontend_architecture", {})
    )
    
    await db.projects.update_one({"_id": project_id}, {"$set": {"entity_discovery": res}})
    project_doc["entity_discovery"] = res
    return {"project_doc": project_doc}

async def entity_generation_planner_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    await broadcast_agent_progress(db, project_id, 75, "Planning Entity Modules Sequence...")
    
    planner = EntityGenerationPlannerAgent()
    res = await planner.plan(project_doc.get("entity_discovery", {}))
    
    await db.projects.update_one({"_id": project_id}, {"$set": {"entity_generation_plan": res}})
    project_doc["entity_generation_plan"] = res
    return {"project_doc": project_doc}

async def entity_generation_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Generates all entity modules batch-by-batch, applying concurrency guards and parallelization."""
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    tech_stack = detect_tech_stack(project_doc)
    backend_tech = tech_stack.get("backend", "fastapi")
    
    plan = project_doc.get("entity_generation_plan", {})
    parallel_groups = plan.get("parallel_groups", [])
    
    await broadcast_agent_progress(db, project_id, 76, "Synthesizing Entity Modules in Parallel...")
    
    backend_gen = BackendEntityGenerator()
    frontend_gen = FrontendEntityGenerator()
    error_correction = ErrorCorrectionAgent()
    
    # Pre-compute shared context for all entity generators
    impl_plan = project_doc.get("implementation_plan", {}) or {}
    sdlc_model = impl_plan.get("recommended_sdlc", "agile") if isinstance(impl_plan, dict) else "agile"
    all_entity_names = [
        e.get("name") or e.get("entity_name", "")
        for e in (project_doc.get("db_architecture", {}) or {}).get("entities", [])
        if isinstance(e, dict)
    ]
    auth_architecture = project_doc.get("auth_architecture") or {}
    realtime_architecture = project_doc.get("realtime_architecture") or {}
    theme_styling = project_doc.get("theme_styling") or {}

    synthesized_modules = {}
    metrics = {}
    
    # Throttle concurrency using semaphores (max 3 entities at once)
    sem = asyncio.Semaphore(3)

    async def process_single_entity(entity: Dict[str, Any]) -> None:
        async with sem:
            name = entity["name"]
            
            # Backend Generation — with full context
            t0 = time.time()
            be_res = await backend_gen.generate(
                entity, [], backend_tech,
                auth_architecture=auth_architecture,
                all_entity_names=all_entity_names,
                sdlc_model=sdlc_model,
                theme_styling=theme_styling,
                realtime_architecture=realtime_architecture,
            )
            be_files = be_res.get("files", [])
            
            # Frontend Generation — with full context
            fe_res = await frontend_gen.generate(
                entity, project_doc.get("theme_styling", {}), project_doc.get("api_architecture", {}),
                auth_architecture=auth_architecture,
                all_entity_names=all_entity_names,
                sdlc_model=sdlc_model,
                theme_styling=theme_styling,
                realtime_architecture=realtime_architecture,
            )
            fe_files = fe_res.get("files", [])
            t1 = time.time()
            
            # Incremental validation and surgical healing
            validated_be = await validate_and_heal_entity(db, project_id, name, be_files, tech_stack, error_correction)
            validated_fe = await validate_and_heal_entity(db, project_id, name, fe_files, tech_stack, error_correction)
            
            synthesized_modules[name] = {
                "backend": validated_be,
                "frontend": validated_fe
            }
            
            metrics[name] = {
                "prompt_tokens": len(json.dumps(entity, default=str)) // 4, # Estimated
                "output_tokens": sum(len(f.get("content", "")) for f in validated_be + validated_fe) // 4,
                "generation_time_seconds": t1 - t0,
                "retry_count": be_res.get("retry_count", 0) + fe_res.get("retry_count", 0)
            }
            
            # Push incremental update to database
            await db.projects.update_one(
                {"_id": project_id},
                {
                    "$set": {
                        f"synthesized_modules.{name}": synthesized_modules[name],
                        f"entity_generation_metrics.{name}": metrics[name]
                    }
                }
            )
            
    # Process sequentially between groups, and concurrently within each group
    discovery_data = project_doc.get("entity_discovery", {})
    entities_list = discovery_data.get("entities", [])
    
    for i, group in enumerate(parallel_groups):
        pass
        entities_in_group = [
            e for e in entities_list if e.get("name") in group
        ]
        tasks = [process_single_entity(e) for e in entities_in_group]
        await asyncio.gather(*tasks)
        
    project_doc["synthesized_modules"] = synthesized_modules
    project_doc["entity_generation_metrics"] = metrics
    return {"project_doc": project_doc}

async def module_assembler_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    await broadcast_agent_progress(db, project_id, 86, "Assembling Compiled Entity Modules...")
    
    assembler = ModuleAssembler(db, project_id)
    assembled_codebase = await assembler.assemble(project_doc, project_doc.get("synthesized_modules", {}))
    
    # Save to 'assembled_codebase' — a staging key separate from 'synthesized_codebase'.
    # This prevents code_synthesis_node from falsely detecting pre-existing files and skipping.
    # code_synthesis_node will merge assembled_codebase + its own output into synthesized_codebase.
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"assembled_codebase": assembled_codebase}}
    )
    
    project_doc["assembled_codebase"] = assembled_codebase
    return {"project_doc": project_doc}

async def dynamic_customization_node(state: AppState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    db = get_db(state, config)
    project_id = state["project_id"]
    project_doc = await db.projects.find_one({"_id": project_id}) or state["project_doc"]
    project_doc = enrich_project_doc_context(project_doc)
    
    await broadcast_agent_progress(db, project_id, 89, "🎨 Applying Dynamic Customization & Branding...")
    
    agent = DynamicCustomizationAgent()
    codebase = project_doc.get("synthesized_codebase", [])
    customized_codebase = await agent.customize_codebase(codebase, project_doc)
    
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {"synthesized_codebase": customized_codebase}}
    )
    
    project_doc["synthesized_codebase"] = customized_codebase
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
    return "research_planning"

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
    """Route after verifier: check if any critical validation error exists to trigger backtrack."""
    validation_logs = state.get("validation_logs", [])
    errors = [log for log in validation_logs if log.get("severity") == "error"]
    if errors:
        pass
        return "backtrack"
    
    if validation_logs:
        pass
    return "code_gen_planner"

def route_after_backtrack(state: AppState) -> str:
    """Scoped backtrack: route to only the failing workspace, not the full pipeline."""
    target = state.get("backtrack_target", "architecture_design")
    allowed = {"architecture_design", "ops_security_workspace"}
    if target not in allowed:
        pass
        return "architecture_design"
    pass
    return target

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
    workflow.add_node("backtrack", backtrack_node)
    
    workflow.add_node("code_gen_planner", code_gen_planner_node)
    workflow.add_node("code_synthesis", code_synthesis_node)
    workflow.add_node("entity_discovery", entity_discovery_node)
    workflow.add_node("entity_generation_planner", entity_generation_planner_node)
    workflow.add_node("entity_generation", entity_generation_node)
    workflow.add_node("module_assembler", module_assembler_node)
    workflow.add_node("dynamic_customization", dynamic_customization_node)
    workflow.add_node("runtime_compilation_verifier", runtime_compilation_verifier_node)
    workflow.add_node("project_export", project_export_node)
    
    # Edges
    workflow.set_entry_point("requirement_analyzer")
    workflow.add_edge("requirement_analyzer", "planner")
    
    workflow.add_edge("planner", "research_planning")
    
    workflow.add_edge("research_planning", "agent_dispatcher")
    
    # Sequential architecture workspaces — downstream agents always see upstream contracts
    workflow.add_edge("agent_dispatcher", "architecture_design")
    workflow.add_edge("architecture_design", "join_workspaces")
    workflow.add_edge("join_workspaces", "ops_security_workspace")
    workflow.add_edge("ops_security_workspace", "verifier_guardrail")
    
    workflow.add_conditional_edges("verifier_guardrail", route_after_verifier, {
        "code_gen_planner": "code_gen_planner",
        "backtrack": "backtrack"
    })
    workflow.add_conditional_edges("backtrack", route_after_backtrack, {
        "architecture_design": "architecture_design",
        "ops_security_workspace": "ops_security_workspace"
    })
    
    # Codegen chain — REDESIGNED for Entity modularity
    workflow.add_edge("code_gen_planner", "entity_discovery")
    workflow.add_edge("entity_discovery", "entity_generation_planner")
    workflow.add_edge("entity_generation_planner", "entity_generation")
    workflow.add_edge("entity_generation", "module_assembler")
    workflow.add_edge("module_assembler", "code_synthesis")
    workflow.add_edge("code_synthesis", "dynamic_customization")
    workflow.add_edge("dynamic_customization", "runtime_compilation_verifier")
    workflow.add_edge("runtime_compilation_verifier", "project_export")
    workflow.add_edge("project_export", END)
    
    # Compile graph with interruption before dispatcher node
    return workflow.compile(
        checkpointer=memory_saver,
        interrupt_before=["agent_dispatcher"]
    )

async def compile_project_workflow(db: Any, project_id: str, project_doc: Dict[str, Any]):
    pass
    app = build_graph()
    config = {"configurable": {"thread_id": project_id, "db": db}}
    
    initial_state = {
        "project_id": project_id,
        "project_doc": project_doc,
        "current_index": 0,
        "feedback": None,
        "retry_count": 0,                                        # Always start fresh
        "latest_output": None,
        "trd": project_doc.get("trd", ""),                       # TRD is the source of truth
        "implementation_plan": project_doc.get("implementation_plan"),
        "hitl_approved": project_doc.get("hitl_approved", False), 
        "hitl_enabled": project_doc.get("hitl_enabled", True),
        "active_dynamic_agents": project_doc.get("active_dynamic_agents", []),
        "validation_logs": [],                                   # Always fresh — no stale logs
        "quality_report": project_doc.get("quality_report"),
        "backtrack_depth": 0,
        "agent_retries": {},
        "active_healing_context": project_doc.get("active_healing_context")
    }
    
    # Run the graph
    state_info = await app.aget_state(config)
    if not state_info.next:
        await app.ainvoke(initial_state, config)
        
    while True:
        state_info = await app.aget_state(config)
        if not state_info.next:
            break
            
        # Check if the user paused the project compilation
        latest_proj = await db.projects.find_one({"_id": project_id})
        if latest_proj and latest_proj.get("status") == "paused":
            pass
            return
            
        if "agent_dispatcher" in state_info.next:
            # Resume execution directly without HITL pause gate
            pass
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
    pass
    
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
            pass
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
            pass
            latest_proj = await db.projects.find_one({"_id": project_id})
            if not latest_proj:
                pass
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
        pass
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

