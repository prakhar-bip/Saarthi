import pytest
import os
import sys

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dependency_dag import (
    DependencyDAG,
    ARTIFACT_TO_AGENT,
    AGENT_TO_ARTIFACT,
    ARTIFACT_TO_DB_KEY,
)


def test_dag_direct_dependencies():
    """Verify that each artifact declares correct direct prerequisites."""
    assert DependencyDAG.get_direct_dependencies("requirements") == []
    assert DependencyDAG.get_direct_dependencies("trd") == ["requirements"]
    assert DependencyDAG.get_direct_dependencies("database_architecture") == ["execution_plan"]
    assert DependencyDAG.get_direct_dependencies("database_model") == ["database_architecture"]
    assert DependencyDAG.get_direct_dependencies("frontend_architecture") == ["execution_plan"]
    assert DependencyDAG.get_direct_dependencies("theme_styling") == ["execution_plan"]
    assert set(DependencyDAG.get_direct_dependencies("ui_components")) == {"frontend_architecture", "theme_styling"}
    assert set(DependencyDAG.get_direct_dependencies("api_architecture")) == {"backend_architecture", "database_model"}


def test_dag_downstream_dependents():
    """Verify recursive downstream subtree calculation."""
    # DatabaseModelGenerationAgent / database_model failure
    db_model_downstream = DependencyDAG.get_downstream_dependents("database_model")
    assert "api_architecture" in db_model_downstream
    assert "api_implementation" in db_model_downstream
    assert "auth_architecture" in db_model_downstream
    assert "security_architecture" in db_model_downstream
    # Must NOT affect independent frontend or theme branches
    assert "frontend_architecture" not in db_model_downstream
    assert "theme_styling" not in db_model_downstream
    assert "ui_components" not in db_model_downstream
    assert "state_management" not in db_model_downstream

    # FrontendArchitectureAgent / frontend_architecture failure
    frontend_downstream = DependencyDAG.get_downstream_dependents("frontend_architecture")
    assert "ui_components" in frontend_downstream
    assert "state_management" in frontend_downstream
    assert "state_implementation" in frontend_downstream
    # Must NOT affect database, backend, or ops branches
    assert "database_architecture" not in frontend_downstream
    assert "database_model" not in frontend_downstream
    assert "backend_architecture" not in frontend_downstream
    assert "api_architecture" not in frontend_downstream
    assert "devops_architecture" not in frontend_downstream


def test_dag_affected_agents():
    """Verify agent list affected by a failure in DatabaseModelGenerationAgent."""
    affected = DependencyDAG.get_affected_agents("DatabaseModelGenerationAgent")
    assert "DatabaseModelGenerationAgent" in affected
    assert "APIAgent" in affected
    assert "APIImplementationAgent" in affected
    # Unrelated agents must NOT be in affected list
    assert "FrontendArchitectureAgent" not in affected
    assert "UIUXArchitectAgent" not in affected
    assert "UIComponentGenerationAgent" not in affected
    assert "StateManagementAgent" not in affected


def test_dag_dependency_hash():
    """Verify that dependency hash changes when prerequisite artifacts change."""
    doc_v1 = {
        "_id": "proj-1",
        "requirements": {"features": ["Auth", "Dashboard"]},
        "db_architecture": {"entities": ["User", "Session"]},
        "backend_architecture": {"strategy": "FastAPI async"},
        "database_model_generation": {"models": ["UserModel", "SessionModel"]},
    }

    hash1 = DependencyDAG.compute_dependency_hash(doc_v1, "api_architecture")
    assert isinstance(hash1, str)
    assert len(hash1) == 64

    # Identical doc produces identical hash (deterministic)
    hash1_repeat = DependencyDAG.compute_dependency_hash(doc_v1, "api_architecture")
    assert hash1 == hash1_repeat

    # Modifying an upstream dependency changes the hash
    doc_v2 = {
        **doc_v1,
        "database_model_generation": {"models": ["UserModel", "SessionModel", "RoleModel"]}
    }
    hash2 = DependencyDAG.compute_dependency_hash(doc_v2, "api_architecture")
    assert hash1 != hash2

    # Modifying an unrelated artifact does NOT change the hash
    doc_v3 = {
        **doc_v1,
        "theme_styling": {"primary_color": "#00ff00"}
    }
    hash3 = DependencyDAG.compute_dependency_hash(doc_v3, "api_architecture")
    assert hash1 == hash3
