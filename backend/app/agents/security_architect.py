import json
from loguru import logger
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class SecurityArchitectureAgent:
    """
    SecurityArchitectureAgent for Sarthi.
    Designs application security, API security, input sanitization, network rules, OWASP defenses, and secrets protection.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "SecurityArchitectureAgent"

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
        theme_styling: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        realtime_architecture: Dict[str, Any],
        state_management: Dict[str, Any],
        devops_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to design the Security & Protection architecture layer.
        """
        agent_inputs = {
            "requirements": requirements,
            "planning": planning,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
            "theme_styling": theme_styling,
            "auth_architecture": auth_architecture,
            "realtime_architecture": realtime_architecture,
            "state_management": state_management,
            "devops_architecture": devops_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using intelligent fallback security architecture design.")
            return enrich_agent_output(self._get_fallback_security_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management, devops_architecture
            ), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design application security, API hardening, auth controls, websocket security, frontend storage rules, secrets, CORS/CSP, and infrastructure protection."
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
Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
Realtime Architecture: {json.dumps(realtime_architecture, indent=2)}
State Management: {json.dumps(state_management, indent=2)}
DevOps Architecture: {json.dumps(devops_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "security_strategy": {{
    "application_security_model": "e.g. Defense-in-depth model utilizing zero-trust access controls.",
    "authentication_security_model": "e.g. Passwordless / Multi-factor JWT token lifecycle hardening.",
    "infrastructure_security_model": "e.g. Container isolation with secure ingress proxies and secret manager stores.",
    "validation_strategy": "e.g. Strict validation boundary checking at ingress, controller, and database ORM layers."
  }},
  "api_security_architecture": {{
    "protected_api_groups": ["api_groups"],
    "rate_limiting_rules": ["limit_rules"],
    "request_validation_rules": ["validation_rules"],
    "api_abuse_prevention": ["prevention_rules"]
  }},
  "authentication_security": {{
    "token_security_rules": ["token_rules"],
    "session_security_rules": ["session_rules"],
    "password_security_rules": ["password_rules"],
    "refresh_token_policies": ["refresh_policies"]
  }},
  "authorization_security": {{
    "rbac_validation_rules": ["rbac_rules"],
    "permission_enforcement_layers": ["enforcement_layers"],
    "protected_resource_groups": ["resource_groups"]
  }},
  "websocket_security": {{
    "connection_validation_rules": ["validation_rules"],
    "realtime_permission_checks": ["permission_checks"],
    "event_authorization_rules": ["event_rules"]
  }},
  "frontend_security": {{
    "protected_frontend_routes": ["frontend_routes"],
    "frontend_validation_rules": ["validation_rules"],
    "secure_storage_rules": ["storage_rules"]
  }},
  "cors_csp_architecture": {{
    "cors_rules": ["cors_rules"],
    "csp_rules": ["csp_rules"],
    "trusted_origin_groups": ["origin_groups"]
  }},
  "input_validation_security": {{
    "sanitization_rules": ["sanitization_rules"],
    "payload_validation_rules": ["payload_rules"],
    "file_upload_security_rules": ["file_rules"]
  }},
  "environment_security": {{
    "secret_management_rules": ["secret_rules"],
    "environment_isolation_rules": ["isolation_rules"],
    "credential_protection_rules": ["credential_rules"]
  }},
  "infrastructure_security": {{
    "container_security_rules": ["container_rules"],
    "deployment_security_rules": ["deployment_rules"],
    "network_security_rules": ["network_rules"]
  }},
  "security_workflows": [
    {{
      "workflow_name": "security_action",
      "security_flow": ["step_by_step_flow"]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_backend_generation": ["backend_notes"],
    "important_notes_for_api_generation": ["api_notes"],
    "important_notes_for_deployment_generation": ["deployment_notes"]
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
                temperature=0.2
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(parse_json_response(raw_response), self.agent_name, agent_inputs)
        except Exception as e:
            logger.error(f"Failed to run SecurityArchitectureAgent LLM call: {e}")
            return enrich_agent_output(self._get_fallback_security_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management, devops_architecture
            ), self.agent_name, agent_inputs)

    def _get_fallback_security_architecture(
        self,
        requirements: Dict[str, Any],
        planning: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        theme_styling: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        realtime_architecture: Dict[str, Any],
        state_management: Dict[str, Any],
        devops_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates structured, valid fallback Security configurations when Nvidia NIM API is offline or returns invalid output.
        """
        has_auth = auth_architecture is not None
        has_realtime = realtime_architecture is not None
        has_devops = devops_architecture is not None

        # Build endpoints protection list
        endpoints = api_architecture.get("endpoints", []) if api_architecture else []
        protected_api_groups = []
        for ep in endpoints:
            ep_path = ep if isinstance(ep, str) else ep.get("path", "")
            if ep_path and not any(k in ep_path.lower() for k in ["login", "signup", "register"]):
                group_name = ep_path.split("/")[2] if len(ep_path.split("/")) > 2 else "general"
                if group_name not in protected_api_groups:
                    protected_api_groups.append(group_name)

        if not protected_api_groups:
            protected_api_groups = ["users", "items"]

        # Build rate limiting rules
        rate_limiting_rules = [
            "Limit general REST API endpoints to 100 requests per minute per IP address.",
            "Limit authentication routes (login/signup) to 5 requests per minute per IP address to block brute force attempts."
        ]

        # WebSockets auth validation
        websocket_validation = [
            "Perform initial handshake authentication checking query string token parameters."
        ]
        if has_realtime:
            websocket_validation.append("Reject WebSocket connection attempts instantly if JWT verification fails or query parameter lacks validation signatures.")

        # Infrastructure rules
        container_security = [
            "Run application containers as non-root users inside Docker settings."
        ]
        if has_devops:
            container_security.append("Verify base Docker images are scanned for vulnerabilities on compilation gates.")

        return {
            "status": "success",
            "security_strategy": {
                "application_security_model": "Defense-in-depth layout isolating service credentials and enforcing authorization tokens.",
                "authentication_security_model": "JWT stateless token pair configuration with sliding rotation rules.",
                "infrastructure_security_model": "VPC container networking, Nginx ingress proxying, and managed secrets manager injections.",
                "validation_strategy": "Double-barrier input sanitization verifying payloads at controller layers and database schemas validation."
            },
            "api_security_architecture": {
                "protected_api_groups": protected_api_groups,
                "rate_limiting_rules": rate_limiting_rules,
                "request_validation_rules": [
                    "Validate incoming payloads against Pydantic model declarations inside controllers.",
                    "Verify Content-Type header matches application/json and drop malformed REST structures."
                ],
                "api_abuse_prevention": [
                    "Reject API calls exceeding limit thresholds with HTTP 429 Too Many Requests status code.",
                    "Configure SQL injection safeguards by executing operations through backend ORM builders."
                ]
            },
            "authentication_security": {
                "token_security_rules": [
                    "Sign access tokens with secure asymmetric signatures or secret keys using HS256 algorithm.",
                    "Limit access token expiration durations to 15 minutes."
                ],
                "session_security_rules": [
                    "Manage refresh tokens within HttpOnly, Secure, SameSite=Strict cookies to block XSS script extraction."
                ],
                "password_security_rules": [
                    "Hash passwords using bcrypt or Argon2id with work factor parameters before committing to databases.",
                    "Enforce minimum password length rules of 8 characters containing letters, numbers, and symbols."
                ],
                "refresh_token_policies": [
                    "Enforce single-use refresh token rotation (RTR) where using a refresh token revokes all sibling sessions."
                ]
            },
            "authorization_security": {
                "rbac_validation_rules": [
                    "Verify user role maps against endpoint authorization annotations inside router filters.",
                    "Return HTTP 403 Forbidden status when role credentials fail target resources validations."
                ],
                "permission_enforcement_layers": [
                    "Gateway path filters verify valid headers.",
                    "Application controller filters verify role privileges scopes."
                ],
                "protected_resource_groups": [
                    "Data access layers (verify ownership IDs before deleting/modifying entities)."
                ]
            },
            "websocket_security": {
                "connection_validation_rules": websocket_validation,
                "realtime_permission_checks": [
                    "Perform subscription validations whenever a client requests to join a channel."
                ],
                "event_authorization_rules": [
                    "Verify user token permissions scopes before broadcast relays trigger for websocket events."
                ]
            },
            "frontend_security": {
                "protected_frontend_routes": [
                    "Block access to dashboards routes when client side isAuthenticated flag is false."
                ],
                "frontend_validation_rules": [
                    "Sanitize form data entries to prevent basic script injections.",
                    "Avoid exposing backend server database structures inside client-side bundles."
                ],
                "secure_storage_rules": [
                    "Store transient access tokens in memory variables inside frontend stores.",
                    "Do not persist JWT access tokens in LocalStorage or SessionStorage."
                ]
            },
            "cors_csp_architecture": {
                "cors_rules": [
                    "Allow CORS headers only from trusted domains listed in configuration files.",
                    "Prevent wildcard '*' CORS access to API routes."
                ],
                "csp_rules": [
                    "Enforce CSP rules: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' wss:;"
                ],
                "trusted_origin_groups": ["localhost:3000", "localhost:5173"]
            },
            "input_validation_security": {
                "sanitization_rules": [
                    "Sanitize strings using libraries to strip script tags and escape HTML chars.",
                    "Strip SQL control characters before routing queries."
                ],
                "payload_validation_rules": [
                    "Reject payloads containing elements exceeding size boundaries.",
                    "Verify request schemas have exactly the types specified."
                ],
                "file_upload_security_rules": [
                    "Scan uploaded file packages using antivirus engines if upload modules exist.",
                    "Enforce strict file type and extension checking, preventing executing binaries."
                ]
            },
            "environment_security": {
                "secret_management_rules": [
                    "Load secrets from environment variables injected by secure vault containers.",
                    "Never commit database connection strings or api keys inside source control."
                ],
                "environment_isolation_rules": [
                    "Maintain distinct isolation boundaries between staging and production database endpoints."
                ],
                "credential_protection_rules": [
                    "Rotate API keys on scheduled intervals to limit vulnerability windows."
                ]
            },
            "infrastructure_security": {
                "container_security_rules": container_security,
                "deployment_security_rules": [
                    "Enable automated dependencies security scanning inside CI pipelines."
                ],
                "network_security_rules": [
                    "Isolate databases containers inside private subnets unreachable from external internet addresses."
                ]
            },
            "security_workflows": [
                {
                    "workflow_name": "API Handshake Token Rotation Flow",
                    "security_flow": [
                        "Client submits refresh token stored in secure cookie.",
                        "Verify refresh token validity and expiration status.",
                        "Generate new access token and new rotated refresh token.",
                        "Set new refresh token cookie and return new access token."
                    ]
                },
                {
                    "workflow_name": "Brute Force IP Lockout Flow",
                    "security_flow": [
                        "Monitor failed login request attempts metrics.",
                        "Block client requests from source IP address for 15 minutes after 5 consecutive failures.",
                        "Log failed attempt event metadata for compliance logging."
                    ]
                }
            ],
            "future_generation_context": {
                "important_notes_for_backend_generation": [
                    "Confirm Pydantic validation handles extreme input sizes to prevent DoS attacks.",
                    "Enforce database cascade constraint validations at model layers."
                ],
                "important_notes_for_api_generation": [
                    "Confirm FastAPI Dependency Injectors enforce oauth2 scheme requirements.",
                    "Apply CORS middlewares before adding routing controllers."
                ],
                "important_notes_for_deployment_generation": [
                    "Verify container configurations drop all permissions privileges after setup."
                ]
            }
        }
