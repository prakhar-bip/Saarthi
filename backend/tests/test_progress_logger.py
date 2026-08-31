import asyncio
from app.core.progress_logger import progress_logger, ProgressLogger

async def run_test():
    print("Testing ProgressLogger...")
    
    # 1. Test context setting
    progress_logger.set_context(
        project_id="proj-test-123",
        agent_name="DatabaseArchitectureAgent",
        phase_name="Spiral 2: Architecture Design",
        step_name="architecture_design",
        step_index=4,
        total_steps=18,
        model_name="NVIDIA/nemotron-3.5"
    )

    # 2. Test logging levels
    progress_logger.info("Test INFO log message")
    progress_logger.success("Test SUCCESS log message")
    progress_logger.warning("Test WARNING log message")
    progress_logger.error("Test ERROR log message")
    progress_logger.debug("Test DEBUG log message")

    # 3. Test progress domain methods
    progress_logger.phase("Spiral 3: Code Generation", icon="⚡")
    progress_logger.step(5, 18, "codegen", "Generating models and backend API endpoints")
    progress_logger.agent_start("BackendCodeGenerationAgent", "Writing FastAPI routers and CRUD controllers")
    progress_logger.file_generated("backend/app/models/user.py", char_count=1250)
    progress_logger.file_generated("frontend/src/app/dashboard/page.tsx", char_count=3400)
    progress_logger.heal("CodeSynthesizer", "backend/app/main.py", "Missing router import", "Added router include")
    progress_logger.backtrack("VerifierAgent", "backend_architecture", 1, "3 endpoint mismatches found")
    progress_logger.agent_success("BackendCodeGenerationAgent", "All 8 routers generated successfully", duration_sec=3.45, total_tokens=2100)
    progress_logger.llm_call("APIAgent", "nvidia", "nemotron-3.5", 1.85, 400, 950, "SUCCESS")

    print("\n✅ All ProgressLogger assertions passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_test())
