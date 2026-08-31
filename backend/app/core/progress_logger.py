import os
import sys
import asyncio
import contextvars
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

# Safe console output on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# Context Variables — Thread-safe & Async-safe execution context
# ─────────────────────────────────────────────────────────────────────────────
_current_project_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_project_id", default=None)
_current_agent_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_agent_name", default=None)
_current_phase_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_phase_name", default=None)
_current_step_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_step_name", default=None)
_current_step_index: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("current_step_index", default=None)
_current_total_steps: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("current_total_steps", default=18)
_current_model_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_model_name", default=None)

# ─────────────────────────────────────────────────────────────────────────────
# ANSI Color Codes for Terminal Output
# ─────────────────────────────────────────────────────────────────────────────
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

LEVEL_COLORS = {
    "INFO": Colors.BRIGHT_BLUE,
    "SUCCESS": Colors.BRIGHT_GREEN,
    "WARNING": Colors.BRIGHT_YELLOW,
    "ERROR": Colors.BRIGHT_RED,
    "DEBUG": Colors.DIM,
    "STEP": Colors.BRIGHT_YELLOW,
    "AGENT": Colors.BRIGHT_CYAN,
    "HEAL": Colors.BRIGHT_CYAN,
    "BACKTRACK": Colors.BRIGHT_MAGENTA,
    "PHASE": Colors.BRIGHT_MAGENTA,
    "MODEL": Colors.MAGENTA,
}

LEVEL_ICONS = {
    "INFO": "[INFO]",
    "SUCCESS": "[OK]",
    "WARNING": "[WARN]",
    "ERROR": "[ERR]",
    "DEBUG": "[DEBUG]",
    "STEP": "[STEP]",
    "AGENT": "[AGENT]",
    "HEAL": "[HEAL]",
    "BACKTRACK": "[BACKTRACK]",
    "PHASE": "[PHASE]",
    "MODEL": "[MODEL]",
}


