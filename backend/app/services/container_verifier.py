import os
import asyncio
from typing import Dict, Any, List, Tuple

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
            except Exception:
                pass

        stdout_task = asyncio.create_task(read_stream(proc.stdout, "[STDOUT] "))
        stderr_task = asyncio.create_task(read_stream(proc.stderr, "[STDERR] "))
        
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.terminate()
                await proc.wait()
            except Exception:
                pass
            logs.append(f"[SYSTEM] Ephemeral container validation timed out after {timeout} seconds.")
            
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        
        duration = asyncio.get_event_loop().time() - t0
        
        return proc.returncode if proc.returncode is not None else -1, logs

    @classmethod
    async def run_daemon_container(
        cls,
        workspace_dir: str,
        image_name: str,
        commands: List[str],
        container_name: str,
        memory_limit: str = "1.5g",
        cpu_limit: float = 1.0,
        run_duration: float = 7.0
    ) -> Tuple[int, List[str]]:
        """
        Launches a detached Docker container, lets it run for run_duration,
        reads its logs, stops, and removes the container.
        """
        mount_path = os.path.abspath(workspace_dir).replace("\\", "/")
        sh_command = " && ".join(commands)
        
        # Ensure any pre-existing container with the same name is removed
        try:
            cleanup_proc = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await cleanup_proc.wait()
        except Exception:
            pass

        docker_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "bridge",
            "-m", memory_limit,
            "--cpus", str(cpu_limit),
            "-v", f"{mount_path}:/workspace",
            "-w", "/workspace",
            image_name,
            "sh", "-c", sh_command
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            err_msg = stderr.decode('utf-8', errors='ignore')
            return proc.returncode if proc.returncode is not None else -1, [f"[SYSTEM] Failed to start daemon: {err_msg}"]

        # Let the container run and sniff dev logs
        await asyncio.sleep(run_duration)

        # Get logs
        logs_proc = await asyncio.create_subprocess_exec(
            "docker", "logs", container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logs_stdout, logs_stderr = await logs_proc.communicate()
        
        logs = []
        for line in logs_stdout.decode('utf-8', errors='ignore').splitlines():
            logs.append(f"[STDOUT] {line}")
        for line in logs_stderr.decode('utf-8', errors='ignore').splitlines():
            logs.append(f"[STDERR] {line}")

        # Stop and remove container
        stop_proc = await asyncio.create_subprocess_exec(
            "docker", "rm", "-f", container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await stop_proc.wait()

        return 0, logs

