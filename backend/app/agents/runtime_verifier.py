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
        self.max_healing_attempts = 5

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

        # Dynamically calculate maximum healing attempts based on number of generated source files (min 5, max 10)
        self.max_healing_attempts = min(10, max(5, 5 + len(synthesized_codebase) // 5))
        logger.info(f"[{project_id}] Dynamic healing attempts set to {self.max_healing_attempts} based on {len(synthesized_codebase)} files.")

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
                errors = await self._run_diagnostic_tests(temp_dir, backend_tech, frontend_tech, db_tech, project_doc, db, project_id)
                
                if not errors:
                    logger.info(f"[{project_id}] All runtime compilation and verification checks PASSED on attempt {attempt}!")
                    success = True
                    break
                
                logger.warning(f"[{project_id}] Compilation checks failed on attempt {attempt} with {len(errors)} issues.")
                
                # Heal all errors/warnings found across files without ignoring any of them
                healed_any = False
                for err_file, err_log in errors:
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
            logger.error(f"[{project_id}] Crash in RuntimeVerifierAgent process execution: {e}", exc_info=True)
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

    async def _terminate_process(self, proc) -> None:
        """Gracefully terminates process tree of a given subprocess."""
        if not proc:
            return
        try:
            if os.name == 'nt':
                # On Windows, kill the process tree using taskkill
                kill_cmd = f"taskkill /F /T /PID {proc.pid}"
                kill_proc = await asyncio.create_subprocess_shell(
                    kill_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await kill_proc.wait()
            else:
                # On Unix, send SIGTERM
                proc.terminate()
                await proc.wait()
        except Exception as e:
            logger.warning(f"Error terminating process {proc.pid}: {e}")

    async def _run_command_with_logging(
        self,
        cmd: str,
        cwd: str,
        timeout: float,
        step_name: str,
        db: Any,
        project_id: str,
        progress: int | float
    ) -> Tuple[int, List[str]]:
        """Runs a command, streams output to logs and broadcasts progress."""
        await self._broadcast(db, project_id, progress, f"⏳ {step_name}...")
        logger.info(f"[{project_id}] Running command: {cmd} inside {cwd}")
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        logs = []
        async def read_stream(stream, prefix):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        logs.append(f"{prefix}{decoded}")
                        if len(decoded) > 120:
                            decoded = decoded[:120] + "..."
                        logger.info(f"{prefix}{decoded}")
            except Exception as e:
                logger.warning(f"Error reading stream in command {cmd}: {e}")

        stdout_task = asyncio.create_task(read_stream(proc.stdout, "[STDOUT] "))
        stderr_task = asyncio.create_task(read_stream(proc.stderr, "[STDERR] "))
        
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Command '{cmd}' timed out after {timeout}s.")
            await self._terminate_process(proc)
            logs.append(f"[SYSTEM] Command timed out after {timeout} seconds.")
        
        try:
            await asyncio.wait_for(asyncio.gather(stdout_task, stderr_task), timeout=5.0)
        except Exception:
            pass
            
        return proc.returncode if proc.returncode is not None else -1, logs

    def _parse_logs_for_errors(self, logs: List[str], base_dir: str, context_type: str) -> List[Tuple[str, str]]:
        """
        Parses testing or startup logs to find errors and maps them to relative file paths.
        Returns list of (rel_path, error_description)
        """
        import re
        errors = []
        
        # 1. Regex patterns for Python traceback
        py_traceback_re = re.compile(r'File "([^"]+)", line (\d+)')
        
        # 2. Regex patterns for Frontend / TS / Next.js compilation errors
        fe_file_re = re.compile(r'(?:\.\/)?(frontend\/src\/[^\s:]+|src\/[^\s:]+|components\/[^\s:]+|pages\/[^\s:]+|app\/[^\s:]+|[a-zA-Z0-9_\-\/]+\.(?:tsx|ts|jsx|js))')

        db_issues = ["ConnectionRefusedError", "ServerSelectionTimeoutError", "MongoNetworkError", "OperationalError", "InterfaceError"]
        has_db_issue = any(any(issue in line for issue in db_issues) for line in logs)
        
        module_missing_re = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
        has_missing_module = None
        for line in logs:
            match = module_missing_re.search(line)
            if match:
                has_missing_module = match.group(1)
                break

        i = 0
        while i < len(logs):
            line = logs[i]
            
            # Check Python Traceback
            py_match = py_traceback_re.search(line)
            pytest_match = re.search(r'(?:\[STDERR\]\s+|\[STDOUT\]\s+)?([a-zA-Z0-9_\-\/\\\.]+\.py):(\d+):', line)
            
            if py_match or pytest_match:
                match = py_match if py_match else pytest_match
                full_path = match.group(1)
                line_no = match.group(2)
                rel_path = full_path
                if os.path.isabs(full_path):
                    try:
                        rel_path = os.path.relpath(full_path, base_dir)
                    except Exception:
                        pass
                
                if "site-packages" not in full_path and "lib/python" not in full_path:
                    context = logs[max(0, i-2):min(len(logs), i+6)]
                    context_str = "\n".join(context)
                    errors.append((rel_path, f"Python Runtime traceback on line {line_no}:\n{context_str}"))
                    i += 1
                    continue

            # Check Frontend file matches
            fe_match = fe_file_re.search(line)
            if fe_match:
                matched_path = fe_match.group(1)
                if "node_modules" not in matched_path and ".next" not in matched_path and "dist" not in matched_path:
                    rel_path = matched_path
                    if not matched_path.startswith("frontend/") and os.path.exists(os.path.join(base_dir, "frontend", matched_path)):
                        rel_path = f"frontend/{matched_path}"
                    elif not matched_path.startswith("frontend/") and os.path.exists(os.path.join(base_dir, matched_path)):
                        rel_path = matched_path
                    
                    context = logs[max(0, i-2):min(len(logs), i+6)]
                    context_str = "\n".join(context)
                    if "error" in context_str.lower() or "warning" in context_str.lower() or "failed" in context_str.lower():
                        errors.append((rel_path, f"Frontend Compilation Issue:\n{context_str}"))
                        i += 1
                        continue
            
            i += 1

        if has_db_issue and not errors:
            db_file = "backend/app/db/session.py"
            if not os.path.exists(os.path.join(base_dir, db_file)):
                db_file = "backend/app/core/config.py"
            errors.append((db_file, f"Database Connection Warning/Crash Sniffed:\n" + "\n".join(logs[-15:])))

        if has_missing_module and not errors:
            req_file = "backend/requirements.txt"
            if not os.path.exists(os.path.join(base_dir, req_file)):
                req_file = "backend/app/main.py"
            errors.append((req_file, f"Missing Python Module Dependency '{has_missing_module}':\n" + "\n".join(logs[-10:])))

        if not errors:
            error_lines = [line for line in logs if "error" in line.lower() or "failed" in line.lower() or "exception" in line.lower() or "traceback" in line.lower()]
            if error_lines:
                if context_type == "frontend":
                    errors.append(("frontend/package.json", "Unmapped Frontend Startup Error:\n" + "\n".join(error_lines[:10])))
                else:
                    main_file = "backend/app/main.py"
                    if not os.path.exists(os.path.join(base_dir, main_file)):
                        main_file = "backend/main.py"
                    errors.append((main_file, "Unmapped Backend Startup Error:\n" + "\n".join(error_lines[:10])))

        deduped = []
        seen = set()
        for f, err in errors:
            f_clean = f.replace("\\", "/")
            if f_clean not in seen:
                seen.add(f_clean)
                deduped.append((f_clean, err))
        return deduped

    def _parse_polyglot_errors(self, logs: List[str], base_dir: str, lang: str) -> List[Tuple[str, str]]:
        """Parses compiler/build logs for multiple languages to map errors to files."""
        import re
        errors = []
        
        if lang == "java":
            maven_err_re = re.compile(r'\[ERROR\]\s+(.*?\.java):\[(\d+),\d+\]\s+(.*)')
            for line in logs:
                match = maven_err_re.search(line)
                if match:
                    full_path, line_no, desc = match.groups()
                    rel_path = os.path.relpath(full_path, base_dir) if os.path.isabs(full_path) else full_path
                    errors.append((rel_path.replace("\\", "/"), f"Java Compile Error on line {line_no}: {desc}"))
                    
        elif lang == "go":
            go_err_re = re.compile(r'(.*?\.go):(\d+):(?:\d+:)?\s+(.*)')
            for line in logs:
                match = go_err_re.search(line)
                if match:
                    full_path, line_no, desc = match.groups()
                    rel_path = os.path.relpath(full_path, base_dir) if os.path.isabs(full_path) else full_path
                    errors.append((rel_path.replace("\\", "/"), f"Go Compile Error on line {line_no}: {desc}"))
                    
        elif lang == "rust":
            rust_err_re = re.compile(r'error(?:\[.*?\])?:\s+(.*)')
            rust_loc_re = re.compile(r'-->\s+(.*?\.rs):(\d+):')
            current_err = ""
            for line in logs:
                match_err = rust_err_re.search(line)
                if match_err:
                    current_err = match_err.group(1)
                match_loc = rust_loc_re.search(line)
                if match_loc and current_err:
                    full_path, line_no = match_loc.groups()
                    rel_path = os.path.relpath(full_path, base_dir) if os.path.isabs(full_path) else full_path
                    errors.append((rel_path.replace("\\", "/"), f"Rust Compile Error on line {line_no}: {current_err}"))
                    current_err = ""
                    
        elif lang == "c":
            c_err_re = re.compile(r'(.*?\.c|.*?\.h|.*?\.cpp|.*?\.hpp):(\d+):(?:\d+:)?\s+error:\s+(.*)')
            for line in logs:
                match = c_err_re.search(line)
                if match:
                    full_path, line_no, desc = match.groups()
                    rel_path = os.path.relpath(full_path, base_dir) if os.path.isabs(full_path) else full_path
                    errors.append((rel_path.replace("\\", "/"), f"C/C++ Compile Error on line {line_no}: {desc}"))
                    
        elif lang == "node":
            errors.extend(self._parse_logs_for_errors(logs, base_dir, "frontend"))
            
        return errors

    async def _broadcast(self, db: Any, project_id: str, progress: int | float, step: str) -> None:
        """Helper to broadcast verification status to UI."""
        try:
            from app.services.workflow import broadcast_agent_progress
            await broadcast_agent_progress(db, project_id, progress, step)
        except Exception as e:
            logger.warning(f"Failed to broadcast progress: {e}")

    async def _run_diagnostic_tests(
        self,
        base_dir: str,
        backend_tech: str,
        frontend_tech: str,
        db_tech: str,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str
    ) -> List[Tuple[str, str]]:
        """
        Runs compilation, syntax checks, typechecks, and startup tests.
        Returns a list of tuples: (failing_file_relative_path, error_logs)
        """
        gen_type = project_doc.get("generation_type", "full_stack")
        errors: List[Tuple[str, str]] = []

        # =================================────────────────=================
        # PHASE 1: Dependency Setup and Testing / Build Compilation Checks
        # =================================────────────────=================

        # ---- 1. Frontend Testing/Build ----
        if gen_type in ["frontend_only", "full_stack"]:
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(frontend_dir):
                # Install frontend dependencies
                install_cmd = "npm install --no-audit --no-fund --prefer-offline"
                code, logs = await self._run_command_with_logging(
                    cmd=install_cmd,
                    cwd=frontend_dir,
                    timeout=90.0,
                    step_name="Installing Frontend Dependencies",
                    db=db,
                    project_id=project_id,
                    progress=91
                )
                if code != 0:
                    errors.append(("frontend/package.json", "Frontend dependency installation failed:\n" + "\n".join(logs[-20:])))
                else:
                    # Run TypeScript/Webpack compilation test
                    build_cmd = "npm run build"
                    code, logs = await self._run_command_with_logging(
                        cmd=build_cmd,
                        cwd=frontend_dir,
                        timeout=120.0,
                        step_name="Running Frontend Compilation (Build) Checks",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        fe_errors = self._parse_logs_for_errors(logs, base_dir, "frontend")
                        errors.extend(fe_errors)

        # ---- 2. Backend Testing/Build ----
        if gen_type in ["backend_only", "full_stack", "microservice"]:
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                # 2a. Java / Spring Boot (Maven)
                if os.path.exists(os.path.join(backend_dir, "pom.xml")):
                    code, logs = await self._run_command_with_logging(
                        cmd="mvn clean compile -DskipTests=true --no-transfer-progress",
                        cwd=backend_dir,
                        timeout=120.0,
                        step_name="Compiling Spring Boot Backend (Maven)",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_polyglot_errors(logs, base_dir, "java"))
                
                # 2b. Go Backend
                elif os.path.exists(os.path.join(backend_dir, "go.mod")):
                    code, logs = await self._run_command_with_logging(
                        cmd="go build ./...",
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Compiling Go Backend",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_polyglot_errors(logs, base_dir, "go"))
                
                # 2c. Rust Backend
                elif os.path.exists(os.path.join(backend_dir, "Cargo.toml")):
                    code, logs = await self._run_command_with_logging(
                        cmd="cargo check",
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Compiling Rust Backend",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_polyglot_errors(logs, base_dir, "rust"))
                
                # 2d. C/C++ Backend (IoT etc.)
                elif os.path.exists(os.path.join(backend_dir, "Makefile")) or os.path.exists(os.path.join(backend_dir, "CMakeLists.txt")):
                    compile_cmd = "make" if os.path.exists(os.path.join(backend_dir, "Makefile")) else "cmake . && cmake --build ."
                    code, logs = await self._run_command_with_logging(
                        cmd=compile_cmd,
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Compiling C/C++ Codebase",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_polyglot_errors(logs, base_dir, "c"))
                
                # 2e. Node.js Backend (Express/Fastify)
                elif os.path.exists(os.path.join(backend_dir, "package.json")):
                    # Install dependencies
                    await self._run_command_with_logging(
                        cmd="npm install --no-audit --no-fund --prefer-offline",
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Installing Backend Node Dependencies",
                        db=db,
                        project_id=project_id,
                        progress=91
                    )
                    # Check compilation
                    code, logs = await self._run_command_with_logging(
                        cmd="npm run build",
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Compiling Node.js Backend",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_polyglot_errors(logs, base_dir, "node"))
                        
                # 2f. Default Python Backend Check
                else:
                    # Install requirements
                    req_file = os.path.join(backend_dir, "requirements.txt")
                    if os.path.exists(req_file):
                        python_executable = sys.executable or "python"
                        install_cmd = f'"{python_executable}" -m pip install -r requirements.txt --prefer-binary --disable-pip-version-check'
                        code, logs = await self._run_command_with_logging(
                            cmd=install_cmd,
                            cwd=backend_dir,
                            timeout=90.0,
                            step_name="Installing Backend Dependencies",
                            db=db,
                            project_id=project_id,
                            progress=91
                        )
                        if code != 0:
                            errors.append(("backend/requirements.txt", "Backend dependencies installation failed:\n" + "\n".join(logs[-20:])))
                    
                    # Check Python Syntax Compile recursively
                    python_executable = sys.executable or "python"
                    await self._broadcast(db, project_id, 92, "⏳ Running Python Compilation Checks")
                    for root, _, files in os.walk(backend_dir):
                        if "venv" in root or ".venv" in root or "__pycache__" in root:
                            continue
                        for file in files:
                            if file.endswith(".py"):
                                py_file_path = os.path.join(root, file)
                                rel_py_path = os.path.relpath(py_file_path, base_dir)
                                
                                proc = await asyncio.create_subprocess_exec(
                                    python_executable, "-m", "py_compile", py_file_path,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                )
                                stdout, stderr = await proc.communicate()
                                if proc.returncode != 0:
                                    err_msg = stderr.decode("utf-8", errors="ignore") or stdout.decode("utf-8", errors="ignore")
                                    errors.append((rel_py_path, f"Syntax Compilation Error:\n{err_msg}"))

                # Run pytest if any
                tests_dir = os.path.join(backend_dir, "tests")
                if os.path.exists(tests_dir):
                    pytest_cmd = f'"{python_executable}" -m pytest'
                    code, logs = await self._run_command_with_logging(
                        cmd=pytest_cmd,
                        cwd=backend_dir,
                        timeout=30.0,
                        step_name="Running Backend Unit Tests",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        be_errors = self._parse_logs_for_errors(logs, base_dir, "backend")
                        errors.extend(be_errors)

        # If we have any compilation or syntax errors, stop and heal immediately
        if errors:
            logger.warning(f"[{project_id}] Phase 1 checks failed with {len(errors)} errors. Skipping Phase 2 server startup sniffing.")
            return errors

        # ==================================================================
        # PHASE 2: Live Server Startup and Log Sniffing Verification
        # =================================────────────────=================
        
        frontend_proc = None
        backend_proc = None
        frontend_logs: List[str] = []
        backend_logs: List[str] = []
        sniffer_tasks = []

        # ---- Start Frontend Server ----
        if gen_type in ["frontend_only", "full_stack"]:
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(frontend_dir):
                await self._broadcast(db, project_id, 93, "🚀 Launching Live Frontend Server")
                dev_cmd = "npm run dev"
                frontend_proc = await asyncio.create_subprocess_shell(
                    dev_cmd,
                    cwd=frontend_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.info(f"[{project_id}] Started Frontend Dev Server (PID: {frontend_proc.pid})")

        # ---- Start Backend Server ----
        if gen_type in ["backend_only", "full_stack", "microservice"]:
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                await self._broadcast(db, project_id, 93, "🚀 Launching Live Backend Server")
                python_executable = sys.executable or "python"
                startup_cmd = ""
                # Find a free port dynamically to prevent socket address already in use conflicts
                import socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', 0))
                        free_port = s.getsockname()[1]
                except Exception:
                    free_port = 8080 # Fallback port if binding fails

                # Determine server startup command based on tech markers for polyglot systems
                if os.path.exists(os.path.join(backend_dir, "pom.xml")):
                    startup_cmd = f"mvn spring-boot:run -Dspring-boot.run.arguments=--server.port={free_port}"
                elif os.path.exists(os.path.join(backend_dir, "go.mod")):
                    startup_cmd = "go run ."
                elif os.path.exists(os.path.join(backend_dir, "Cargo.toml")):
                    startup_cmd = "cargo run"
                elif os.path.exists(os.path.join(backend_dir, "package.json")):
                    startup_cmd = "npm start"
                elif backend_tech == "fastapi":
                    startup_cmd = f'"{python_executable}" -m uvicorn app.main:app --host 127.0.0.1 --port {free_port}'
                elif backend_tech == "django":
                    startup_cmd = f'"{python_executable}" manage.py runserver 127.0.0.1:{free_port}'
                elif backend_tech == "flask":
                    startup_cmd = f'"{python_executable}" -m flask run --host=127.0.0.1 --port={free_port}'
                else:
                    if os.path.exists(os.path.join(backend_dir, "main.py")):
                        startup_cmd = f'"{python_executable}" main.py'
                    elif os.path.exists(os.path.join(backend_dir, "app/main.py")):
                        startup_cmd = f'"{python_executable}" app/main.py'
                    else:
                        startup_cmd = f'"{python_executable}" -m uvicorn app.main:app --host 127.0.0.1 --port {free_port}'

                env = os.environ.copy()
                env["PYTHONPATH"] = f"{backend_dir};{env.get('PYTHONPATH', '')}"
                backend_proc = await asyncio.create_subprocess_shell(
                    startup_cmd,
                    cwd=backend_dir,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.info(f"[{project_id}] Started Backend Server (PID: {backend_proc.pid})")

        # ---- Concurrent Log Sniffing ----
        async def read_stream_to_list(stream, log_list, prefix=""):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        log_list.append(decoded)
                        logger.info(f"{prefix}{decoded}")
            except Exception as e:
                logger.warning(f"Error reading stream: {e}")

        if frontend_proc:
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(frontend_proc.stdout, frontend_logs, "[FE-STDOUT] ")))
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(frontend_proc.stderr, frontend_logs, "[FE-STDERR] ")))
        if backend_proc:
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(backend_proc.stdout, backend_logs, "[BE-STDOUT] ")))
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(backend_proc.stderr, backend_logs, "[BE-STDERR] ")))

        if sniffer_tasks:
            await self._broadcast(db, project_id, 94, "🩺 Sniffing Active Server Startup Logs...")
            await asyncio.sleep(7.0)

        # ---- Graceful Server Cleanup ----
        await self._broadcast(db, project_id, 94, "🧹 Shutting Down Servers & Releasing Ports")
        if frontend_proc:
            await self._terminate_process(frontend_proc)
        if backend_proc:
            await self._terminate_process(backend_proc)

        try:
            await asyncio.wait_for(asyncio.gather(*sniffer_tasks), timeout=2.0)
        except Exception:
            pass

        # ---- Parse Startup Logs ----
        if frontend_logs:
            fe_errors = self._parse_logs_for_errors(frontend_logs, base_dir, "frontend")
            errors.extend(fe_errors)
        if backend_logs:
            be_errors = self._parse_logs_for_errors(backend_logs, base_dir, "backend")
            errors.extend(be_errors)

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

    def _apply_patch(self, original_content: str, start_line: int, end_line: int, replacement_code: str) -> str:
        """
        Helper to apply a line-range patch to the original file content.
        Lines are 1-indexed.
        """
        lines = original_content.splitlines(keepends=True)
        # Convert 1-indexed line numbers to 0-indexed list indices
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        # Format the replacement code to end with proper newline matching the file structure
        if replacement_code and not replacement_code.endswith("\n"):
            ending = "\n"
            if start_idx < len(lines) and lines[start_idx].endswith("\r\n"):
                ending = "\r\n"
            replacement_code += ending
            
        new_lines = lines[:start_idx] + [replacement_code] + lines[end_idx:]
        return "".join(new_lines)

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
            "and output the specific repair details which are guaranteed to compile and run perfectly."
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
        
        Provide the correction. You can EITHER provide a targeted line-range patch OR correct the entire file.
        
        Rules:
        1. If the error can be resolved with a specific line replacement or line range replacement, provide `target_line_range` (a 1-indexed list containing `[start_line, end_line]`) and the specific `replacement_code`. Do not output the entire file in `replacement_code`.
        2. If the error requires major changes, or if you prefer to correct the entire file, set `target_line_range` to null and provide the complete file content in `corrected_code`.
        
        Return ONLY valid JSON in this exact schema format:
        {{
          "status": "success",
          "root_cause_reason": "Description of the compilation error cause",
          "target_line_range": [start_line, end_line], // e.g. [12, 15] or null
          "replacement_code": "code to replace the target range with (if range is specified)",
          "corrected_code": "complete Drops-in replacement healed code content (if range is null)"
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
            
            target_range = parsed.get("target_line_range")
            if isinstance(target_range, list) and len(target_range) == 2:
                start_line, end_line = target_range
                replacement = parsed.get("replacement_code")
                if replacement is not None:
                    logger.info(f"[{self.agent_name}] Applying targeted line-range patch [{start_line}-{end_line}] to {file_path}")
                    return self._apply_patch(file_content, int(start_line), int(end_line), replacement)
            
            logger.info(f"[{self.agent_name}] Applying full drop-in file replacement for {file_path}")
            return parsed.get("corrected_code")
        except Exception as e:
            logger.error(f"Failed to get healed file content from LLM for {file_path}: {e}")
            return None
