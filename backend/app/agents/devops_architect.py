import json
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class DevOpsArchitectureAgent:
    """
    DevOpsArchitectureAgent for Sarthi.
    Designs cloud deployment strategies, containerization models, CI/CD pipelines, reverse proxies, and monitoring systems.
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NVIDIA_MODEL
        self.agent_name = "DevOpsArchitectureAgent"

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
        state_management: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all previous pipeline architectures to design DevOps and cloud infrastructure configurations.
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
        }
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(self._get_fallback_devops_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management
            ), self.agent_name, agent_inputs)

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            "Design DevOps, CI/CD, containerization, environments, reverse proxy, observability, infrastructure, and deployment scalability contracts."
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

Return ONLY valid JSON in this exact format:
{{
  "status": "success",
  "infrastructure_strategy": {{
    "deployment_model": "e.g. Containerized multi-tier microservices layout.",
    "containerization_strategy": "e.g. Multi-stage Docker builds isolating development and production bundles.",
    "cloud_strategy": "e.g. Serverless container orchestration platform (AWS Fargate / GCP Cloud Run).",
    "scalability_strategy": "e.g. Horizontal autoscaling based on CPU utilization and request rate thresholds."
  }},
  "containerization_architecture": {{
    "docker_required": true,
    "container_groups": ["frontend", "backend", "cache", "db"],
    "service_containers": [
      {{
        "name": "service_name",
        "image": "base_docker_image",
        "ports": ["host:container"],
        "env_vars": ["ENV_VAR_KEYS"]
      }}
    ],
    "orchestration_strategy": ["orchestration_description"]
  }},
  "deployment_pipeline_architecture": {{
    "deployment_stages": ["stage_name"],
    "environment_flow": ["staging_prod_flow"],
    "rollback_strategy": ["rollback_description"]
  }},
  "cicd_architecture": {{
    "pipeline_stages": ["stage_name"],
    "automation_targets": ["target_actions"],
    "testing_gates": ["gate_validations"]
  }},
  "cloud_infrastructure": {{
    "providers": ["cloud_provider"],
    "service_groups": ["aws_gcp_services_listed"],
    "deployment_targets": ["target_hostings"]
  }},
  "reverse_proxy_architecture": {{
    "gateway_strategy": "e.g. Nginx reverse proxy with SSL termination and WebSocket upgrades.",
    "load_balancing_rules": ["lb_rules"],
    "routing_rules": ["routing_rules"]
  }},
  "monitoring_observability": {{
    "monitoring_targets": ["target_components"],
    "logging_strategy": ["logging_rules"],
    "alerting_systems": ["alerting_channels"]
  }},
  "environment_management": {{
    "environment_groups": ["env_names"],
    "secret_management_rules": ["secret_rules"],
    "configuration_layers": ["layer_rules"]
  }},
  "distributed_scalability": {{
    "horizontal_scaling": true,
    "autoscaling_targets": ["target_services"],
    "high_load_services": ["high_load_services"]
  }},
  "production_optimization": {{
    "performance_targets": ["performance_targets"],
    "caching_layers": ["cache_services"],
    "optimization_rules": ["optimizations"]
  }},
  "deployment_workflows": [
    {{
      "workflow_name": "workflow_action",
      "deployment_flow": ["step_by_step_flow"]
    }}
  ],
  "future_generation_context": {{
    "important_notes_for_deployment_generation": ["deployment_generation_notes"],
    "important_notes_for_backend_generation": ["backend_generation_notes"],
    "important_notes_for_monitoring_agents": ["monitoring_generation_notes"]
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
            return enrich_agent_output(self._get_fallback_devops_architecture(
                requirements, planning, db_architecture, backend_architecture, 
                api_architecture, frontend_architecture, theme_styling, auth_architecture, 
                realtime_architecture, state_management
            ), self.agent_name, agent_inputs)

    def _get_fallback_devops_architecture(
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
        state_management: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates structured, valid fallback DevOps configurations when Nvidia NIM API is offline or returns invalid output.
        """
        # Read properties from previous architecture layers
        has_realtime = realtime_architecture is not None
        has_auth = auth_architecture is not None
        
        # Primary DB check
        primary_db = "MongoDB"
        if db_architecture and db_architecture.get("database_strategy"):
            primary_db = db_architecture.get("database_strategy", {}).get("primary_database", "MongoDB")

        # Frontend Strategy check
        fe_framework = "React (Vite SPA)"
        if frontend_architecture and frontend_architecture.get("frontend_strategy"):
            fe_framework = frontend_architecture.get("frontend_strategy", {}).get("frontend_framework", "React (Vite SPA)")

        # Port mapping logic
        fe_port = "3000:3000" if "next" in fe_framework.lower() else "5173:5173"
        be_port = "8000:8000"

        db_env = "DATABASE_URL" if primary_db.lower() in ["postgresql", "sqlite", "mysql"] else "MONGODB_URI"

        # Docker Container List
        service_containers = [
            {
                "name": "frontend",
                "image": "node:20-alpine",
                "ports": [fe_port],
                "env_vars": ["VITE_API_URL", "NODE_ENV"]
            },
            {
                "name": "backend",
                "image": "python:3.11-slim",
                "ports": [be_port],
                "env_vars": [db_env, "REDIS_HOST", "JWT_SECRET", "NODE_ENV"]
            }
        ]

        # Conditionally add database/cache containers to service container stack if they run in local docker-compose
        container_groups = ["frontend", "backend"]
        if primary_db.lower() == "postgresql":
            service_containers.append({
                "name": "postgres_db",
                "image": "postgres:15-alpine",
                "ports": ["5432:5432"],
                "env_vars": ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
            })
            container_groups.append("db")
        elif primary_db.lower() == "mongodb":
            service_containers.append({
                "name": "mongodb",
                "image": "mongo:6.0",
                "ports": ["27017:27017"],
                "env_vars": ["MONGO_INITDB_ROOT_USERNAME", "MONGO_INITDB_ROOT_PASSWORD"]
            })
            container_groups.append("db")

        # Add Redis cache container if realtime or caching is required
        if has_realtime or (state_management and "redis" in str(state_management).lower()):
            service_containers.append({
                "name": "redis_cache",
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "env_vars": []
            })
            container_groups.append("cache")

        # Reverse Proxy Routing rules
        routing_rules = [
            "Route '/' and static files directly to frontend container.",
            f"Route '/api/v1/*' requests to backend REST API service on port {be_port.split(':')[1]}."
        ]
        if has_realtime:
            routing_rules.append("Upgrade requests matching '/ws/v1/*' to standard bidirectional WebSocket connections and route to backend socket layer.")

        return {
            "status": "success",
            "infrastructure_strategy": {
                "deployment_model": "Containerized multi-tier architecture using microservices distribution.",
                "containerization_strategy": "Multi-stage production Dockerfiles isolating build assets from lightweight runtimes.",
                "cloud_strategy": "Managed serverless container service (AWS ECS Fargate or Google Cloud Run) backed by managed SQL/NoSQL resources.",
                "scalability_strategy": "Horizontal application autoscaling with Redis container backend session replication."
            },
            "containerization_architecture": {
                "docker_required": True,
                "container_groups": container_groups,
                "service_containers": service_containers,
                "orchestration_strategy": [
                    "Docker Compose orchestration handles local frontend, backend, caching, and database replication.",
                    "Production Kubernetes (K8s) Deployment definitions with horizontal pod autoscaler targets."
                ]
            },
            "deployment_pipeline_architecture": {
                "deployment_stages": ["lint", "test", "build_image", "push_registry", "deploy_stage", "deploy_prod"],
                "environment_flow": [
                    "Developer Branch -> Merge to Main -> Deploy to Staging (validation) -> Promote to Production (blue/green)."
                ],
                "rollback_strategy": [
                    "Automatic image-version rollback to previous Docker repository SHA target on health check ping failures."
                ]
            },
            "cicd_architecture": {
                "pipeline_stages": ["CI Validation", "CD Artifact Generation", "CD Deployment Orchestration"],
                "automation_targets": [
                    "Trigger automated tests and Docker image compilation on pull request merges.",
                    "Sync infrastructure declarations with GitOps controllers (e.g. ArgoCD)."
                ],
                "testing_gates": [
                    "Unit test suites coverage threshold must exceed 80%.",
                    "Static application security testing (SAST) scanning with zero high vulnerabilities allowed."
                ]
            },
            "cloud_infrastructure": {
                "providers": ["AWS (Amazon Web Services)", "GCP (Google Cloud Platform)"],
                "service_groups": [
                    "AWS ECS (Elastic Container Service) or GCP Cloud Run for application containers.",
                    "Amazon RDS or GCP Cloud SQL for database backend layers.",
                    "Amazon ElastiCache or GCP Cloud Memorystore for fast Redis caching."
                ],
                "deployment_targets": [
                    "Secure VPC subnet container endpoints behind Application Load Balancer layers."
                ]
            },
            "reverse_proxy_architecture": {
                "gateway_strategy": "Nginx edge ingress controller handling SSL termination and payload routing.",
                "load_balancing_rules": [
                    "Round-robin distribution of API requests across active healthy backend pod replicas.",
                    "WebSocket clients sticky sessions routing based on client IP hash rules."
                ],
                "routing_rules": routing_rules
            },
            "monitoring_observability": {
                "monitoring_targets": [
                    "Backend CPU/Memory utilization logs.",
                    "API request response times (Latency metrics).",
                    "Database active network connections and active operations pool."
                ],
                "logging_strategy": [
                    "Consolidate container stdout/stderr records into Central Logging service (AWS CloudWatch / ELK Stack)."
                ],
                "alerting_systems": [
                    "Pushes critical server errors notifications directly to Slack alerts / PagerDuty integration."
                ]
            },
            "environment_management": {
                "environment_groups": ["development", "staging", "production"],
                "secret_management_rules": [
                    "Inject database credentials, JWT secrets, and third-party APIs from cloud-native vaults (AWS Secrets Manager / GCP Secret Manager).",
                    "Prevent storing secrets, keys, or configurations in git codebase repositories."
                ],
                "configuration_layers": [
                    "Manage non-sensitive env variables inside environment files (.env) or K8s ConfigMaps."
                ]
            },
            "distributed_scalability": {
                "horizontal_scaling": True,
                "autoscaling_targets": ["backend", "frontend"],
                "high_load_services": ["backend"]
            },
            "production_optimization": {
                "performance_targets": [
                    "Ensure response latency remains under 200ms for REST requests.",
                    "Optimize Docker image bundle sizing to remain under 150MB."
                ],
                "caching_layers": ["Redis API route cache", "CDN static assets cache"],
                "optimization_rules": [
                    "Enable Gzip/Brotli compression at the Nginx edge layer.",
                    "Configure client-side browser caching headers for static frontend assets."
                ]
            },
            "deployment_workflows": [
                {
                    "workflow_name": "Staging Deployment Action",
                    "deployment_flow": [
                        "Lint and execute unit tests on backend/frontend code.",
                        "Build docker container images for all updated components.",
                        "Push compiled images to Docker Registry tag 'staging'.",
                        "Restart staging cluster containers and verify health endpoints status."
                    ]
                },
                {
                    "workflow_name": "Production Deployment Action",
                    "deployment_flow": [
                        "Perform blue/green environment switchover setup.",
                        "Promote 'staging' Docker image tag to release registry version tag.",
                        "Direct 10% traffic to green deployments pool and monitor logs.",
                        "Route 100% user traffic to green pool and terminate old blue server instances."
                    ]
                }
            ],
            "future_generation_context": {
                "important_notes_for_deployment_generation": [
                    "Ensure Nginx configs support WebSocket upgrade request headers.",
                    "Confirm database host variables resolve to docker network namespaces locally."
                ],
                "important_notes_for_backend_generation": [
                    "Do not bundle secrets inside the build. Inject them via runtime environment maps.",
                    "Configure database connection pools to handle dynamically scale backend pod counts."
                ],
                "important_notes_for_monitoring_agents": [
                    "Export metrics on '/metrics' endpoint using Prometheus format.",
                    "Provide logs containing trace-ids mapping REST endpoints to background workers."
                ]
            }
        }
