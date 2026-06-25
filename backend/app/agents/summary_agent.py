import json
from loguru import logger
from typing import Dict, Any
from app.services.llm_router import get_llm_completion
from app.agents.context import parse_json_response

class SummaryAgent:
    """
    SummaryAgent compresses large upstream agent outputs into 4-tier storage formats:
    - _full: The original detailed output.
    - _summary: A detailed conceptual summary strictly conforming to architectural word limits.
    - _compressed: An extreme, highly condensed, and dense summary under 200 words.
    - _contracts: A lightweight contract map (schemas, APIs, keys, variables).
    """

    def __init__(self):
        self.agent_name = "SummaryAgent"

    def _get_limit_category(self, agent_name: str) -> tuple:
        """Returns the word limit and category name for a given agent."""
        limits = {
            "RequirementAnalyzerAgent": (1000, "Requirements"),
            "PlannerAgent": (800, "Planning"),
            "ResearchPlanningAgent": (800, "Research"),
            "DatabaseArchitectureAgent": (1200, "Architecture"),
            "BackendArchitectureAgent": (1200, "Architecture"),
            "APIAgent": (1200, "Architecture"),
            "FrontendArchitectureAgent": (1200, "Architecture"),
            "UIUXArchitectAgent": (1200, "Architecture"),
            "AuthArchitectureAgent": (1200, "Architecture"),
            "RealtimeArchitectureAgent": (1200, "Architecture"),
            "StateManagementAgent": (1200, "Architecture"),
            "DevOpsArchitectureAgent": (1200, "Architecture"),
            "SecurityArchitectureAgent": (500, "Security/Validation/Ops"),
            "TestingArchitectureAgent": (500, "Security/Validation/Ops"),
            "ValidationArchitectureAgent": (500, "Security/Validation/Ops"),
            "OptimizationArchitectureAgent": (500, "Security/Validation/Ops"),
        }
        return limits.get(agent_name, (1200, "Architecture"))

    def estimate_tokens(self, text: str) -> int:
        """Fast character-to-token ratio estimation helper (~4 characters per token)."""
        return max(1, len(text) // 4)

    async def summarize(self, target_agent_name: str, agent_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw agent outputs and generates detailed summaries, extreme compressed representations, 
        and lightweight schemas/contracts.
        """
        word_limit, category = self._get_limit_category(target_agent_name)
        
        system_prompt = (
            "You are a Production-Grade Hierarchical Summarization Layer in Saarthi.\n"
            "Your job is to digest a highly detailed JSON configuration file from an upstream agent "
            "and compress it into three clean, standard levels of documentation with zero hallucinations.\n\n"
            "## Requirements:\n"
            f"1. **summary_output**: A structured conceptual summary of the system design and decisions. "
            f"It MUST be strictly under {word_limit} words for this {category} phase.\n"
            "2. **compressed_output**: An extremely condensed, dense, bullet-pointed, or highly abbreviated summary "
            "intended for quick high-level LLM context. It MUST be under 200 words.\n"
            "3. **critical_contracts**: A lightweight dictionary (JSON object) listing only the crucial entities, "
            "endpoints, schema fields, key styling variables, or components. Exclude implementation details, "
            "descriptions, and commentary. Only keep pure identifiers, paths, types, or signatures.\n\n"
            "## Constraints:\n"
            "- Your response must be valid JSON in the specified format.\n"
            "- Do not add explanations, comments, or markdown fences outside the JSON object.\n"
            "- If the original document contains list collections, preserve just their names/schemas in critical_contracts.\n"
        )

        user_prompt = (
            f"Please summarize the following JSON output produced by {target_agent_name}:\n\n"
            f"{json.dumps(agent_output, indent=2)}\n\n"
            "Format your output EXACTLY as this JSON structure:\n"
            "{\n"
            '  "summary_output": "your conceptual summary text here",\n'
            '  "compressed_output": "your ultra-dense under-200-word text here",\n'
            '  "critical_contracts": { ... lightweight dict of endpoints, entities, models, methods ... }\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info(f"[SummaryLayer] Summarizing output for {target_agent_name}...")
        
        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=messages,
                temperature=0.2,
                max_tokens=4000
            )
            parsed_response = parse_json_response(raw_response)
            
            # Default fallbacks if keys are missing
            summary_output = parsed_response.get("summary_output", "")
            compressed_output = parsed_response.get("compressed_output", "")
            critical_contracts = parsed_response.get("critical_contracts", {})
        except Exception as e:
            logger.error(f"[SummaryLayer] Failed to generate summary for {target_agent_name}: {e}. Falling back to default values.")
            summary_output = f"Summary fallback due to error: {str(e)}"
            compressed_output = "Fallback compressed summary."
            critical_contracts = {"fallback": True}

        # Calculate metrics for logging
        original_str = json.dumps(agent_output)
        summary_payload_str = summary_output + compressed_output + json.dumps(critical_contracts)
        
        original_tokens = self.estimate_tokens(original_str)
        summary_tokens = self.estimate_tokens(summary_payload_str)
        compression_ratio = round(summary_tokens / max(1, original_tokens), 2)

        # Print/Log exact required fields for [SummaryLayer]
        from app.services.workflow import get_agent_db_key
        db_key = get_agent_db_key(target_agent_name)
        
        logger.info(
            f"\n"
            f"[SummaryLayer]\n"
            f"Document: {db_key}\n"
            f"Original Tokens: {original_tokens}\n"
            f"Summary Tokens: {summary_tokens}\n"
            f"Compression Ratio: {compression_ratio}\n"
        )

        return {
            "summary_output": summary_output,
            "compressed_output": compressed_output,
            "critical_contracts": critical_contracts
        }
