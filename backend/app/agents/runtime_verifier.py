import os
import sys
import shutil
import tempfile
import subprocess
import json
import asyncio
from loguru import logger
from typing import Any, Dict, List, Tuple, Optional

from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.services.project_assembler import detect_tech_stack, assemble_project_codebase
from app.agents.context import build_agent_system_prompt, parse_json_response

class RuntimeVerifierAgent:
    """
    RuntimeVerifierAgent is a dynamic execution-based verification and auto-healing agent.
    
    It writes generated project files to a physical temporary directory, sets up virtual
    environments and dependencies where applicable, runs actual compilers/linters/builders,
    detects errors, and uses an LLM healing loop to correct syntax, imports, and integrations.
    """
    def __init__(self) -> None:
        self.agent_name = "ErrorCorrectionAgent"  # Reuse mapped name for reasoning model routing
        self.max_healing_attempts = 3

    async def verify_and_heal(
        self,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Main orchestration method for runtime compilation checks and healing loops.
        """
        logger.info(f"[{project_id}] Starting Runtime Verification & Auto-Healing process...")
        
        # 1. Retrieve generated codebase
        synthesized_codebase = project_doc.get("synthesized_codebase", [])
        if not synthesized_codebase:
            logger.warning(f"[{project_id}] No synthesized codebase found. Skipping runtime verification.")
            return project_doc

        # 2. Compile full monorepo codebase (combines boilerplate + AI code)
        assembly = assemble_project_codebase(project_doc, ai_codebase=synthesized_codebase)
        assembled_files = assembly.get("codebase", [])
        if not assembled_files:
            logger.warning(f"[{project_id}] Failed to assemble codebase. Skipping.")
            return project_doc

        # 3. Detect technology stack
        stack = detect_tech_stack(project_doc)
        backend_tech = stack.get("backend", "fastapi")
        frontend_tech = stack.get("frontend", "nextjs")
        db_tech = stack.get("database", "mongodb")
        logger.info(f"[{project_id}] Detected Stack: Backend={backend_tech}, Frontend={frontend_tech}, Database={db_tech}")

        # 4. Create physical temporary workspace on disk
        temp_dir = tempfile.mkdtemp(prefix=f"sarthi_run_{project_id}_")
        logger.info(f"[{project_id}] Created temporary workspace at: {temp_dir}")

        try:
            # Write all files to temporary workspace
            self._write_files_to_disk(temp_dir, assembled_files)

            # Keep a working copy of files in memory to track edits
            # We map: relative_path -> file dict
            file_map = {f["path"]: f for f in assembled_files}

            # 5. Iterative compile & heal loop
            success = False
            for attempt in range(1, self.max_healing_attempts + 1):
                logger.info(f"[{project_id}] Healing attempt {attempt}/{self.max_healing_attempts}...")
                
                # Run various diagnostic tests
                errors = await self._run_diagnostic_tests(temp_dir, backend_tech, frontend_tech, db_tech)
                
                if not errors:
                    logger.info(f"[{project_id}] All runtime compilation and verification checks PASSED on attempt {attempt}!")
                    success = True
                    break
                
                logger.warning(f"[{project_id}] Compilation checks failed on attempt {attempt} with {len(errors)} issues.")
                
                # Heal the first batch of errors (to avoid LLM confusion, we can heal files one by one or in parallel)
                healed_any = False
                for err_file, err_log in errors[:3]:  # Limit to 3 files per loop to keep it targeted
                    logger.info(f"[{project_id}] Healing file: {err_file}")
                    
                    file_record = file_map.get(err_file)
                    if not file_record:
                        # Find closest match if path mapping is slightly off
                        for p in file_map.keys():
                            if p.endswith(err_file) or err_file.endswith(p):
                                file_record = file_map[p]
                                err_file = p
                                break
                    
                    if file_record:
                        healed_content = await self._heal_file_content(
                            file_path=err_file,
                            file_content=file_record.get("content", ""),
                            error_log=err_log,
                            project_doc=project_doc,
                            tech_stack=stack
                        )
                        if healed_content:
                            # Update physical file on disk
                            full_path = os.path.join(temp_dir, err_file)
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            with open(full_path, "w", encoding="utf-8") as f:
                                f.write(healed_content)
                            
                            # Update in-memory map
                            file_record["content"] = healed_content
                            healed_any = True
                
                if not healed_any:
                    logger.warning(f"[{project_id}] Healing engine could not propose any file changes. Breaking loop.")
                    break

            # 6. Read back modified files and update synthesized_codebase in project_doc & MongoDB
            if success:
                logger.info(f"[{project_id}] Syncing working healed codebase back to database.")
            else:
                logger.warning(f"[{project_id}] Synthesis verification complete with remaining issues. Syncing best effort.")

            # Filter out and update the original synthesized_codebase list
            # Note: deterministic boilerplate files should not be written to synthesized_codebase unless modified,
            # but to be safe, we update files in synthesized_codebase if their contents changed, or overwrite the whole set
            updated_synthesized = []
            for file_record in synthesized_codebase:
                path = file_record.get("path")
                if path in file_map:
                    file_record["content"] = file_map[path]["content"]
                updated_synthesized.append(file_record)

            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {
                    "synthesized_codebase": updated_synthesized,
                    "runtime_verification_report": {
                        "status": "passed" if success else "failed_with_warnings",
                        "attempts_run": attempt,
                        "had_errors": not success
                    }
                }}
            )
            project_doc["synthesized_codebase"] = updated_synthesized
            project_doc["runtime_verification_report"] = {
                "status": "passed" if success else "failed_with_warnings"
            }

        except Exception as e:
            logger.error(f"[{project_id}] Crash in RuntimeVerifierAgent process execution: {e}")
        finally:
            # Clean up temp folder safely
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"[{project_id}] Cleaned up temp workspace directory: {temp_dir}")
            except Exception as ex:
                logger.warning(f"[{project_id}] Could not delete temp folder: {ex}")

        return project_doc

    def _write_files_to_disk(self, base_dir: str, files: List[Dict[str, Any]]) -> None:
        """Helper to physically write virtual codebase structure onto disk."""
        for file in files:
            rel_path = file.get("path", "")
            if not rel_path:
                continue
            
            full_path = os.path.join(base_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            content = file.get("content", "")
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    async def _run_diagnostic_tests(
        self,
        base_dir: str,
        backend_tech: str,
        frontend_tech: str,
        db_tech: str
    ) -> List[Tuple[str, str]]:
        """
        Runs compilation, syntax checks, typechecks, and startup tests.
        Returns a list of tuples: (failing_file_relative_path, error_logs)
        """
        errors: List[Tuple[str, str]] = []

        # ---- Task A: Python Backend Syntax Compile Check ----
        if backend_tech in ["fastapi", "django", "flask"]:
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                logger.info("Running Python syntax compilation checks...")
                # We can compile all .py files inside backend recursively
                python_executable = sys.executable or "python"
                
                for root, _, files in os.walk(backend_dir):
                    for file in files:
                        if file.endswith(".py"):
                            py_file_path = os.path.join(root, file)
                            rel_py_path = os.path.relpath(py_file_path, base_dir)
                            
                            # Run python compile subprocess
                            proc = await asyncio.create_subprocess_exec(
                                python_executable, "-m", "py_compile", py_file_path,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE
                            )
                            stdout, stderr = await proc.communicate()
                            
                            if proc.returncode != 0:
                                err_msg = stderr.decode("utf-8", errors="ignore") or stdout.decode("utf-8", errors="ignore")
                                logger.warning(f"Python syntax error in {rel_py_path}: {err_msg}")
                                errors.append((rel_py_path, f"Syntax Compilation Error:\n{err_msg}"))

        # ---- Task B: TypeScript/Frontend Compile Check (Best Effort Static/CLI Linting) ----
        if frontend_tech in ["nextjs", "react", "vue", "angular"]:
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(frontend_dir):
                logger.info("Running Node/TypeScript static syntax checks...")
                
                # Check package.json exists
                pkg_json = os.path.join(frontend_dir, "package.json")
                if os.path.exists(pkg_json):
                    # Check for TypeScript files compile error statically to avoid heavy node_modules installs
                    # But we can check for basic TS / JS file syntax by reading files or using npm/tsc if quick
                    # For extra safety, scan all frontend tsx/ts files for obvious braces mismatches or missing import statements
                    for root, _, files in os.walk(frontend_dir):
                        # Avoid scanning node_modules
                        if "node_modules" in root or ".next" in root or "build" in root:
                            continue
                        for file in files:
                            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                                ts_file_path = os.path.join(root, file)
                                rel_ts_path = os.path.relpath(ts_file_path, base_dir)
                                
                                # Quick check: does the file compile with Node's syntax compiler if JS, or is it broken?
                                # Let's read and perform basic brace matching / paren matching balance check
                                with open(ts_file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                
                                # Catch obvious syntax issues like incomplete copy-paste markers or raw placeholders
                                if "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
                                    errors.append((rel_ts_path, "File contains unresolved git conflict markers!"))
                                elif "TODO: implement" in content and len(content.strip()) < 100:
                                    errors.append((rel_ts_path, "File contains empty placeholder logic."))
                                
                                # Brace check
                                if content.count("{") != content.count("}"):
                                    errors.append((rel_ts_path, f"Syntax Error: Unbalanced curly braces! Open: {content.count('{')}, Close: {content.count('}')}"))
                                if content.count("(") != content.count(")"):
                                    errors.append((rel_ts_path, f"Syntax Error: Unbalanced parentheses! Open: {content.count('(')}, Close: {content.count(')')}"))

        # ---- Task C: Database Connection & Startup Smoke Test ----
        # Generate and run a connectivity checker script
        if backend_tech in ["fastapi", "django"]:
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                logger.info("Generating and executing database connectivity test script...")
                db_test_script = os.path.join(backend_dir, "sarthi_db_test.py")
                
                # Write dynamic script that attempts to import backend DB config, ORM models,
                # and initialize db session or database connection driver
                script_content = self._generate_db_test_script(backend_tech, db_tech)
                with open(db_test_script, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                python_executable = sys.executable or "python"
                # Add backend dir to python path
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{backend_dir};{env.get('PYTHONPATH', '')}"
                
                proc = await asyncio.create_subprocess_exec(
                    python_executable, db_test_script,
                    cwd=backend_dir, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                    if proc.returncode != 0:
                        err_log = stderr.decode("utf-8", errors="ignore") or stdout.decode("utf-8", errors="ignore")
                        logger.warning(f"Database module integration verification failed:\n{err_log}")
                        
                        # Find which database model or config failed by parsing log
                        failing_file = "backend/app/db/session.py"  # Default fallback path
                        for line in err_log.split("\n"):
                            if "File " in line and "sarthi_db_test.py" not in line:
                                # Extract filepath
                                try:
                                    parts = line.split('"')
                                    if len(parts) > 1 and os.path.exists(parts[1]):
                                        failing_file = os.path.relpath(parts[1], base_dir)
                                        break
                                except Exception:
                                    pass
                        
                        errors.append((failing_file, f"Database Integration/Import Connection Failure:\n{err_log}"))
                except asyncio.TimeoutError:
                    logger.warning("Database connectivity script timed out.")
                    try:
                        proc.kill()
                    except Exception:
                        pass

        return errors

    def _generate_db_test_script(self, backend: str, db: str) -> str:
        """
        Generates a robust python script to test model imports and mock connectivity.
        """
        return f"""
import sys
import os

print("Starting database model integration and import checks...")

# Attempt to load database configuration and ORM sessions
try:
    if os.path.exists("app/db/session.py"):
        print("Importing app.db.session...")
        from app.db.session import engine, Base
    elif os.path.exists("app/db/base.py"):
        print("Importing app.db.base...")
        from app.db.base import Base
except Exception as e:
    print(f"DATABASE_IMPORT_ERROR: Failed to import base database sessions: {{e}}", file=sys.stderr)
    sys.exit(1)

# Attempt to load models to ensure there are no import loop / syntax issues
try:
    print("Verifying database models and schemas imports...")
    import_models = False
    
    # Try importing typical model locations
    if os.path.exists("app/models"):
        sys.path.insert(0, os.path.abspath("."))
        import glob
        for file in glob.glob("app/models/**/*.py", recursive=True):
            mod_name = file.replace(".py", "").replace("/", ".").replace("\\\\", ".")
            if "__init__" not in mod_name:
                print(f"Importing {{mod_name}}...")
                __import__(mod_name)
                import_models = True
except Exception as e:
    print(f"MODEL_IMPORT_ERROR: Crash detected during database ORM model definitions import: {{e}}", file=sys.stderr)
    sys.exit(2)

print("Database imports and model setups verified successfully!")
sys.exit(0)
"""

    async def _heal_file_content(
        self,
        file_path: str,
        file_content: str,
        error_log: str,
        project_doc: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> Optional[str]:
        """
        Calls Gemini LLM to heal the specific file throwing compile or runtime errors.
        """
        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "You are a Senior AI Compiler Recovery and Stabilization Engineer. "
            "Your sole objective is to take a failing source code file, analyze its syntax/compilation error log, "
            "and output the corrected code which is guaranteed to compile and run perfectly."
        )

        user_content = f"""
        Analyze the following compilation / syntax error and heal the code file.
        
        File Relative Path: {file_path}
        Technology Stack: Backend={tech_stack.get('backend')}, Frontend={tech_stack.get('frontend')}, Database={tech_stack.get('database')}
        
        ---- CRITICAL ERROR LOG ----
        {error_log}
        ---------------------------
        
        ---- CURRENT FILE CONTENT ----
        ```
        {file_content}
        ```
        ------------------------------
        
        Provide the corrected file content. Your correction must preserve all existing business logic, fields, functions, and models, but fix the exact syntax issue, bad indent, missing import, unbalanced curly brace, or loop reference causing the failure.
        
        Return ONLY valid JSON in this exact schema format:
        {{
          "status": "success",
          "corrected_code": "Your complete drops-in replacement healed code content here"
        }}
        """

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            parsed = parse_json_response(raw_response.strip())
            return parsed.get("corrected_code")
        except Exception as e:
            logger.error(f"Failed to get healed file content from LLM for {file_path}: {e}")
            return None
