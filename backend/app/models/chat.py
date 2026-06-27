from pydantic import BaseModel
from typing import List, Optional

class MessageSchema(BaseModel):
    id: str
    sender: str  # "user" or "ai"
    text: str
    timestamp: str

class ProjectSuggestionSchema(BaseModel):
    name: str
    idea: str
    features: List[str]
    tech_stack: str
    hitl_enabled: Optional[bool] = False

class ChatSessionCreate(BaseModel):
    category: str
    title: str
    selected_project: Optional[ProjectSuggestionSchema] = None

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    category: str
    messages: List[MessageSchema] = []
    created: str
    user_id: str
    selected_project: Optional[ProjectSuggestionSchema] = None
    is_confirmed: bool = False
    project_id: Optional[str] = None
    is_paused: bool = False

    class Config:
        from_attributes = True
        populate_by_name = True

