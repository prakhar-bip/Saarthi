import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.api_agent import APIAgent
from app.agents.verifier_agent import VerifierAgent
from app.services.api_contracts import ensure_entity_crud_endpoints, endpoint_matches_entity
from app.services.artifact_cache import ArtifactCache
from app.services.contract_auditor import ContractAuditor
from app.services.dependency_dag import AGENT_TO_ARTIFACT, DependencyDAG
from app.services.workflow import get_agent_db_key, run_single_agent
from tests.test_validation_backtrack import MockDatabase


def _blog_db_architecture():
    return {
        "entities": [
            {
                "entity_name": "PostCategory",
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "slug", "type": "string", "required": True},
                ],
            },
            {
                "entity_name": "Post",
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "title", "type": "string", "required": True},
                    {"name": "content", "type": "string", "required": True},
                ],
            },
            {
                "entity_name": "Comment",
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "body", "type": "string", "required": True},
                ],
            },
            {"entity_name": "RefreshToken", "fields": [{"name": "token", "type": "string"}]},
        ]
    }


def test_entity_route_matching_accepts_kebab_case_plural_without_false_parent_match():
    category_endpoint = {"path": "/api/v1/post-categories/{id}", "method": "GET"}

    assert endpoint_matches_entity(category_endpoint, "PostCategory")
    assert not endpoint_matches_entity(category_endpoint, "Post")


def test_api_contract_reconciliation_adds_missing_crud_for_domain_entities():
    api_architecture = {
        "status": "success",
        "api_strategy": {"base_path": "/api/v1"},
        "endpoints": [
            {"group_name": "Authentication API", "path": "/api/v1/auth/login", "method": "POST"}
        ],
        "future_agent_context": {"important_notes_for_backend_agents": []},
    }

    reconciled = ensure_entity_crud_endpoints(api_architecture, _blog_db_architecture(), True)
    endpoints = reconciled["endpoints"]

    for resource in ("post-categories", "posts", "comments"):
        route_methods = {
            (endpoint["method"], endpoint["path"])
            for endpoint in endpoints
            if endpoint.get("path", "").startswith(f"/api/v1/{resource}")
        }
        assert ("GET", f"/api/v1/{resource}") in route_methods
        assert ("POST", f"/api/v1/{resource}") in route_methods
        assert ("GET", f"/api/v1/{resource}/{{id}}") in route_methods
        assert ("PUT", f"/api/v1/{resource}/{{id}}") in route_methods
        assert ("DELETE", f"/api/v1/{resource}/{{id}}") in route_methods

    assert not any(endpoint.get("path", "").startswith("/api/v1/refresh-tokens") for endpoint in endpoints)


@pytest.mark.asyncio
async def test_incremental_verifier_accepts_reconciled_post_comment_routes():
    api_architecture = ensure_entity_crud_endpoints(
        {
            "status": "success",
            "api_strategy": {"base_path": "/api/v1"},
            "endpoints": [],
            "global_configurations": {"cors_policy": {}, "rate_limiting": {}},
        },
        _blog_db_architecture(),
        True,
    )

    verifier = VerifierAgent()
    is_valid, feedback, logs = await verifier.verify_incremental(
        "APIAgent",
        api_architecture,
        {"generation_type": "full_stack", "db_architecture": _blog_db_architecture()},
    )

    assert is_valid
    assert feedback == ""
    assert logs == []


def test_fallback_api_architecture_generates_complete_crud_paths():
    api_agent = APIAgent()

    result = api_agent._get_fallback_api_architecture(
        {"authentication": {"required": True}},
        {},
        _blog_db_architecture(),
        {},
    )

    paths = {(endpoint["method"], endpoint["path"]) for endpoint in result["endpoints"]}
    assert ("GET", "/api/v1/post-categories") in paths
    assert ("PUT", "/api/v1/post-categories/{id}") in paths
    assert ("DELETE", "/api/v1/comments/{id}") in paths
    assert not any(endpoint["path"].startswith("/api/v1/refresh-tokens") for endpoint in result["endpoints"])


