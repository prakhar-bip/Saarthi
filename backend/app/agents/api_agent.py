import json
from loguru import logger
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class APIAgent:
    """
    APIAgent for Sarthi.
    Designs standard API structures, group routes, specific endpoints, query schemas, and security parameters.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "APIAgent"

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=10.0
        )

    async def design(
        self, 
        requirements: Dict[str, Any], 
        planning: Dict[str, Any], 
        db_architecture: Dict[str, Any], 
        backend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze requirements, plan, db, and backend architecture to output structural API design specs.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback API architecture design.")
            return enrich_agent_output(self._get_fallback_api_architecture(requirements, planning, db_architecture, backend_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior API architect. Design a complete, production-grade REST API surface: endpoints, request/response schemas, error contracts, security schemes, and CORS configuration.\n\n"
                "## Instructions\n"
                "1. Think step by step: start with auth endpoints (signup, login, refresh) if authentication is required → then generate CRUD endpoints (GET list, POST create, GET by id, PUT update, DELETE) for each entity in db_architecture.entities → then add custom business endpoints from backend_architecture.backend_workflows.\n"
                "2. Every endpoint MUST include: group_name, path, method, description, request_body, query_parameters, response_payload, requires_auth, and roles_allowed.\n"
                "3. Paths must follow RESTful conventions: /api/v1/{resource_plural} for collections, /api/v1/{resource_plural}/{id} for individual resources.\n"
                "4. response_payload must show the exact JSON shape the frontend will receive.\n"
                "5. error_codes must cover: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 422 (Validation), 500 (Server Error).\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- Endpoint paths must use lowercase kebab-case resource names.\n"
                "- request_body field types must be: 'string', 'integer', 'number', 'boolean', 'array', 'object'.\n"
                "- The endpoints array is the primary contract consumed by FrontendArchitectureAgent — accuracy is critical."
            )
        )

        user_content = f"""
