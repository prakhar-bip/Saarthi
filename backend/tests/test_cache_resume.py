import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backtrack import BacktrackManager
from tests.test_validation_backtrack import MockDatabase, MockCollection


@pytest.mark.asyncio
async def test_clear_downstream_keys_surgical_wipe():
    db = MockDatabase()
    project_id = "test-proj-cache-resume"

    # Seed project document with full design phase outputs
    project_doc = {
        "_id": project_id,
        # Upstream - should not be cleared when target is APIAgent
        "requirements": {"req_spec": "v1"},
        "requirements_full": {"req_spec": "v1"},
        "requirements_summary": "Requirements summary",
        
        "planning": {"steps": []},
        "planning_full": {"steps": []},

        # Target Agent - APIAgent
        "api_architecture": {"endpoints": ["/users"]},
        "api_architecture_full": {"endpoints": ["/users"]},
        "api_architecture_summary": "API summary",

        # Downstream of APIAgent (AuthArchitectureAgent and RealtimeArchitectureAgent)
        "auth_architecture": {"policies": ["allow_all"]},
        "auth_architecture_full": {"policies": ["allow_all"]},
        
        "realtime_architecture": {"channels": ["updates"]},
        "realtime_architecture_full": {"channels": ["updates"]},

        # Unrelated to APIAgent downstream (UIUXArchitectAgent and state_management)
        "theme_styling": {"primary_color": "#ff0000"},
        "state_management": {"slices": []},

        # Compiled Codebase Keys (must be cleared)
        "synthesized_codebase": [{"path": "backend/app/main.py", "content": "print()"}],
        "codebase": [{"path": "backend/app/main.py", "content": "print()"}],
        "validation_logs": [{"severity": "warning", "error": "deprecated API"}],
        "active_healing_context": {"responsible_agent": "APIAgent"}
    }
    await db.projects.insert_one(project_doc)

    # Invoke the topological clearing method for target APIAgent
    triggered = await BacktrackManager.clear_downstream_keys(db, project_id, "APIAgent")

    # Retrieve updated document
    updated = await db.projects.find_one({"_id": project_id})

    # Assert triggered list includes target and all topological dependents
    assert "APIAgent" in triggered
    assert "AuthArchitectureAgent" in triggered
    assert "RealtimeArchitectureAgent" in triggered
    assert "SecurityArchitectureAgent" in triggered
    assert "TestingArchitectureAgent" in triggered
    assert "ValidationArchitectureAgent" in triggered
    assert "OptimizationArchitectureAgent" in triggered
    # Database architecture is UPSTREAM, should NOT be in triggered
    assert "DatabaseArchitectureAgent" not in triggered

    # Assert cache retention (upstreams/unrelated remain intact)
    assert updated.get("requirements") == {"req_spec": "v1"}
    assert updated.get("requirements_full") == {"req_spec": "v1"}
    assert updated.get("requirements_summary") == "Requirements summary"
    assert updated.get("planning") == {"steps": []}
    assert updated.get("planning_full") == {"steps": []}
    assert updated.get("theme_styling") == {"primary_color": "#ff0000"}
    assert updated.get("state_management") == {"slices": []}

    # Assert target and downstream are cleared completely
    assert "api_architecture" not in updated
    assert "api_architecture_full" not in updated
    assert "api_architecture_summary" not in updated
    assert "auth_architecture" not in updated
    assert "auth_architecture_full" not in updated
    assert "realtime_architecture" not in updated
    assert "realtime_architecture_full" not in updated

    # Assert codebase and healing/compilation fields are cleared
    assert "synthesized_codebase" not in updated
    assert "codebase" not in updated
    assert "validation_logs" not in updated
    assert "active_healing_context" not in updated


