import sys
import os
import json

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.context_builder import build_context

def run_tests():
    print("=========================================")
    print("RUNNING MANUALLY WRITTEN VERIFICATION TESTS")
    print("=========================================\n")

    # Test 1: Dependency Pruning
    print("--- Test 1: Dependency Pruning ---")
    project_doc = {
        "requirements": {"project_overview": {"name": "Test Saarthi"}},
        "db_architecture": {"entities": ["User", "Post"]},
        "theme_styling": {"design_style": "Dark Glassmorphism"},
        "frontend_architecture": {"pages": ["Home", "Dashboard"]}
    }

    pruned_db_agent = build_context("DatabaseArchitectureAgent", project_doc)
    assert "requirements" in pruned_db_agent, "Database agent should have requirements"
    assert "db_architecture" not in pruned_db_agent, "Database agent should NOT have db_architecture"
    assert "theme_styling" not in pruned_db_agent, "Database agent should NOT have theme_styling"
    assert "frontend_architecture" not in pruned_db_agent, "Database agent should NOT have frontend_architecture"
    print("Test 1 Passed: Dependency pruning is working successfully.\n")

    # Test 2: Full context selection
    print("--- Test 2: Full Context Selection ---")
    project_doc_small = {
        "requirements": {"project_overview": {"name": "Small App"}}
    }
    context_small = build_context("PlannerAgent", project_doc_small)
    assert "requirements" in context_small
    assert context_small["requirements"].get("project_overview", {}).get("name") == "Small App"
    assert "is_degraded" not in context_small["requirements"], "Small context should not be degraded"
    print("Test 2 Passed: Small context correctly uses FULL level.\n")

    # Test 3: Degradation to SUMMARY
    print("--- Test 3: Degradation to SUMMARY ---")
    huge_string = "x" * 330000  # Over 80k tokens
    project_doc_huge = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "This is a detailed conceptual summary of the requirements.",
        "requirements_compressed": "Ultra condensed summary.",
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }
    context_huge = build_context("PlannerAgent", project_doc_huge)
    assert "requirements" in context_huge
    assert context_huge["requirements"].get("is_degraded") is True, "Huge context should be degraded"
    assert context_huge["requirements"].get("context_level") == "SUMMARY", "Huge context should degrade to SUMMARY"
    assert context_huge["requirements"].get("summary") == "This is a detailed conceptual summary of the requirements."
    print("Test 3 Passed: Huge context correctly degrades to SUMMARY level.\n")

    # Test 4: Degradation to COMPRESSED
    print("--- Test 4: Degradation to COMPRESSED ---")
    project_doc_compressed = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "x" * 330000,
        "requirements_compressed": "Ultra condensed summary of 10 words.",
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }
    context_compressed = build_context("PlannerAgent", project_doc_compressed)
    assert "requirements" in context_compressed
    assert context_compressed["requirements"].get("is_degraded") is True
    assert context_compressed["requirements"].get("context_level") == "COMPRESSED"
    assert context_compressed["requirements"].get("summary") == "Ultra condensed summary of 10 words."
    print("Test 4 Passed: Context correctly degrades to COMPRESSED level.\n")

    # Test 5: Degradation to CONTRACTS
    print("--- Test 5: Degradation to CONTRACTS ---")
    project_doc_contracts = {
        "requirements": {
            "project_overview": {"name": "Huge App"},
            "bloat_data": huge_string
        },
        "requirements_summary": "x" * 330000,
        "requirements_compressed": "x" * 330000,
        "requirements_contracts": {"api_keys": ["dummy_key"]}
    }
    context_contracts = build_context("PlannerAgent", project_doc_contracts)
    assert "requirements" in context_contracts
    assert context_contracts["requirements"].get("is_degraded") is True
    assert context_contracts["requirements"].get("context_level") == "CONTRACTS"
    assert context_contracts["requirements"].get("api_keys") == ["dummy_key"]
    print("Test 5 Passed: Context correctly degrades to CONTRACTS level.\n")

    print("=========================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=========================================")

if __name__ == "__main__":
    run_tests()
