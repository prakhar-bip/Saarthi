import json
from loguru import logger
from typing import Dict, Any, List
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class EntityGenerationPlannerAgent:
    """
    Entity Generation Planner Agent for Sarthi.
    Analyzes entities list and relations to compute a dependency graph,
    designing parallelizable topological compilation batches.
    """

    def __init__(self) -> None:
        self.agent_name = "EntityGenerationPlannerAgent"

    async def plan(self, entities_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Plan topological generation schedules for discovered entities."""
        agent_inputs = {"entities_dict": entities_dict}

        # Check for API keys
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("No LLM API keys configured. Using fallback generation plan.")
            return enrich_agent_output(
                self._get_fallback_plan(entities_dict),
                self.agent_name,
                agent_inputs,
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are Sarthi's Principal AI Systems Scheduler. Your job is to read entity contracts "
                "and design a deterministic topological generation sequence. Group independent entities "
                "into concurrent batches, while routing dependent entities into subsequent batches.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown formatting fences, no explanations.\n"
                "- generation_order must contain all entities.\n"
                "- parallel_groups is a list of lists of entity names that can be generated concurrently.\n"
            ),
        )

        user_content = f"""
        Discovered Entity List:
        {json.dumps(entities_dict, indent=2)}

        Analyze each entity and its relationships. Create:
        1. generation_order: Sequential topological order from least dependent to most dependent.
        2. parallel_groups: Group entities into batches. Entities inside a batch should have no dependencies on each other.
        3. blocking_dependencies: List blocking relations (e.g. Task depends on User).

        Return ONLY valid JSON in this exact structure:
        {{
          "generation_order": ["User", "Notification", "Task"],
          "parallel_groups": [
            ["User", "Notification"],
            ["Task"]
          ],
          "blocking_dependencies": [
            {{"entity": "Task", "depends_on": ["User"]}}
          ]
        }}
        """

        try:
            logger.info("[EntityGenerationPlanner] Planning topological generation schedules...")
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            raw_response = raw_response.strip()
            parsed = parse_json_response(raw_response)
            logger.info(f"[EntityGenerationPlanner] Generation plan created with {len(parsed.get('parallel_groups', []))} batches.")
            return enrich_agent_output(parsed, self.agent_name, agent_inputs)
        except Exception as e:
            logger.error(f"Failed to run EntityGenerationPlannerAgent: {e}. Executing fallback.")
            return enrich_agent_output(
                self._get_fallback_plan(entities_dict),
                self.agent_name,
                agent_inputs,
            )

    def _get_fallback_plan(self, entities_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Topological fallback planner when LLM call is unavailable."""
        entities = entities_dict.get("entities", [])
        
        # Build dependency list deterministically
        generation_order = []
        blocking_dependencies = []
        
        # Parse basic relationships
        for e in entities:
            name = e["name"]
            generation_order.append(name)
            relationships = e.get("relationships", []) or []
            for rel in relationships:
                to_entity = rel.get("to_entity")
                rel_type = rel.get("type", "")
                if to_entity and to_entity != name:
                    # If this entity has a many-to-one relationship, it depends on the parent
                    if rel_type == "many-to-one":
                        blocking_dependencies.append({
                            "entity": name,
                            "depends_on": [to_entity]
                        })
                    # Or parent has a one-to-many to children, which means children depend on parent
                    elif rel_type == "one-to-many":
                        blocking_dependencies.append({
                            "entity": to_entity,
                            "depends_on": [name]
                        })

        # Calculate a simple 2-batch parallel group (Batch 1: no dependencies, Batch 2: dependent entities)
        dependent_entities = set()
        for dep in blocking_dependencies:
            dependent_entities.add(dep["entity"])

        batch1 = [e["name"] for e in entities if e["name"] not in dependent_entities]
        batch2 = [e["name"] for e in entities if e["name"] in dependent_entities]

        parallel_groups = []
        if batch1:
            parallel_groups.append(batch1)
        if batch2:
            parallel_groups.append(batch2)

        # Make sure generation_order matches groupings
        final_order = []
        for g in parallel_groups:
            final_order.extend(g)

        return {
            "generation_order": final_order,
            "parallel_groups": parallel_groups,
            "blocking_dependencies": blocking_dependencies,
        }
