from typing import Any, Tuple, Dict
from loguru import logger
from app.agents.context import IncompleteJSONError

class VerifierAgent:
    """
    VerifierAgent checks the output of upstream agents for completeness and validity.
    It returns a tuple: (is_complete, feedback)
    """
    def __init__(self):
        self.agent_name = "VerifierAgent"

    async def verify(self, agent_name: str, agent_output: Any) -> Tuple[bool, str]:
        """
        Evaluate if the output is complete.
        If it's an IncompleteJSONError, it means the LLM truncated the JSON.
        If it's a dict, we can do semantic checks if needed.
        """
        if isinstance(agent_output, IncompleteJSONError):
            logger.warning(f"[VerifierAgent] {agent_name} output was truncated. Requesting retry.")
            # We don't append the raw output in the feedback directly if it's too large,
            # but we tell the LLM exactly what went wrong.
            feedback = (
                f"Your previous JSON response was truncated and invalid: {str(agent_output)}. "
                "Please generate the complete JSON object from the beginning. Ensure it is fully closed."
            )
            return False, feedback
            
        if not isinstance(agent_output, dict):
            return False, "Output was not a valid JSON dictionary."
            
        # Basic check to ensure it has a status
        if "status" not in agent_output:
            logger.warning(f"[VerifierAgent] {agent_name} output missing 'status' key.")
            return False, "The generated JSON is missing the required 'status' key. Please ensure it adheres to the requested schema."

        # If it reached here, it's a complete JSON dict that passed parsing!
        logger.info(f"[VerifierAgent] {agent_name} output verified successfully.")
        return True, ""
