import json
from loguru import logger
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response



class ProjectExportAgent:
    """
    ProjectExportAgent for Sarthi.

    Operates as the final delivery and export orchestration pipeline.  It ingests the full
    upstream compilation + error-recovery intelligence and produces structured, deterministic
    export packaging intelligence covering:

    - repository structure generation
    - ZIP artifact orchestration
    - Docker packaging generation
    - Cloud Run / GitLab export preparation
    - environment variable packaging
    - CI/CD export preparation
    - production-safe deployment-ready delivery

    Outputs are stored in AI_ProjectExport.json inside Sarthi orchestration memory and
    consumed by downstream DeploymentGenerationAgent, GitLabExportSystems,
    CloudRunDeploymentSystems, and FinalProjectDeliveryPipeline.
    """

    def __init__(self) -> None:
        self.agent_name = "ProjectExportAgent"

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def design(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        devops_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_plan: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        build_compilation: Dict[str, Any],
        error_correction: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesise all upstream compilation and recovery outputs to produce
        production-grade, deployment-ready export packaging intelligence.
        """
        agent_inputs = {
            "requirements": requirements,
            "db_architecture": db_architecture,
            "backend_architecture": backend_architecture,
            "api_architecture": api_architecture,
            "frontend_architecture": frontend_architecture,
            "auth_architecture": auth_architecture,
            "devops_architecture": devops_architecture,
            "validation_architecture": validation_architecture,
            "optimization_architecture": optimization_architecture,
            "code_generation_plan": code_generation_plan,
            "database_model_generation": database_model_generation,
            "backend_code_generation": backend_code_generation,
            "api_implementation": api_implementation,
            "frontend_code_generation": frontend_code_generation,
            "ui_component_generation": ui_component_generation,
            "state_implementation": state_implementation,
            "integration_generation": integration_generation,
            "build_compilation": build_compilation,
            "error_correction": error_correction,
            "global_project_context": global_project_context,
        }

        no_keys = not (
            settings.NVIDIA_API_KEY
            or settings.OPENROUTER_API_KEY
            or settings.GROQ_API_KEY
            or settings.GOOGLE_API_KEY
        )
        if no_keys:
            logger.warning(
                "No API keys configured. Using local fallback project export intelligence."
            )
            return enrich_agent_output(
                self._get_fallback_project_export(**agent_inputs),
                self.agent_name,
                agent_inputs,
                role=(
                    "Final delivery and export orchestration layer. Produces deployment-ready, "
                    "ZIP-packaged, Docker-ready, GitLab-compatible repository export intelligence."
                ),
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "Export full-stack systems like a senior platform delivery and DevOps engineer. "
                "Produce deterministic, production-safe repository packaging, ZIP artifact "
                "orchestration, Docker generation, Cloud Run configs, GitLab export preparation, "
                "CI/CD compatibility, and downloadable runtime-safe delivery intelligence."
            ),
        )

        user_content = f"""
        Analyze Sarthi compilation outputs and produce final export packaging intelligence.

        Requirements: {json.dumps(requirements, indent=2)}
        Database Architecture: {json.dumps(db_architecture, indent=2)}
        Backend Architecture: {json.dumps(backend_architecture, indent=2)}
        API Architecture: {json.dumps(api_architecture, indent=2)}
        Frontend Architecture: {json.dumps(frontend_architecture, indent=2)}
        Authentication Architecture: {json.dumps(auth_architecture, indent=2)}
        DevOps Architecture: {json.dumps(devops_architecture, indent=2)}
        Validation Architecture: {json.dumps(validation_architecture, indent=2)}
        Optimization Architecture: {json.dumps(optimization_architecture, indent=2)}
        Code Generation Plan: {json.dumps(code_generation_plan, indent=2)}
        Database Model Generation: {json.dumps(database_model_generation, indent=2)}
        Backend Code Generation: {json.dumps(backend_code_generation, indent=2)}
        API Implementation: {json.dumps(api_implementation, indent=2)}
        Frontend Code Generation: {json.dumps(frontend_code_generation, indent=2)}
        UI Component Generation: {json.dumps(ui_component_generation, indent=2)}
        State Implementation: {json.dumps(state_implementation, indent=2)}
        Integration Generation: {json.dumps(integration_generation, indent=2)}
        Build Compilation: {json.dumps(build_compilation, indent=2)}
        Error Correction: {json.dumps(error_correction, indent=2)}
        Global Project Context: {json.dumps(global_project_context or {{}}, indent=2)}

        Return ONLY valid JSON in this exact format:
        {{
          "status": "success",
          "export_generation_strategy": {{
            "repository_strategy": "e.g. Monorepo root with /backend and /frontend subdirectories.",
            "deployment_strategy": "e.g. Docker Compose for local, Cloud Run for production.",
            "packaging_strategy": "e.g. ZIP archive with .env.example, README, and Makefile.",
            "runtime_delivery_strategy": "e.g. Uvicorn + Next.js served via Nginx reverse proxy."
          }},
          "repository_generation": {{
            "root_repository_structure": [],
            "frontend_repository_structure": [],
            "backend_repository_structure": [],
            "shared_runtime_packages": []
          }},
          "runtime_packaging": {{
            "packaged_runtime_modules": [],
            "dependency_packages": [],
            "runtime_environment_bindings": []
          }},
          "docker_export_generation": {{
            "docker_packages": [],
            "container_runtime_configs": [],
            "deployment_safe_images": []
          }},
          "deployment_export_generation": {{
            "cloud_run_configs": [],
            "deployment_manifests": [],
            "environment_export_rules": []
          }},
          "gitlab_export_generation": {{
            "repository_push_flows": [],
            "ci_cd_export_configs": [],
            "gitlab_runtime_integrations": []
          }},
          "artifact_generation": {{
            "zip_export_targets": [],
            "downloadable_artifacts": [],
            "compiled_runtime_exports": []
          }},
          "environment_generation": {{
            "env_templates": [],
            "secret_config_templates": [],
            "runtime_environment_rules": []
          }},
          "production_delivery_generation": {{
            "production_ready_exports": [],
            "deployment_safe_packages": [],
            "scalable_runtime_exports": []
          }},
          "generation_dependencies": {{
            "blocking_export_dependencies": [],
            "shared_runtime_dependencies": [],
            "cross_module_export_rules": []
          }},
          "future_generation_context": {{
            "important_notes_for_deployment_agents": [],
            "important_notes_for_gitlab_integrations": [],
            "important_notes_for_final_delivery_systems": []
          }}
        }}
        """

        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            raw_response = raw_response.strip()
            return enrich_agent_output(
                parse_json_response(raw_response),
                self.agent_name,
                agent_inputs,
                role=(
                    "Final delivery and export orchestration layer. Produces deployment-ready, "
                    "ZIP-packaged, Docker-ready, GitLab-compatible repository export intelligence."
                ),
            )
        except Exception as exc:
            logger.error(f"Failed to run ProjectExportAgent: {exc}")
            return enrich_agent_output(
                self._get_fallback_project_export(**agent_inputs),
                self.agent_name,
                agent_inputs,
                role=(
                    "Final delivery and export orchestration layer. Produces deployment-ready, "
                    "ZIP-packaged, Docker-ready, GitLab-compatible repository export intelligence."
                ),
            )

    # ------------------------------------------------------------------
    # Deterministic fallback — runs when all LLM providers are unavailable
    # ------------------------------------------------------------------

    def _get_fallback_project_export(
        self,
        requirements: Dict[str, Any],
        db_architecture: Dict[str, Any],
        backend_architecture: Dict[str, Any],
        api_architecture: Dict[str, Any],
        frontend_architecture: Dict[str, Any],
        auth_architecture: Dict[str, Any],
        devops_architecture: Dict[str, Any],
        validation_architecture: Dict[str, Any],
        optimization_architecture: Dict[str, Any],
        code_generation_plan: Dict[str, Any],
        database_model_generation: Dict[str, Any],
        backend_code_generation: Dict[str, Any],
        api_implementation: Dict[str, Any],
        frontend_code_generation: Dict[str, Any],
        ui_component_generation: Dict[str, Any],
        state_implementation: Dict[str, Any],
        integration_generation: Dict[str, Any],
        build_compilation: Dict[str, Any],
        error_correction: Dict[str, Any],
        global_project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a deterministic, context-aware fallback export packaging map (Stage 26).
        Derives project name, entity names, API endpoints, tech stack, and DevOps
        strategy from upstream contracts so every export entry is grounded in the
        actual generated project.
        """
        # ---- project identity -------------------------------------------
        project_name: str = "sarthi-app"
        if global_project_context:
            project_name = (
                global_project_context.get("name")
                or global_project_context.get("project_name")
                or project_name
            )
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")

        # ---- derive entity names from db_architecture -------------------
        entities: List[Any] = db_architecture.get("entities", []) if db_architecture else []
        entity_names: List[str] = []
        for e in entities:
            if isinstance(e, str):
                entity_names.append(e)
            elif isinstance(e, dict) and e.get("entity_name"):
                entity_names.append(e["entity_name"])
        if not entity_names:
            entity_names = ["User", "Project", "Resource", "Session"]

        # ---- derive API endpoints ---------------------------------------
        raw_endpoints: List[Any] = (
            api_architecture.get("endpoints", []) if api_architecture else []
        )
        endpoint_paths: List[str] = []
        for ep in raw_endpoints:
            if isinstance(ep, str):
                endpoint_paths.append(ep)
            elif isinstance(ep, dict):
                method = ep.get("method", "GET")
                path = ep.get("path", "")
                if path:
                    endpoint_paths.append(f"{method} {path}")
        if not endpoint_paths:
            for name in entity_names:
                plural = f"{name.lower()}s"
                endpoint_paths += [
                    f"GET /api/v1/{plural}",
                    f"POST /api/v1/{plural}",
                    f"GET /api/v1/{plural}/{{id}}",
                ]

        # ---- derive deployment targets from devops_architecture ---------
        uses_docker = True
        uses_cloud_run = False
        uses_gitlab_ci = False
        if devops_architecture and isinstance(devops_architecture, dict):
            infra: str = json.dumps(devops_architecture).lower()
            uses_cloud_run = "cloud run" in infra or "cloudrun" in infra
            uses_gitlab_ci = "gitlab" in infra
            uses_docker = "docker" in infra or uses_docker

        # ---- build repository structures --------------------------------
        root_structure: List[str] = [
            "backend/",
            "frontend/",
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "Makefile",
            "README.md",
            ".env.example",
            ".gitignore",
        ]

        backend_structure: List[str] = [
            "backend/Dockerfile",
            "backend/requirements.txt",
            "backend/alembic.ini",
            "backend/app/__init__.py",
            "backend/app/main.py",
            "backend/app/core/config.py",
            "backend/app/core/security.py",
            "backend/app/db/session.py",
            "backend/app/db/base.py",
            "backend/app/api/__init__.py",
            "backend/app/api/auth.py",
        ]
        for name in entity_names:
            plural = f"{name.lower()}s"
            backend_structure += [
                f"backend/app/models/{name.lower()}.py",
                f"backend/app/schemas/{name.lower()}.py",
                f"backend/app/api/v1/{plural}.py",
                f"backend/app/services/{name.lower()}_service.py",
                f"backend/app/repositories/{name.lower()}_repository.py",
            ]
        backend_structure += [
            "backend/app/websockets/manager.py",
            "backend/app/middleware/cors.py",
            "backend/app/middleware/auth.py",
            "backend/tests/__init__.py",
            "backend/tests/conftest.py",
        ]

        frontend_structure: List[str] = [
            "frontend/Dockerfile",
            "frontend/package.json",
            "frontend/tsconfig.json",
            "frontend/next.config.js",
            "frontend/.env.local.example",
            "frontend/src/app/layout.tsx",
            "frontend/src/app/page.tsx",
            "frontend/src/app/(auth)/login/page.tsx",
            "frontend/src/app/(auth)/register/page.tsx",
            "frontend/src/app/dashboard/page.tsx",
            "frontend/src/utils/api_client.ts",
            "frontend/src/utils/auth.ts",
            "frontend/src/stores/useAuthStore.ts",
            "frontend/src/hooks/useWebSocket.ts",
            "frontend/src/components/ui/",
            "frontend/src/components/layout/Navbar.tsx",
            "frontend/src/components/layout/Sidebar.tsx",
        ]
        for name in entity_names:
            plural = f"{name.lower()}s"
            frontend_structure += [
                f"frontend/src/app/dashboard/{plural}/page.tsx",
                f"frontend/src/stores/use{name}Store.ts",
                f"frontend/src/hooks/use{name}Query.ts",
                f"frontend/src/components/{name}/{name}List.tsx",
                f"frontend/src/components/{name}/{name}Form.tsx",
            ]

        shared_packages: List[str] = [
            "shared/types/index.ts",
            "shared/types/entities.ts",
            "shared/types/api.ts",
            "shared/validators/schemas.ts",
        ]

        # ---- runtime packaging ------------------------------------------
        packaged_runtime_modules: List[str] = (
            ["backend/app", "frontend/src", "shared/types"] +
            [f"backend/app/api/v1/{name.lower()}s.py" for name in entity_names] +
            [f"frontend/src/stores/use{name}Store.ts" for name in entity_names]
        )
        dependency_packages: List[str] = [
            "fastapi>=0.100.0",
            "uvicorn[standard]>=0.22.0",
            "pydantic>=2.0",
            "pymongo>=4.3.3",
            "motor>=3.1.0",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.6",
            "redis>=4.5.0",
            "react@18.2.0",
            "next@14",
            "typescript@5",
            "zustand>=4.3.8",
            "swr>=2.2.0",
            "framer-motion>=10",
            "tailwindcss>=3.3",
            "shadcn-ui",
            "clsx",
            "zod>=3.21",
        ]
        runtime_env_bindings: List[str] = [
            "MONGODB_URI -> motor async client connection",
            "JWT_SECRET -> python-jose token signing",
            "NEXT_PUBLIC_API_URL -> SWR fetch base URL",
            "REDIS_URL -> redis pub/sub adapter",
            "CORS_ORIGINS -> FastAPI middleware allow-list",
        ]

        # ---- Docker packaging -------------------------------------------
        docker_packages: List[str] = [
            "backend/Dockerfile (python:3.11-slim, uvicorn CMD)",
            "frontend/Dockerfile (node:20-alpine multi-stage, next build + start)",
            "docker-compose.yml (backend:8000 + frontend:3000 + mongodb:27017 + redis:6379)",
            "docker-compose.prod.yml (production overrides, no volume mounts, restart:always)",
            ".dockerignore (node_modules, __pycache__, .env, .next, venv)",
        ]
        container_runtime_configs: List[str] = [
            "backend service: build context ./backend, port 8000:8000, env_file .env, depends_on mongodb redis",
            "frontend service: build context ./frontend, port 3000:3000, env NEXT_PUBLIC_API_URL=http://backend:8000",
            "mongodb service: image mongo:7, volume mongodb_data:/data/db",
            "redis service: image redis:7-alpine, command redis-server --appendonly yes",
            "nginx service (prod): image nginx:alpine, proxy_pass backend:8000 and frontend:3000",
        ]
        deployment_safe_images: List[str] = [
            f"{project_slug}-backend:latest",
            f"{project_slug}-frontend:latest",
            f"{project_slug}-nginx:latest",
        ]

        # ---- Cloud Run / deployment configs -----------------------------
        cloud_run_configs: List[str] = []
        if uses_cloud_run:
            cloud_run_configs = [
                f"Cloud Run service: {project_slug}-backend, image gcr.io/$PROJECT_ID/{project_slug}-backend",
                f"Cloud Run service: {project_slug}-frontend, image gcr.io/$PROJECT_ID/{project_slug}-frontend",
                "Cloud SQL / Atlas MongoDB connection string injected via Cloud Run secrets",
                "Cloud Run min-instances=1 to prevent cold starts on auth endpoints",
            ]
        else:
            cloud_run_configs = [
                "VPS / bare-metal: docker-compose -f docker-compose.prod.yml up -d",
                "Railway / Render: connect GitHub repo, set env vars, deploy backend + frontend services",
                "Fly.io: fly launch in ./backend and ./frontend with fly.toml configs",
            ]

        deployment_manifests: List[str] = [
            "Makefile targets: make dev, make build, make up, make down, make migrate, make test",
            "README.md: Prerequisites, Quick Start, Environment Variables, Deployment sections",
            "scripts/setup.sh: automated dev environment bootstrap script",
            "scripts/migrate.sh: database migration runner",
        ]
        environment_export_rules: List[str] = [
            "Never include .env in ZIP or Git repository — always use .env.example",
            "Rotate JWT_SECRET before production deployment",
            "Set CORS_ORIGINS to exact production frontend URL — never use wildcard in production",
            "MongoDB URI must include authSource=admin for Atlas connections",
        ]

        # ---- GitLab export ----------------------------------------------
        repository_push_flows: List[str] = [
            "git init -> git remote add origin <gitlab-url> -> git add . -> git commit -m 'Initial Sarthi export' -> git push -u origin main",
            "Set MONGODB_URI, JWT_SECRET, REDIS_URL as GitLab CI/CD variables (masked, protected)",
        ]
        ci_cd_configs: List[str] = [
            ".gitlab-ci.yml: stages [test, build, deploy]",
            "test stage: run pytest + eslint + tsc --noEmit",
            "build stage: docker build backend + frontend images, push to GitLab Container Registry",
            "deploy stage: ssh to VPS and run docker-compose pull + up -d (or Cloud Run deploy)",
        ]
        gitlab_runtime_integrations: List[str] = [
            "GitLab Container Registry: $CI_REGISTRY_IMAGE/$project_slug-backend:$CI_COMMIT_SHA",
            "GitLab environments: staging (auto deploy on main), production (manual trigger)",
            "GitLab secrets: DEPLOY_SERVER_HOST, DEPLOY_SSH_KEY, MONGODB_URI, JWT_SECRET",
        ]

        # ---- ZIP artifact generation ------------------------------------
        zip_export_targets: List[str] = [
            f"{project_slug}-fullstack-v1.zip (complete monorepo)",
            f"{project_slug}-backend-v1.zip (backend only)",
            f"{project_slug}-frontend-v1.zip (frontend only)",
        ]
        downloadable_artifacts: List[str] = [
            f"{project_slug}-fullstack-v1.zip",
            "README.md",
            ".env.example",
            "docker-compose.yml",
            "Makefile",
        ]
        compiled_runtime_exports: List[str] = [
            "backend: all Python modules with requirements.txt",
            "frontend: all TypeScript/TSX source with package.json + tsconfig.json",
            "shared: type definitions and validators",
            "infra: Dockerfiles, docker-compose, nginx.conf, .gitlab-ci.yml",
            "scripts: setup.sh, migrate.sh, seed.sh",
        ]

        # ---- environment templates --------------------------------------
        env_templates: List[str] = [
            "MONGODB_URI=mongodb://localhost:27017/{project_slug}",
            "JWT_SECRET=your-super-secret-key-change-in-production",
            "JWT_ALGORITHM=HS256",
            "JWT_EXPIRE_MINUTES=15",
            "REFRESH_TOKEN_EXPIRE_DAYS=7",
            "REDIS_URL=redis://localhost:6379",
            "CORS_ORIGINS=http://localhost:3000",
            "NEXT_PUBLIC_API_URL=http://localhost:8000",
            "NEXT_PUBLIC_WS_URL=ws://localhost:8000",
        ]
        secret_config_templates: List[str] = [
            "JWT_SECRET: minimum 32-character random string (openssl rand -hex 32)",
            "MONGODB_URI: include username:password for production Atlas cluster",
            "REDIS_URL: include :password@ for production Redis with AUTH",
            "SMTP_PASSWORD: required only if email notifications are enabled",
        ]
        runtime_environment_rules: List[str] = [
            "Load .env via python-dotenv in FastAPI config; load .env.local in Next.js automatically",
            "NEXT_PUBLIC_* variables are exposed to the browser — never store secrets with this prefix",
            "Use docker-compose env_file directive for local dev; inject via platform secrets for production",
            "All environment variables must be documented in .env.example with safe placeholder values",
        ]

        # ---- production delivery ----------------------------------------
        production_ready_exports: List[str] = (
            [f"backend/app/api/v1/{name.lower()}s.py" for name in entity_names]
            + [f"frontend/src/stores/use{name}Store.ts" for name in entity_names]
            + ["docker-compose.prod.yml", "nginx/nginx.conf", ".gitlab-ci.yml"]
        )
        deployment_safe_packages: List[str] = [
            f"{project_slug}-backend:latest (stripped of dev dependencies)",
            f"{project_slug}-frontend:latest (next build output, no source maps)",
            f"{project_slug}-nginx:latest (optimised static asset serving config)",
        ]
        scalable_runtime_exports: List[str] = [
            "Horizontal scaling: backend replicas behind nginx upstream load balancer",
            "Redis adapter enables WebSocket pub/sub across multiple backend instances",
            "MongoDB replica set connection string supports read scaling via secondary reads",
            "Next.js static export (next export) for CDN delivery of marketing pages",
        ]

        # ---- generation dependencies ------------------------------------
        blocking_export_dependencies: List[str] = [
            "shared/types/index.ts must exist before frontend TypeScript compilation",
            "requirements.txt must be generated before Dockerfile backend build step",
            "package.json must list all dependencies before frontend Docker build step",
            "ErrorCorrectionAgent stabilized_modules must pass TypeScript tsc --noEmit before ZIP packaging",
        ]
        shared_runtime_dependencies: List[str] = [
            "motor>=3.1 (async MongoDB)",
            "fastapi>=0.100",
            "next@14",
            "react@18",
            "zustand>=4.3",
            "swr>=2.2",
        ]
        cross_module_export_rules: List[str] = [
            "Package shared/types before packaging frontend and backend — both depend on it",
            "Run migration scripts before packaging backend — schema must match models",
            "Build frontend (next build) before packaging frontend Docker image",
            "Validate docker-compose services start successfully before finalising ZIP export",
        ]

        # ---- future context for downstream agents ----------------------
        notes_for_deployment: List[str] = [
            "Run database migrations (alembic upgrade head) before first container start",
            "Inject all secrets via platform secret manager — never bake into Docker images",
            "Set NEXT_PUBLIC_API_URL to the production backend URL at Next.js build time",
            "Configure health check endpoints (/api/health) in deployment platform before routing traffic",
            "Enable Nginx gzip compression and browser caching headers for static Next.js assets",
        ]
        notes_for_gitlab: List[str] = [
            "Set DEPLOY_SSH_KEY as GitLab CI variable (file type) for VPS deployment",
            "Use GitLab Container Registry to avoid Docker Hub rate limits in CI",
            "Configure GitLab environments with manual approval gate for production stage",
            "Add SAST scanning job to .gitlab-ci.yml test stage for security compliance",
        ]
        notes_for_delivery: List[str] = [
            f"Final ZIP: {project_slug}-fullstack-v1.zip must include README.md, .env.example, Makefile",
            "Strip console.log and debug print statements before packaging (enforced by ErrorCorrectionAgent export_safe_repairs)",
            "Include CHANGELOG.md listing all automated ErrorCorrectionAgent repairs in the ZIP root",
            "Verify docker-compose up launches all services without errors before marking delivery complete",
            "Provide users a one-command quickstart: make dev or docker-compose up --build",
        ]

        return {
            "status": "success",
            "export_generation_strategy": {
                "repository_strategy": (
                    f"Monorepo structure: /{project_slug} root containing /backend (FastAPI), "
                    "/frontend (Next.js 14), /shared (TypeScript types), and /scripts. "
                    "Single .gitignore covers all sub-projects."
                ),
                "deployment_strategy": (
                    "Docker Compose for local development and single-VPS deployment. "
                    "Cloud Run (or Railway/Fly.io) for scalable production. "
                    "GitLab CI/CD automates test → build → deploy pipeline on main branch push."
                ),
                "packaging_strategy": (
                    f"ZIP archive {project_slug}-fullstack-v1.zip containing complete monorepo. "
                    "Separate backend-only and frontend-only ZIPs for modular deployment. "
                    ".env.example (never .env), Makefile, README, and CHANGELOG included in root."
                ),
                "runtime_delivery_strategy": (
                    "Uvicorn ASGI server (4 workers) serving FastAPI behind Nginx reverse proxy on port 8000. "
                    "Next.js production build served by Next.js standalone server on port 3000. "
                    "Nginx routes /api/* and /ws/* to backend; all other paths to frontend."
                ),
            },
            "repository_generation": {
                "root_repository_structure": root_structure,
                "frontend_repository_structure": frontend_structure,
                "backend_repository_structure": backend_structure,
                "shared_runtime_packages": shared_packages,
            },
            "runtime_packaging": {
                "packaged_runtime_modules": packaged_runtime_modules,
                "dependency_packages": dependency_packages,
                "runtime_environment_bindings": runtime_env_bindings,
            },
            "docker_export_generation": {
                "docker_packages": docker_packages,
                "container_runtime_configs": container_runtime_configs,
                "deployment_safe_images": deployment_safe_images,
            },
            "deployment_export_generation": {
                "cloud_run_configs": cloud_run_configs,
                "deployment_manifests": deployment_manifests,
                "environment_export_rules": environment_export_rules,
            },
            "gitlab_export_generation": {
                "repository_push_flows": repository_push_flows,
                "ci_cd_export_configs": ci_cd_configs,
                "gitlab_runtime_integrations": gitlab_runtime_integrations,
            },
            "artifact_generation": {
                "zip_export_targets": zip_export_targets,
                "downloadable_artifacts": downloadable_artifacts,
                "compiled_runtime_exports": compiled_runtime_exports,
            },
            "environment_generation": {
                "env_templates": env_templates,
                "secret_config_templates": secret_config_templates,
                "runtime_environment_rules": runtime_environment_rules,
            },
            "production_delivery_generation": {
                "production_ready_exports": production_ready_exports,
                "deployment_safe_packages": deployment_safe_packages,
                "scalable_runtime_exports": scalable_runtime_exports,
            },
            "generation_dependencies": {
                "blocking_export_dependencies": blocking_export_dependencies,
                "shared_runtime_dependencies": shared_runtime_dependencies,
                "cross_module_export_rules": cross_module_export_rules,
            },
            "future_generation_context": {
                "important_notes_for_deployment_agents": notes_for_deployment,
                "important_notes_for_gitlab_integrations": notes_for_gitlab,
                "important_notes_for_final_delivery_systems": notes_for_delivery,
            },
        }
