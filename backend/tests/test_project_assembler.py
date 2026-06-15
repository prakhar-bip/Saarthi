from app.services.project_assembler import assemble_project_codebase


def _sample_project_doc():
    return {
        "name": "ShopCart",
        "category": "commerce",
        "blueprint": {
            "name": "ShopCart",
            "idea": "An online retail app with accounts, products, and checkout.",
            "features": ["User authentication", "Product catalog", "Order checkout"],
            "tech_stack": "Next.js, FastAPI, MongoDB",
        },
        "requirements": {
            "features": ["user_authentication", "product_catalog", "order_checkout"],
            "database_requirements": {
                "required": True,
                "entities": ["User", "Product", "Order"],
            },
        },
        "db_architecture": {
            "entities": [
                {"entity_name": "User", "fields": [{"name": "email", "type": "string", "required": True}]},
                {"entity_name": "Product", "fields": [{"name": "price", "type": "number", "required": True}]},
                {"entity_name": "Order", "fields": [{"name": "total", "type": "number", "required": True}]},
            ]
        },
    }


def test_assembler_generates_connected_quality_gated_project():
    result = assemble_project_codebase(_sample_project_doc())
    paths = {file["path"] for file in result["codebase"]}

    assert result["quality_report"]["status"] == "passed"
    assert "backend/app/main.py" in paths
    assert "frontend/src/components/EntityWorkspace.tsx" in paths
    assert "shared/contracts/project.json" in paths
    assert result["generated_project_contract"]["entities"][1]["route"] == "products"


def test_assembler_keeps_non_core_ai_files_but_owns_core_runtime_files():
    result = assemble_project_codebase(
        _sample_project_doc(),
        ai_codebase=[
            {
                "name": "main.py",
                "path": "backend/app/main.py",
                "language": "python",
                "content": "broken python !!!",
            },
            {
                "name": "notes.md",
                "path": "docs/notes.md",
                "language": "markdown",
                "content": "# Custom Notes",
            },
        ],
    )
    by_path = {file["path"]: file for file in result["codebase"]}

    assert result["quality_report"]["status"] == "passed"
    assert by_path["docs/notes.md"]["content"] == "# Custom Notes"
    assert "FastAPI" in by_path["backend/app/main.py"]["content"]