@pytest.mark.asyncio
async def test_compile_endpoint_force_run_param():
    from app.api.projects import compile_project_codebase
    from fastapi import HTTPException

    db = MockDatabase()
    project_id = "test-compile-proj"
    current_user = {"id": "test-user-id", "email": "test@sarthi.com"}

    # Initialize mock project document
    project_doc = {
        "_id": project_id,
        "user_id": current_user["id"],
        "name": "Test Project",
        "category": "E-Commerce",
        "status": "idle",
        "api_architecture": {"endpoints": []},
        "codebase": []
    }
    await db.projects.insert_one(project_doc)

    background_tasks = MagicMock()

    # Patch the db helper and execution workflow inside projects api
    with patch("app.api.projects.get_database", return_ok=db) as mock_get_db, \
         patch("app.api.projects.run_project_compilation") as mock_pipeline_task:
        
        mock_get_db.return_value = db

        # 1. Assert invalid agent name throws HTTPException 400
        with pytest.raises(HTTPException) as exc_info:
            await compile_project_codebase(
                project_id=project_id,
                background_tasks=background_tasks,
                force_run_from_agent="InvalidAgentNameSpecifier",
                current_user=current_user
            )
        assert exc_info.value.status_code == 400
        assert "Unknown agent name" in exc_info.value.detail

        # 2. Assert valid force agent clears target keys and starts compilation
        await compile_project_codebase(
            project_id=project_id,
            background_tasks=background_tasks,
            force_run_from_agent="APIAgent",
            current_user=current_user
        )

        # Confirm target keys got unset
        updated = await db.projects.find_one({"_id": project_id})
        assert "api_architecture" not in updated
        assert updated.get("codebase") == []
        assert updated["status"] == "generating"

        # Confirm compilation pipeline was triggered in background
        background_tasks.add_task.assert_called_once()
        assert background_tasks.add_task.call_args[0][0] == mock_pipeline_task


@pytest.mark.asyncio
async def test_pause_project_endpoint():
    from app.api.projects import pause_project_compilation
    from fastapi import HTTPException

    db = MockDatabase()
    project_id = "test-pause-proj"
    current_user = {"id": "test-user-id", "email": "test@sarthi.com"}

    # Initialize mock project document
    project_doc = {
        "_id": project_id,
        "user_id": current_user["id"],
        "name": "Test Project",
        "category": "E-Commerce",
        "status": "generating",
        "progress": 42
    }
    await db.projects.insert_one(project_doc)

    with patch("app.api.projects.get_database", return_value=db) as mock_get_db, \
         patch("app.api.projects.manager.broadcast_progress", new_callable=AsyncMock) as mock_broadcast:
        
        mock_get_db.return_value = db

        # Call pause
        res = await pause_project_compilation(project_id=project_id, current_user=current_user)

        # Check DB state was updated
        updated = await db.projects.find_one({"_id": project_id})
        assert updated["status"] == "paused"
        assert updated["step"] == "Compilation paused by user"
        assert updated["progress"] == 42

        # Check WS broadcast occurred
        mock_broadcast.assert_called_once_with(
            project_id=project_id,
            progress=42,
            step="Compilation paused by user",
            status="paused"
        )

        # Confirm non-generating status throws HTTPException 400
        await db.projects.update_one({"_id": project_id}, {"$set": {"status": "idle"}})
        with pytest.raises(HTTPException) as exc_info:
            await pause_project_compilation(project_id=project_id, current_user=current_user)
        assert exc_info.value.status_code == 400
        assert "cannot be paused" in exc_info.value.detail


@pytest.mark.asyncio
async def test_resume_project_endpoint():
    from app.api.projects import resume_project_compilation
    from fastapi import HTTPException

    db = MockDatabase()
    project_id = "test-resume-proj"
    current_user = {"id": "test-user-id", "email": "test@sarthi.com"}

    # Initialize mock project document
    project_doc = {
        "_id": project_id,
        "user_id": current_user["id"],
        "name": "Test Project",
        "category": "E-Commerce",
        "status": "paused",
        "progress": 42
    }
    await db.projects.insert_one(project_doc)

    background_tasks = MagicMock()

    with patch("app.api.projects.get_database", return_value=db) as mock_get_db, \
         patch("app.api.projects.manager.broadcast_progress", new_callable=AsyncMock) as mock_broadcast, \
         patch("app.services.workflow.resume_project_workflow") as mock_resume_workflow:
        
        mock_get_db.return_value = db

        # Call resume
        res = await resume_project_compilation(
            project_id=project_id,
            background_tasks=background_tasks,
            current_user=current_user
        )

        # Check DB state was updated
        updated = await db.projects.find_one({"_id": project_id})
        assert updated["status"] == "generating"
        assert updated["step"] == "Resuming codebase compilation..."

        # Check WS broadcast occurred
        mock_broadcast.assert_called_once_with(
            project_id=project_id,
            progress=42,
            step="Resuming codebase compilation...",
            status="generating"
        )

        # Check background task was added
        background_tasks.add_task.assert_called_once_with(
            mock_resume_workflow,
            db,
            project_id,
            None
        )

        # Confirm non-paused status throws HTTPException 400
        await db.projects.update_one({"_id": project_id}, {"$set": {"status": "idle"}})
        with pytest.raises(HTTPException) as exc_info:
            await resume_project_compilation(
                project_id=project_id,
                background_tasks=background_tasks,
                current_user=current_user
            )
        assert exc_info.value.status_code == 400
        assert "cannot be resumed" in exc_info.value.detail
