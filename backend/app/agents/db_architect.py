import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

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
            "Design the database architecture layer for backend, API, authentication, frontend, state, testing, and validation agents."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "database_strategy": {{
    "primary_database": "PostgreSQL / MongoDB / etc.",
    "secondary_databases": [],
    "cache_layer": "Redis / Memcached / None",
    "vector_database": "Pinecone / pgvector / None",
    "database_reasoning": ["Reason 1"]
  }},
  "entities": [
    {{
      "entity_name": "User",
      "entity_type": "Table / Collection",
      "description": "User profile table",
      "fields": [
        {{
          "name": "id",
          "type": "UUID / String / Integer",
          "required": true,
          "unique": true,
          "indexed": true,
          "default": "uuid_generate_v4()"
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "from_entity": "User",
      "to_entity": "Portfolio",
      "relationship_type": "One-to-Many / One-to-One",
      "description": "A user has one or more portfolios"
    }}
  ],
  "authentication_storage": {{
    "required": true,
    "auth_entities": ["User"],
    "security_requirements": ["Hash passwords using bcrypt", "Encrypt refresh tokens"],
    "token_storage_strategy": "Store active JWT refresh tokens in Redis cache"
  }},
  "indexing_strategy": {{
    "indexes": ["idx_users_email"],
    "search_optimization": [],
    "vector_indexes": []
  }},
  "realtime_architecture": {{
    "required": false,
    "sync_strategy": [],
    "event_driven_entities": []
  }},
  "scalability_strategy": {{
    "horizontal_scaling": false,
    "sharding_required": false,
    "high_write_load_entities": [],
    "caching_targets": []
  }},
  "backend_integration_context": {{
    "important_models": ["UserModel", "PortfolioModel"],
    "service_dependencies": [],
    "repository_patterns": ["UserRepository", "PortfolioRepository"]
  }},
  "api_integration_context": {{
    "crud_entities": ["User", "Portfolio"],
    "protected_entities": ["Portfolio"],
    "high_frequency_routes": ["GET /api/portfolio/stats"]
  }},
  "frontend_data_contracts": {{
    "stateful_entities": ["User", "Portfolio"],
    "realtime_entities": [],
    "dashboard_entities": ["Portfolio"]
  }},
  "workflow_mappings": [
    {{
      "workflow": "User registration",
      "database_interactions": ["Insert into User table"]
    }}
  ],
  "future_agent_context": {{
    "important_notes_for_backend_agents": ["Implement soft deletes on User table"],
    "important_notes_for_api_agents": [],
    "important_notes_for_frontend_agents": []
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
        realtime_req = planning.get("realtime_architecture", {}).get("required", False)
        overview = requirements.get("project_overview", {})
        name = overview.get("name", "FinSight")
        tech_stack = requirements.get("tech_stack", {})
        db_req = requirements.get("database_requirements", {})
        entities = db_req.get("entities", ["User", "Portfolio", "Asset", "Transaction"])
        
        # Detect database type
        db_list = tech_stack.get("database", [])
        primary_db = db_list[0] if db_list else "PostgreSQL"
        
        cache = "None"
        for tech in tech_stack.get("backend", []) + tech_stack.get("database", []):
            if "redis" in tech.lower():
                cache = "Redis"
                
        # Detect if SQL
        is_sql = "postgre" in primary_db.lower() or "mysql" in primary_db.lower() or "sqlite" in primary_db.lower()
        entity_type = "Table" if is_sql else "Collection"
        id_type = "UUID" if is_sql else "ObjectID"
        
        fields_map = {
            "User": [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()"},
                {"name": "email", "type": "String", "required": True, "unique": True, "indexed": True, "default": None},
                {"name": "password_hash", "type": "String", "required": True, "unique": False, "indexed": False, "default": None},
                {"name": "name", "type": "String", "required": True, "unique": False, "indexed": False, "default": None},
                {"name": "created_at", "type": "DateTime", "required": True, "unique": False, "indexed": False, "default": "Now()"}
            ],
            "Portfolio": [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()"},
                {"name": "user_id", "type": id_type, "required": True, "unique": False, "indexed": True, "default": None},
                {"name": "name", "type": "String", "required": True, "unique": False, "indexed": False, "default": "'Default Portfolio'"},
                {"name": "risk_score", "type": "Integer", "required": False, "unique": False, "indexed": False, "default": "5"},
                {"name": "created_at", "type": "DateTime", "required": True, "unique": False, "indexed": False, "default": "Now()"}
            ],
            "Asset": [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()"},
                {"name": "portfolio_id", "type": id_type, "required": True, "unique": False, "indexed": True, "default": None},
                {"name": "ticker", "type": "String", "required": True, "unique": False, "indexed": True, "default": None},
                {"name": "shares", "type": "Decimal", "required": True, "unique": False, "indexed": False, "default": "0.0"},
                {"name": "avg_buy_price", "type": "Decimal", "required": True, "unique": False, "indexed": False, "default": "0.0"}
            ],
            "Transaction": [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()"},
                {"name": "user_id", "type": id_type, "required": True, "unique": False, "indexed": True, "default": None},
                {"name": "amount", "type": "Decimal", "required": True, "unique": False, "indexed": False, "default": None},
                {"name": "type", "type": "String", "required": True, "unique": False, "indexed": False, "default": None},
                {"name": "timestamp", "type": "DateTime", "required": True, "unique": False, "indexed": True, "default": "Now()"}
            ]
        }
        
        fallback_entities = []
        for ent in entities:
            fields = fields_map.get(ent, [
                {"name": "id", "type": id_type, "required": True, "unique": True, "indexed": True, "default": "GenUUID()"},
                {"name": "name", "type": "String", "required": True, "unique": False, "indexed": False, "default": None},
                {"name": "created_at", "type": "DateTime", "required": True, "unique": False, "indexed": False, "default": "Now()"}
            ])
            fallback_entities.append({
                "entity_name": ent,
                "entity_type": entity_type,
                "description": f"Stores details for project entity {ent}.",
                "fields": fields
            })
            
        relationships = [
            {
                "from_entity": "User",
                "to_entity": "Portfolio",
                "relationship_type": "One-to-Many",
                "description": "A user can have multiple investment portfolios."
            },
            {
                "from_entity": "Portfolio",
                "to_entity": "Asset",
                "relationship_type": "One-to-Many",
                "description": "A portfolio owns multiple asset holdings."
            },
            {
                "from_entity": "User",
                "to_entity": "Transaction",
                "relationship_type": "One-to-Many",
                "description": "A user records multiple micro-savings transactions."
            }
        ]

        return {
            "status": "success",
            "database_strategy": {
                "primary_database": primary_db,
                "secondary_databases": [],
                "cache_layer": "Redis" if cache == "Redis" else "None",
                "vector_database": "None",
                "database_reasoning": [
                    f"Selected {primary_db} to provide robust transaction handling and data integrity.",
                    "Configured Redis cache target tables to ensure fast dashboard rendering."
                ]
            },
            "entities": fallback_entities,
            "relationships": relationships,
            "authentication_storage": {
                "required": True,
                "auth_entities": ["User"],
                "security_requirements": [
                    "Bcrypt hashing for user password storage.",
                    "Enable SSL verification for active database pool."
                ],
                "token_storage_strategy": "Store refresh tokens in Redis with 24-hour expiration."
            },
            "indexing_strategy": {
                "indexes": [
                    "idx_user_email",
                    "idx_portfolio_user",
                    "idx_transaction_timestamp"
                ],
                "search_optimization": [
                    "Full-text search indexed on asset ticker names."
                ],
                "vector_indexes": []
            },
            "realtime_architecture": {
                "required": realtime_req,
                "sync_strategy": ["WebSocket pushes on Transaction insert and leaderboard rank update."] if realtime_req else [],
                "event_driven_entities": ["Transaction"] if realtime_req else []
            },
            "scalability_strategy": {
                "horizontal_scaling": True,
                "sharding_required": False,
                "high_write_load_entities": ["Transaction"],
                "caching_targets": ["Portfolio holdings", "User session profile"]
            },
            "backend_integration_context": {
                "important_models": [f"{e}Model" for e in entities],
                "service_dependencies": ["Database Connection Pool", "Redis Client Pool"],
                "repository_patterns": [f"{e}Repository" for e in entities]
            },
            "api_integration_context": {
                "crud_entities": entities,
                "protected_entities": [e for e in entities if e != "User"],
                "high_frequency_routes": [
                    "GET /api/portfolios",
                    "POST /api/transactions/roundup"
                ]
            },
            "frontend_data_contracts": {
                "stateful_entities": entities,
                "realtime_entities": ["Transaction"],
                "dashboard_entities": ["Portfolio", "Asset"]
            },
            "workflow_mappings": [
                {
                    "workflow": "User risk assessment submission",
                    "database_interactions": ["Update risk_score in Portfolio table."]
                },
                {
                    "workflow": "Micro-savings auto roundup",
                    "database_interactions": ["Insert Transaction record.", "Increment Asset shares or balance."]
                }
            ],
            "future_agent_context": {
                "important_notes_for_backend_agents": [
                    "Use SQLAlchemy or Motor ORM/ODM models with lazy loading on assets relationship."
                ],
                "important_notes_for_api_agents": [
                    "Add JWT validation to all endpoints querying Portfolio or holdings data."
                ],
                "important_notes_for_frontend_agents": [
                    "Dashboard should pool or WebSocket listen to transaction updates."
                ]
            }
        }
