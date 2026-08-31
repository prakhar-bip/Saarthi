import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class TestingArchitectureAgent:
    """
    TestingArchitectureAgent for Sarthi.
    Designs unit testing frameworks, integration suites, API validations, realtime connection checks, and load test scripts.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "TestingArchitectureAgent"

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
        devops_architecture: Dict[str, Any],
        security_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to design the Testing & QA architecture layer.
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
            "security_architecture": security_architecture,
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_testing_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management, devops_architecture, security_architecture
            ), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design backend, frontend, API, auth, realtime, E2E, load, fixture, and CI/CD testing architecture using all prior contracts."
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
Security Architecture: {json.dumps(security_architecture, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "testing_strategy": {{
    "testing_model": "e.g. Pyramid testing strategy with unit, integration, and E2E gates.",
    "automation_strategy": "e.g. Automated test validation run on CI pull requests.",
    "validation_strategy": "e.g. Strict validation matching request models and testing database states.",
    "quality_gate_strategy": "e.g. Quality gates blocking deployments on test failures or poor coverage."
  }},
  "unit_testing_architecture": {{
    "backend_unit_targets": ["backend_files_to_test"],
    "frontend_unit_targets": ["frontend_hooks_to_test"],
    "shared_module_targets": ["shared_helpers_to_test"]
  }},
  "integration_testing_architecture": {{
    "integration_flows": ["flow_descriptions"],
    "cross_module_validation": ["validation_descriptions"],
    "service_interaction_tests": ["tests_list"]
  }},
  "api_testing_architecture": {{
    "api_validation_targets": ["endpoints_path"],
    "request_response_validation": ["validation_checks"],
    "rate_limit_testing_rules": ["rules_list"]
  }},
  "frontend_testing_architecture": {{
    "component_testing_targets": ["component_names"],
    "ui_interaction_flows": ["interaction_steps"],
    "frontend_state_validation": ["state_validation_rules"]
  }},
  "authentication_testing": {{
    "auth_validation_flows": ["validation_steps"],
    "permission_testing_rules": ["permission_rules"],
    "session_validation_rules": ["session_rules"]
  }},
  "realtime_testing_architecture": {{
    "websocket_test_flows": ["test_flows"],
    "event_validation_rules": ["event_rules"],
    "realtime_sync_validation": ["sync_rules"]
  }},
  "e2e_testing_architecture": {{
    "critical_user_flows": ["user_flows"],
    "workflow_validation_targets": ["validation_steps"],
    "cross_platform_validation": ["platform_rules"]
  }},
  "load_testing_architecture": {{
    "high_load_targets": ["load_targets"],
    "stress_testing_flows": ["stress_flows"],
    "performance_validation_rules": ["validation_rules"]
  }},
  "mocking_fixture_architecture": {{
    "mock_services": ["services_to_mock"],
    "fixture_groups": ["fixture_data_groups"],
    "test_environment_rules": ["env_rules"]
  }},
  "cicd_testing_gates": {{
    "pipeline_validation_stages": ["stages_list"],
    "blocking_conditions": ["failure_blocks"],
    "quality_thresholds": ["thresholds"]
  }},
  "future_generation_context": {{
    "important_notes_for_test_generation": ["test_generation_notes"],
    "important_notes_for_backend_generation": ["backend_notes"],
    "important_notes_for_frontend_generation": ["frontend_notes"]
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
            return enrich_agent_output(self._get_fallback_testing_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management, devops_architecture, security_architecture
            ), self.agent_name, agent_inputs)

    def _get_fallback_testing_architecture(
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
        devops_architecture: Dict[str, Any],
        security_architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates structured, valid fallback Testing configurations when Nvidia NIM API is offline or returns invalid output.
        """
        has_auth = auth_architecture is not None
        has_realtime = realtime_architecture is not None
        has_devops = devops_architecture is not None
        has_security = security_architecture is not None

        # Build backend unit targets
        backend_unit_targets = ["app/core/security.py", "app/api/auth.py"]
        if api_architecture:
            backend_unit_targets.append("app/api/projects.py")
        
        # Build frontend unit targets
        frontend_unit_targets = ["src/hooks/useAuth.ts"]
        if state_management:
            frontend_unit_targets.append("src/store/useDashboardStore.ts")

        # WebSockets testing rules
        websocket_test_flows = []
        if has_realtime:
            websocket_test_flows.extend([
                "Connect test client to WebSocket gateway `/ws/v1/updates`.",
                "Send mock subscription payload and verify immediate confirmation packet.",
                "Assert broadcast events are received by multiple connected test socket instances."
            ])
        else:
            websocket_test_flows.append("No active realtime WebSocket channels configured for testing.")

        # E2E Critical User Flows
        critical_user_flows = [
            "User visits LandingPage -> logs in via LoginPage -> redirects to UserDashboard view."
        ]
        if has_auth:
            critical_user_flows.append("Session expiry redirects unauthorized user instantly back to LoginPage.")

        # Load testing
        high_load_targets = ["backend REST API gateway"]
        if has_realtime:
            high_load_targets.append("WebSocket connections broker engine")

        return {
            "status": "success",
            "testing_strategy": {
                "testing_model": "Pyramid testing model: comprehensive unit tests, target API integration tests, and critical path end-to-end tests.",
                "automation_strategy": "Automated testing pipeline triggered on git push and pull request activities.",
                "validation_strategy": "Strict assertions on REST schemas structure and state cache consistency checks.",
                "quality_gate_strategy": "Block merge approvals on failing test coverage gates or syntax validation failures."
            },
            "unit_testing_architecture": {
                "backend_unit_targets": backend_unit_targets,
                "frontend_unit_targets": frontend_unit_targets,
                "shared_module_targets": ["app/core/config.py", "src/utils/helpers.ts"]
            },
            "integration_testing_architecture": {
                "integration_flows": [
                    "User auth flow verifying database insertions and token cookie returns.",
                    "Project creation flows storing blueprint details and triggering background compile runners."
                ],
                "cross_module_validation": [
                    "Database ORM entity saves verify against controller serialization outputs.",
                    "WebSocket event triggers update local Zustand store metrics objects."
                ],
                "service_interaction_tests": [
                    "Validate backend services connect cleanly to MongoDB and Redis cache clients."
                ]
            },
            "api_testing_architecture": {
                "api_validation_targets": [
                    "/api/v1/auth/login",
                    "/api/v1/projects"
                ],
                "request_response_validation": [
                    "Assert API returns HTTP 200 OK with correct schema mapping on valid parameters.",
                    "Assert API returns HTTP 422 Unprocessable Entity on schema validation mismatches."
                ],
                "rate_limit_testing_rules": [
                    "Simulate high request frequencies using Locust to verify HTTP 429 rate limit triggers."
                ]
            },
            "frontend_testing_architecture": {
                "component_testing_targets": [
                    "ProjectViewer",
                    "SidebarNavigation",
                    "CategorySelectorPanel"
                ],
                "ui_interaction_flows": [
                    "User clicks categories -> assert project suggestion sliders render suggestions.",
                    "User selects suggestions -> verify selection discussion thread loads."
                ],
                "frontend_state_validation": [
                    "Assert Zustand stores mutate values correctly on action dispatches.",
                    "Assert SWR local caches reload query lists automatically on focus events."
                ]
            },
            "authentication_testing": {
                "auth_validation_flows": [
                    "Login API submits passwords -> verify Bcrypt hash matches.",
                    "Assert JWT token headers match HS256 encryption keys."
                ],
                "permission_testing_rules": [
                    "Request user details as unauthenticated guest -> assert API returns HTTP 401 Unauthorized.",
                    "Request admin utilities using standard role permissions -> assert API returns HTTP 403 Forbidden."
                ],
                "session_validation_rules": [
                    "Simulate expired token usage -> assert token rotation refresh loop triggers correctly."
                ]
            },
            "realtime_testing_architecture": {
                "websocket_test_flows": websocket_test_flows,
                "event_validation_rules": [
                    "Assert broadcasts drop client connection on malformed packet uploads."
                ],
                "realtime_sync_validation": [
                    "Verify clients receive updates state packet matches current server database values."
                ]
            },
            "e2e_testing_architecture": {
                "critical_user_flows": critical_user_flows,
                "workflow_validation_targets": [
                    "Verify generated virtual file viewer pane renders codebase JSON configs after compilation completes."
                ],
                "cross_platform_validation": [
                    "Verify responsive UI layouts adapt cleanly on mobile and desktop layout frame boundaries."
                ]
            },
            "load_testing_architecture": {
                "high_load_targets": high_load_targets,
                "stress_testing_flows": [
                    "Increase virtual users count up to 1000 requests/sec and monitor database connection pooling states."
                ],
                "performance_validation_rules": [
                    "Average API response times must remain under 300ms under load conditions."
                ]
            },
            "mocking_fixture_architecture": {
                "mock_services": [
                    "Nvidia NIM completions endpoint",
                    "OAuth login providers callbacks"
                ],
                "fixture_groups": [
                    "Mock User profiles datasets",
                    "Mock Project blueprints JSON files"
                ],
                "test_environment_rules": [
                    "Use separate test databases (e.g. sarthi_test MongoDB) and drop db after unit test suite runs."
                ]
            },
            "cicd_testing_gates": {
                "pipeline_validation_stages": [
                    "PR lint check",
                    "Unit testing suite execution",
                    "Build validations gate"
                ],
                "blocking_conditions": [
                    "Block branch merging on test suites failures or coverage drops under 80%."
                ],
                "quality_thresholds": [
                    "Lint rules must pass with zero critical code quality errors."
                ]
            },
            "future_generation_context": {
                "important_notes_for_test_generation": [
                    "Ensure tests use mock databases to prevent local workspace data corruption.",
                    "Confirm all test runs cleanly close databases sessions pools to avoid network hangs."
                ],
                "important_notes_for_backend_generation": [
                    "Provide explicit API endpoint routers configurations to enable automated integration test scans."
                ],
                "important_notes_for_frontend_generation": [
                    "Include data-testid properties inside key UI components to support automated Playwright test targets."
                ]
            }
        }
