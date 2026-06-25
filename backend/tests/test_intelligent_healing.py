import pytest
import os
import sys
from unittest.mock import MagicMock

# Add backend dir to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backtrack import ValidationFailureAnalyzer, BacktrackManager
from app.agents.context import generate_agent_prompt

# Reuse Mock Database structures for simple unit verification
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
        self.validation_backtrack_metrics = MockCollection()


@pytest.mark.asyncio
async def test_backtrack_captures_active_healing_context():
    db = MockDatabase()
    project_id = "test-project-123"
    
    # Initialize mock project document
    project_doc = {
        "_id": project_id,
        "status": "GENERATING",
        "requirements": {"app_name": "TestApp"},
        "db_architecture": {"entities": []}
    }
    db.projects.data[project_id] = project_doc
    
    # Mock a validation error targeting the database architecture
    validation_logs = [
        {
            "module": "database",
            "severity": "error",
            "error": "Entity User lacks a primary key mapping in DB architecture"
        }
    ]
    
    # Run the ValidationFailureAnalyzer
    analyzer_result = ValidationFailureAnalyzer.analyze(validation_logs, "verifier_guardrail", {})
    assert analyzer_result["responsible_agent"] == "DatabaseArchitectureAgent"
    
    # Trigger backtracking
    manager = BacktrackManager(db, project_id)
    backtrack_res = await manager.backtrack(
        project_doc=project_doc,
        validation_logs=validation_logs,
        analyzer_result=analyzer_result,
        state={"backtrack_depth": 0, "agent_retries": {}}
    )
    
    assert backtrack_res["status"] == "BACKTRACK_SUCCESS"
    
    # Verify active_healing_context was set in the fresh project document
    clean_doc = backtrack_res["project_doc"]
    assert "active_healing_context" in clean_doc
    
    healing_ctx = clean_doc["active_healing_context"]
    assert healing_ctx["responsible_agent"] == "DatabaseArchitectureAgent"
    assert "Entity User lacks a primary key mapping" in healing_ctx["error_msg"]
    assert healing_ctx["failure_type"] == "Missing Entity Mapping"
    assert "DatabaseArchitectureAgent" in healing_ctx["triggered_agents"]
    
    # Verify it was pushed to healing_history
    assert "healing_history" in clean_doc
    assert len(clean_doc["healing_history"]) == 1
    assert clean_doc["healing_history"][0]["responsible_agent"] == "DatabaseArchitectureAgent"


def test_generate_agent_prompt_self_healing_injection():
    # 1. Test Self-Healing Prompt Injection (Responsible Agent)
    active_healing_context = {
        "responsible_agent": "DatabaseArchitectureAgent",
        "error_msg": "Entity User lacks a primary key mapping in DB architecture",
        "failure_type": "Missing Entity Mapping",
        "recommended_action": "Regenerate database architecture and define the primary schema entities.",
        "triggered_agents": ["DatabaseArchitectureAgent", "APIAgent", "BackendArchitectureAgent"],
        "timestamp": "2026-06-24"
    }
    
    state = {
        "requirements": {"app_name": "TestApp"},
        "active_healing_context": active_healing_context,
        "generation_type": "full_stack"
    }
    
    # Current agent is the responsible agent
    prompt_self_healing = generate_agent_prompt("DatabaseArchitectureAgent", state)
    
    assert "CRITICAL: SELF-HEALING & ERROR RESOLUTION REQUIRED" in prompt_self_healing
    assert "Entity User lacks a primary key mapping" in prompt_self_healing
    assert "Regenerate database architecture" in prompt_self_healing
    assert "UPSTREAM CONTRACT ADAPTATION" not in prompt_self_healing


def test_generate_agent_prompt_upstream_adaptation_injection():
    # 2. Test Upstream Contract Adaptation Prompt Injection (Downstream Agent)
    active_healing_context = {
        "responsible_agent": "DatabaseArchitectureAgent",
        "error_msg": "Entity User lacks a primary key mapping in DB architecture",
        "failure_type": "Missing Entity Mapping",
        "recommended_action": "Regenerate database architecture and define the primary schema entities.",
        "triggered_agents": ["DatabaseArchitectureAgent", "APIAgent", "BackendArchitectureAgent"],
        "timestamp": "2026-06-24"
    }
    
    state = {
        "requirements": {"app_name": "TestApp"},
        "active_healing_context": active_healing_context,
        "generation_type": "full_stack"
    }
    
    # Current agent is a downstream dependent being re-triggered
    prompt_adaptation = generate_agent_prompt("APIAgent", state)
    
    assert "IMPORTANT: UPSTREAM CONTRACT ADAPTATION & MODULATION INSTRUCTIONS" in prompt_adaptation
    assert "DatabaseArchitectureAgent" in prompt_adaptation
    assert "Entity User lacks a primary key mapping" in prompt_adaptation
    assert "CRITICAL: SELF-HEALING" not in prompt_adaptation


def test_generate_agent_prompt_no_injection():
    # 3. Test No Prompt Injection for agents not involved
    active_healing_context = {
        "responsible_agent": "DatabaseArchitectureAgent",
        "error_msg": "Entity User lacks a primary key mapping in DB architecture",
        "failure_type": "Missing Entity Mapping",
        "recommended_action": "Regenerate database architecture and define the primary schema entities.",
        "triggered_agents": ["DatabaseArchitectureAgent", "APIAgent", "BackendArchitectureAgent"],
        "timestamp": "2026-06-24"
    }
    
    state = {
        "requirements": {"app_name": "TestApp"},
        "active_healing_context": active_healing_context,
        "generation_type": "full_stack"
    }
    
    # DevOpsArchitectureAgent is not in triggered_agents or responsible_agent
    prompt_unaffected = generate_agent_prompt("DevOpsArchitectureAgent", state)
    
    assert "CRITICAL: SELF-HEALING" not in prompt_unaffected
    assert "IMPORTANT: UPSTREAM CONTRACT ADAPTATION" not in prompt_unaffected


@pytest.mark.asyncio
async def test_record_regeneration_success_unsets_healing_context():
    db = MockDatabase()
    project_id = "test-project-123"
    
    # Initialize mock project document WITH active healing context
    project_doc = {
        "_id": project_id,
        "status": "GENERATING",
        "active_healing_context": {
            "responsible_agent": "DatabaseArchitectureAgent",
            "error_msg": "Fixed primary key"
        }
    }
    db.projects.data[project_id] = project_doc
    
    manager = BacktrackManager(db, project_id)
    
    # Success is recorded (zero validation errors)
    await manager.record_regeneration_success(validation_errors=None)
    
    # Verify active_healing_context was unset from MongoDB
    updated_doc = db.projects.data[project_id]
    assert "active_healing_context" not in updated_doc
