import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add backend dir to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backtrack import ValidationFailureAnalyzer, BacktrackManager

# Mock Database structures
class MockCollection:
    def __init__(self, initial_data=None):
        self.data = initial_data or {}
        self.update_calls = []

    async def find_one(self, query, *args, **kwargs):
        doc_id = query.get("_id")
        if doc_id:
            doc = self.data.get(doc_id)
            if not doc:
                return None
            for k, v in query.items():
                if k == "_id":
                    continue
                if doc.get(k) != v:
                    return None
            return doc
        for doc in self.data.values():
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    async def update_many(self, query, update, *args, **kwargs):
        self.update_calls.append((query, update))
        set_ops = update.get("$set", {})
        for doc_id, doc in list(self.data.items()):
            for k, v in set_ops.items():
                doc[k] = v

    async def insert_one(self, doc, *args, **kwargs):
        self.data[doc["_id"]] = doc

    async def update_one(self, query, update, *args, **kwargs):
        self.update_calls.append((query, update))
        doc_id = query.get("_id")
        
        # If the document doesn't exist, and this is an upsert, we initialize it
        if doc_id not in self.data and kwargs.get("upsert"):
            self.data[doc_id] = {"_id": doc_id}
            
        if doc_id in self.data:
            doc = self.data[doc_id]
            
            # Handle $unset
            unset_ops = update.get("$unset", {})
            for k in unset_ops.keys():
                doc.pop(k, None)
                
            # Handle $push
            push_ops = update.get("$push", {})
            for k, v in push_ops.items():
                if k not in doc:
                    doc[k] = []
                doc[k].append(v)
                
            # Handle $set
            set_ops = update.get("$set", {})
            for k, v in set_ops.items():
                doc[k] = v
                
            # Handle $inc
            inc_ops = update.get("$inc", {})
            for k, v in inc_ops.items():
                # Nested fields handling
                if "." in k:
                    parts = k.split(".")
                    curr = doc
                    for part in parts[:-1]:
                        if part not in curr:
                            curr[part] = {}
                        curr = curr[part]
                    curr[parts[-1]] = curr.get(parts[-1], 0) + v
                else:
                    doc[k] = doc.get(k, 0) + v
                    
        return MagicMock()

class MockDatabase:
    def __init__(self):
        self.projects = MockCollection()
        self.chats = MockCollection()
        self.artifact_cache = MockCollection()
        self.validation_backtrack_metrics = MockCollection()


