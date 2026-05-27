import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response

logger = logging.getLogger(__name__)

class AuthArchitectureAgent:
    """
    AuthArchitectureAgent for Sarthi.
    Designs token strategies, cookie policies, RBAC user hierarchies, API path access controls, and security middlewares.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "AuthArchitectureAgent"

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
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        theme_styling: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze requirements, planning, db, backend, api, frontend, and theme outputs to design the authentication and security architecture.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
            "theme_styling": theme_styling,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback authentication architecture design.")
            return enrich_agent_output(self._get_fallback_auth_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design authentication, authorization, sessions, RBAC, protected frontend/backend routes, realtime auth, and security handoffs."
        )

        user_content = f"""
Analyze the following inputs:
Requirements: {json.dumps(requirements, indent=2)}
Planning: {json.dumps(planning, indent=2)}
Database Architecture: {json.dumps(db_architecture, indent=2)}
Backend Architecture: {json.dumps(backend_architecture, indent=2)}
API Architecture: {json.dumps(api_architecture, indent=2)}
Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}
Theme Styling: {json.dumps(theme_styling, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "authentication_strategy": {{
    "auth_type": "e.g. JWT-based stateless bearer tokens",
    "session_strategy": "e.g. Token-based browser memory storage",
    "token_strategy": "e.g. Access token + Refresh token rotation",
    "authorization_model": "e.g. RBAC (Role-Based Access Control)"
  }},
  "authentication_entities": [
    {{
      "entity_name": "User",
      "purpose": "Stores core credentials and user access roles.",
      "related_permissions": ["read:profile", "write:profile"]
    }}
  ],
  "role_based_access_control": {{
    "enabled": true,
    "roles": ["User", "Admin"],
    "permission_groups": ["profile_management", "stress_logs_management"],
    "role_hierarchy": ["Admin > User"]
  }},
  "protected_route_architecture": {{
    "backend_protected_routes": ["GET /api/v1/stresslogs"],
    "frontend_protected_routes": ["/dashboard"],
    "permission_based_routes": []
  }},
  "authentication_workflows": [
    {{
      "workflow_name": "Email login",
      "execution_flow": [
        "Validate inputs on client.",
        "POST request is verified on backend using password hashing.",
        "Generate access and refresh tokens."
      ]
    }}
  ],
  "session_management_architecture": {{
    "multi_device_support": true,
    "session_persistence": ["Refresh token saved inside HttpOnly cookies"],
    "logout_strategy": ["Blacklist active access token key inside Redis cache"]
  }},
  "oauth_architecture": {{
    "enabled": false,
    "providers": [],
    "social_login_flows": []
  }},
  "realtime_authentication": {{
    "required": false,
    "websocket_auth_strategy": ["Token validation during query upgrade handshake"],
    "realtime_permission_checks": []
  }},
  "authentication_middleware_architecture": {{
    "middlewares": ["FastAPI JWTBearer dependencies handler"],
    "security_layers": ["CORS policy origin checker"],
    "request_validation_layers": ["Pydantic payload constraint checkers"]
  }},
  "frontend_authentication_flow": {{
    "auth_pages": ["/login", "/signup"],
    "auth_states": ["isAuthenticated", "userProfile"],
    "protected_ui_flows": ["Redirect to /login on fetch returning HTTP 401 status"]
  }},
  "security_considerations": {{
    "password_security_rules": ["Minimum length 8 characters"],
    "token_security_rules": ["Access token expiry set to 15 minutes"],
    "authentication_risks": ["Token hijacking via client localstorage if cookies fail"]
  }},
  "future_generation_context": {{
    "important_notes_for_backend_generation": [],
    "important_notes_for_frontend_generation": [],
    "important_notes_for_security_agents": []
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
            logger.error(f"Failed to run AuthArchitectureAgent: {e}")
            return enrich_agent_output(self._get_fallback_auth_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

    def _get_fallback_auth_architecture(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        auth_req = requirements.get("authentication", {}).get("required", True)
        
        entities = db_architecture.get("entities", []) if db_architecture else []
        endpoints = api_architecture.get("endpoints", []) if api_architecture else []
        pages = frontend_architecture.get("pages", []) if frontend_architecture else []
        
        # Determine protected routes based on entities and endpoints
        backend_protected = []
        for ep in endpoints:
            if ep.get("requires_auth", True):
                backend_protected.append(f"{ep.get('method', 'GET')} {ep.get('path')}")
                
        frontend_protected = []
        for pg in pages:
            if pg.get("protected", True):
                frontend_protected.append(f"/{pg.get('page_name', '').lower()}")

        roles = ["User"]
        if auth_req:
            roles.append("Admin")
            
        workflows = []
        if auth_req:
            workflows.append({
                "workflow_name": "Credential Login & Session Issue",
                "execution_flow": [
                    "Validate email input format and password constraints.",
                    "POST credentials to /api/v1/auth/login.",
                    "Backend performs password verification using bcrypt context.",
                    "Generate access token (HS256) and set HttpOnly HTTP cookie with refresh token.",
                    "State context sets active user profile and routes to protected dashboard."
                ]
            })
            workflows.append({
                "workflow_name": "Access Token Refresh",
                "execution_flow": [
                    "Detect client-side request returning HTTP 401 Unauthorized status.",
                    "Dispatch POST /api/v1/auth/refresh with HttpOnly cookie payload.",
                    "Validate refresh token signature and check blacklist store inside Redis.",
                    "Issue new active JWT token to header state."
                ]
            })

        return {
            "status": "success",
            "authentication_strategy": {
                "auth_type": "JWT-based stateless bearer tokens" if auth_req else "None",
                "session_strategy": "Secure HttpOnly cookie rotation storage" if auth_req else "None",
                "token_strategy": "Access token + Refresh token rotation" if auth_req else "None",
                "authorization_model": "RBAC (Role-Based Access Control) with role hierarchies" if auth_req else "None"
            },
            "authentication_entities": [
                {
                    "entity_name": "User",
                    "purpose": "Stores credentials hashes, email records, and assigned user roles.",
                    "related_permissions": ["read:profile", "write:profile", "delete:profile"]
                }
            ],
            "role_based_access_control": {
                "enabled": auth_req,
                "roles": roles,
                "permission_groups": ["auth_management"] + [f"{e.get('entity_name', '').lower()}_management" for e in entities],
                "role_hierarchy": ["Admin > User"] if auth_req else []
            },
            "protected_route_architecture": {
                "backend_protected_routes": backend_protected or ["GET /api/v1/users/me"],
                "frontend_protected_routes": frontend_protected or ["/dashboard"],
                "permission_based_routes": [f"DELETE /api/v1/{e.get('entity_name', '').lower()}s" for e in entities]
            },
            "authentication_workflows": workflows or [{
                "workflow_name": "Open access session",
                "execution_flow": [
                    "Access dashboard directly without login redirects.",
                    "State loads local records from LocalStorage."
                ]
            }],
            "session_management_architecture": {
                "multi_device_support": auth_req,
                "session_persistence": ["Refresh token saved inside HttpOnly cookies"] if auth_req else [],
                "logout_strategy": ["Blacklist active access token inside Redis cache"] if auth_req else []
            },
            "oauth_architecture": {
                "enabled": False,
                "providers": [],
                "social_login_flows": []
            },
            "realtime_authentication": {
                "required": False,
                "websocket_auth_strategy": ["Token validation during query upgrade handshake"],
                "realtime_permission_checks": []
            },
            "authentication_middleware_architecture": {
                "middlewares": ["FastAPI JWTBearer dependencies wrapper"] if auth_req else [],
                "security_layers": ["CORS policy origin checker", "XSS cookie protection flags"] if auth_req else [],
                "request_validation_layers": ["Pydantic payload schema validators"]
            },
            "frontend_authentication_flow": {
                "auth_pages": ["/login", "/signup"] if auth_req else [],
                "auth_states": ["isAuthenticated", "userProfile", "jwtAccessToken"] if auth_req else [],
                "protected_ui_flows": ["Redirect to /login on fetch returning HTTP 401 status"] if auth_req else []
            },
            "security_considerations": {
                "password_security_rules": [
                    "Minimum length 8 characters",
                    "Must contain at least one special symbol and number"
                ] if auth_req else [],
                "token_security_rules": [
                    "Access token expiry set to 15 minutes",
                    "Refresh token expiry set to 7 days"
                ] if auth_req else [],
                "authentication_risks": [
                    "Token hijacking via client localstorage if cookies fail",
                    "Replay attacks if TLS is not enforced"
                ]
            },
            "future_generation_context": {
                "important_notes_for_backend_generation": [
                    "Use passlib with bcrypt context for password hashing.",
                    "Enforce strict token signature validation inside fastapi dependencies."
                ] if auth_req else [],
                "important_notes_for_frontend_generation": [
                    "Protect workspace pages using React Router DOM Navigate guards."
                ] if auth_req else [],
                "important_notes_for_security_agents": [
                    "Perform input validation to prevent SQL/NoSQL Injection vulnerabilities."
                ]
            }
        }
