import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.change_impact_analyzer import ChangeImpactAnalyzer
from app.services.container_verifier import ContainerVerifier
from app.agents.runtime_verifier import RuntimeVerifierAgent

def test_change_impact_analyzer_sha256():
    c1 = "print('hello')"
    c2 = "print('hello')"
    c3 = "print('world')"
    
    h1 = ChangeImpactAnalyzer.compute_sha256(c1)
    h2 = ChangeImpactAnalyzer.compute_sha256(c2)
    h3 = ChangeImpactAnalyzer.compute_sha256(c3)
    
    assert h1 == h2
    assert h1 != h3

def test_change_impact_analyzer_identify_changed_files():
    current_files = [
        {"path": "backend/app/main.py", "content": "print('hello')"},
        {"path": "frontend/src/App.tsx", "content": "console.log('test')"}
    ]
    previous_hashes = {
        "backend/app/main.py": ChangeImpactAnalyzer.compute_sha256("print('old')"),
        "frontend/src/App.tsx": ChangeImpactAnalyzer.compute_sha256("console.log('test')")
    }
    
    changed = ChangeImpactAnalyzer.identify_changed_files(current_files, previous_hashes)
    assert changed == ["backend/app/main.py"]

def test_change_impact_analyzer_parse_imports():
    py_code = """
import os, sys
from app.core.config import settings
import app.main
"""
    imports = ChangeImpactAnalyzer.parse_imports("backend/app/main.py", py_code)
    assert "os" in imports
    assert "sys" in imports
    assert "app.core.config" in imports

    ts_code = """
import React from 'react';
import { Button } from './components/Button';
import '@/styles/main.css';
"""
    ts_imports = ChangeImpactAnalyzer.parse_imports("frontend/src/App.tsx", ts_code)
    assert "react" in ts_imports
    assert "./components/Button" in ts_imports
    assert "@/styles/main.css" in ts_imports

def test_change_impact_analyzer_build_dependency_graph():
    files = [
        {"path": "backend/app/main.py", "content": "from app.core.config import settings"},
        {"path": "backend/app/core/config.py", "content": "import os"}
    ]
    import_map, dependent_map = ChangeImpactAnalyzer.build_dependency_graph(files)
    
    assert "backend/app/main.py" in import_map
    assert "backend/app/core/config.py" in dependent_map

def test_change_impact_analyzer_determine_validation_scope():
    assert ChangeImpactAnalyzer.determine_validation_scope({"backend/app/main.py"}) == "backend"
    assert ChangeImpactAnalyzer.determine_validation_scope({"frontend/src/App.tsx"}) == "frontend"
    assert ChangeImpactAnalyzer.determine_validation_scope({"backend/app/main.py", "frontend/src/App.tsx"}) == "full_stack"

@pytest.mark.asyncio
async def test_container_verifier_docker_availability():
    # Patch subprocess to mock docker info check
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.wait = AsyncMock(return_value=0)
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        is_avail = await ContainerVerifier.is_docker_available()
        assert is_avail is True

@pytest.mark.asyncio
async def test_container_verifier_run_in_container():
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.wait = AsyncMock(return_value=0)
        mock_proc.returncode = 0
        
        # Stream read mockers
        mock_proc.stdout.readline = AsyncMock(side_effect=[b"Log 1\n", b""])
        mock_proc.stderr.readline = AsyncMock(side_effect=[b""])
        
        mock_exec.return_value = mock_proc
        
        code, logs = await ContainerVerifier.run_in_container(
            workspace_dir=".",
            image_name="node:18-alpine",
            commands=["npm run build"]
        )
        assert code == 0
        assert any("Log 1" in log for log in logs)

@pytest.mark.asyncio
async def test_runtime_verifier_agent_verify_and_heal_fallback():
    # Verify fallback mode behaves correctly when Docker is stopped
    agent = RuntimeVerifierAgent()
    project_doc = {
        "name": "FallbackProj",
        "category": "productivity",
        "synthesized_codebase": [
            {"path": "backend/app/main.py", "content": "print('running')"}
        ]
    }
    
    mock_db = AsyncMock()
    mock_db.runtime_verification_analytics.insert_one = AsyncMock()
    mock_db.projects.update_one = AsyncMock()
    
    with patch.object(ContainerVerifier, "is_docker_available", return_value=False), \
         patch.object(agent, "_run_host_compilation", return_value=[]) as mock_host_compile, \
         patch.object(agent, "_run_host_startup_sniffing", return_value=[]) as mock_sniff:
        
        res = await agent.verify_and_heal(project_doc, mock_db, "proj-123")
        
        assert res["runtime_verification_report"]["status"] == "passed"
        mock_host_compile.assert_called_once()
        mock_sniff.assert_called_once()