class ProgressLogger:
    """
    Next-Gen Progress & Execution Logging System.
    Dispatches rich structured progress events to:
      1. Terminal Console (Colorized & Structured)
      2. Connected WebSockets (Live UI Terminal & File Stream)
      3. MongoDB (Persistent project compilation logs)
    """

    @classmethod
    def set_context(
        cls,
        project_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        phase_name: Optional[str] = None,
        step_name: Optional[str] = None,
        step_index: Optional[int] = None,
        total_steps: Optional[int] = None,
        model_name: Optional[str] = None,
    ):
        """Sets active execution context for automatic log enrichment."""
        if project_id is not None:
            _current_project_id.set(project_id)
        if agent_name is not None:
            _current_agent_name.set(agent_name)
        if phase_name is not None:
            _current_phase_name.set(phase_name)
        if step_name is not None:
            _current_step_name.set(step_name)
        if step_index is not None:
            _current_step_index.set(step_index)
        if total_steps is not None:
            _current_total_steps.set(total_steps)
        if model_name is not None:
            _current_model_name.set(model_name)

    @classmethod
    def get_project_id(cls) -> Optional[str]:
        return _current_project_id.get()

    @classmethod
    def _dispatch(
        cls,
        level: str,
        message: str,
        project_id: Optional[str] = None,
        agent: Optional[str] = None,
        step: Optional[str] = None,
        phase: Optional[str] = None,
        model: Optional[str] = None,
        execution: Optional[Dict[str, Any]] = None,
        failure: Optional[Dict[str, Any]] = None,
        broadcast: bool = True,
    ):
        """Internal dispatcher that outputs to console, WebSocket, and MongoDB."""
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        full_time_str = now.strftime("%H:%M:%S.%f")[:-3]

        proj_id = project_id or _current_project_id.get()
        active_agent = agent or _current_agent_name.get() or "System"
        active_step = step or _current_step_name.get()
        active_phase = phase or _current_phase_name.get()
        active_model = model or _current_model_name.get()

        # 1. Console Output
        lvl_color = LEVEL_COLORS.get(level, Colors.WHITE)
        icon = LEVEL_ICONS.get(level, "")
        
        meta_parts = []
        if active_agent and active_agent != "System":
            meta_parts.append(f"{Colors.CYAN}[{active_agent}]{Colors.RESET}")
        if active_step:
            step_idx = _current_step_index.get()
            tot_steps = _current_total_steps.get() or 18
            if step_idx is not None:
                meta_parts.append(f"{Colors.YELLOW}[Step {step_idx}/{tot_steps}: {active_step}]{Colors.RESET}")
            else:
                meta_parts.append(f"{Colors.YELLOW}[{active_step}]{Colors.RESET}")
        if active_model:
            meta_parts.append(f"{Colors.MAGENTA}[{active_model}]{Colors.RESET}")

        meta_str = " " + " ".join(meta_parts) if meta_parts else ""
        badge = f"{lvl_color}{Colors.BOLD}[{level:^7}]{Colors.RESET}"
        timestamp_formatted = f"{Colors.DIM}{time_str}{Colors.RESET}"

        exec_suffix = ""
        if execution and isinstance(execution, dict):
            parts = []
            dur = execution.get("duration_sec")
            toks = execution.get("total_tokens")
            if dur is not None:
                parts.append(f"{dur:.2f}s")
            if toks is not None:
                parts.append(f"{toks} tokens")
            if parts:
                exec_suffix = f" {Colors.DIM}({' | '.join(parts)}){Colors.RESET}"

        failure_suffix = ""
        if failure and isinstance(failure, dict):
            err_type = failure.get("error_type", "Error")
            action = failure.get("action")
            f_parts = [err_type]
            if action:
                f_parts.append(f"action: {action}")
            failure_suffix = f"\n  {Colors.RED}↳ { ' | '.join(f_parts) }{Colors.RESET}"
            if failure.get("details"):
                failure_suffix += f"\n  {Colors.DIM}↳ {str(failure['details'])[:200]}{Colors.RESET}"

        try:
            print(f"{timestamp_formatted} {badge}{meta_str} {icon} {message}{exec_suffix}{failure_suffix}")
        except Exception:
            try:
                # Fallback to plain ascii output if terminal cannot print unicode
                clean_msg = message.encode("ascii", errors="replace").decode("ascii")
                print(f"{time_str} [{level:^7}] {clean_msg}")
            except Exception:
                pass

        # 2. Build standard payload matching frontend expectations
        payload = {
            "type": "log",
            "date": date_str,
            "time": full_time_str,
            "timestamp": time_str,
            "tag": level,
            "level": level,
            "project_id": proj_id,
            "agent": active_agent,
            "sender": active_agent,
            "step": active_step,
            "phase": active_phase,
            "model": active_model,
            "message": message,
            "execution": execution,
            "failure": failure,
        }

        # 3. Async Sinks (WebSocket broadcast + MongoDB persistence)
        if proj_id and broadcast:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # 3a. WebSocket Broadcast
                    try:
                        from app.services.ws_manager import manager
                        loop.create_task(manager.broadcast_to_project(proj_id, payload))
                    except Exception:
                        pass

                    # 3b. MongoDB Persistence
                    try:
                        from app.db.mongodb import get_database
                        db = get_database()
                        if db is not None:
                            loop.create_task(db.projects.update_one(
                                {"_id": proj_id},
                                {"$push": {"compilation_logs": payload}}
                            ))
                    except Exception:
                        pass
            except RuntimeError:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    # Public Logging API
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def info(cls, message: str, project_id: Optional[str] = None, agent: Optional[str] = None, **kwargs):
        cls._dispatch("INFO", message, project_id=project_id, agent=agent, **kwargs)

    @classmethod
    def success(cls, message: str, project_id: Optional[str] = None, agent: Optional[str] = None, **kwargs):
        cls._dispatch("SUCCESS", message, project_id=project_id, agent=agent, **kwargs)

    @classmethod
    def warning(cls, message: str, project_id: Optional[str] = None, agent: Optional[str] = None, **kwargs):
        cls._dispatch("WARNING", message, project_id=project_id, agent=agent, **kwargs)

    @classmethod
    def error(cls, message: str, project_id: Optional[str] = None, agent: Optional[str] = None, **kwargs):
        cls._dispatch("ERROR", message, project_id=project_id, agent=agent, **kwargs)

    @classmethod
    def debug(cls, message: str, project_id: Optional[str] = None, agent: Optional[str] = None, **kwargs):
        cls._dispatch("DEBUG", message, project_id=project_id, agent=agent, **kwargs)

    @classmethod
    def phase(cls, phase_title: str, icon: str = "[PHASE]", project_id: Optional[str] = None):
        """Logs high-level SDLC phase transitions."""
        _current_phase_name.set(phase_title)
        line = "=" * 60
        cls._dispatch(
            "PHASE",
            f"\n{line}\n  {icon}  PHASE: {phase_title.upper()}\n{line}",
            project_id=project_id,
            phase=phase_title,
        )

    @classmethod
    def step(cls, step_idx: int, total_steps: int, name: str, description: str, project_id: Optional[str] = None):
        """Records a LangGraph pipeline stage step transition."""
        _current_step_index.set(step_idx)
        _current_total_steps.set(total_steps)
        _current_step_name.set(name)
        cls._dispatch(
            "STEP",
            f"Entering pipeline step [{step_idx}/{total_steps}]: {description}",
            project_id=project_id,
            step=name,
        )

    @classmethod
    def agent_start(cls, agent_name: str, task: str, model: Optional[str] = None, project_id: Optional[str] = None):
        """Logs the start of an agent execution."""
        _current_agent_name.set(agent_name)
        if model:
            _current_model_name.set(model)
        cls._dispatch(
            "AGENT",
            f"Started work: {task}",
            project_id=project_id,
            agent=agent_name,
            model=model,
        )

    @classmethod
    def agent_success(
        cls,
        agent_name: str,
        message: str,
        duration_sec: Optional[float] = None,
        total_tokens: Optional[int] = None,
        project_id: Optional[str] = None,
    ):
        """Logs successful agent completion with execution metrics."""
        exec_data = {}
        if duration_sec is not None:
            exec_data["duration_sec"] = duration_sec
        if total_tokens is not None:
            exec_data["total_tokens"] = total_tokens
        cls._dispatch(
            "SUCCESS",
            f"[{agent_name}] {message}",
            project_id=project_id,
            agent=agent_name,
            execution=exec_data if exec_data else None,
        )

    @classmethod
    def agent_failure(
        cls,
        agent_name: str,
        error: Union[str, Exception],
        retry_count: int = 0,
        recovery_action: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """Logs failure diagnostics for an agent."""
        failure_dict = {
            "error_type": error.__class__.__name__ if isinstance(error, Exception) else "ExecutionError",
            "details": str(error),
            "retry_count": retry_count,
            "action": recovery_action or "Initiating retry / auto-heal",
        }
        cls._dispatch(
            "ERROR",
            f"[{agent_name}] Attempt {retry_count} failed: {str(error)[:200]}",
            project_id=project_id,
            agent=agent_name,
            failure=failure_dict,
        )

    @classmethod
    def file_generated(cls, file_path: str, char_count: Optional[int] = None, project_id: Optional[str] = None):
        """
        Logs individual generated code file.
        Formats file paths so frontend live explorer immediately detects and populates them.
        """
        size_info = f" ({char_count} chars)" if char_count is not None else ""
        cls._dispatch(
            "SUCCESS",
            f"Synthesized file: {file_path}{size_info}",
            project_id=project_id,
            agent=_current_agent_name.get() or "CodeSynthesizer",
        )

    @classmethod
    def heal(
        cls,
        agent_name: str,
        file_path: str,
        issue: str,
        resolution: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """Logs code auto-healing / repair events."""
        res_text = f" | Resolution: {resolution}" if resolution else ""
        cls._dispatch(
            "HEAL",
            f"Repaired {file_path} -> Issue: {issue}{res_text}",
            project_id=project_id,
            agent=agent_name,
        )

    @classmethod
    def backtrack(
        cls,
        responsible_agent: str,
        target_workspace: str,
        depth: int,
        reason: str,
        project_id: Optional[str] = None,
    ):
        """Logs SDLC spiral backtrack / regeneration routing."""
        failure_dict = {
            "error_type": "BacktrackTriggered",
            "details": reason,
            "action": f"Re-enter {target_workspace}",
        }
        cls._dispatch(
            "BACKTRACK",
            f"Depth {depth} -> Scoped re-entry at '{target_workspace}' due to {reason}",
            project_id=project_id,
            agent=responsible_agent,
            failure=failure_dict,
        )

    @classmethod
    def llm_call(
        cls,
        agent_name: str,
        provider: str,
        model: str,
        latency_sec: float,
        input_len: int,
        output_len: int,
        status: str,
        error: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """Logs LLM API call metrics, model name, tokens, and latency."""
        est_prompt_tokens = int(input_len / 4)
        est_completion_tokens = int(output_len / 4)
        total_tokens = est_prompt_tokens + est_completion_tokens

        exec_dict = {
            "duration_sec": latency_sec,
            "prompt_tokens": est_prompt_tokens,
            "completion_tokens": est_completion_tokens,
            "total_tokens": total_tokens,
        }

        if status == "SUCCESS":
            cls._dispatch(
                "MODEL",
                f"LLM Success ({latency_sec:.2f}s, ~{total_tokens} toks) [{provider.upper()} -> {model}]",
                project_id=project_id,
                agent=agent_name,
                model=f"{provider.upper()}/{model}",
                execution=exec_dict,
            )
        else:
            failure_dict = {
                "error_type": "LLMProviderError",
                "details": error or "Unknown provider error",
                "action": "Cascading to fallback provider",
            }
            cls._dispatch(
                "WARNING",
                f"LLM Failed ({latency_sec:.2f}s) on [{provider.upper()} -> {model}]: {error}",
                project_id=project_id,
                agent=agent_name,
                model=f"{provider.upper()}/{model}",
                execution=exec_dict,
                failure=failure_dict,
            )


# Singleton instance alias
progress_logger = ProgressLogger
