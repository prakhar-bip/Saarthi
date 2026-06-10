import json
from loguru import logger
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class OptimizationArchitectureAgent:
    """
    OptimizationArchitectureAgent for Sarthi.
    Designs performance, cache, latency, realtime, resource, and distributed scaling optimization metadata.
    """

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "OptimizationArchitectureAgent"

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
        security_architecture: Dict[str, Any],
        testing_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to produce optimization intelligence.
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
            "testing_architecture": testing_architecture,
            "validation_architecture": validation_architecture,
            "global_project_context": global_project_context,
        }

        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            logger.warning("NVIDIA_API_KEY not configured. Using fallback optimization architecture.")
            return enrich_agent_output(
                self._get_fallback_optimization_architecture(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design backend, database, frontend, API, realtime, cache, resource, infrastructure, and distributed scaling optimization intelligence."
        )

        user_content = f"""
Analyze these connected Sarthi architecture inputs:
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
Testing Architecture: {json.dumps(testing_architecture, indent=2)}
Validation Architecture: {json.dumps(validation_architecture, indent=2)}
Global Project Context: {json.dumps(global_project_context or {}, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "optimization_strategy": {{
    "performance_model": "",
    "scalability_strategy": "",
    "cache_strategy": "",
    "resource_optimization_strategy": ""
  }},
  "backend_optimization": {{
    "high_load_services": [],
    "async_optimization_targets": [],
    "query_optimization_rules": []
  }},
  "database_optimization": {{
    "indexing_targets": [],
    "high_frequency_queries": [],
    "cacheable_entities": []
  }},
  "frontend_optimization": {{
    "lazy_loading_targets": [],
    "memoization_targets": [],
    "bundle_optimization_rules": []
  }},
  "api_optimization": {{
    "high_frequency_routes": [],
    "response_optimization_rules": [],
    "rate_optimization_targets": []
  }},
  "realtime_optimization": {{
    "websocket_optimization_targets": [],
    "event_batching_rules": [],
    "realtime_scaling_rules": []
  }},
  "cache_architecture": {{
    "cache_layers": [],
    "cache_invalidation_rules": [],
    "distributed_cache_targets": []
  }},
  "infrastructure_optimization": {{
    "autoscaling_targets": [],
    "resource_limits": [],
    "high_availability_rules": []
  }},
  "scalability_analysis": {{
    "potential_bottlenecks": [],
    "high_risk_workflows": [],
    "scaling_recommendations": []
  }},
  "optimization_workflows": [
    {{
      "workflow_name": "",
      "optimization_flow": []
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_backend_generation": [],
    "important_notes_for_frontend_generation": [],
    "important_notes_for_deployment_generation": []
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
            logger.error(f"Failed to run OptimizationArchitectureAgent: {e}")
            return enrich_agent_output(
                self._get_fallback_optimization_architecture(**agent_inputs),
                self.agent_name,
                agent_inputs
            )

    def _get_fallback_optimization_architecture(
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
        security_architecture: Dict[str, Any],
        testing_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        entities = db_architecture.get("entities", []) if db_architecture else []
        entity_names = [e.get("entity_name", "Core") for e in entities if isinstance(e, dict)] or ["User", "Project"]
        endpoints = api_architecture.get("endpoints", []) if api_architecture else []
        high_frequency_routes = []
        protected_routes = []
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            route = f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}"
            if endpoint.get("method") == "GET":
                high_frequency_routes.append(route)
            if endpoint.get("requires_auth"):
                protected_routes.append(route)

        db_indexes = db_architecture.get("indexing_strategy", {}).get("indexes", []) if db_architecture else []
        cache_targets = (
            db_architecture.get("scalability_strategy", {}).get("caching_targets", [])
            if db_architecture else []
        )
        if not cache_targets:
            cache_targets = entity_names[:4]

        pages = frontend_architecture.get("pages", []) if frontend_architecture else []
        page_names = [p.get("page_name", "Dashboard") for p in pages if isinstance(p, dict)] or ["Dashboard"]
        components = frontend_architecture.get("component_hierarchy", []) if frontend_architecture else []
        component_names = [c.get("component_name", "Widget") for c in components if isinstance(c, dict)]

        realtime_enabled = bool(
            realtime_architecture
            and realtime_architecture.get("websocket_architecture", {}).get("enabled", False)
        )
        websocket_channels = (
            realtime_architecture.get("websocket_architecture", {}).get("websocket_channels", [])
            if realtime_architecture else []
        )

        backend_services = backend_architecture.get("service_architecture", []) if backend_architecture else []
        service_names = [s.get("service_name", "CoreService") for s in backend_services if isinstance(s, dict)]
        if not service_names:
            service_names = [f"{name}Service" for name in entity_names]

        autoscaling_targets = (
            devops_architecture.get("distributed_scalability", {}).get("autoscaling_targets", [])
            if devops_architecture else []
        ) or ["backend", "frontend"]

        bottlenecks = planning.get("risk_analysis", {}).get("potential_bottlenecks", []) if planning else []
        validation_blockers = (
            validation_architecture.get("compilation_readiness", {}).get("blocking_issues", [])
            if validation_architecture else []
        )

        return {
            "status": "success",
            "optimization_strategy": {
                "performance_model": "Contract-driven performance model optimizing hot API routes, indexed persistence access, memoized frontend rendering, and bounded realtime fanout.",
                "scalability_strategy": "Stateless backend workers scale horizontally behind the gateway while Redis-backed cache/pubsub isolates bursty workloads.",
                "cache_strategy": "Layered cache plan using browser state caches, API response caching, Redis distributed cache, and targeted invalidation on mutations.",
                "resource_optimization_strategy": "Allocate resources by high-load services, limit websocket fanout, lazy-load non-critical UI, and cap container CPU/memory with autoscaling thresholds."
            },
            "backend_optimization": {
                "high_load_services": service_names[:8],
                "async_optimization_targets": [
                    "Convert external API calls, AI calls, websocket broadcasts, and dashboard aggregation into async service tasks.",
                    "Use non-blocking database drivers and connection pooling for all high-frequency service operations.",
                    "Move long-running compilation or analytics jobs into background workers where request latency would exceed interactive thresholds."
                ],
                "query_optimization_rules": [
                    "Route list endpoints through paginated repository methods with explicit sort keys.",
                    "Avoid per-row relationship lookups by batching related entity reads.",
                    "Pre-compute dashboard aggregates for repeated high-frequency GET routes."
                ]
            },
            "database_optimization": {
                "indexing_targets": db_indexes or [f"idx_{name.lower()}_id" for name in entity_names],
                "high_frequency_queries": high_frequency_routes[:12] or ["GET /api/v1/users/me"],
                "cacheable_entities": cache_targets
            },
            "frontend_optimization": {
                "lazy_loading_targets": page_names[1:] or page_names,
                "memoization_targets": component_names[:8] or ["DashboardMetrics", "DataTable", "ChartPanel"],
                "bundle_optimization_rules": [
                    "Lazy-load route-level panels and expensive chart/detail components.",
                    "Keep shared UI primitives in stable modules to avoid duplicate bundles.",
                    "Defer non-critical animations and generated previews until the active viewport needs them."
                ]
            },
            "api_optimization": {
                "high_frequency_routes": high_frequency_routes[:12] or protected_routes[:8],
                "response_optimization_rules": [
                    "Return compact response DTOs that match frontend state requirements.",
                    "Apply pagination, filtering, and field projection to list endpoints.",
                    "Use ETag or last-modified style validators for cacheable GET responses where possible."
                ],
                "rate_optimization_targets": protected_routes[:8] or high_frequency_routes[:8]
            },
            "realtime_optimization": {
                "websocket_optimization_targets": websocket_channels if realtime_enabled else [],
                "event_batching_rules": [
                    "Batch high-frequency events into short time windows before broadcasting.",
                    "Deduplicate repeated state updates by entity id and event type.",
                    "Send deltas instead of full snapshots for large realtime lists."
                ] if realtime_enabled else [],
                "realtime_scaling_rules": [
                    "Back websocket fanout with Redis pub/sub when multiple backend replicas are active.",
                    "Use heartbeat and backoff policies to prevent reconnect storms.",
                    "Scope subscriptions by user, project, or dashboard channel to limit broadcast volume."
                ] if realtime_enabled else []
            },
            "cache_architecture": {
                "cache_layers": ["browser_state_cache", "frontend_query_cache", "backend_response_cache", "redis_distributed_cache"],
                "cache_invalidation_rules": [
                    "Invalidate entity list caches after POST/PUT/DELETE mutations for the same entity group.",
                    "Invalidate dashboard aggregate caches when contributing transactional entities change.",
                    "Expire user/session scoped caches on logout, token refresh failure, or permission changes."
                ],
                "distributed_cache_targets": cache_targets
            },
            "infrastructure_optimization": {
                "autoscaling_targets": autoscaling_targets,
                "resource_limits": [
                    "backend: start with balanced CPU/memory requests and scale on request latency, CPU, and queue depth.",
                    "frontend: serve static assets through CDN with immutable cache headers for hashed files.",
                    "redis: monitor memory pressure, eviction rate, and pub/sub throughput."
                ],
                "high_availability_rules": [
                    "Run more than one backend replica for production API availability.",
                    "Use health checks and readiness probes before routing traffic to new containers.",
                    "Keep database and cache services in private network segments with managed backup policies."
                ]
            },
            "scalability_analysis": {
                "potential_bottlenecks": bottlenecks or [
                    "Dashboard aggregation endpoints can become slow without indexes and pre-computed summaries.",
                    "Realtime broadcast fanout can overload a single backend instance without broker-backed distribution.",
                    "Large frontend route bundles can delay first interaction on mobile networks."
                ],
                "high_risk_workflows": validation_blockers or [
                    "Authenticated dashboard load",
                    "High-frequency list query and mutation loop",
                    "Realtime notification broadcast",
                    "Project compilation background workflow"
                ],
                "scaling_recommendations": [
                    "Scale API workers independently from frontend static hosting.",
                    "Use queue-backed workers for compilation, AI, analytics, and external integration tasks.",
                    "Add index and cache budgets to testing gates for high-frequency routes."
                ]
            },
            "optimization_workflows": [
                {
                    "workflow_name": "Hot dashboard read optimization",
                    "optimization_flow": [
                        "Frontend requests dashboard state through cache-aware GET route.",
                        "Backend checks response cache keyed by user/project/filter.",
                        "On cache miss, repository executes indexed paginated query and aggregate read.",
                        "Response is stored with scoped TTL and invalidated by relevant mutations."
                    ]
                },
                {
                    "workflow_name": "Realtime fanout optimization",
                    "optimization_flow": [
                        "Domain change emits compact event payload.",
                        "Backend batches and deduplicates related events.",
                        "Broker distributes event to subscribed channel workers.",
                        "Frontend store applies delta update without full page re-render."
                    ]
                }
            ],
            "future_generation_context": {
                "important_notes_for_backend_generation": [
                    "Generate repository functions with pagination, filters, projection, and index-aware query patterns.",
                    "Keep long-running work out of request handlers and behind async/background task boundaries.",
                    "Use explicit cache keys and invalidation hooks around mutation service methods."
                ],
                "important_notes_for_frontend_generation": [
                    "Generate route-level lazy loading and memoize expensive dashboards, charts, tables, and derived selectors.",
                    "Keep realtime handlers in a single shared hook/store to avoid duplicate socket connections.",
                    "Use optimistic UI only where rollback rules are available from state management architecture."
                ],
                "important_notes_for_deployment_generation": [
                    "Include resource requests/limits, health checks, autoscaling signals, and cache service configuration.",
                    "Ensure reverse proxy supports websocket upgrades and compression for API responses.",
                    "Expose monitoring for latency, cache hit ratio, websocket connection count, and worker queue depth."
                ]
            }
        }
