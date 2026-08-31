import json
from typing import Dict, Any, List

from app.services.llm_router import get_llm_completion
from app.agents.context import parse_json_response, AGENT_ROLES


class SurgicalGapFiller:
    """Surgical Gap Filler for the Saarthi multi-agent pipeline.
    
    Generates ONLY the missing items identified by ContractAuditor,
    using a compact targeted LLM call (max_tokens=2000) to avoid
    truncation and keep the operation fast (~2-4 seconds).
    """

    @staticmethod
    def _summarize_existing(output: Dict[str, Any]) -> str:
        """Create a compact summary of what already exists in the output."""
        summary = []
        for key, value in output.items():
            if key in ("agent_handoff", "status"):
                continue
            if isinstance(value, list):
                count = len(value)
                names = []
                for item in value[:5]:
                    if isinstance(item, dict):
                        name = (
                            item.get("entity_name")
                            or item.get("page_name")
                            or item.get("component_name")
                            or item.get("name")
                            or item.get("path")
                            or str(item)[:40]
                        )
                        names.append(str(name))
                    else:
                        names.append(str(item)[:30])
                summary.append(f"- {key}: {count} items [{', '.join(names)}]")
            elif isinstance(value, dict):
                summary.append(f"- {key}: dict with keys [{', '.join(list(value.keys())[:6])}]")
            elif isinstance(value, str) and len(value) > 50:
                summary.append(f"- {key}: present ({len(value)} chars)")
            else:
                summary.append(f"- {key}: {str(value)[:60]}")
        return "\n".join(summary) if summary else "No existing items."

    @staticmethod
    async def fill_gaps(
        agent_name: str,
        gaps: List[str],
        existing_output: Dict[str, Any],
        project_doc: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate ONLY the missing items identified by the ContractAuditor.
        
        Uses a compact targeted LLM call (max_tokens=2000) to avoid truncation.
        Returns a delta dict with the missing items, or {} on failure.
        """
        try:
            if not gaps:
                return {}

            agent_role = AGENT_ROLES.get(agent_name, f"Architecture agent for {agent_name}")
            existing_summary = SurgicalGapFiller._summarize_existing(existing_output)

            # Extract requirements (the master source of truth)
            requirements = project_doc.get("requirements", {})
            if isinstance(requirements, dict):
                requirements_str = json.dumps(requirements, default=str)[:4000]
            else:
                requirements_str = str(requirements)[:4000]

            # Extract TRD document
            trd_doc = project_doc.get("trd", "")
            if isinstance(trd_doc, dict):
                trd_doc = json.dumps(trd_doc, default=str)
            trd_str = str(trd_doc)[:3000] if trd_doc else "No TRD available."

            system_prompt = (
                "You are Sarthi's Contract Gap Filler — a precision surgical code architect.\n"
                "You must generate ONLY the missing items listed below.\n"
                "Do NOT regenerate any items that already exist in the current output.\n"
                "Return ONLY valid JSON containing the missing items in the SAME schema "
                "as the original agent output. Keep descriptions concise (max 15 words each)."
            )

            user_prompt = (
                f"Agent: {agent_name}\n"
                f"Agent Role: {agent_role}\n\n"
                f"MISSING ITEMS (Gaps to fill):\n{json.dumps(gaps, indent=2)}\n\n"
                f"ALREADY EXISTS (Do NOT regenerate):\n{existing_summary}\n\n"
                f"MASTER REQUIREMENTS:\n{requirements_str}\n\n"
                f"TRD:\n{trd_str}\n\n"
                f"Generate ONLY the missing items as valid JSON. Output ONLY JSON."
            )


            response_text = await get_llm_completion(
                agent_name=f"{agent_name}_GapFiller",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            if not response_text:
                return {}

            delta_dict = parse_json_response(response_text)
            if not isinstance(delta_dict, dict):
                return {}

            return delta_dict

        except Exception as e:
            return {}
