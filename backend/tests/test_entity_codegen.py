import pytest
import os
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Add backend dir to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.workflow import (
    AppState,
    validate_and_heal_entity,
    entity_discovery_node,
    entity_generation_planner_node,
    entity_generation_node,
    module_assembler_node,
)
from app.agents.entity_discovery import EntityDiscoveryAgent
from app.agents.entity_generation_planner import EntityGenerationPlannerAgent
from app.agents.entity_generators import BackendEntityGenerator, FrontendEntityGenerator
from app.agents.error_correction import ErrorCorrectionAgent

# Mock Database structures
class MockCollection:
    def __init__(self, initial_data=None):
        self.data = initial_data or {}
        self.update_calls = []

    async def find_one(self, query, *args, **kwargs):
        return self.data.get(query.get("_id"))

    async def insert_one(self, doc, *args, **kwargs):
        self.data[doc["_id"]] = doc

    async def update_one(self, query, update, *args, **kwargs):
        self.update_calls.append((query, update))
        doc_id = query.get("_id")
        
        if doc_id not in self.data and kwargs.get("upsert"):
            self.data[doc_id] = {"_id": doc_id}
            
        if doc_id in self.data:
            doc = self.data[doc_id]
            
            # Handle $unset
            unset_ops = update.get("$unset", {})
            for k in unset_ops.keys():
                doc.pop(k, None)
                
            # Handle $set
            set_ops = update.get("$set", {})
            for k, v in set_ops.items():
                # Handle nested fields (e.g. "synthesized_modules.User")
                if "." in k:
                    parts = k.split(".")
                    curr = doc
                    for part in parts[:-1]:
                        if part not in curr:
                            curr[part] = {}
                        curr = curr[part]
                    curr[parts[-1]] = v
                else:
                    doc[k] = v
                    
        return MagicMock()

class MockDatabase:
    def __init__(self):
        self.projects = MockCollection()


@pytest.mark.asyncio
async def test_validate_and_heal_entity_success():
    # Correct python code
    files = [
        {
            "name": "user.py",
            "path": "backend/app/models/user.py",
            "content": "def test():\n    return 'hello'"
        }
    ]
    
    mock_db = MockDatabase()
    mock_error_correction = AsyncMock()
    
    res = await validate_and_heal_entity(
        db=mock_db,
        project_id="p123",
        entity_name="User",
        files=files,
        tech_stack="fastapi",
        error_correction_agent=mock_error_correction
    )
    
    # Python code parses cleanly, so error correction should NOT be called
    assert res == files
    mock_error_correction.heal.assert_not_called()


@pytest.mark.asyncio
async def test_validate_and_heal_entity_with_errors():
    # Code with python SyntaxError (missing colon)
    bad_files = [
        {
            "name": "user.py",
            "path": "backend/app/models/user.py",
            "content": "def test()\n    return 'hello'"
        }
    ]
    
    mock_db = MockDatabase()
    mock_error_correction = AsyncMock()
    
    # Mock successful healing
    mock_error_correction.heal.return_value = {
        "corrected_code": "def test():\n    return 'hello'"
    }
    
    res = await validate_and_heal_entity(
        db=mock_db,
        project_id="p123",
        entity_name="User",
        files=bad_files,
        tech_stack="fastapi",
        error_correction_agent=mock_error_correction
    )
    
    # Healing should be invoked and fix the files
    mock_error_correction.heal.assert_called_once()
    assert res[0]["content"] == "def test():\n    return 'hello'"


@pytest.mark.asyncio
async def test_validate_and_heal_entity_malformed_import():
    # TSX Code with bad import format
    bad_files = [
        {
            "name": "page.tsx",
            "path": "frontend/src/app/dashboard/users/page.tsx",
            "content": "import { useState } \n export default function Page() { return <div /> }"
        }
    ]
    
    mock_db = MockDatabase()
    mock_error_correction = AsyncMock()
    
    # Mock successful healing
    mock_error_correction.heal.return_value = {
        "corrected_code": "import { useState } from 'react';\n export default function Page() { return <div /> }"
    }
    
    res = await validate_and_heal_entity(
        db=mock_db,
        project_id="p123",
        entity_name="User",
        files=bad_files,
        tech_stack="fastapi",
        error_correction_agent=mock_error_correction
    )
    
    # Healing should be invoked and fix the files
    mock_error_correction.heal.assert_called_once()
    assert "from 'react'" in res[0]["content"]


