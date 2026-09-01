import pytest
from app.services.suggestion_cache import SuggestionCache
from app.services.agent_failure_inspector import AgentFailureInspector
from app.agents.verifier_agent import VerifierAgent

@pytest.mark.asyncio
async def test_suggestion_cache_lifecycle():
    SuggestionCache.clear_all()
    assert SuggestionCache.get("health") is None
    
    # Store items
    sample = [{"title": "Fitness Tracker", "category": "health"}]
    SuggestionCache.set("health", sample)
    
    # Cache hit
    hit = SuggestionCache.get("health")
    assert hit == sample
    stats = SuggestionCache.stats()
    assert stats["hits"] == 1
    assert stats["cached_entries"] == 1
    
    # Invalidate
    SuggestionCache.invalidate("health")
    assert SuggestionCache.get("health") is None

@pytest.mark.asyncio
async def test_verifier_agent_incremental_validation():
    verifier = VerifierAgent()
    doc = {"generation_type": "full_stack"}
    
    # 1. DatabaseArchitectureAgent missing entities
    ok, fb, logs = await verifier.verify_incremental("DatabaseArchitectureAgent", {"entities": []}, doc)
    assert not ok
    assert any("No entities defined" in l["error"] for l in logs)

    # 2. DatabaseArchitectureAgent valid entities
    valid_db = {"entities": [{"entity_name": "User", "fields": ["id", "email"]}]}
    ok, fb, logs = await verifier.verify_incremental("DatabaseArchitectureAgent", valid_db, doc)
    assert ok
    assert len(logs) == 0

    # 3. APIAgent cross-reference check for missing domain entities
    doc_with_db = {"generation_type": "full_stack", "db_architecture": valid_db}
    # No endpoints defined
    ok, fb, logs = await verifier.verify_incremental("APIAgent", {"endpoints": []}, doc_with_db)
    assert not ok
    assert any("No API endpoints defined" in l["error"] for l in logs)

    # Endpoints defined for User
    valid_api = {"endpoints": [{"path": "/api/users", "method": "GET", "resource": "user"}]}
    ok, fb, logs = await verifier.verify_incremental("APIAgent", valid_api, doc_with_db)
    assert ok
    assert len(logs) == 0

@pytest.mark.asyncio
async def test_agent_failure_inspector_diagnosis():
    analyzer_result = {
        "responsible_agent": "APIAgent",
        "failure_type": "Missing API Endpoint",
        "error_id": "err_api_99",
        "recommended_action": "Generate CRUD endpoints for entities."
    }
    validation_logs = [{
        "module": "API",
        "severity": "error",
        "error": "No API endpoints defined despite having entities."
    }]
    
    # Inspect empty API output
    report = await AgentFailureInspector.inspect(
        db=None,
        project_id="proj_test_123",
        project_doc={"api_architecture": {"endpoints": []}},
        responsible_agent="APIAgent",
        validation_logs=validation_logs,
        analyzer_result=analyzer_result,
        backtrack_depth=1
    )
    
    assert report["agent_name"] == "APIAgent"
    assert report["backtrack_depth"] == 1
    assert report["error_id"] == "err_api_99"
    assert "api_strategy" in report["missing_keys"]
    assert "endpoints" in report["empty_keys"]
    assert "Your output is missing these required keys" in report["healing_hint"]
    assert "Generate CRUD endpoints" in report["healing_hint"]
