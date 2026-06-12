import json
from loguru import logger
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class DatabaseArchitectureAgent:
    """
    DatabaseArchitectureAgent for Sarthi.
    Transforms structured technical requirements and plans into a database architecture layer.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "DatabaseArchitectureAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(self, requirements: Dict[str, Any], planning: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze requirements and planning data to output the database architecture.
        """
        agent_inputs = {"requirements": requirements, "planning": planning}
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback database design.")
            return enrich_agent_output(self._get_fallback_db_architecture(requirements, planning), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior database architect. Design the complete persistence layer: entities, fields, relationships, indexes, caching, and data contracts that all downstream agents will consume.\n\n"
                "## Instructions\n"
                "1. Think step by step: first choose the primary database based on the tech stack, then derive entities from requirements.database_requirements.entities and core_modules, then define fields with proper types and constraints, then map relationships.\n"
                "2. Every entity MUST have: id (primary key), created_at (timestamp). Include foreign key fields for relationships.\n"
                "3. Apply 3NF normalization for relational DBs. For document DBs, design embedded vs referenced patterns explicitly.\n"
                "4. Index all foreign keys and fields used in WHERE/ORDER BY clauses.\n"
                "5. backend_integration_context and api_integration_context are critical contracts — downstream agents rely on these names exactly.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- Entity names must be PascalCase. Field names must be snake_case.\n"
                "- field.type must be one of: UUID, ObjectID, String, Integer, Decimal, Boolean, DateTime, JSON, Text.\n"
                "- relationship_type must be one of: One-to-One, One-to-Many, Many-to-Many."
            )
        )

        user_content = f"""
Design the database architecture for this project. Think step by step:
1. Choose the primary database from requirements.tech_stack.database. Justify the choice.
2. Derive entities from requirements.database_requirements.entities — create complete field definitions for each.
3. Map relationships between entities (include foreign key fields in the child entity).
4. Design indexes for all foreign keys, unique fields, and frequently queried columns.
5. Define integration contracts that downstream BackendArchitectureAgent, APIAgent, and FrontendArchitectureAgent will consume.

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "database_strategy": {{
    "primary_database": "string — exact DB name, e.g. 'PostgreSQL', 'MongoDB', 'SQLite'",
    "secondary_databases": ["string — additional DBs if needed, otherwise []"],
    "cache_layer": "string — 'Redis', 'Memcached', or 'None'",
    "vector_database": "string — 'pgvector', 'Pinecone', or 'None'",
    "database_reasoning": ["string — 1-3 justifications for the database choices"]
  }},
  "entities": [
    {{
      "entity_name": "string — PascalCase entity name",
      "entity_type": "string — 'Table' for SQL, 'Collection' for NoSQL",
      "description": "string — what this entity stores",
      "fields": [
        {{
          "name": "string — snake_case field name",
          "type": "string — one of: UUID, ObjectID, String, Integer, Decimal, Boolean, DateTime, JSON, Text",
          "required": "boolean",
          "unique": "boolean",
          "indexed": "boolean",
          "default": "string or null — default value expression"
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "from_entity": "string — parent entity PascalCase name",
      "to_entity": "string — child entity PascalCase name",
      "relationship_type": "string — 'One-to-One', 'One-to-Many', or 'Many-to-Many'",
      "description": "string — describes the relationship"
    }}
  ],
  "authentication_storage": {{
    "required": "boolean",
    "auth_entities": ["string — entities storing credentials"],
    "security_requirements": ["string — hashing, encryption rules"],
    "token_storage_strategy": "string — where/how tokens are persisted"
  }},
  "indexing_strategy": {{
    "indexes": ["string — index names in format idx_tablename_column"],
    "search_optimization": ["string — full-text or search index descriptions"],
    "vector_indexes": ["string — vector index descriptions, or []"]
  }},
  "realtime_architecture": {{
    "required": "boolean",
    "sync_strategy": ["string — how realtime data sync works"],
    "event_driven_entities": ["string — entities triggering realtime events"]
  }},
  "scalability_strategy": {{
    "horizontal_scaling": "boolean",
    "sharding_required": "boolean",
    "high_write_load_entities": ["string — entities with frequent writes"],
    "caching_targets": ["string — data worth caching"]
  }},
  "backend_integration_context": {{
    "important_models": ["string — ORM model class names: EntityNameModel"],
    "service_dependencies": ["string — infrastructure services needed"],
    "repository_patterns": ["string — repository class names: EntityNameRepository"]
  }},
  "api_integration_context": {{
    "crud_entities": ["string — entities needing CRUD endpoints"],
    "protected_entities": ["string — entities requiring auth to access"],
    "high_frequency_routes": ["string — METHOD /path for frequently called routes"]
  }},
  "frontend_data_contracts": {{
    "stateful_entities": ["string — entities stored in frontend state"],
    "realtime_entities": ["string — entities updated via WebSocket"],
    "dashboard_entities": ["string — entities displayed on dashboards"]
  }},
  "workflow_mappings": [
    {{
      "workflow": "string — user workflow name",
      "database_interactions": ["string — specific DB operations for this workflow"]
    }}
  ],
  "future_agent_context": {{
    "important_notes_for_backend_agents": ["string — ORM/ODM guidance"],
    "important_notes_for_api_agents": ["string — endpoint design notes"],
    "important_notes_for_frontend_agents": ["string — data fetching notes"]
  }}
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
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
            logger.error(f"Failed to run DatabaseArchitectureAgent: {e}")
            return enrich_agent_output(self._get_fallback_db_architecture(requirements, planning), self.agent_name, agent_inputs)

    def _get_fallback_db_architecture(self, requirements: Dict[str, Any], planning: Dict[str, Any]) -> Dict[str, Any]:
        overview = requirements.get("project_overview", {})
        tech_stack = requirements.get("tech_stack", {})
        db_req = requirements.get("database_requirements", {})
        entities = db_req.get("entities", ["User", "Item"])
        
        db_list = tech_stack.get("database", [])
        primary_db = db_list[0] if db_list else "MongoDB"
        
        is_sql = any(db in primary_db.lower() for db in ["postgre", "mysql", "sqlite", "sql"])
        entity_type = "Table" if is_sql else "Collection"
        id_type = "UUID" if is_sql else "ObjectID"
        
        fallback_entities = []
        relationships = []
        
        # Always ensure User is present if auth is required
        auth_req = requirements.get("authentication", {}).get("required", True)
        if auth_req and "User" not in entities:
            entities = ["User"] + [e for e in entities if e != "User"]

        for ent in entities:
            fields = [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()" if is_sql else None},
                {"name": "created_at", "type": "DateTime", "required": True, "unique": False, "indexed": False, "default": "Now()"}
            ]
            
            if ent == "User":
                fields.append({"name": "email", "type": "String", "required": True, "unique": True, "indexed": True, "default": None})
                fields.append({"name": "password_hash", "type": "String", "required": True, "unique": False, "indexed": False, "default": None})
                fields.append({"name": "name", "type": "String", "required": True, "unique": False, "indexed": False, "default": None})
            else:
                fields.append({"name": "name", "type": "String", "required": True, "unique": False, "indexed": False, "default": None})
                if auth_req and "User" in entities:
                    # Link to user
                    fields.append({"name": "user_id", "type": id_type, "required": True, "unique": False, "indexed": True, "default": None})
                    relationships.append({
                        "from_entity": "User",
                        "to_entity": ent,
                        "relationship_type": "One-to-Many",
                        "description": f"A user can own multiple {ent} records."
                    })
            
            fallback_entities.append({
                "entity_name": ent,
                "entity_type": entity_type,
                "description": f"Stores details for project entity {ent}.",
                "fields": fields
            })
            
        return {
            "status": "success",
            "database_strategy": {
                "primary_database": primary_db,
                "secondary_databases": [],
                "cache_layer": "Redis" if any("redis" in str(t).lower() for t in tech_stack.get("backend", []) + tech_stack.get("database", [])) else "None",
                "vector_database": "None",
                "database_reasoning": [
                    f"Selected {primary_db} to match requirements.",
                    "Configured schemas based on project entity requirements."
                ]
            },
            "entities": fallback_entities,
            "relationships": relationships,
            "authentication_storage": {
                "required": auth_req,
                "auth_entities": ["User"] if auth_req else [],
                "security_requirements": ["Bcrypt hashing for user credentials."] if auth_req else [],
                "token_storage_strategy": "Stateless client-side JWT with optional server-side session lookup."
            },
            "indexing_strategy": {
                "indexes": [f"idx_{e.lower()}_id" for e in entities],
                "search_optimization": [],
                "vector_indexes": []
            },
            "realtime_architecture": {
                "required": False,
                "sync_strategy": [],
                "event_driven_entities": []
            },
            "scalability_strategy": {
                "horizontal_scaling": True,
                "sharding_required": False,
                "high_write_load_entities": [],
                "caching_targets": []
            },
            "backend_integration_context": {
                "important_models": [f"{e}Model" for e in entities],
                "service_dependencies": ["Database Connection Pool"],
                "repository_patterns": [f"{e}Repository" for e in entities]
            },
            "api_integration_context": {
                "crud_entities": entities,
                "protected_entities": [e for e in entities if e != "User"],
                "high_frequency_routes": []
            },
            "frontend_data_contracts": {
                "stateful_entities": entities,
                "realtime_entities": [],
                "dashboard_entities": entities
            },
            "workflow_mappings": [],
            "future_agent_context": {
                "important_notes_for_backend_agents": ["Use async repositories connected to primary DB."],
                "important_notes_for_api_agents": ["Verify route access permissions map to roles."],
                "important_notes_for_frontend_agents": ["Perform client-side validation before api fetch."]
            }
        }
