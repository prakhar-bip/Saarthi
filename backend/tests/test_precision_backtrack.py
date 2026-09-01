import pytest
import os
import sys

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backtrack import ValidationFailureAnalyzer, BacktrackManager
from tests.test_validation_backtrack import MockDatabase


@pytest.mark.asyncio
async def test_precision_backtrack_database_model_failure():
    """
    Test that an error in DatabaseModelGenerationAgent invalidates ONLY
    downstream dependents (APIAgent, APIImplementationAgent, etc.) and leaves
    Frontend, UIUX, Theme, and independent modules completely intact!
    """
    db = MockDatabase()
    project_id = "test-precision-proj-1"

    project_doc = {
        "_id": project_id,
        "requirements": {"name": "FinanceApp"},
        "planning": {"strategy": "MVC"},
        "db_architecture": {"entities": ["Account", "Transaction"]},
        "database_model_generation": {"models": ["AccountModel"]},
        "backend_architecture": {"framework": "FastAPI"},
        "api_architecture": {"endpoints": ["/api/v1/accounts"]},
        "api_implementation": {"code": "..."},
        "frontend_architecture": {"pages": ["/dashboard", "/login"]},
        "theme_styling": {"primary": "#336699"},
        "ui_component_generation": {"components": ["AccountCard"]},
        "state_management": {"stores": ["useAccountStore"]},
        "state_implementation": {"code": "..."},
        "backtrack_history": []
    }
    await db.projects.insert_one(project_doc)

    manager = BacktrackManager(db, project_id)

    analyzer_result = {
        "failure_type": "Database Model Error",
        "responsible_agent": "DatabaseModelGenerationAgent",
        "severity": "error",
        "recommended_action": "Regenerate database models matching entities",
        "error_id": "err-db-model-42"
    }

    validation_logs = [{"error": "AccountModel is missing foreign key relation to User", "module": "databasemodel", "severity": "error"}]
    state = {
        "backtrack_depth": 0,
        "agent_retries": {}
    }

    res = await manager.backtrack(project_doc, validation_logs, analyzer_result, state)

    assert res["status"] == "BACKTRACK_SUCCESS"
    assert res["backtrack_depth"] == 1

    updated = await db.projects.find_one({"_id": project_id})

    # Responsible agent and its downstream dependents are wiped
    assert "database_model_generation" not in updated
    assert "api_architecture" not in updated
    assert "api_implementation" not in updated

    # Upstream and independent branches MUST be preserved!
    assert "requirements" in updated
    assert "planning" in updated
    assert "db_architecture" in updated
    assert "frontend_architecture" in updated
    assert "theme_styling" in updated
    assert "ui_component_generation" in updated
    assert "state_management" in updated
    assert "state_implementation" in updated


@pytest.mark.asyncio
async def test_precision_backtrack_frontend_failure():
    """
    Test that an error in FrontendArchitectureAgent invalidates ONLY
    UI/State downstream dependents and leaves Database/Backend/APIs untouched!
    """
    db = MockDatabase()
    project_id = "test-precision-proj-2"

    project_doc = {
        "_id": project_id,
        "requirements": {"name": "FinanceApp"},
        "planning": {"strategy": "MVC"},
        "db_architecture": {"entities": ["Account"]},
        "database_model_generation": {"models": ["AccountModel"]},
        "backend_architecture": {"framework": "FastAPI"},
        "api_architecture": {"endpoints": ["/api/v1/accounts"]},
        "frontend_architecture": {"pages": ["/dashboard"]},
        "theme_styling": {"primary": "#336699"},
        "ui_component_generation": {"components": ["AccountCard"]},
        "state_management": {"stores": ["useAccountStore"]},
        "state_implementation": {"code": "..."},
        "backtrack_history": []
    }
    await db.projects.insert_one(project_doc)

    manager = BacktrackManager(db, project_id)

    analyzer_result = {
        "failure_type": "Missing Route",
        "responsible_agent": "FrontendArchitectureAgent",
        "severity": "error",
        "recommended_action": "Regenerate frontend architecture",
        "error_id": "err-fe-route-99"
    }

    validation_logs = [{"error": "Route /analytics missing in frontend pages", "module": "frontend", "severity": "error"}]
    state = {"backtrack_depth": 0, "agent_retries": {}}

    res = await manager.backtrack(project_doc, validation_logs, analyzer_result, state)
    assert res["status"] == "BACKTRACK_SUCCESS"

    updated = await db.projects.find_one({"_id": project_id})

    # Frontend and downstream state/components wiped
    assert "frontend_architecture" not in updated
    assert "ui_component_generation" not in updated
    assert "state_management" not in updated
    assert "state_implementation" not in updated

    # Database and backend branches remain completely untouched
    assert "db_architecture" in updated
    assert "database_model_generation" in updated
    assert "backend_architecture" in updated
    assert "api_architecture" in updated
