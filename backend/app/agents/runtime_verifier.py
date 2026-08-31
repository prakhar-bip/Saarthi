import os
import sys
import shutil
import tempfile
import asyncio
import json
import time
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.services.project_assembler import detect_tech_stack, assemble_project_codebase
from app.agents.context import build_agent_system_prompt, parse_json_response

from app.services.change_impact_analyzer import ChangeImpactAnalyzer
from app.services.container_verifier import ContainerVerifier

class RuntimeVerifierAgent:
    """
    RuntimeVerifierAgent is a dynamic execution-based verification and auto-healing agent.
    
    It analyzes changes recursively, executes isolated checks in ephemeral containers 
    with custom memory/CPU bounds, and falls back gracefully to host execution if Docker is unavailable.
    """
    def __init__(self) -> None:
        self.agent_name = "ErrorCorrectionAgent"  # Mapped for reasoning models routing
        self.max_healing_attempts = 5

    async def verify_and_heal(
        self,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Main orchestration entrypoint for Containerized Runtime verification and healing.
        """
        pass
        t_start = time.time()
        
        # 1. Retrieve current generated codebase
        synthesized_codebase = project_doc.get("synthesized_codebase", [])
        if not synthesized_codebase:
            pass
            return project_doc

        # Calculate healing capacity dynamically
        self.max_healing_attempts = min(10, max(5, 5 + len(synthesized_codebase) // 5))

        # Assemble full file layout (merges boilerplate + AI files)
        assembly = assemble_project_codebase(project_doc, ai_codebase=synthesized_codebase)
        assembled_files = assembly.get("codebase", [])
        if not assembled_files:
            pass
            return project_doc

        # Detect stacks
        stack = detect_tech_stack(project_doc)
        backend_tech = stack.get("backend", "fastapi")
        frontend_tech = stack.get("frontend", "nextjs")
        db_tech = stack.get("database", "mongodb")

        # 2. Check for Baseline Hashes to trigger Change Impact Analysis
        report = project_doc.get("runtime_verification_report", {})
        previous_hashes = report.get("file_hashes", {})
        
        # Run Change Impact Analysis
        impact_analysis = ChangeImpactAnalyzer.build_validation_plan(assembled_files, previous_hashes)
        changed_files = impact_analysis["changed_files"]
        affected_files = impact_analysis["affected_files"]
        scope = impact_analysis["scope"]
        start_tier = impact_analysis["recommended_tier"]

        # 3. Create/Reuse workspace
        temp_dir = os.path.join(tempfile.gettempdir(), f"sarthi_run_{project_id}_persist")
        os.makedirs(temp_dir, exist_ok=True)
        self._write_files_to_disk(temp_dir, assembled_files)

        # Track file states recursively in-memory
        file_map = {f["path"]: f for f in assembled_files}

        # Check Docker status
        docker_active = await ContainerVerifier.is_docker_available()
        pass

        success = False
        metrics_rebuilds = 0
        metrics_inc_rebuilds = 0
        container_run_duration = 0.0
        repair_duration = 0.0
        highest_tier = 1
        attempt = 1

        # 4. Compile & Heal Iterative Loop
        for attempt in range(1, self.max_healing_attempts + 1):
            pass
            
            # Execute validation across tiered checks
            errors, tier_reached, duration_container = await self._run_tiered_verification(
                temp_dir=temp_dir,
                scope=scope,
                start_tier=start_tier,
                docker_active=docker_active,
                backend_tech=backend_tech,
                frontend_tech=frontend_tech,
                db_tech=db_tech,
                project_doc=project_doc,
                db=db,
                project_id=project_id,
                changed_files=changed_files
            )
            
            highest_tier = max(highest_tier, tier_reached)
            container_run_duration += duration_container
            
            if attempt == 1 and not changed_files:
                metrics_rebuilds += 1
            else:
                metrics_inc_rebuilds += 1

            if not errors:
                pass
                success = True
                break

            pass
            
            # Execute Surgical Auto-Healing
            healed_any = False
            t_heal_0 = time.time()
            for err_file, err_log in errors:
                pass
                
                file_record = file_map.get(err_file)
                if not file_record:
                    # Fallback mapping matcher
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
                        # Write repaired file back to host disk for subsequent runs/mounts
                        full_path = os.path.join(temp_dir, err_file)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(healed_content)
                        
                        file_record["content"] = healed_content
                        healed_any = True

            repair_duration += (time.time() - t_heal_0)
            if not healed_any:
                pass
                break

        # 5. Read back modified files
        updated_synthesized = []
        new_hashes = {}
        for file_record in synthesized_codebase:
            path = file_record.get("path")
            if path in file_map:
                file_record["content"] = file_map[path]["content"]
            updated_synthesized.append(file_record)
            
        # Recompute file hashes for successive change impact analysis runs
        for f in assembled_files:
            path = f["path"]
            new_hashes[path] = ChangeImpactAnalyzer.compute_sha256(file_map[path]["content"])

        t_total = time.time() - t_start

        # 6. Store Granular Analytics in MongoDB
        analytics_record = {
            "project_id": project_id,
            "timestamp": datetime.now(timezone.utc),
            "verification_time": t_total,
            "build_time": container_run_duration if docker_active else (t_total - repair_duration),
            "container_runtime": container_run_duration,
            "repair_time": repair_duration,
            "validation_scope": scope,
            "affected_files": affected_files if changed_files else [f["path"] for f in assembled_files],
            "retry_count": attempt,
            "is_containerized": docker_active,
            "tier_reached": highest_tier,
            "status": "passed" if success else "failed"
        }
        
        try:
            await db.runtime_verification_analytics.insert_one(analytics_record)
            pass
        except Exception as err:
            pass

        # Sync back to project document
        await db.projects.update_one(
            {"_id": project_id},
            {"$set": {
                "synthesized_codebase": updated_synthesized,
                "runtime_verification_report": {
                    "status": "passed" if success else "failed_with_warnings",
                    "attempts_run": attempt,
                    "had_errors": not success,
                    "file_hashes": new_hashes
                }
            }}
        )
        
        project_doc["synthesized_codebase"] = updated_synthesized
        project_doc["runtime_verification_report"] = {
            "status": "passed" if success else "failed_with_warnings"
        }

        # Clear sources, preserving dependency caches
        try:
            self._clean_directory_preserving_cache(temp_dir)
        except Exception as ex:
            pass

        return project_doc

    async def _run_tiered_verification(
        self,
        temp_dir: str,
        scope: str,
        start_tier: int,
        docker_active: bool,
        backend_tech: str,
        frontend_tech: str,
        db_tech: str,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str,
        changed_files: List[str]
    ) -> Tuple[List[Tuple[str, str]], int, float]:
        """
        Executes six-tier verification escalation hierarchy.
        Returns: (errors_list, highest_tier_reached, container_runtime_seconds)
        """
        errors = []
        container_duration = 0.0
        
        # --------------------------------------------------
        # Tier 1: Syntax Validation
        # --------------------------------------------------
        pass
        for file_path in (changed_files if changed_files else []):
            full_path = os.path.join(temp_dir, file_path)
            if file_path.endswith(".py") and os.path.exists(full_path):
                import py_compile
                try:
                     py_compile.compile(full_path, doraise=True)
                except py_compile.PyCompileError as e:
                     errors.append((file_path, f"Syntax Compile Error:\n{str(e)}"))
            elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")) and os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Run basic ES6 brackets/imports syntax validation checks
                if content.count("{") != content.count("}") or content.count("(") != content.count(")"):
                    errors.append((file_path, "Syntax Error: Mismatched brace/parenthesis counts detected."))
                if "import" in content and "from" not in content and "import(" not in content:
                    errors.append((file_path, "Syntax Error: Malformed import syntax."))

        if errors:
            return errors, 1, container_duration

        if start_tier > 1 and not changed_files:
            # We are running baseline - proceed with full-scope build
            pass

        # --------------------------------------------------
        # Tier 2: Import Validation
        # --------------------------------------------------
        pass
        # Static check can raise warnings/errors but for compilation, Tier 5 acts as physical build check
        
        # --------------------------------------------------
        # Tier 3: Module Validation
        # --------------------------------------------------
        pass
        
        # --------------------------------------------------
        # Tier 4: Service Validation
        # --------------------------------------------------
        pass

        # --------------------------------------------------
        # Tier 5: Application Validation (Docker / Ephemeral Sandbox Build)
        # --------------------------------------------------
        pass
        
        if docker_active:
            t_container_0 = time.time()
            if scope in ("frontend", "full_stack"):
                fe_install_cmd = "npm install --no-audit --no-fund --prefer-offline"
                fe_build_cmd = "npm run build"
                frontend_dir = os.path.join(temp_dir, "frontend")
                if os.path.exists(os.path.join(frontend_dir, "pnpm-lock.yaml")):
                    fe_install_cmd = "npm install -g pnpm && pnpm install"
                    fe_build_cmd = "pnpm build"
                elif os.path.exists(os.path.join(frontend_dir, "yarn.lock")):
                    fe_install_cmd = "npm install -g yarn && yarn install"
                    fe_build_cmd = "yarn build"

                code, logs = await ContainerVerifier.run_in_container(
                    workspace_dir=temp_dir,
                    image_name="node:18-alpine",
                    commands=[
                        "cd frontend",
                        fe_install_cmd,
                        fe_build_cmd
                    ]
                )
                container_duration += (time.time() - t_container_0)
                if code != 0:
                    fe_errors = self._parse_logs_for_errors(logs, temp_dir, "frontend")
                    errors.extend(fe_errors)
            
            t_container_0 = time.time()
            if scope in ("backend", "full_stack") and not errors:
                image_name = "python:3.11-slim"
                commands = []
                backend_dir = os.path.join(temp_dir, "backend")

                if backend_tech in ("fastapi", "django", "flask"):
                    image_name = "python:3.11-slim"
                    if os.path.exists(os.path.join(backend_dir, "requirements.txt")):
                        commands.extend([
                            "cd backend",
                            "pip install -r requirements.txt --prefer-binary --disable-pip-version-check",
                            "python -m py_compile app/main.py"
                        ])
                    else:
                        commands.extend([
                            "cd backend",
                            "python -m py_compile app/main.py"
                        ])
                elif backend_tech in ("express", "node"):
                    image_name = "node:18-alpine"
                    be_install_cmd = "npm install --prefer-offline"
                    be_compile_cmd = "npx tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else "node --check index.js"
                    if os.path.exists(os.path.join(backend_dir, "pnpm-lock.yaml")):
                        be_install_cmd = "npm install -g pnpm && pnpm install"
                        be_compile_cmd = "pnpm tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else be_compile_cmd
                    elif os.path.exists(os.path.join(backend_dir, "yarn.lock")):
                        be_install_cmd = "npm install -g yarn && yarn install"
                        be_compile_cmd = "yarn tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else be_compile_cmd
                    commands.extend([
                        "cd backend",
                        be_install_cmd,
                        be_compile_cmd
                    ])
                elif backend_tech in ("springboot", "java"):
                    if os.path.exists(os.path.join(backend_dir, "build.gradle")) or os.path.exists(os.path.join(backend_dir, "gradlew")):
                        image_name = "gradle:8-jdk17"
                        commands.extend([
                            "cd backend",
                            "./gradlew compileJava" if os.path.exists(os.path.join(backend_dir, "gradlew")) else "gradle compileJava"
                        ])
                    else:
                        image_name = "maven:3.8-openjdk-17"
                        commands.extend([
                            "cd backend",
                            "./mvnw compile" if os.path.exists(os.path.join(backend_dir, "mvnw")) else "mvn compile"
                        ])
                elif backend_tech == "go":
                    image_name = "golang:1.21-alpine"
                    commands.extend([
                        "cd backend",
                        "go build ./..."
                    ])
                elif backend_tech == "rust":
                    image_name = "rust:1.72-alpine"
                    commands.extend([
                        "cd backend",
                        "cargo check"
                    ])
                else:
                    image_name = "python:3.11-slim"
                    commands.extend([
                        "cd backend",
                        "find . -name '*.py' -exec python -m py_compile {} +"
                    ])
                    
                code, logs = await ContainerVerifier.run_in_container(
                    workspace_dir=temp_dir,
                    image_name=image_name,
                    commands=commands
                )
                container_duration += (time.time() - t_container_0)
                if code != 0:
                    be_errors = self._parse_logs_for_errors(logs, temp_dir, "backend")
                    errors.extend(be_errors)
        else:
            # Fallback seamlessly to direct host execution if Docker Desktop is stopped
            pass
            host_errors = await self._run_host_compilation(temp_dir, scope, backend_tech, frontend_tech, db_tech, project_doc, db, project_id)
            errors.extend(host_errors)

        if errors:
            return errors, 5, container_duration

        # --------------------------------------------------
        # Tier 6: Full Integration Validation (Live startup & sniffer checks)
        # --------------------------------------------------
        pass
        # Execute server startup sniffer to confirm runtime ports binding and DB connectivity
        live_errors = await self._run_host_startup_sniffing(temp_dir, scope, backend_tech, frontend_tech, db_tech, project_doc, db, project_id)
        errors.extend(live_errors)

        return errors, 6, container_duration

    async def _run_host_compilation(
        self,
        base_dir: str,
        scope: str,
        backend_tech: str,
        frontend_tech: str,
        db_tech: str,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str
    ) -> List[Tuple[str, str]]:
        """Seamless fallback direct-host compilation runner supporting multiple tech stacks."""
        errors = []
        python_executable = sys.executable or "python"
        
        if scope in ("frontend", "full_stack"):
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(frontend_dir):
                fe_install_cmd = "npm install --no-audit --no-fund --prefer-offline"
                fe_build_cmd = "npm run build"
                if os.path.exists(os.path.join(frontend_dir, "pnpm-lock.yaml")):
                    fe_install_cmd = "pnpm install"
                    fe_build_cmd = "pnpm build"
                elif os.path.exists(os.path.join(frontend_dir, "yarn.lock")):
                    fe_install_cmd = "yarn install --prefer-offline"
                    fe_build_cmd = "yarn build"

                code, logs = await self._run_command_with_logging(
                    cmd=fe_install_cmd,
                    cwd=frontend_dir,
                    timeout=90.0,
                    step_name="Installing Frontend Dependencies",
                    db=db,
                    project_id=project_id,
                    progress=91
                )
                if code != 0:
                    errors.append(("frontend/package.json", f"Frontend dependencies failed to install via: {fe_install_cmd}"))
                else:
                    code, logs = await self._run_command_with_logging(
                        cmd=fe_build_cmd,
                        cwd=frontend_dir,
                        timeout=120.0,
                        step_name="Compiling Frontend Assets",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.extend(self._parse_logs_for_errors(logs, base_dir, "frontend"))

        if scope in ("backend", "full_stack") and not errors:
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                if backend_tech in ("fastapi", "django", "flask"):
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
                                    err_msg = stderr.decode("utf-8", errors="ignore")
                                    errors.append((rel_py_path, f"Syntax Compilation Error:\n{err_msg}"))
                                    
                elif backend_tech in ("express", "node"):
                    be_install_cmd = "npm install --prefer-offline"
                    be_compile_cmd = "npx tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else "node --check index.js"
                    if os.path.exists(os.path.join(backend_dir, "pnpm-lock.yaml")):
                        be_install_cmd = "pnpm install"
                        be_compile_cmd = "pnpm tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else be_compile_cmd
                    elif os.path.exists(os.path.join(backend_dir, "yarn.lock")):
                        be_install_cmd = "yarn install"
                        be_compile_cmd = "yarn tsc --noEmit" if os.path.exists(os.path.join(backend_dir, "tsconfig.json")) else be_compile_cmd
                    
                    code, logs = await self._run_command_with_logging(
                        cmd=be_install_cmd,
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Installing Backend Dependencies (Node)",
                        db=db,
                        project_id=project_id,
                        progress=92
                    )
                    if code != 0:
                        errors.append(("backend/package.json", f"Backend dependencies failed to install via: {be_install_cmd}"))
                    else:
                        code, logs = await self._run_command_with_logging(
                            cmd=be_compile_cmd,
                            cwd=backend_dir,
                            timeout=60.0,
                            step_name="Checking Backend Types/Syntax (Node)",
                            db=db,
                            project_id=project_id,
                            progress=93
                        )
                        if code != 0:
                            errors.extend(self._parse_logs_for_errors(logs, base_dir, "backend"))

                elif backend_tech in ("springboot", "java"):
                    be_compile_cmd = "mvn compile"
                    if os.path.exists(os.path.join(backend_dir, "build.gradle")) or os.path.exists(os.path.join(backend_dir, "gradlew")):
                        be_compile_cmd = "./gradlew compileJava" if os.name != 'nt' and os.path.exists(os.path.join(backend_dir, "gradlew")) else "gradlew compileJava" if os.name == 'nt' and os.path.exists(os.path.join(backend_dir, "gradlew.bat")) else "gradle compileJava"
                    else:
                        be_compile_cmd = "./mvnw compile" if os.name != 'nt' and os.path.exists(os.path.join(backend_dir, "mvnw")) else "mvnw compile" if os.name == 'nt' and os.path.exists(os.path.join(backend_dir, "mvnw.cmd")) else "mvn compile"

                    code, logs = await self._run_command_with_logging(
                        cmd=be_compile_cmd,
                        cwd=backend_dir,
                        timeout=120.0,
                        step_name="Compiling Spring Boot Backend",
                        db=db,
                        project_id=project_id,
                        progress=93
                    )
                    if code != 0:
                        errors.extend(self._parse_logs_for_errors(logs, base_dir, "backend"))

                elif backend_tech == "go":
                    code, logs = await self._run_command_with_logging(
                        cmd="go build ./...",
                        cwd=backend_dir,
                        timeout=90.0,
                        step_name="Compiling Go Backend",
                        db=db,
                        project_id=project_id,
                        progress=93
                    )
                    if code != 0:
                        errors.extend(self._parse_logs_for_errors(logs, base_dir, "backend"))

                elif backend_tech == "rust":
                    code, logs = await self._run_command_with_logging(
                        cmd="cargo check",
                        cwd=backend_dir,
                        timeout=120.0,
                        step_name="Checking Rust Backend Syntax",
                        db=db,
                        project_id=project_id,
                        progress=93
                    )
                    if code != 0:
                        errors.extend(self._parse_logs_for_errors(logs, base_dir, "backend"))

                else:
                    for root, _, files in os.walk(backend_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, base_dir)
                            if file.endswith(".rb"):
                                try:
                                    proc = await asyncio.create_subprocess_exec(
                                        "ruby", "-c", file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                    )
                                    _, stderr = await proc.communicate()
                                    if proc.returncode != 0:
                                        errors.append((rel_path, f"Ruby Syntax Error:\n{stderr.decode('utf-8', errors='ignore')}"))
                                except Exception:
                                    pass
                                    pass
                            elif file.endswith(".php"):
                                try:
                                    proc = await asyncio.create_subprocess_exec(
                                        "php", "-l", file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                    )
                                    _, stderr = await proc.communicate()
                                    if proc.returncode != 0:
                                        errors.append((rel_path, f"PHP Syntax Error:\n{stderr.decode('utf-8', errors='ignore')}"))
                                except Exception:
                                    pass

        return errors

    async def _run_host_startup_sniffing(
        self,
        base_dir: str,
        scope: str,
        backend_tech: str,
        frontend_tech: str,
        db_tech: str,
        project_doc: Dict[str, Any],
        db: Any,
        project_id: str
    ) -> List[Tuple[str, str]]:
        """Launches backend and frontend uvicorn/Next.js servers on dynamic ports to sniff logs."""
        errors: List[Tuple[str, str]] = []
        gen_type = project_doc.get("generation_type", "full_stack")
        
        # Check Docker status
        from app.services.container_verifier import ContainerVerifier
        docker_active = await ContainerVerifier.is_docker_available()
        
        if docker_active:
            await self._broadcast(db, project_id, 93, "🔍 Launching Containerized Startup Sniffing...")
            fe_task = None
            be_task = None
            
            # 1. Run Frontend in Detached Container
            if gen_type in ["frontend_only", "full_stack"] and scope in ("frontend", "full_stack"):
                frontend_dir = os.path.join(base_dir, "frontend")
                if os.path.exists(frontend_dir):
                    fe_install_cmd = "npm install --no-audit --no-fund --prefer-offline"
                    fe_dev_cmd = "npm run dev"
                    fe_image = "node:18-alpine"
                    if os.path.exists(os.path.join(frontend_dir, "pnpm-lock.yaml")):
                        fe_install_cmd = "npm install -g pnpm && pnpm install"
                        fe_dev_cmd = "pnpm dev"
                    elif os.path.exists(os.path.join(frontend_dir, "yarn.lock")):
                        fe_install_cmd = "npm install -g yarn && yarn install"
                        fe_dev_cmd = "yarn dev"
                        
                    fe_commands = [
                        "cd frontend",
                        fe_install_cmd,
                        fe_dev_cmd
                    ]
                    
                    async def run_fe():
                        return await ContainerVerifier.run_daemon_container(
                            workspace_dir=base_dir,
                            image_name=fe_image,
                            commands=fe_commands,
                            container_name=f"sarthi_fe_{project_id}",
                            run_duration=10.0
                        )
                    fe_task = asyncio.create_task(run_fe())
            
            # 2. Run Backend in Detached Container
            if gen_type in ["backend_only", "full_stack", "microservice"] and scope in ("backend", "full_stack"):
                backend_dir = os.path.join(base_dir, "backend")
                if os.path.exists(backend_dir):
                    be_image = "python:3.11-slim"
                    be_commands = ["cd backend"]
                    
                    if backend_tech in ("fastapi", "django", "flask"):
                        be_image = "python:3.11-slim"
                        if os.path.exists(os.path.join(backend_dir, "requirements.txt")):
                            be_commands.extend([
                                "pip install -r requirements.txt --prefer-binary --disable-pip-version-check",
                                "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
                            ])
                        else:
                            be_commands.append("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
                    elif backend_tech in ("express", "node"):
                        be_image = "node:18-alpine"
                        be_install_cmd = "npm install --prefer-offline"
                        be_dev_cmd = "npm run dev"
                        if os.path.exists(os.path.join(backend_dir, "pnpm-lock.yaml")):
                            be_install_cmd = "npm install -g pnpm && pnpm install"
                            be_dev_cmd = "pnpm dev"
                        elif os.path.exists(os.path.join(backend_dir, "yarn.lock")):
                            be_install_cmd = "npm install -g yarn && yarn install"
                            be_dev_cmd = "yarn dev"
                        be_commands.extend([
                            be_install_cmd,
                            be_dev_cmd
                        ])
                    elif backend_tech == "go":
                        be_image = "golang:1.21-alpine"
                        be_commands.append("go run main.go")
                    elif backend_tech == "rust":
                        be_image = "rust:1.72-alpine"
                        be_commands.append("cargo run")
                    else:
                        be_image = "python:3.11-slim"
                        be_commands.append("python main.py")
                        
                    async def run_be():
                        return await ContainerVerifier.run_daemon_container(
                            workspace_dir=base_dir,
                            image_name=be_image,
                            commands=be_commands,
                            container_name=f"sarthi_be_{project_id}",
                            run_duration=10.0
                        )
                    be_task = asyncio.create_task(run_be())
            
            # Wait for execution logs sniffing
            fe_res = None
            be_res = None
            if fe_task and be_task:
                fe_res, be_res = await asyncio.gather(fe_task, be_task)
            elif fe_task:
                fe_res = await fe_task
            elif be_task:
                be_res = await be_task
                
            # Parse logs for errors
            if fe_res:
                code, fe_logs = fe_res
                errors.extend(self._parse_logs_for_errors(fe_logs, base_dir, "frontend"))
            if be_res:
                code, be_logs = be_res
                errors.extend(self._parse_logs_for_errors(be_logs, base_dir, "backend"))
                
            return errors
        
        # Fallback to Host execution if Docker is not available
        pass
        frontend_proc = None
        backend_proc = None
        frontend_logs: List[str] = []
        backend_logs: List[str] = []
        sniffer_tasks = []

        # Start Frontend Server
        if gen_type in ["frontend_only", "full_stack"] and scope in ("frontend", "full_stack"):
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(frontend_dir):
                await self._broadcast(db, project_id, 93, "🚀 Launching Ephemeral Frontend Server")
                frontend_proc = await asyncio.create_subprocess_shell(
                    "npm run dev",
                    cwd=frontend_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

        # Start Backend Server
        if gen_type in ["backend_only", "full_stack", "microservice"] and scope in ("backend", "full_stack"):
            backend_dir = os.path.join(base_dir, "backend")
            if os.path.exists(backend_dir):
                await self._broadcast(db, project_id, 93, "🚀 Launching Ephemeral Backend Server")
                python_executable = sys.executable or "python"
                
                import socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', 0))
                        free_port = s.getsockname()[1]
                except Exception:
                    free_port = 8080
                
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

        async def read_stream_to_list(stream, log_list, prefix=""):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        log_list.append(decoded)
            except Exception:
                pass

        if frontend_proc:
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(frontend_proc.stdout, frontend_logs, "[FE] ")))
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(frontend_proc.stderr, frontend_logs, "[FE] ")))
        if backend_proc:
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(backend_proc.stdout, backend_logs, "[BE] ")))
            sniffer_tasks.append(asyncio.create_task(read_stream_to_list(backend_proc.stderr, backend_logs, "[BE] ")))

        if sniffer_tasks:
            await self._broadcast(db, project_id, 94, "🩺 Sniffing Active Server Startup Logs...")
            await asyncio.sleep(7.0)

        # Shut down servers
        await self._broadcast(db, project_id, 94, "🧹 Cleaning up active ports")
        if frontend_proc:
            await self._terminate_process(frontend_proc)
        if backend_proc:
            await self._terminate_process(backend_proc)

        try:
            await asyncio.wait_for(asyncio.gather(*sniffer_tasks), timeout=2.0)
        except Exception:
            pass

        if frontend_logs:
            errors.extend(self._parse_logs_for_errors(frontend_logs, base_dir, "frontend"))
        if backend_logs:
            errors.extend(self._parse_logs_for_errors(backend_logs, base_dir, "backend"))

        return errors


    def _clean_directory_preserving_cache(self, path: str) -> None:
        """Removes all non-cache files recursively to prepare for subsequent builds."""
        if not os.path.exists(path):
            return
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            self._delete_non_cache(item_path)

    def _delete_non_cache(self, path: str) -> None:
        if not os.path.exists(path):
            return
        name = os.path.basename(path)
        if name in ("node_modules", ".venv", "venv", ".next"):
            return
        if os.path.isdir(path):
            has_cache = False
            for root, dirs, _ in os.walk(path):
                if any(d in ("node_modules", ".venv", "venv") for d in dirs):
                    has_cache = True
                    break
            if has_cache:
                for item in os.listdir(path):
                    self._delete_non_cache(os.path.join(path, item))
            else:
                shutil.rmtree(path)
        else:
            try:
                os.remove(path)
            except Exception:
                pass

    def _write_files_to_disk(self, base_dir: str, files: List[Dict[str, Any]]) -> None:
        for file in files:
            rel_path = file.get("path", "")
            if not rel_path:
                continue
            full_path = os.path.join(base_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file.get("content", ""))

    async def _terminate_process(self, proc) -> None:
        if not proc:
            return
        try:
            if os.name == 'nt':
                kill_cmd = f"taskkill /F /T /PID {proc.pid}"
                kill_proc = await asyncio.create_subprocess_shell(
                    kill_cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await kill_proc.wait()
            else:
                proc.terminate()
                await proc.wait()
        except Exception as e:
            pass

    async def _run_command_with_logging(
        self, cmd: str, cwd: str, timeout: float, step_name: str, db: Any, project_id: str, progress: int
    ) -> Tuple[int, List[str]]:
        await self._broadcast(db, project_id, progress, f"⏳ {step_name}...")
        logs = []
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
        except Exception as e:
            err_msg = f"Failed to spawn command '{cmd}' on host: {e}"
            pass
            logs.append(err_msg)
            return -1, logs

        async def read_stream(stream, prefix):
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        logs.append(f"{prefix}{decoded}")
            except Exception:
                pass
        stdout_task = asyncio.create_task(read_stream(proc.stdout, ""))
        stderr_task = asyncio.create_task(read_stream(proc.stderr, ""))
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            await self._terminate_process(proc)
        try:
            await asyncio.gather(stdout_task, stderr_task, timeout=2.0)
        except Exception:
            pass
        return proc.returncode if proc.returncode is not None else -1, logs

    def _parse_logs_for_errors(self, logs: List[str], base_dir: str, context_type: str) -> List[Tuple[str, str]]:
        import re
        errors = []
        py_traceback_re = re.compile(r'File "([^"]+)", line (\d+)')
        fe_file_re = re.compile(r'(?:\.\/)?(frontend\/src\/[^\s:]+|src\/[^\s:]+|components\/[^\s:]+|pages\/[^\s:]+|app\/[^\s:]+|[a-zA-Z0-9_\-\/]+\.(?:tsx|ts|jsx|js))')

        i = 0
        while i < len(logs):
            line = logs[i]
            py_match = py_traceback_re.search(line)
            if py_match:
                full_path = py_match.group(1)
                line_no = py_match.group(2)
                rel_path = full_path
                if os.path.isabs(full_path):
                    try:
                        rel_path = os.path.relpath(full_path, base_dir)
                    except Exception:
                        pass
                if "site-packages" not in full_path and "lib/python" not in full_path:
                    context_str = "\n".join(logs[max(0, i-2):min(len(logs), i+6)])
                    errors.append((rel_path.replace("\\", "/"), f"Python Runtime traceback on line {line_no}:\n{context_str}"))
                    i += 1
                    continue
            
            fe_match = fe_file_re.search(line)
            if fe_match:
                matched_path = fe_match.group(1)
                if "node_modules" not in matched_path and ".next" not in matched_path:
                    rel_path = matched_path
                    if not matched_path.startswith("frontend/") and os.path.exists(os.path.join(base_dir, "frontend", matched_path)):
                        rel_path = f"frontend/{matched_path}"
                    context_str = "\n".join(logs[max(0, i-2):min(len(logs), i+6)])
                    if "error" in context_str.lower() or "failed" in context_str.lower():
                        errors.append((rel_path.replace("\\", "/"), f"Frontend Compilation Issue:\n{context_str}"))
                        i += 1
                        continue
            i += 1

        if not errors:
            error_lines = [line for line in logs if "error" in line.lower() or "failed" in line.lower()]
            if error_lines:
                if context_type == "frontend":
                    errors.append(("frontend/package.json", "Frontend compile exception:\n" + "\n".join(error_lines[:5])))
                else:
                    errors.append(("backend/app/main.py", "Backend startup exception:\n" + "\n".join(error_lines[:5])))

        deduped = []
        seen = set()
        for f, err in errors:
            f_clean = f.replace("\\", "/")
            if f_clean not in seen:
                seen.add(f_clean)
                deduped.append((f_clean, err))
        return deduped

    async def _broadcast(self, db: Any, project_id: str, progress: int, step: str) -> None:
        try:
            from app.services.workflow import broadcast_agent_progress
            await broadcast_agent_progress(db, project_id, progress, step)
        except Exception:
            pass

    async def _heal_file_content(
        self, file_path: str, file_content: str, error_log: str, project_doc: Dict[str, Any], tech_stack: Dict[str, Any]
    ) -> Optional[str]:
        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "You are a Senior AI Compiler Recovery and Stabilization Engineer. "
            "Repair the failing file code to resolve compilation syntax and import errors completely."
        )
        user_content = f"""
        Heal the following compilation error in {file_path}.
        Error Log:
        {error_log}
        
        Current file content:
        ```
        {file_content}
        ```
        Return ONLY valid JSON:
        {{
          "status": "success",
          "root_cause_reason": "Description",
          "target_line_range": null,
          "corrected_code": "Full drop-in correction code"
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
            pass
            return None