Design the complete API surface for this project. Think step by step:
1. If authentication is required, create auth endpoints first: POST /signup, POST /login, POST /refresh, POST /logout.
2. For each entity in db_architecture.entities, generate CRUD endpoints: GET /{{plural}} (list), POST /{{plural}} (create), GET /{{plural}}/{{id}} (read), PUT /{{plural}}/{{id}} (update), DELETE /{{plural}}/{{id}} (delete).
3. Add custom business endpoints from backend_architecture.backend_workflows.
4. Define error codes covering all standard HTTP error scenarios.
5. Set CORS and rate limiting for production readiness.

Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "api_strategy": {{
    "protocol": "string — 'HTTP/REST', 'GraphQL', or 'gRPC'",
    "base_path": "string — e.g. '/api/v1'",
    "versioning": "string — 'URL Path', 'Headers', or 'Query Parameters'",
    "default_response_format": "string — 'application/json'"
  }},
  "endpoints": [
    {{
      "group_name": "string — logical grouping, e.g. 'Authentication API', 'User API'",
      "path": "string — RESTful path, e.g. '/api/v1/auth/login'",
      "method": "string — 'GET', 'POST', 'PUT', 'PATCH', or 'DELETE'",
      "description": "string — what this endpoint does",
      "request_body": {{"field_name": {{"type": "string", "required": true}}}},
      "query_parameters": [{{"name": "string", "type": "string", "required": false, "default": "value"}}],
      "response_payload": {{"status": "success", "data_field": "type description"}},
      "requires_auth": "boolean — true if Authorization header needed",
      "roles_allowed": ["string — role names, or [] for any authenticated user"]
    }}
  ],
  "global_configurations": {{
    "cors_policy": {{
      "allowed_origins": ["string — origin URLs"],
      "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      "allowed_headers": ["Content-Type", "Authorization"]
    }},
    "rate_limiting": {{
      "rate_limit_enabled": "boolean",
      "max_requests_per_minute": "integer",
      "block_duration_seconds": "integer"
    }}
  }},
  "security_schemes": {{
    "bearer_auth": {{
      "type": "http",
      "scheme": "bearer",
      "bearer_format": "JWT",
      "header_name": "Authorization"
    }}
  }},
  "error_architecture": {{
    "error_response_format": {{
      "error": {{"code": "string", "message": "string", "details": "array or object"}}
    }},
    "error_codes": [
      {{"code": "string — UPPER_SNAKE_CASE error code", "http_status": "integer", "message": "string — user-facing message"}}
    ]
  }},
  "future_agent_context": {{
    "important_notes_for_frontend_agents": ["string — how frontend should consume these APIs"],
    "important_notes_for_backend_agents": ["string — implementation guidance"],
    "important_notes_for_devops_agents": ["string — deployment/proxy notes"]
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
            logger.error(f"Failed to run APIAgent: {e}")
            return enrich_agent_output(self._get_fallback_api_architecture(requirements, planning, db_architecture, backend_architecture), self.agent_name, agent_inputs)

    def _get_fallback_api_architecture(
        self, 
        requirements: Dict[str, Any], 
        planning: Dict[str, Any], 
        db_architecture: Dict[str, Any], 
        backend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Extract features and entities
        overview = requirements.get("project_overview", {})
        name = overview.get("name", "FinSight")
        tech_stack = requirements.get("tech_stack", {})
        entities = db_architecture.get("entities", [])
        
        # Build endpoints based on database entities
        endpoints = []
        
        # 1. Login/Signup endpoint if authentication is active
        auth_req = requirements.get("authentication", {}).get("required", True)
        if auth_req:
            endpoints.append({
                "group_name": "Authentication API",
                "path": "/api/v1/auth/signup",
                "method": "POST",
                "description": "Registers a new user account profile.",
                "request_body": {
                    "name": { "type": "string", "required": True },
                    "email": { "type": "string", "format": "email", "required": True },
                    "password": { "type": "string", "required": True }
                },
                "query_parameters": [],
                "response_payload": {
                    "status": "success",
                    "message": "User registered successfully.",
                    "user_id": "string"
                },
                "requires_auth": False,
                "roles_allowed": []
            })
            endpoints.append({
                "group_name": "Authentication API",
                "path": "/api/v1/auth/login",
                "method": "POST",
                "description": "Verifies password and issues JWT token credentials.",
                "request_body": {
                    "email": { "type": "string", "format": "email", "required": True },
                    "password": { "type": "string", "required": True }
                },
                "query_parameters": [],
                "response_payload": {
                    "status": "success",
                    "access_token": "string",
                    "refresh_token": "string",
                    "user": { "id": "string", "name": "string", "email": "string" }
                },
                "requires_auth": False,
                "roles_allowed": []
            })

        # 2. CRUD routes for entities
        for ent in entities:
            ent_name = ent.get("entity_name", "Core")
            ent_lower = ent_name.lower()
            
            # List entities route
            endpoints.append({
                "group_name": f"{ent_name} API",
                "path": f"/api/v1/{ent_lower}s",
                "method": "GET",
                "description": f"Retrieves a list of {ent_name} records filtered by query options.",
                "request_body": {},
                "query_parameters": [
                    { "name": "limit", "type": "integer", "required": False, "default": 20 },
                    { "name": "offset", "type": "integer", "required": False, "default": 0 }
                ],
                "response_payload": {
                    "status": "success",
                    f"{ent_lower}s": "array"
                },
                "requires_auth": auth_req and ent_name != "User",
                "roles_allowed": []
            })

            # Create entity route
            fields_creation = {}
            for f in ent.get("fields", []):
                if f.get("name") not in ["id", "created_at", "updated_at"]:
                    fields_creation[f.get("name")] = {
                        "type": f.get("type", "string").lower(),
                        "required": f.get("required", False)
                    }

            endpoints.append({
                "group_name": f"{ent_name} API",
                "path": f"/api/v1/{ent_lower}s",
                "method": "POST",
                "description": f"Creates a new {ent_name} record.",
                "request_body": fields_creation or { "name": { "type": "string", "required": True } },
                "query_parameters": [],
                "response_payload": {
                    "status": "success",
                    "id": "string",
                    "message": f"{ent_name} record created successfully."
                },
                "requires_auth": auth_req,
                "roles_allowed": []
            })

            # Get specific entity route
            endpoints.append({
                "group_name": f"{ent_name} API",
                "path": f"/api/v1/{ent_lower}s/{{id}}",
                "method": "GET",
                "description": f"Fetches details of a single {ent_name} by unique identifier.",
                "request_body": {},
                "query_parameters": [],
                "response_payload": {
                    "status": "success",
                    ent_lower: "object"
                },
                "requires_auth": auth_req,
                "roles_allowed": []
            })

            # Delete specific entity route
            endpoints.append({
                "group_name": f"{ent_name} API",
                "path": f"/api/v1/{ent_lower}s/{{id}}",
                "method": "DELETE",
                "description": f"Deletes a specific {ent_name} record.",
                "request_body": {},
                "query_parameters": [],
                "response_payload": {
                    "status": "success",
                    "message": f"{ent_name} deleted successfully."
                },
                "requires_auth": auth_req,
                "roles_allowed": []
            })

        return {
            "status": "success",
            "api_strategy": {
                "protocol": "HTTP/REST",
                "base_path": "/api/v1",
                "versioning": "URL Path prefixing",
                "default_response_format": "application/json"
            },
            "endpoints": endpoints,
            "global_configurations": {
                "cors_policy": {
                    "allowed_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allowed_headers": ["Content-Type", "Authorization", "X-Requested-With"]
                },
                "rate_limiting": {
                    "rate_limit_enabled": True,
                    "max_requests_per_minute": 100,
                    "block_duration_seconds": 300
                }
            },
            "security_schemes": {
                "bearer_auth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearer_format": "JWT",
                    "header_name": "Authorization"
                }
            },
            "error_architecture": {
                "error_response_format": {
                    "error": {
                        "code": "string",
                        "message": "string",
                        "details": "array"
                    }
                },
                "error_codes": [
                    { "code": "UNAUTHORIZED", "http_status": 401, "message": "Access credential headers are missing or expired." },
                    { "code": "FORBIDDEN", "http_status": 403, "message": "You do not have privilege to execute this action." },
                    { "code": "NOT_FOUND", "http_status": 404, "message": "Requested database entity record was not found." },
                    { "code": "VALIDATION_FAILED", "http_status": 422, "message": "Request validation rule checks failed." },
                    { "code": "INTERNAL_SERVER_ERROR", "http_status": 500, "message": "An unexpected error occurred during execution." }
                ]
            },
            "future_agent_context": {
                "important_notes_for_frontend_agents": [
                    "Construct API helper functions mappings using path variables matching group routing structures.",
                    "Verify Authorization header is set on all endpoints requires_auth = true."
                ],
                "important_notes_for_backend_agents": [
                    "Decorate endpoint routers with Dependency injection checking token requirements.",
                    "Return standardized JSON models for exception/validation errors."
                ],
                "important_notes_for_devops_agents": [
                    "Expose routing ports in docker-compose configs matching frontend cors configurations.",
                    "Set rate-limiting threshold variables via deployment environment settings."
                ]
            }
        }