@pytest.mark.asyncio
async def test_runtime_verifier_run_command_with_logging_exception():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    
    with patch("asyncio.create_subprocess_shell", side_effect=OSError("executable not found")):
        code, logs = await agent._run_command_with_logging(
            cmd="nonexistent-cmd",
            cwd=".",
            timeout=10.0,
            step_name="Testing invalid cmd",
            db=mock_db,
            project_id="proj-123",
            progress=90
        )
        assert code == -1
        assert any("Failed to spawn command 'nonexistent-cmd' on host: executable not found" in log for log in logs)


@pytest.mark.asyncio
async def test_run_host_compilation_frontend_yarn():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "frontend" in path_str:
            if "yarn.lock" in path_str:
                return True
            if "pnpm-lock.yaml" in path_str:
                return False
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="frontend",
            backend_tech="python",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_any_call(
            cmd="yarn install --prefer-offline",
            cwd=os.path.join(base_dir, "frontend"),
            timeout=90.0,
            step_name="Installing Frontend Dependencies",
            db=mock_db,
            project_id="proj-123",
            progress=91
        )
        mock_run.assert_any_call(
            cmd="yarn build",
            cwd=os.path.join(base_dir, "frontend"),
            timeout=120.0,
            step_name="Compiling Frontend Assets",
            db=mock_db,
            project_id="proj-123",
            progress=92
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_node_ts():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            if "tsconfig.json" in path_str:
                return True
            if "pnpm-lock.yaml" in path_str or "yarn.lock" in path_str:
                return False
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="express",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_any_call(
            cmd="npm install --prefer-offline",
            cwd=os.path.join(base_dir, "backend"),
            timeout=90.0,
            step_name="Installing Backend Dependencies (Node)",
            db=mock_db,
            project_id="proj-123",
            progress=92
        )
        mock_run.assert_any_call(
            cmd="npx tsc --noEmit",
            cwd=os.path.join(base_dir, "backend"),
            timeout=60.0,
            step_name="Checking Backend Types/Syntax (Node)",
            db=mock_db,
            project_id="proj-123",
            progress=93
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_golang():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="go",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_called_once_with(
            cmd="go build ./...",
            cwd=os.path.join(base_dir, "backend"),
            timeout=90.0,
            step_name="Compiling Go Backend",
            db=mock_db,
            project_id="proj-123",
            progress=93
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_rust():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="rust",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_called_once_with(
            cmd="cargo check",
            cwd=os.path.join(base_dir, "backend"),
            timeout=120.0,
            step_name="Checking Rust Backend Syntax",
            db=mock_db,
            project_id="proj-123",
            progress=93
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_springboot_gradle_nt():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            if "build.gradle" in path_str or "gradlew" in path_str or "gradlew.bat" in path_str:
                return True
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch("os.name", "nt"), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="springboot",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_called_once_with(
            cmd="gradlew compileJava",
            cwd=os.path.join(base_dir, "backend"),
            timeout=120.0,
            step_name="Compiling Spring Boot Backend",
            db=mock_db,
            project_id="proj-123",
            progress=93
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_springboot_maven_unix():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            if "mvnw" in path_str:
                return True
            if "build.gradle" in path_str or "gradlew" in path_str:
                return False
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch("os.name", "posix"), \
         patch.object(agent, "_run_command_with_logging", return_value=(0, [])) as mock_run:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="springboot",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_run.assert_called_once_with(
            cmd="./mvnw compile",
            cwd=os.path.join(base_dir, "backend"),
            timeout=120.0,
            step_name="Compiling Spring Boot Backend",
            db=mock_db,
            project_id="proj-123",
            progress=93
        )


@pytest.mark.asyncio
async def test_run_host_compilation_backend_ruby():
    agent = RuntimeVerifierAgent()
    mock_db = AsyncMock()
    import os
    import subprocess
    
    base_dir = os.path.normpath("/tmp/project")
    
    def exists_side_effect(path):
        path_str = str(path).replace("\\", "/")
        if "backend" in path_str:
            return True
        return False

    mock_walk = [
        (os.path.join(base_dir, "backend"), [], ["app.rb"])
    ]

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))
    mock_proc.returncode = 0

    with patch("os.path.exists", side_effect=exists_side_effect), \
         patch("os.walk", return_value=mock_walk), \
         patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        
        errors = await agent._run_host_compilation(
            base_dir=base_dir,
            scope="backend",
            backend_tech="ruby",
            frontend_tech="nextjs",
            db_tech="postgresql",
            project_doc={},
            db=mock_db,
            project_id="proj-123"
        )
        assert len(errors) == 0
        mock_exec.assert_called_once_with(
            "ruby", "-c", os.path.join(base_dir, "backend", "app.rb"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