@pytest.mark.asyncio
@patch("app.services.workflow.get_db")
@patch("app.services.workflow.broadcast_agent_progress")
@patch.object(EntityDiscoveryAgent, "discover")
async def test_entity_discovery_node(mock_discover, mock_broadcast, mock_get_db):
    mock_db = MockDatabase()
    mock_db.projects.data["p123"] = {
        "_id": "p123",
        "requirements": {"app": "todo"},
        "db_architecture": {"schema": "todo"},
        "api_architecture": {"routes": "todo"},
        "frontend_architecture": {"pages": "todo"}
    }
    mock_get_db.return_value = mock_db
    mock_broadcast.return_value = None
    
    discovery_result = {
        "entities": [
            {"name": "User", "fields": []}
        ]
    }
    mock_discover.return_value = discovery_result
    
    state = {
        "project_id": "p123",
        "project_doc": mock_db.projects.data["p123"]
    }
    
    result = await entity_discovery_node(state)
    
    # Verify entity discovery updates the project doc
    assert "entity_discovery" in result["project_doc"]
    assert result["project_doc"]["entity_discovery"] == discovery_result
    assert mock_db.projects.data["p123"]["entity_discovery"] == discovery_result


@pytest.mark.asyncio
@patch("app.services.workflow.get_db")
@patch("app.services.workflow.broadcast_agent_progress")
@patch.object(EntityGenerationPlannerAgent, "plan")
async def test_entity_generation_planner_node(mock_plan, mock_broadcast, mock_get_db):
    mock_db = MockDatabase()
    mock_db.projects.data["p123"] = {
        "_id": "p123",
        "entity_discovery": {"entities": [{"name": "User"}]}
    }
    mock_get_db.return_value = mock_db
    mock_broadcast.return_value = None
    
    plan_result = {
        "generation_order": ["User"],
        "parallel_groups": [["User"]],
        "blocking_dependencies": []
    }
    mock_plan.return_value = plan_result
    
    state = {
        "project_id": "p123",
        "project_doc": mock_db.projects.data["p123"]
    }
    
    result = await entity_generation_planner_node(state)
    
    assert "entity_generation_plan" in result["project_doc"]
    assert result["project_doc"]["entity_generation_plan"] == plan_result
    assert mock_db.projects.data["p123"]["entity_generation_plan"] == plan_result


@pytest.mark.asyncio
@patch("app.services.workflow.get_db")
@patch("app.services.workflow.broadcast_agent_progress")
@patch.object(BackendEntityGenerator, "generate")
@patch.object(FrontendEntityGenerator, "generate")
@patch.object(ErrorCorrectionAgent, "heal")
async def test_entity_generation_node(mock_heal, mock_fe_generate, mock_be_generate, mock_broadcast, mock_get_db):
    mock_db = MockDatabase()
    mock_db.projects.data["p123"] = {
        "_id": "p123",
        "entity_discovery": {
            "entities": [{"name": "User"}]
        },
        "entity_generation_plan": {
            "generation_order": ["User"],
            "parallel_groups": [["User"]],
            "blocking_dependencies": []
        }
    }
    mock_get_db.return_value = mock_db
    mock_broadcast.return_value = None
    
    # Mock Generator outputs
    mock_be_generate.return_value = {
        "files": [{"name": "user.py", "path": "backend/app/models/user.py", "content": "class User: pass"}]
    }
    mock_fe_generate.return_value = {
        "files": [{"name": "page.tsx", "path": "frontend/src/app/dashboard/users/page.tsx", "content": "export default function Page() { return null; }"}]
    }
    
    state = {
        "project_id": "p123",
        "project_doc": mock_db.projects.data["p123"]
    }
    
    result = await entity_generation_node(state)
    
    assert "synthesized_modules" in result["project_doc"]
    assert "User" in result["project_doc"]["synthesized_modules"]
    user_module = result["project_doc"]["synthesized_modules"]["User"]
    assert len(user_module["backend"]) == 1
    assert len(user_module["frontend"]) == 1
    assert user_module["backend"][0]["name"] == "user.py"
    assert user_module["frontend"][0]["name"] == "page.tsx"


@pytest.mark.asyncio
@patch("app.services.workflow.get_db")
@patch("app.services.workflow.broadcast_agent_progress")
async def test_module_assembler_node(mock_broadcast, mock_get_db):
    mock_db = MockDatabase()
    mock_db.projects.data["p123"] = {
        "_id": "p123",
        "synthesized_modules": {
            "User": {
                "backend": [{"name": "user.py", "path": "backend/app/models/user.py", "content": "class User: pass"}],
                "frontend": [{"name": "page.tsx", "path": "frontend/src/app/dashboard/users/page.tsx", "content": "export default function Page() { return null; }"}]
            }
        }
    }
    mock_get_db.return_value = mock_db
    mock_broadcast.return_value = None
    
    state = {
        "project_id": "p123",
        "project_doc": mock_db.projects.data["p123"]
    }
    
    result = await module_assembler_node(state)
    
    assert "assembled_codebase" in result["project_doc"]
    codebase = result["project_doc"]["assembled_codebase"]
    # Should contain user.py, page.tsx, main.py (assembled router), and index.ts (assembled store)
    paths = [file["path"] for file in codebase]
    assert "backend/app/models/user.py" in paths
    assert "frontend/src/app/dashboard/users/page.tsx" in paths
    assert "backend/app/main.py" in paths
    assert "frontend/src/stores/index.ts" in paths
