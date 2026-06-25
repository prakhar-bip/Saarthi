import os
import asyncio
from typing import Dict, Any, List, Tuple
from loguru import logger

class ContainerVerifier:
    """
    Orchestrates the lifecycle of ephemeral, isolated, and secure Docker containers
    for compilation and runtime verification.
    """
    
    @classmethod
    async def is_docker_available(cls) -> bool:
        """Pings the Docker daemon to check if it is running and accessible."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=3.0)
            return proc.returncode == 0
        except Exception:
            return False

    @classmethod
    async def run_in_container(
        cls,
        workspace_dir: str,
        image_name: str,
        commands: List[str],
        memory_limit: str = "1.5g",
        cpu_limit: float = 1.0,
        timeout: float = 120.0
    ) -> Tuple[int, List[str]]:
        """
        Launches an ephemeral Docker container, mounts the workspace, runs verification, 
        collects the execution logs, and destroys the container on exit.
        """
        logger.info(f"[ContainerVerifier] Executing containerized checks using image '{image_name}'...")
        
        # Establish robust container invocation CLI
        # --rm: Ephemeral, destroy container on exit
        # --network=bridge: Allow network for pip/npm installs
        # -m / --cpus: CPU and Memory limits
        # -v: Volume mount
        # -w: Working directory
        
        mount_path = os.path.abspath(workspace_dir).replace("\\", "/")
        sh_command = " && ".join(commands)
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "bridge",
            "-m", memory_limit,
            "--cpus", str(cpu_limit),
            "-v", f"{mount_path}:/workspace",
            "-w", "/workspace",
            image_name,
            "sh", "-c", sh_command
        ]
        
        logger.info(f"[ContainerVerifier] Invoking command: {' '.join(docker_cmd)}")
        
        t0 = asyncio.get_event_loop().time()
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
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
                        logger.info(f"{prefix}{decoded}")
            except Exception:
                pass

        stdout_task = asyncio.create_task(read_stream(proc.stdout, "[STDOUT] "))
        stderr_task = asyncio.create_task(read_stream(proc.stderr, "[STDERR] "))
        
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[ContainerVerifier] Execution timed out after {timeout} seconds. Killing process...")
            try:
                proc.terminate()
                await proc.wait()
            except Exception:
                pass
            logs.append(f"[SYSTEM] Ephemeral container validation timed out after {timeout} seconds.")
            
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        
        duration = asyncio.get_event_loop().time() - t0
        logger.info(f"[ContainerVerifier] Ephemeral container finished in {duration:.2f}s with exit code {proc.returncode}")
        
        return proc.returncode if proc.returncode is not None else -1, logs
