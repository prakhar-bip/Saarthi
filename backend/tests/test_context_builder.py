import pytest
from app.services.context_builder import build_context, DEPENDENCY_MAP

def test_dependency_pruning():
    """
    Verify that ContextBuilder strictly prunes non-dependency fields 
    based on the agent's target profile matrix.
    """
    # Create a mock project doc containing various architecture fields
    project_doc = {
        "requirements": {"project_overview": {"name": "Test Saarthi"}},
        "db_architecture": {"entities": ["User", "Post"]},
        "theme_styling": {"design_style": "Dark Glassmorphism"},
        "frontend_architecture": {"pages": ["Home", "Dashboard"]}
    }

    # DatabaseArchitectureAgent depends on requirements, planning.
    # It should NOT receive theme_styling or frontend_architecture.
    pruned_db_agent = build_context("DatabaseArchitectureAgent", project_doc)
    assert "requirements" in pruned_db_agent
    assert "db_architecture" not in pruned_db_agent  # Not in dependencies of DatabaseArchitectureAgent
    assert "theme_styling" not in pruned_db_agent
    assert "frontend_architecture" not in pruned_db_agent

    # FrontendArchitectureAgent depends on requirements, theme_styling.
    # It should NOT receive db_architecture.
    pruned_fe_agent = build_context("FrontendArchitectureAgent", project_doc)
    assert "requirements" in pruned_fe_agent
    assert "theme_styling" in pruned_fe_agent
    assert "db_architecture" not in pruned_fe_agent
    assert "frontend_architecture" not in pruned_fe_agent

def test_context_degradation_full():
    """
    Verify that if the context size is small, the builder selects the FULL level.
    """
    project_doc = {
        "requirements": {"project_overview": {"name": "Small App"}}
    }
    context = build_context("PlannerAgent", project_doc)
    
    # It should be at FULL level
    assert "requirements" in context
    assert context["requirements"].get("project_overview", {}).get("name") == "Small App"
    # Not wrapped with is_degraded since it's at FULL level
    assert "is_degraded" not in context["requirements"]

def test_context_degradation_to_summary():
    """
    Verify that if the FULL level exceeds the WARNING_THRESHOLD (80000 tokens),
    but the SUMMARY level is within the threshold, it degrades to SUMMARY.
    """
    # 1 token ≈ 4 characters. To exceed 80,000 tokens, we need > 320,000 characters.
    huge_string = "x" * 330000
    project_doc = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "This is a detailed conceptual summary of the requirements.",
        "requirements_compressed": "Ultra condensed summary.",
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }

    context = build_context("PlannerAgent", project_doc)
    
    # It should degrade to SUMMARY level
    assert "requirements" in context
    assert context["requirements"].get("is_degraded") is True
    assert context["requirements"].get("context_level") == "SUMMARY"
    assert context["requirements"].get("summary") == "This is a detailed conceptual summary of the requirements."
    # Standard python fallback dict-access keys are preserved
    assert context["requirements"].get("project_overview", {}).get("name") == "Huge App"

def test_context_degradation_to_compressed():
    """
    Verify that if the SUMMARY level is also too large, it degrades to COMPRESSED.
    """
    huge_string = "x" * 330000
    project_doc = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "x" * 330000,  # summary is also huge
        "requirements_compressed": "Ultra condensed summary of 10 words.",
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }

    context = build_context("PlannerAgent", project_doc)
    
    assert "requirements" in context
    assert context["requirements"].get("is_degraded") is True
    assert context["requirements"].get("context_level") == "COMPRESSED"
    assert context["requirements"].get("summary") == "Ultra condensed summary of 10 words."

def test_context_degradation_to_contracts():
    """
    Verify that if both FULL and SUMMARY levels exceed limits, and COMPRESSED also exceeds limits,
    it falls back to CONTRACTS.
    """
    huge_string = "x" * 330000
    project_doc = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "x" * 330000,
        "requirements_compressed": "x" * 330000,
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }

    context = build_context("PlannerAgent", project_doc)
    
    assert "requirements" in context
    assert context["requirements"].get("is_degraded") is True
    assert context["requirements"].get("context_level") == "CONTRACTS"
    assert context["requirements"].get("api_keys") == ["dummy_key"]
