import pytest
import os
import sys

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.artifact_cache import ArtifactCache
from tests.test_validation_backtrack import MockDatabase


@pytest.mark.asyncio
async def test_deterministic_cache_hits_and_invalidation():
    db = MockDatabase()
    project_id = "test-cache-proj"
    agent_name = "DatabaseArchitectureAgent"

    ArtifactCache.clear_all()

    # 1. Compute initial cache key
    key1 = ArtifactCache.compute_cache_key(
        project_id=project_id,
        agent_name=agent_name,
        agent_version="1.0.0",
        input_hash="input_v1",
        dependency_hash="dep_v1",
        prompt_version="1.0",
        model="gemini-2.5-flash"
    )

    # 2. Assert initial cache miss
    cached = await ArtifactCache.get(db, project_id, agent_name, key1)
    assert cached is None

    # 3. Store artifact
    content = {"entities": ["User", "Product"], "status": "success"}
    await ArtifactCache.set(
        db=db,
        project_id=project_id,
        agent_name=agent_name,
        cache_key=key1,
        content=content,
        input_hash="input_v1",
        dependency_hash="dep_v1",
        summary="Database with User and Product entities"
    )

    # 4. Assert cache hit
    cached_hit = await ArtifactCache.get(db, project_id, agent_name, key1)
    assert cached_hit == content

    stats = ArtifactCache.get_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1

    # 5. Dependency change causes different cache key (CACHE MISS)
    key_changed_dep = ArtifactCache.compute_cache_key(
        project_id=project_id,
        agent_name=agent_name,
        agent_version="1.0.0",
        input_hash="input_v1",
        dependency_hash="dep_v2_MODIFIED",
        prompt_version="1.0",
        model="gemini-2.5-flash"
    )
    assert key_changed_dep != key1
    cached_changed = await ArtifactCache.get(db, project_id, agent_name, key_changed_dep)
    assert cached_changed is None

    # 6. Invalidate agent cache
    await ArtifactCache.invalidate(db, project_id, agent_name)
    cached_after_invalidation = await ArtifactCache.get(db, project_id, agent_name, key1)
    assert cached_after_invalidation is None


@pytest.mark.asyncio
async def test_cache_survives_backtracking_for_unaffected_agents():
    """
    Test that invalidating DatabaseModelGenerationAgent downstream
    leaves FrontendArchitectureAgent cache completely intact!
    """
    db = MockDatabase()
    project_id = "test-cache-backtrack-proj"

    ArtifactCache.clear_all()

    # Cache Frontend artifact
    fe_key = ArtifactCache.compute_cache_key(
        project_id=project_id,
        agent_name="FrontendArchitectureAgent",
        input_hash="fe_input",
        dependency_hash="fe_dep"
    )
    fe_content = {"pages": ["/home", "/dashboard"], "status": "success"}
    await ArtifactCache.set(db, project_id, "FrontendArchitectureAgent", fe_key, fe_content)

    # Cache DatabaseModel artifact
    db_model_key = ArtifactCache.compute_cache_key(
        project_id=project_id,
        agent_name="DatabaseModelGenerationAgent",
        input_hash="db_input",
        dependency_hash="db_dep"
    )
    db_model_content = {"models": ["UserModel"], "status": "success"}
    await ArtifactCache.set(db, project_id, "DatabaseModelGenerationAgent", db_model_key, db_model_content)

    # Trigger downstream invalidation for DatabaseModelGenerationAgent
    invalidated = await ArtifactCache.invalidate_downstream(db, project_id, "DatabaseModelGenerationAgent")
    assert "DatabaseModelGenerationAgent" in invalidated
    assert "FrontendArchitectureAgent" not in invalidated

    # DB model cache is invalidated
    db_cached = await ArtifactCache.get(db, project_id, "DatabaseModelGenerationAgent", db_model_key)
    assert db_cached is None

    # Frontend cache SURVIVES backtracking!
    fe_cached = await ArtifactCache.get(db, project_id, "FrontendArchitectureAgent", fe_key)
    assert fe_cached == fe_content
