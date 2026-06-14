import asyncio
from unittest.mock import MagicMock, AsyncMock

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
    print("\n[Step 1] Running compile_project_workflow (HITL=True)...")
    await compile_project_workflow(db, project_id, project_doc)
    
    # Verify it suspended at the gate
    updated_doc = db.projects.data[project_id]
    print("Project status after compilation start:", updated_doc["status"])
    print("Project step after compilation start:", updated_doc["step"])
    print("Project progress after compilation start:", updated_doc["progress"])
    
    assert updated_doc["status"] == "waiting_approval", "Should halt and wait for approval!"
    assert updated_doc["implementation_plan"] is not None, "Should generate an implementation plan!"
    assert "proposed_changes" in updated_doc["implementation_plan"], "Implementation plan should have proposed changes!"
    print("Generated plan changes count:", len(updated_doc["implementation_plan"]["proposed_changes"]))
    
    # 3. Resume the workflow
    print("\n[Step 2] Resuming workflow with approval...")
    edits = updated_doc["implementation_plan"]
    edits["plan_markdown"] += "\n- Added custom test notes."
    
    await resume_project_workflow(db, project_id, edits)
    
    # Verify it finished compilation
    final_doc = db.projects.data[project_id]
    print("Project status after resume:", final_doc["status"])
    print("Project step after resume:", final_doc["step"])
    print("Project final progress:", final_doc["progress"])
    
    assert final_doc["status"] == "completed" or final_doc["status"] == "generating", "Should resume past the dispatcher!"
    print("\nSUCCESS: Sarthi 2.0 Map-Reduce parallel workflow verified successfully!")

if __name__ == "__main__":
    asyncio.run(run_parallel_workflow_test())