def test_contract_auditor_accepts_reconciled_kebab_case_api_routes():
    api_architecture = ensure_entity_crud_endpoints(
        {
            "status": "success",
            "api_strategy": {"base_path": "/api/v1"},
            "endpoints": [],
        },
        _blog_db_architecture(),
        True,
    )

    gaps = ContractAuditor.audit(
        "APIAgent",
        api_architecture,
        {
            "requirements": {
                "database_requirements": {
                    "entities": ["PostCategory", "Post", "Comment", "RefreshToken"]
                }
            }
        },
    )

    assert gaps == []


@pytest.mark.asyncio
async def test_run_single_agent_repairs_existing_api_contract_before_skip():
    db = MockDatabase()
    project_id = "api-existing-repair"
    project_doc = {
        "_id": project_id,
        "generation_type": "full_stack",
        "requirements": {"authentication": {"required": True}},
        "db_architecture": _blog_db_architecture(),
        "api_architecture": {
            "status": "success",
            "api_strategy": {"base_path": "/api/v1"},
            "global_configurations": {"cors_policy": {}, "rate_limiting": {}},
            "endpoints": [
                {"group_name": "Authentication API", "path": "/api/v1/auth/login", "method": "POST"}
            ],
        },
    }
    await db.projects.insert_one(project_doc)

    result = await run_single_agent(db, project_id, project_doc, "APIAgent")

    paths = {(endpoint["method"], endpoint["path"]) for endpoint in result["endpoints"]}
    assert ("GET", "/api/v1/post-categories") in paths
    assert ("DELETE", "/api/v1/comments/{id}") in paths

    updated = await db.projects.find_one({"_id": project_id})
    updated_paths = {(endpoint["method"], endpoint["path"]) for endpoint in updated["api_architecture"]["endpoints"]}
    assert ("PUT", "/api/v1/posts/{id}") in updated_paths


@pytest.mark.asyncio
async def test_run_single_agent_repairs_cached_api_contract_before_reuse():
    db = MockDatabase()
    project_id = "api-cache-repair"
    project_doc = {
        "_id": project_id,
        "generation_type": "full_stack",
        "requirements": {"authentication": {"required": True}},
        "db_architecture": _blog_db_architecture(),
        "backend_architecture": {"backend_strategy": "service"},
        "database_model_generation": {"generated_models": ["PostCategory", "Post", "Comment"]},
        "blueprint": {"name": "Blog"},
    }
    await db.projects.insert_one(project_doc)
    ArtifactCache.clear_all()

    agent_name = "APIAgent"
    art_type = AGENT_TO_ARTIFACT.get(agent_name, agent_name.lower())
    input_hash = ArtifactCache.compute_input_hash(project_doc["blueprint"])
    dep_hash = DependencyDAG.compute_dependency_hash(project_doc, art_type)
    cache_key = ArtifactCache.compute_cache_key(project_id, agent_name, input_hash=input_hash, dependency_hash=dep_hash)

    await ArtifactCache.set(
        db,
        project_id,
        agent_name,
        cache_key,
        {
            "status": "success",
            "api_strategy": {"base_path": "/api/v1"},
            "global_configurations": {"cors_policy": {}, "rate_limiting": {}},
            "endpoints": [
                {"group_name": "Authentication API", "path": "/api/v1/auth/login", "method": "POST"}
            ],
        },
        input_hash=input_hash,
        dependency_hash=dep_hash,
    )

    result = await run_single_agent(db, project_id, project_doc, agent_name)

    paths = {(endpoint["method"], endpoint["path"]) for endpoint in result["endpoints"]}
    assert ("GET", "/api/v1/post-categories") in paths
    assert ("POST", "/api/v1/comments") in paths
    assert get_agent_db_key(agent_name) in project_doc
