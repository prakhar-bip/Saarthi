from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json


class Artifact(BaseModel):
    """
    Standard structured artifact produced by Sarthi agents.
    Every major agent produces a well-defined artifact conforming to this model.
    """
    artifact_id: str = Field(..., description="Unique identifier for the artifact instance")
    artifact_type: str = Field(..., description="Canonical artifact type name, e.g. 'database_architecture'")
    project_id: str = Field(..., description="Parent project ID")
    version: int = Field(default=1, description="Version number of this artifact")
    input_hash: str = Field(..., description="Hash of the direct inputs to the producing agent")
    dependency_hash: str = Field(..., description="Combined hash of all upstream prerequisite artifacts")
    agent_version: str = Field(default="1.0.0", description="Version of the producing agent")
    status: str = Field(default="valid", description="'valid', 'invalidated', or 'failed'")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content: Dict[str, Any] = Field(default_factory=dict, description="Compact machine-readable structured JSON payload")
    summary: str = Field(default="", description="Concise human-readable conceptual summary")
    key_decisions: List[str] = Field(default_factory=list, description="Key architecture decisions made")
    dependencies: List[str] = Field(default_factory=list, description="Artifact types this artifact depends on")
    risks: List[str] = Field(default_factory=list, description="Identified risks and mitigation notes")

    def compute_cache_key(self, prompt_version: str = "1.0", model: str = "", configuration: str = "") -> str:
        """Calculates a deterministic cache key for artifact-level caching."""
        key_raw = f"{self.project_id}:{self.artifact_type}:{self.agent_version}:{self.input_hash}:{self.dependency_hash}:{prompt_version}:{model}:{configuration}"
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

    @classmethod
    def compute_input_hash(cls, data: Any) -> str:
        """Computes deterministic hash of agent inputs."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