def test_validation_failure_analyzer():
    # Test api endpoint failure
    errors_api = [{"error": "Missing GET api endpoint for users", "module": "api", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_api, "verifier_guardrail", {})
    assert res["responsible_agent"] == "APIAgent"
    assert res["failure_type"] == "Missing API Endpoint"

    # Test route / page failure
    errors_route = [{"error": "Route /dashboard not found", "module": "crossref-routes", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_route, "verifier_guardrail", {})
    assert res["responsible_agent"] == "FrontendArchitectureAgent"
    assert res["failure_type"] == "Missing Route"

    # Test database entity failure
    errors_db = [{"error": "Entity Product lacks DB schema design", "module": "database", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_db, "verifier_guardrail", {})
    assert res["responsible_agent"] == "DatabaseArchitectureAgent"
    assert res["failure_type"] == "Missing Entity Mapping"

    # Test auth failure
    errors_auth = [{"error": "Protected path dashboard lacks active policy gates", "module": "auth", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_auth, "verifier_guardrail", {})
    assert res["responsible_agent"] == "AuthArchitectureAgent"
    assert res["failure_type"] == "Missing Auth Rule"

    # Test integration failure
    errors_integ = [{"error": "Integration check failed for external auth", "module": "integration", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_integ, "verifier_guardrail", {})
    assert res["responsible_agent"] == "IntegrationGenerationAgent"
    assert res["failure_type"] == "Broken Integration"

    # Test backend failure
    errors_backend = [{"error": "Backend infrastructure design contract missing key", "module": "backend", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_backend, "verifier_guardrail", {})
    assert res["responsible_agent"] == "BackendArchitectureAgent"
    assert res["failure_type"] == "Missing Backend Architecture"

    # Test theme / styling failure
    errors_theme = [{"error": "Theme is missing palette fields", "module": "themestyling", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_theme, "verifier_guardrail", {})
    assert res["responsible_agent"] == "UIUXArchitectAgent"
    assert res["failure_type"] == "Missing Theme Styling"

    # Test state failure
    errors_state = [{"error": "State reducer function has incorrect dispatch logic", "module": "statemanagement", "severity": "error"}]
    res = ValidationFailureAnalyzer.analyze(errors_state, "verifier_guardrail", {})
    assert res["responsible_agent"] == "StateManagementAgent"
    assert res["failure_type"] == "Missing State Management"


def test_dependency_resolution():
    db = MockDatabase()
    manager = BacktrackManager(db, "proj-123")
    
    # DatabaseArchitectureAgent dependents should include DatabaseModelGenerationAgent, BackendArchitectureAgent, APIAgent, etc.
    deps = manager.get_downstream_dependents("DatabaseArchitectureAgent")
    assert "DatabaseModelGenerationAgent" in deps
    assert "BackendArchitectureAgent" in deps
    assert "APIAgent" in deps
    assert "AuthArchitectureAgent" in deps
    assert "RealtimeArchitectureAgent" in deps
    assert "SecurityArchitectureAgent" in deps
    assert "DevOpsArchitectureAgent" in deps
    assert "TestingArchitectureAgent" in deps
    assert "ValidationArchitectureAgent" in deps
    assert "OptimizationArchitectureAgent" in deps
    
    # APIAgent dependents
    deps_api = manager.get_downstream_dependents("APIAgent")
    assert "AuthArchitectureAgent" in deps_api
    assert "RealtimeArchitectureAgent" in deps_api
    assert "SecurityArchitectureAgent" in deps_api
    assert "TestingArchitectureAgent" in deps_api
    assert "ValidationArchitectureAgent" in deps_api
    assert "OptimizationArchitectureAgent" in deps_api
    assert "DatabaseArchitectureAgent" not in deps_api

    # UIUXArchitectAgent dependents
    deps_uiux = manager.get_downstream_dependents("UIUXArchitectAgent")
    assert "UIComponentGenerationAgent" in deps_uiux
    assert "StateImplementationAgent" in deps_uiux


@pytest.mark.asyncio
async def test_backtrack_execution():
    db = MockDatabase()
    project_id = "test-proj-123"
    project_doc = {
        "_id": project_id,
        "db_architecture": {"entities": ["User"]},
        "database_model_generation": {"models": ["UserModel"]},
        "backend_architecture": {"config": "some_config"},
        "api_architecture": {"endpoints": []},
        "backtrack_history": []
    }
    await db.projects.insert_one(project_doc)

    manager = BacktrackManager(db, project_id)

    # Let's say DatabaseArchitectureAgent fails validation
    analyzer_result = {
        "failure_type": "Missing Entity Mapping",
        "responsible_agent": "DatabaseArchitectureAgent",
        "severity": "error",
        "recommended_action": "Regenerate database architecture"
    }

    validation_logs = [{"error": "Missing User schema mapping", "module": "database", "severity": "error"}]
    state = {
        "backtrack_depth": 0,
        "agent_retries": {}
    }

    res = await manager.backtrack(project_doc, validation_logs, analyzer_result, state)
    
    assert res["status"] == "BACKTRACK_SUCCESS"
    assert res["backtrack_depth"] == 1
    assert res["agent_retries"]["DatabaseArchitectureAgent"] == 1

    # Check MongoDB was updated correctly
    updated_doc = await db.projects.get(project_id) if hasattr(db.projects, "get") else await db.projects.find_one({"_id": project_id})
    assert "db_architecture" not in updated_doc
    assert "database_model_generation" not in updated_doc
    assert "backend_architecture" not in updated_doc
    assert len(updated_doc["backtrack_history"]) == 1
    assert updated_doc["backtrack_history"][0]["responsible_agent"] == "DatabaseArchitectureAgent"
    assert "DatabaseModelGenerationAgent" in updated_doc["backtrack_history"][0]["triggered_agents"]

    # Verify telemetry metrics updated in MongoDB
    metrics = await db.validation_backtrack_metrics.find_one({"_id": "global_metrics"})
    assert metrics["total_regenerations_triggered"] == 1
    assert metrics["total_backtracks_triggered"] == 1
    assert metrics["validation_failure_types"]["Missing Entity Mapping"] == 1
    assert metrics["most_common_failing_agents"]["DatabaseArchitectureAgent"] == 1


@pytest.mark.asyncio
async def test_backtrack_limits_enforced():
    db = MockDatabase()
    project_id = "test-proj-456"
    project_doc = {
        "_id": project_id,
        "db_architecture": {"entities": ["User"]},
        "backtrack_history": []
    }
    await db.projects.insert_one(project_doc)

    manager = BacktrackManager(db, project_id)

    # 1. Test MAX_AGENT_RETRIES limit (3 retries allowed, 4th fails)
    analyzer_result = {
        "failure_type": "Missing Entity Mapping",
        "responsible_agent": "DatabaseArchitectureAgent"
    }
    validation_logs = [{"error": "Error message", "module": "database", "severity": "error"}]
    state = {
        "backtrack_depth": 2,
        "agent_retries": {"DatabaseArchitectureAgent": 3} # Already had 3 retries
    }

    res = await manager.backtrack(project_doc, validation_logs, analyzer_result, state)
    assert res["status"] == "FAILED_REQUIRES_HUMAN_REVIEW"

    metrics = await db.validation_backtrack_metrics.find_one({"_id": "global_metrics"})
    assert metrics["total_human_interventions"] == 1

    # 2. Test MAX_BACKTRACK_DEPTH limit (5 deep allowed, 6th fails)
    state_depth = {
        "backtrack_depth": 5,
        "agent_retries": {"DatabaseArchitectureAgent": 0}
    }
    res_depth = await manager.backtrack(project_doc, validation_logs, analyzer_result, state_depth)
    assert res_depth["status"] == "FAILED_REQUIRES_HUMAN_REVIEW"


@pytest.mark.asyncio
async def test_record_regeneration_success():
    db = MockDatabase()
    manager = BacktrackManager(db, "proj-789")
    
    # Record success
    await manager.record_regeneration_success()
    metrics = await db.validation_backtrack_metrics.find_one({"_id": "global_metrics"})
    assert metrics["total_backtracks_succeeded"] == 1
    assert metrics["total_regenerations_succeeded"] == 1
