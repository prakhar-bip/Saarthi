from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CodeFileSchema(BaseModel):
    name: str
    path: str
    content: str
    language: str

class ThemePaletteSchema(BaseModel):
    primary: str
    secondary: str
    background: str
    card_bg: str
    text: str
    border: str
    is_dark: bool

class BlueprintSchema(BaseModel):
    name: str
    idea: str
    features: List[str]
    tech_stack: str

class ProjectCreate(BaseModel):
    chat_id: str
    name: str
    category: str
    theme: Optional[str] = None
    blueprint: Optional[BlueprintSchema] = None
    theme_palette: Optional[ThemePaletteSchema] = None
    hitl_enabled: Optional[bool] = True

class ProjectResponse(BaseModel):
    id: str
    name: str
    category: str
    status: str  # "idle" | "generating" | "completed" | "failed" | "waiting_approval"
    progress: int
    step: str
    summary: str
    codebase: List[CodeFileSchema] = []
    created: str
    user_id: str
    chat_id: str
    theme: Optional[str] = None
    blueprint: Optional[BlueprintSchema] = None
    theme_palette: Optional[ThemePaletteSchema] = None
    requirements: Optional[Dict[str, Any]] = None
    planning: Optional[Dict[str, Any]] = None
    db_architecture: Optional[Dict[str, Any]] = None
    backend_architecture: Optional[Dict[str, Any]] = None
    api_architecture: Optional[Dict[str, Any]] = None
    frontend_architecture: Optional[Dict[str, Any]] = None
    theme_styling: Optional[Dict[str, Any]] = None
    auth_architecture: Optional[Dict[str, Any]] = None
    realtime_architecture: Optional[Dict[str, Any]] = None
    state_management: Optional[Dict[str, Any]] = None
    devops_architecture: Optional[Dict[str, Any]] = None
    security_architecture: Optional[Dict[str, Any]] = None
    testing_architecture: Optional[Dict[str, Any]] = None
    validation_architecture: Optional[Dict[str, Any]] = None
    optimization_architecture: Optional[Dict[str, Any]] = None
    code_generation_plan: Optional[Dict[str, Any]] = None
    database_model_generation: Optional[Dict[str, Any]] = None
    backend_code_generation: Optional[Dict[str, Any]] = None
    api_implementation: Optional[Dict[str, Any]] = None
    frontend_code_generation: Optional[Dict[str, Any]] = None
    ui_component_generation: Optional[Dict[str, Any]] = None
    state_implementation: Optional[Dict[str, Any]] = None
    integration_generation: Optional[Dict[str, Any]] = None
    build_compilation: Optional[Dict[str, Any]] = None
    error_correction: Optional[Dict[str, Any]] = None
    project_export: Optional[Dict[str, Any]] = None
    agent_context: Optional[Dict[str, Any]] = None
    hackathon_metadata: Optional[Dict[str, Any]] = None
    mcp_evidence: Optional[Dict[str, Any]] = None
    prd: Optional[str] = None
    mrd: Optional[str] = None
    trd: Optional[str] = None
    
    # Sarthi 2.0 dynamic fields
    hitl_enabled: Optional[bool] = True
    hitl_approved: Optional[bool] = False
    implementation_plan: Optional[Dict[str, Any]] = None
    validation_logs: Optional[List[Dict[str, Any]]] = []

    class Config:
        from_attributes = True
        populate_by_name = True
