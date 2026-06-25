import json
from loguru import logger
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class EntityDiscoveryAgent:
    """
    Entity Discovery Agent for Sarthi.
    Analyzes API architecture, database architecture, frontend architecture, and requirements
    to decompose the project into distinct, isolated entity contracts.
    """

    def __init__(self) -> None:
        self.agent_name = "EntityDiscoveryAgent"

    async def discover(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Decompose specs into distinct, isolated entity contracts."""
        agent_inputs = {
            "requirements": requirements,
            "db_architecture": db_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
        }

        # Check for API keys
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("No LLM API keys configured. Using fallback discovered entities.")
            return enrich_agent_output(
                self._get_fallback_entities(db_architecture, api_architecture),
                self.agent_name,
                agent_inputs,
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are Sarthi's Principal Entity Discovery Engineer. Your job is to analyze "
                "requirements, database design, APIs, and frontend architectures, and decompose them "
                "into distinct, isolated entity contracts.\n\n"
                "An entity represents a core database schema or collection, its associated CRUD APIs, "
                "and its relevant frontend pages and components.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown formatting fences, no explanations, no extra keys.\n"
                "- Ensure every field is fully specified. Do NOT use ellipsis (...) or placeholders.\n"
            ),
        )

        user_content = f"""
        Analyze the following architectures and requirements. Extract distinct, isolated entities.
        For each entity, specify fields, relationships (e.g. to_entity, type: 'one-to-many' / 'many-to-one'),
        its CRUD APIs, and its associated frontend pages/views.

        Requirements: {json.dumps(requirements, indent=2)}
        Database Architecture: {json.dumps(db_architecture, indent=2)}
        API Architecture: {json.dumps(api_architecture, indent=2)}
        Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}

        Return ONLY valid JSON in this exact structure:
        {{
          "entities": [
            {{
              "name": "EntityName (PascalCase, e.g., 'User', 'Task', 'Notification')",
              "fields": [
                {{"name": "field_name", "type": "string|integer|boolean|datetime", "required": true, "indexed": false}}
              ],
              "relationships": [
                {{"to_entity": "TargetEntityName", "type": "one-to-many|many-to-one|one-to-one", "inverse": "field_name"}}
              ],
              "apis": [
                {{"method": "POST|GET|PUT|DELETE", "path": "/api/v1/endpoints", "handler": "handler_function_name", "requires_auth": true}}
              ],
              "frontend_pages": [
                {{"name": "PageName", "route": "/dashboard/items", "protected": true}}
              ]
            }}
          ]
        }}
        """

        try:
            logger.info("[EntityDiscovery] Running LLM Entity Discovery...")
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
            logger.info(f"[EntityDiscovery] Successfully discovered {len(parsed.get('entities', []))} entities.")
            return enrich_agent_output(parsed, self.agent_name, agent_inputs)
        except Exception as e:
            logger.error(f"Failed to run EntityDiscoveryAgent: {e}. Executing fallback.")
            return enrich_agent_output(
                self._get_fallback_entities(db_architecture, api_architecture),
                self.agent_name,
                agent_inputs,
            )

    def _get_fallback_entities(self, db_arch: Dict, api_arch: Dict) -> Dict[str, Any]:
        """Provide a clean fallback structure of basic entities if discovery fails."""
        # Try to extract from DB architecture collections
        entities = []
        db_schemas = db_arch.get("schemas", {}) or db_arch.get("collections", {}) or {}
        
        if not db_schemas:
            # Absolute fallback
            return {
                "entities": [
                    {
                        "name": "User",
                        "fields": [
                            {"name": "id", "type": "string", "required": True, "indexed": True},
                            {"name": "email", "type": "string", "required": True, "indexed": True},
                            {"name": "name", "type": "string", "required": False, "indexed": False},
                        ],
                        "relationships": [],
                        "apis": [
                            {"method": "POST", "path": "/api/v1/users", "handler": "create_user", "requires_auth": False},
                            {"method": "GET", "path": "/api/v1/users/me", "handler": "get_current_user", "requires_auth": True},
                        ],
                        "frontend_pages": [
                            {"name": "UserProfile", "route": "/dashboard/profile", "protected": True}
                        ]
                    },
                    {
                        "name": "Task",
                        "fields": [
                            {"name": "id", "type": "string", "required": True, "indexed": True},
                            {"name": "title", "type": "string", "required": True, "indexed": False},
                            {"name": "description", "type": "string", "required": False, "indexed": False},
                            {"name": "status", "type": "string", "required": True, "indexed": True},
                            {"name": "user_id", "type": "string", "required": True, "indexed": True},
                        ],
                        "relationships": [
                            {"to_entity": "User", "type": "many-to-one", "inverse": "tasks"}
                        ],
                        "apis": [
                            {"method": "GET", "path": "/api/v1/tasks", "handler": "get_tasks", "requires_auth": True},
                            {"method": "POST", "path": "/api/v1/tasks", "handler": "create_task", "requires_auth": True},
                        ],
                        "frontend_pages": [
                            {"name": "TaskDashboard", "route": "/dashboard/tasks", "protected": True}
                        ]
                    }
                ]
            }

        # Dynamically map entities from DB schema structure
        for name, schema in db_schemas.items():
            fields = []
            props = schema.get("properties", {}) or schema.get("fields", {}) or {}
            for f_name, f_info in props.items():
                f_type = "string"
                if isinstance(f_info, dict):
                    f_type = f_info.get("type", "string")
                elif isinstance(f_info, str):
                    f_type = f_info
                fields.append({
                    "name": f_name,
                    "type": f_type,
                    "required": f_name in schema.get("required", []),
                    "indexed": f_name in ("id", "_id", "email", "user_id"),
                })

            # Match matching endpoints
            apis = []
            endpoints = api_arch.get("endpoints", []) or []
            var_name = name.lower()
            for ep in endpoints:
                path = ep.get("path", "")
                if f"/{var_name}" in path or f"/{name.lower()}" in path:
                    apis.append({
                        "method": ep.get("method", "GET"),
                        "path": path,
                        "handler": ep.get("handler", f"handle_{var_name}"),
                        "requires_auth": ep.get("requires_auth", True),
                    })

            entities.append({
                "name": name,
                "fields": fields,
                "relationships": [],
                "apis": apis if apis else [{"method": "GET", "path": f"/api/v1/{var_name}s", "handler": f"get_{var_name}s", "requires_auth": True}],
                "frontend_pages": [
                    {"name": f"{name}Dashboard", "route": f"/dashboard/{var_name}s", "protected": True}
                ]
            })

        return {"entities": entities}
