import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override settings to empty values BEFORE loading workflow to force immediate fallbacks
from app.core.config import settings
settings.GOOGLE_API_KEY = ""
settings.NVIDIA_API_KEY = ""
settings.OPENROUTER_API_KEY = ""
settings.USE_VERTEX_AI = False

from app.services.workflow import build_graph, compile_project_workflow, resume_project_workflow

class MockCollection:
    def __init__(self, data=None):
        self.data = data or {}
    async def find_one(self, query, *args, **kwargs):
        return self.data.get(query.get("_id"))
    async def insert_one(self, doc, *args, **kwargs):
        self.data[doc["_id"]] = doc
    async def update_one(self, query, update, *args, **kwargs):
        doc = self.data.get(query.get("_id"))
        if doc:
            set_ops = update.get("$set", {})
            for k, v in set_ops.items():
                doc[k] = v
            # Handle pushes
            push_ops = update.get("$push", {})
            for k, v in push_ops.items():
                if k not in doc:
                    doc[k] = []
                doc[k].append(v)
        return MagicMock()

class MockDatabase:
    def __init__(self):
        self.projects = MockCollection()
        self.chats = MockCollection()
        self.validation_backtrack_metrics = MockCollection()


async def run_parallel_workflow_test():
    print("Initializing Sarthi 2.0 Workflow Test (Fast Fallbacks Mode)...")
    
    db = MockDatabase()
    
    project_id = "test-proj-123"
    project_doc = {
        "_id": project_id,
        "name": "E-Commerce App",
        "category": "e-commerce",
        "status": "documents_ready",
        "progress": 100,
        "step": "Documents Generated",
        "initial_prompt": {
            "name": "E-Commerce App",
            "idea": "An online retail store with user authentication and payment processing.",
            "features": ["User authentication", "Product catalog", "Stripe payment"],
            "tech_stack": "React, FastAPI, MongoDB"
        },
        "hitl_enabled": True,
        "hitl_approved": False,
        "requirements": {
            "status": "success",
            "project_overview": {
                "name": "E-Commerce App",
                "type": "E-Commerce",
                "description": "Retail app",
                "complexity": "Medium"
            },
            "tech_stack": {
                "frontend": ["React"],
                "backend": ["FastAPI"],
                "database": ["MongoDB"]
            },
            "database_requirements": {
                "required": True,
                "entities": ["User", "Product", "Order"]
            }
        },
        "planning": {
            "status": "success",
            "execution_strategy": {
                "project_type": "E-Commerce",
                "architecture_style": "Client-Server"
            }
        }
    }
    
    await db.projects.insert_one(project_doc)
    
    # 2. Run the initial compilation workflow
    print("\n[Step 1] Running compile_project_workflow...")
    await compile_project_workflow(db, project_id, project_doc)
    
    # Verify it finished compilation directly
    final_doc = db.projects.data[project_id]
    print("Project status after compilation:", final_doc["status"])
    print("Project step after compilation:", final_doc["step"])
    print("Project final progress:", final_doc["progress"])
    
    print("VALIDATION LOGS FOR PROJECT test-proj-123:", final_doc.get("validation_logs"))
    assert final_doc["status"] in ("completed", "completed_with_issues"), f"Should finish the project build! Status: {final_doc['status']}. Step: {final_doc.get('step')}"

    assert final_doc["codebase"], "Workflow should produce a downloadable codebase."
    assert final_doc["quality_report"]["status"] in ("passed", "failed"), "Generated codebase should have a quality report status."
    assert any(file["path"] == "backend/app/main.py" for file in final_doc["codebase"])
    assert any(file["path"] == "frontend/src/app/page.tsx" for file in final_doc["codebase"])
    
    # ──────────────────────────────────────────────────────────
    # [Project 2] Frontend Only Workflow
    # ──────────────────────────────────────────────────────────
    print("\n==================================================")
    print("Testing Frontend-Only Workflow...")
    print("==================================================")
    fe_proj_id = "test-fe-123"
    fe_doc = {
        "_id": fe_proj_id,
        "name": "Frontend App",
        "category": "frontend_only",
        "status": "documents_ready",
        "progress": 100,
        "step": "Documents Generated",
        "initial_prompt": {
            "name": "Frontend App",
            "idea": "A web interface.",
            "features": ["User dashboard", "Auth forms", "Theme toggle"],
            "tech_stack": "React, CSS"
        },
        "hitl_enabled": False,
        "generation_type": "frontend_only",
        "requirements": {
            "status": "success",
            "project_overview": {"name": "Frontend App", "type": "Frontend SPA"},
            "tech_stack": {"frontend": ["React"]},
        },
        "planning": {
            "status": "success",
            "execution_strategy": {"project_type": "Frontend SPA"}
        }
    }
    await db.projects.insert_one(fe_doc)
    await compile_project_workflow(db, fe_proj_id, fe_doc)
    final_fe_doc = db.projects.data[fe_proj_id]
    print("Frontend-only status:", final_fe_doc["status"])
    assert final_fe_doc["status"] in ("completed", "completed_with_issues")
    assert not any(f["path"].startswith("backend/") for f in final_fe_doc["codebase"])
    assert any(f["path"].startswith("frontend/") for f in final_fe_doc["codebase"])

    # ──────────────────────────────────────────────────────────
    # [Project 3] Backend Only Workflow
    # ──────────────────────────────────────────────────────────
    print("\n==================================================")
    print("Testing Backend-Only Workflow...")
    print("==================================================")
    be_proj_id = "test-be-123"
    be_doc = {
        "_id": be_proj_id,
        "name": "Backend App",
        "category": "backend_only",
        "status": "documents_ready",
        "progress": 100,
        "step": "Documents Generated",
        "initial_prompt": {
            "name": "Backend App",
            "idea": "A REST API server.",
            "features": ["REST endpoints", "Auth validation"],
            "tech_stack": "FastAPI"
        },
        "hitl_enabled": False,
        "generation_type": "backend_only",
        "requirements": {
            "status": "success",
            "project_overview": {"name": "Backend App", "type": "Web API"},
            "tech_stack": {"backend": ["FastAPI"]},
            "database_requirements": {"required": True, "entities": ["User"]}
        },
        "planning": {
            "status": "success",
            "execution_strategy": {"project_type": "Web API"}
        }
    }
    await db.projects.insert_one(be_doc)
    await compile_project_workflow(db, be_proj_id, be_doc)
    final_be_doc = db.projects.data[be_proj_id]
    print("Backend-only status:", final_be_doc["status"])
    assert final_be_doc["status"] in ("completed", "completed_with_issues")
    assert any(f["path"].startswith("backend/") for f in final_be_doc["codebase"])
    assert not any(f["path"].startswith("frontend/") for f in final_be_doc["codebase"])

    print("\nSUCCESS: All Sarthi 2.0 dynamic options workflows verified successfully!")

if __name__ == "__main__":
    asyncio.run(run_parallel_workflow_test())
