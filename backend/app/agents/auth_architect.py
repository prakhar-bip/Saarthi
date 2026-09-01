import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


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
            return enrich_agent_output(self._get_fallback_auth_architecture(requirements, planning, db_architecture, backend_architecture, api_architecture, frontend_architecture), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "## Role\n"
                "You are a senior security architect specializing in authentication and authorization. Design the complete auth architecture: identity strategy, token management, RBAC, protected routes (backend + frontend), session handling, OAuth, and security middleware.\n\n"
                "## Instructions\n"
                "1. Think step by step: check if requirements.authentication.required is true → choose auth strategy (JWT, session, OAuth) → derive protected backend routes from api_architecture.endpoints where requires_auth=true → derive protected frontend routes from frontend_architecture.pages where protected=true → design RBAC roles and permissions → define auth workflows (login, signup, refresh, logout) → set security rules.\n"
                "2. protected_route_architecture MUST be derived from actual upstream contracts — list real endpoint paths from api_architecture and real page paths from frontend_architecture.\n"
                "3. authentication_workflows must describe the full end-to-end flow from UI to database for each auth action.\n"
                "4. security_considerations must follow OWASP best practices: bcrypt for passwords, short-lived access tokens, HttpOnly cookies for refresh tokens, XSS/CSRF protection.\n"
                "5. If requirements.authentication.required is false, set all auth-related fields to their disabled/empty states but still return the full JSON structure.\n\n"
                "## Constraints\n"
                "- Return ONLY valid JSON. No markdown fences, no commentary.\n"
                "- Token expiry values must be specific (e.g. '15 minutes', '7 days'), not vague.\n"
                "- Role names must be PascalCase. Permission strings must use 'action:resource' format (e.g. 'read:profile').\n"
                "- All route paths must exactly match paths from api_architecture and frontend_architecture."
            )
        )

        user_content = f"""
Design the authentication and authorization architecture. Think step by step:
1. Check requirements.authentication.required — if false, return all auth fields as disabled/empty but preserve the full JSON structure.
2. Choose the auth strategy based on requirements.authentication.type and backend_architecture.authentication_backend_flow.
3. Derive backend_protected_routes by scanning api_architecture.endpoints for requires_auth=true — list each as "METHOD /path".
4. Derive frontend_protected_routes by scanning frontend_architecture.pages for protected=true — list each as "/pagename".
5. Define RBAC roles, permissions (action:resource format), and hierarchy.
6. Design auth workflows: login, signup, token refresh, logout — each with full UI-to-DB execution flow.
7. Set OWASP-aligned security rules: bcrypt hashing, short-lived tokens, HttpOnly cookies, XSS protection.

Requirements: {json.dumps(requirements.get("project_overview", requirements), default=str)}
Database Entities: {json.dumps(db_architecture.get("entities", []) if db_architecture else [], default=str)}
API Architecture: {json.dumps(api_architecture, default=str)}

Return ONLY valid JSON (no markdown fences, no explanation) in this exact structure:
{{
  "status": "success",
  "authentication_strategy": {{
    "auth_type": "string — e.g. 'JWT-based stateless bearer tokens' or 'None'",
    "session_strategy": "string — e.g. 'HttpOnly cookie rotation' or 'None'",
    "token_strategy": "string — e.g. 'Access token (15min) + Refresh token (7d) rotation' or 'None'",
    "authorization_model": "string — 'RBAC', 'ABAC', or 'None'"
  }},
  "authentication_entities": [
    {{
      "entity_name": "string — must match a db_architecture entity name",
      "purpose": "string — what auth data this entity stores",
      "related_permissions": ["string — action:resource format, e.g. 'read:profile'"]
    }}
  ],
  "role_based_access_control": {{
    "enabled": "boolean",
    "roles": ["string — PascalCase role names, e.g. 'User', 'Admin'"],
    "permission_groups": ["string — snake_case permission group names"],
    "role_hierarchy": ["string — hierarchy expressions, e.g. 'Admin > User'"]
  }},
  "protected_route_architecture": {{
    "backend_protected_routes": ["string — 'METHOD /path' from api_architecture endpoints where requires_auth=true"],
    "frontend_protected_routes": ["string — '/route' from frontend_architecture pages where protected=true"],
    "permission_based_routes": ["string — routes requiring specific role/permission"]
  }},
  "authentication_workflows": [
    {{
      "workflow_name": "string — e.g. 'Email Login', 'Token Refresh', 'Logout'",
      "execution_flow": ["string — ordered steps from UI input to DB operation to response"]
    }}
  ],
  "session_management_architecture": {{
    "multi_device_support": "boolean",
    "session_persistence": ["string — where/how sessions are stored"],
    "logout_strategy": ["string — how active sessions are invalidated"]
  }},
  "oauth_architecture": {{
    "enabled": "boolean",
    "providers": ["string — OAuth provider names if enabled"],
    "social_login_flows": ["string — OAuth flow descriptions"]
  }},
  "realtime_authentication": {{
    "required": "boolean",
    "websocket_auth_strategy": ["string — how WebSocket connections are authenticated"],
    "realtime_permission_checks": ["string — per-message permission checks"]
  }},
  "authentication_middleware_architecture": {{
    "middlewares": ["string — auth middleware component names"],
    "security_layers": ["string — security middleware names (CORS, XSS, CSRF)"],
    "request_validation_layers": ["string — input validation middleware"]
  }},
  "frontend_authentication_flow": {{
    "auth_pages": ["string — auth route paths from frontend_architecture"],
    "auth_states": ["string — frontend state variable names for auth"],
    "protected_ui_flows": ["string — how unauthorized access is handled in UI"]
  }},
  "security_considerations": {{
    "token_security_rules": ["string — token signing, expiry, rotation rules"],
    "credential_storage": ["string — hashing algorithm and salt rounds"],
    "authentication_risks": ["string — known attack vectors and mitigations"]
  }},
  "future_generation_context": {{
    "important_notes_for_backend_generation": ["string — auth implementation guidance"],
    "important_notes_for_frontend_generation": ["string — auth UI implementation guidance"],
    "important_notes_for_security_agents": ["string — security hardening guidance"]
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
                temperature=0.1,
                max_tokens=2048
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
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
