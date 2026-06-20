"""
CodeSynthesizerAgent for Sarthi.

Replaces the old single-call monolithic code generation (max_tokens=6000, ~5 files)
with a multi-phase synthesis engine that generates a complete, integrated, production-ready
project like Claude Code, Antigravity, or Codex would.

Phases:
  1. Backend  — models, schemas, services, API routes, config, auth middleware
  2. Frontend — pages, components, stores, hooks, styles, layout
  3. Infrastructure — Docker, README, env, tests, shared types, scripts
  4. Review & Self-Heal — validates cross-file integrity, fixes broken imports/contracts
"""

import json
from loguru import logger
from typing import Any, Dict, List, Optional
from app.services.llm_router import get_llm_completion
from app.agents.context import parse_json_response


class CodeSynthesizerAgent:

    def __init__(self) -> None:
        self.agent_name = "CodeSynthesizerAgent"

    # ──────────────────────────────────────────────────────────────
    # Context Extraction Helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_project_info(project_doc: Dict) -> Dict:
        reqs = project_doc.get("requirements", {}) or {}
        bp = project_doc.get("blueprint", {}) or project_doc.get("initial_prompt", {}) or {}
        overview = reqs.get("project_overview", {}) or {}
        return {
            "name": overview.get("name") or bp.get("name") or project_doc.get("name", "SarthiApp"),
            "description": overview.get("description") or bp.get("idea", "A full-stack web application"),
            "features": reqs.get("features", []) or bp.get("features", []),
            "tech_stack": reqs.get("tech_stack", {}),
            "category": project_doc.get("category", "web"),
        }

    @staticmethod
    def _extract_document_context(project_doc: Dict) -> Dict:
        """Extract PRD/TRD/MRD content to drive code generation."""
        prd = project_doc.get("prd", "") or ""
        trd = project_doc.get("trd", "") or ""
        mrd = project_doc.get("mrd", "") or ""
        impl_plan = project_doc.get("implementation_plan", {}) or {}

        return {
            "prd_summary": prd[:5000] if prd else "No PRD available",
            "trd_summary": trd[:5000] if trd else "No TRD available",
            "mrd_summary": mrd[:4000] if mrd else "No MRD available",
            "implementation_plan": json.dumps(impl_plan)[:4000] if impl_plan else "No implementation plan",
        }

    @staticmethod
    def _extract_entities(project_doc: Dict) -> List[Dict]:
        db_arch = project_doc.get("db_architecture", {}) or {}
        raw = db_arch.get("entities", [])
        out: List[Dict] = []
        for e in raw:
            if isinstance(e, dict):
                out.append({
                    "name": e.get("entity_name", "Item"),
                    "fields": e.get("fields", []),
                    "description": e.get("description", ""),
                })
            elif isinstance(e, str):
                out.append({"name": e, "fields": [], "description": ""})
        if not out:
            out = [{"name": "User", "fields": [
                {"name": "email", "type": "string", "required": True, "indexed": True},
                {"name": "password_hash", "type": "string", "required": True},
                {"name": "full_name", "type": "string", "required": False},
                {"name": "role", "type": "string", "required": False},
                {"name": "is_active", "type": "boolean", "required": False},
            ], "description": "Application user"}]
        return out

    @staticmethod
    def _extract_relationships(project_doc: Dict) -> List[Dict]:
        db_arch = project_doc.get("db_architecture", {}) or {}
        raw = db_arch.get("relationships", [])
        out: List[Dict] = []
        for r in raw:
            if isinstance(r, dict):
                out.append({
                    "from": r.get("from_entity", ""),
                    "to": r.get("to_entity", ""),
                    "type": r.get("relationship_type", "one-to-many"),
                })
        return out

    @staticmethod
    def _extract_endpoints(project_doc: Dict) -> List[Dict]:
        api_arch = project_doc.get("api_architecture", {}) or {}
        raw = api_arch.get("endpoints", [])
        out: List[Dict] = []
        for ep in raw:
            if isinstance(ep, dict):
                out.append({
                    "method": ep.get("method", "GET"),
                    "path": ep.get("path", ""),
                    "description": ep.get("description", ""),
                    "requires_auth": ep.get("requires_auth", False),
                    "request_body": ep.get("request_body", {}),
                    "response_payload": ep.get("response_payload", {}),
                })
            elif isinstance(ep, str):
                parts = ep.split(" ", 1)
                out.append({"method": parts[0] if len(parts) > 1 else "GET", "path": parts[-1]})
        return out

    @staticmethod
    def _extract_pages(project_doc: Dict) -> List[Dict]:
        fe_arch = project_doc.get("frontend_architecture", {}) or {}
        raw = fe_arch.get("pages", [])
        out: List[Dict] = []
        for p in raw:
            if isinstance(p, dict):
                out.append({
                    "name": p.get("page_name", "Page"),
                    "route": p.get("route", "/"),
                    "protected": p.get("protected", False),
                })
            elif isinstance(p, str):
                out.append({"name": p, "route": f"/{p.lower()}", "protected": False})
        return out

    @staticmethod
    def _extract_design_tokens(project_doc: Dict) -> Dict:
        theme = project_doc.get("theme_styling", {}) or {}
        color_palette = theme.get("color_palette", {})
        if not color_palette and project_doc.get("theme_palette"):
            # Fallback to UI-selected theme palette
            tp = project_doc.get("theme_palette")
            color_palette = {
                "primary": tp.get("primary"),
                "secondary": tp.get("secondary"),
                "background": tp.get("background"),
                "card_bg": tp.get("card_bg"),
                "text": tp.get("text"),
                "border": tp.get("border"),
                "is_dark": tp.get("is_dark")
            }
        return {
            "color_palette": color_palette,
            "typography": theme.get("typography_system", {}),
            "dark_mode": theme.get("dark_light_mode", {}),
            "component_styling": theme.get("component_styling", {}),
            "spacing": theme.get("spacing_system", theme.get("spacing", {})),
            "layout": theme.get("layout_system", theme.get("layout", {})),
            "border_radius": theme.get("border_radius", {}),
            "shadows": theme.get("shadows", theme.get("box_shadows", {})),
        }

    @staticmethod
    def _extract_auth_config(project_doc: Dict) -> Dict:
        auth = project_doc.get("auth_architecture", {}) or {}
        return {
            "strategy": auth.get("authentication_strategy", {}),
            "rbac": auth.get("role_based_access_control", {}),
        }

    @staticmethod
    def _extract_stores(project_doc: Dict) -> List[Dict]:
        state = project_doc.get("state_management", {}) or {}
        gs = state.get("global_state_architecture", {}) or {}
        raw = gs.get("global_states", [])
        out: List[Dict] = []
        for s in raw:
            if isinstance(s, dict):
                out.append({"name": s.get("store_name", ""), "variables": s.get("state_variables", [])})
        return out

    @staticmethod
    def _get_db_type(project_doc: Dict) -> str:
        db_arch = project_doc.get("db_architecture", {}) or {}
        strat = db_arch.get("database_strategy", {}) or {}
        return strat.get("primary_database", "MongoDB")

    # ──────────────────────────────────────────────────────────────
    # Prompt Builders
    # ──────────────────────────────────────────────────────────────

    def _fmt_entities(self, entities: List[Dict]) -> str:
        lines: List[str] = []
        for e in entities:
            fields_str = ""
            for f in e.get("fields", []):
                if isinstance(f, dict):
                    fields_str += f"\n      - {f.get('name','field')}: {f.get('type','string')} (required={f.get('required',False)}, indexed={f.get('indexed',False)})"
            lines.append(f"  {e['name']}: {e.get('description','')}{fields_str}")
        return "\n".join(lines) or "  No entities defined — create User entity with basic CRUD"

    def _fmt_endpoints(self, endpoints: List[Dict], limit: int = 40) -> str:
        lines = [f"  {ep.get('method','GET')} {ep.get('path','')} — auth={ep.get('requires_auth',False)}" for ep in endpoints[:limit]]
        return "\n".join(lines) or "  Generate standard CRUD endpoints per entity"

    def _fmt_file_list(self, files: List[Dict], limit: int = 50) -> str:
        return "\n".join([f"  - {f.get('path','')}" for f in files[:limit]])

    # ---------- Phase 1: Backend ----------

    def _build_backend_prompt(self, info: Dict, entities: List[Dict], rels: List[Dict],
                              endpoints: List[Dict], auth: Dict, db_type: str,
                              stack: Dict[str, Any], doc_context: Optional[Dict] = None) -> str:
        rels_text = "\n".join([f"  {r['from']} -> {r['to']} ({r['type']})" for r in rels]) or "  None"
        
        backend_framework = stack["backend"]
        
        if backend_framework == "fastapi":
            if db_type.lower() in ("postgresql", "postgres", "sqlite", "mysql", "mariadb"):
                db_inst = (
                    f"Use {db_type} with SQLAlchemy async engine (asyncpg driver).\n"
                    "Create declarative Base models. Include Alembic migration setup."
                )
            else:
                db_inst = (
                    "Use MongoDB with motor async driver.\n"
                    "Create Pydantic models for document schemas.\n"
                    "Do NOT use $search — use $text or regex for search."
                )
            
            entity_file_list = ""
            for e in entities:
                ename = e['name'].lower()
                entity_file_list += f"  - backend/app/models/{ename}.py — {e['name']} DB model with ALL fields\n"
                entity_file_list += f"  - backend/app/schemas/{ename}.py — {e['name']}Create, {e['name']}Update, {e['name']}Response Pydantic schemas\n"
                entity_file_list += f"  - backend/app/api/v1/{ename}s.py — full CRUD routes for {e['name']} (GET list, GET by id, POST, PUT, DELETE)\n"
                entity_file_list += f"  - backend/app/services/{ename}_service.py — {e['name']} business logic layer\n"

            files_to_gen = f"""1. backend/requirements.txt — all deps with pinned versions
2. backend/app/__init__.py
3. backend/app/main.py — FastAPI app, CORS, lifespan, include ALL routers matching the PRD
4. backend/app/core/__init__.py
5. backend/app/core/config.py — Pydantic BaseSettings, env vars
6. backend/app/core/security.py — JWT create/verify, password hash/verify
7. backend/app/database.py — DB connection setup + client
8. backend/app/api/__init__.py
9. backend/app/api/auth.py — /auth/signup, /auth/login, /auth/refresh, /auth/me
10. backend/app/middleware/auth.py — get_current_user dependency
PER-ENTITY FILES (generate ALL of these for EVERY entity mentioned in PRD/TRD, at minimum yielding 5 functional interconnected modules):
{entity_file_list}"""
            
            rules = """- EVERY file must be 100% COMPLETE — never use "...", "pass", "add more here", or omitting sections. Write out the actual implementations.
- ALL imports must resolve to actual files listed above.
- Ensure the API logic matches the TRD closely.
- Use async/await for ALL DB operations.
- Proper error handling with HTTPException.
- Use Depends() for auth injection on protected routes.
- You MUST generate model, schema, route, and service files for EVERY entity."""

        elif backend_framework == "django":
            db_inst = f"Use Django ORM configured for {db_type}."
            files_to_gen = f"""1. backend/requirements.txt — django, djangorestframework, djangorestframework-simplejwt, corsheaders, and database drivers.
2. backend/manage.py — Django management script
3. backend/project/settings.py — Django settings with SimpleJWT and CORS configured
4. backend/project/urls.py — Django root URL config
5. backend/project/wsgi.py / asgi.py
6. backend/app/models.py — Django models for all entities: {", ".join([e['name'] for e in entities])}
7. backend/app/serializers.py — DRF serializers for all entities
8. backend/app/views.py — DRF ViewSets / views for CRUD and authentication
9. backend/app/urls.py — app specific endpoints routing to views
10. backend/app/admin.py — django admin registrations"""
            
            rules = """- Use Django and Django REST Framework (DRF) with SimpleJWT auth.
- Write full, complete django files.
- Setup standard Django project layout under `backend/project` and app under `backend/app`.
- Ensure all views return correct data structures matching the endpoints contract."""

        elif backend_framework == "springboot":
            db_inst = f"Use Spring Data JPA configured for {db_type}."
            entity_classes = ""
            for e in entities:
                ename = e['name']
                entity_classes += f"  - backend/src/main/java/com/sarthi/app/model/{ename}.java — JPA Entity class\n"
                entity_classes += f"  - backend/src/main/java/com/sarthi/app/repository/{ename}Repository.java — Repository interface\n"
                entity_classes += f"  - backend/src/main/java/com/sarthi/app/service/{ename}Service.java — Service class\n"
                entity_classes += f"  - backend/src/main/java/com/sarthi/app/controller/{ename}Controller.java — RestController class\n"

            files_to_gen = f"""1. backend/pom.xml — Maven configuration with spring-boot-starter-web, spring-boot-starter-data-jpa, spring-boot-starter-security, spring-boot-starter-validation, jwt dependencies, and DB driver.
2. backend/src/main/resources/application.properties — spring datasource and server configurations.
3. backend/src/main/java/com/sarthi/app/Application.java — Spring Boot entry point with @SpringBootApplication
4. backend/src/main/java/com/sarthi/app/config/SecurityConfig.java — Spring Security configuration with JWT filter
5. backend/src/main/java/com/sarthi/app/config/JwtUtils.java — JWT token generation and validation utilities
6. backend/src/main/java/com/sarthi/app/controller/AuthController.java — Auth endpoints (/login, /signup)
PER-ENTITY Java Classes (generate Entity, Repository, Service, Controller for each):
{entity_classes}"""
            
            rules = """- Use Spring Boot 3.x with Java 17.
- Write complete Java files with all annotations (@Entity, @Repository, @Service, @RestController, etc.).
- Ensure package structure: com.sarthi.app."""

        elif backend_framework == "express":
            db_inst = f"Use Express.js with database driver for {db_type}."
            entity_files = ""
            for e in entities:
                ename = e['name'].lower()
                entity_files += f"  - backend/src/models/{e['name']}.js — DB schema model\n"
                entity_files += f"  - backend/src/controllers/{ename}Controller.js — controller handlers\n"
                entity_files += f"  - backend/src/routes/{ename}Routes.js — route declarations\n"

            files_to_gen = f"""1. backend/package.json — express, mongoose/pg, jsonwebtoken, bcryptjs, cors, dotenv.
2. backend/src/index.js — express entrypoint with routing, middleware, server listener
3. backend/src/config/db.js — database connection configuration
4. backend/src/middleware/auth.js — JWT verification middleware
5. backend/src/controllers/authController.js — authentication views (login/signup)
PER-ENTITY Files:
{entity_files}"""
            
            rules = """- Use Node.js Express.
- Structure routes, controllers, and models cleanly.
- Write complete Javascript/ES6 files."""

        else:
            db_inst = f"Use database driver for {db_type}."
            files_to_gen = f"""1. backend/requirements.txt
2. backend/app.py — main application entrypoint
3. backend/models.py — database models
4. backend/routes.py — app routing and controllers"""
            rules = f"- Use {backend_framework} backend."

        # Document context section
        doc_section = ""
        if doc_context:
            doc_section = f"""\nPROJECT DOCUMENTATION (SINGLE SOURCE OF TRUTH — ALL generated features MUST ALIGN exactly with these docs):
PRD: {doc_context['prd_summary']}
TRD: {doc_context['trd_summary']}
MRD: {doc_context['mrd_summary']}
Implementation Plan: {doc_context['implementation_plan']}

MINIMUM SCOPE REQUIREMENT: You MUST generate a production-ready backend supporting AT LEAST 5 core features or modules derived from the above documents. If the PRD demands more, generate them all. Ensure absolute complete interconnectivity without omitting ANY controllers, routes, or services.
"""

        return f"""Generate the COMPLETE backend codebase for "{info['name']}" using {backend_framework.upper()} tech stack.
Description: {info['description']}
Features: {json.dumps(info['features'][:12])}
{doc_section}
DATABASE: {db_type}
{db_inst}

ENTITIES ({len(entities)} total — generate model/schema/route/service for EACH):
{self._fmt_entities(entities)}

RELATIONSHIPS:
{rels_text}

API ENDPOINTS:
{self._fmt_endpoints(endpoints)}

FILES TO GENERATE (each with COMPLETE, RUNNABLE code — ABSOLUTELY NO TODOs or PLACEHOLDERS):
{files_to_gen}

CRITICAL RULES FOR PRODUCTION-READY BACKEND:
{rules}
- EVERY file must be 100% COMPLETE — never use "...", "pass", "add more here", or omitting sections. Write out the actual implementations.
- ALL imports must resolve to actual files.
- Use async/await for ALL DB operations.
- Proper error handling.

Return ONLY valid JSON — no markdown wrapper:
{{
  "codebase": [
    {{"name":"filename.py","path":"backend/path/file.py","language":"python","content":"full integrated code without fragmentation"}}
  ]
}}"""

    # ---------- Phase 2: Frontend ----------

    def _build_frontend_prompt(self, info: Dict, entities: List[Dict], endpoints: List[Dict],
                               pages: List[Dict], tokens: Dict, stores: List[Dict],
                               backend_files: List[Dict], stack: Dict[str, Any],
                               doc_context: Optional[Dict] = None, gen_type: str = "full_stack",
                               phase: str = "all") -> str:
        entity_names = [e["name"] for e in entities]
        pages_text = "\n".join([f"  - {p['name']} at {p['route']} (protected={p.get('protected',False)})" for p in pages[:20]]) or "  Auto-generate: Landing, Login, Register, Dashboard + per-entity pages"
        colors_text = json.dumps(tokens.get("color_palette", {}), indent=2) if tokens.get("color_palette") else "Modern dark theme with vibrant accent — use slate/zinc base, blue/violet accents"

        # Build comprehensive theme section
        typography_text = json.dumps(tokens.get("typography", {}), indent=2) if tokens.get("typography") else "System font stack with proper hierarchy (Inter/Geist recommended)"
        dark_mode_text = json.dumps(tokens.get("dark_mode", {}), indent=2) if tokens.get("dark_mode") else "Class-based dark mode with system preference detection"
        component_styling_text = json.dumps(tokens.get("component_styling", {}), indent=2) if tokens.get("component_styling") else "Consistent rounded corners, subtle shadows, smooth transitions"
        spacing_text = json.dumps(tokens.get("spacing", {}), indent=2) if tokens.get("spacing") else "4px base unit spacing scale"
        layout_text = json.dumps(tokens.get("layout", {}), indent=2) if tokens.get("layout") else "Sidebar + topbar layout for dashboard, centered layout for auth pages"
        border_radius_text = json.dumps(tokens.get("border_radius", {}), indent=2) if tokens.get("border_radius") else "rounded-lg for cards, rounded-xl for modals, rounded-md for buttons"
        shadows_text = json.dumps(tokens.get("shadows", {}), indent=2) if tokens.get("shadows") else "Layered shadow system: sm for inputs, md for cards, lg for modals"

        frontend_framework = stack["frontend"]
        
        if frontend_framework == "nextjs":
            tech = "Next.js 14 App Router, TypeScript, Tailwind CSS, Zustand, SWR, Framer Motion"
            if phase == "config":
                files_to_gen = """1. frontend/package.json — next@14, react@18, typescript, tailwindcss@3, zustand, swr, framer-motion, lucide-react, clsx, zod, @radix-ui/react-*
2. frontend/tsconfig.json — path aliases @/*
3. frontend/next.config.js — rewrites /api proxy to backend
4. frontend/tailwind.config.ts — custom colors from palette, dark mode class, typography, spacing
5. frontend/postcss.config.js
6. frontend/src/app/globals.css — Tailwind directives + CSS variables from design system + custom styles
7. frontend/src/utils/api.ts — axios/fetch client, auth headers, BASE_URL from env
8. frontend/src/utils/auth.ts — token storage, refresh logic
9. frontend/src/stores/useAuthStore.ts — Zustand auth state + persist
10. FOR EACH ENTITY: frontend/src/stores/use<Entity>Store.ts — entity state
11. FOR EACH ENTITY: frontend/src/hooks/use<Entity>.ts — SWR data hooks matching backend routes
12. frontend/src/components/ui/Button.tsx, Input.tsx, Card.tsx, Modal.tsx, Toast.tsx, Badge.tsx, Spinner.tsx — styled using design system tokens
13. frontend/src/components/layout/Navbar.tsx, Sidebar.tsx — styled using layout and spacing tokens"""
            elif phase == "pages":
                files_to_gen = """1. frontend/src/app/layout.tsx — root layout, metadata, font (match typography system), providers
2. frontend/src/app/page.tsx — beautiful landing page with hero, features, CTA
3. frontend/src/app/(auth)/login/page.tsx — login form with validation
4. frontend/src/app/(auth)/register/page.tsx — register form
5. frontend/src/app/dashboard/page.tsx — main dashboard with stats + entity summaries
6. FOR EACH ENTITY: frontend/src/app/dashboard/<plural>/page.tsx — entity list + CRUD fully integrated with API
7. FOR EACH ENTITY: frontend/src/components/<Entity>/<Entity>List.tsx, <Entity>Form.tsx"""
            else:
                files_to_gen = """1. frontend/package.json
2. frontend/tsconfig.json
3. frontend/next.config.js
4. frontend/tailwind.config.ts
5. frontend/postcss.config.js
6. frontend/src/app/globals.css
7. frontend/src/app/layout.tsx
8. frontend/src/app/page.tsx
9. frontend/src/app/(auth)/login/page.tsx
10. frontend/src/app/(auth)/register/page.tsx
11. frontend/src/app/dashboard/page.tsx
12. FOR EACH ENTITY: frontend/src/app/dashboard/<plural>/page.tsx
13. frontend/src/utils/api.ts
14. frontend/src/utils/auth.ts
15. frontend/src/stores/useAuthStore.ts
16. FOR EACH ENTITY: frontend/src/stores/use<Entity>Store.ts
17. FOR EACH ENTITY: frontend/src/hooks/use<Entity>.ts
18. frontend/src/components/ui/Button.tsx, Input.tsx, Card.tsx, Modal.tsx, Toast.tsx, Badge.tsx, Spinner.tsx
19. frontend/src/components/layout/Navbar.tsx, Sidebar.tsx
20. FOR EACH ENTITY: frontend/src/components/<Entity>/<Entity>List.tsx, <Entity>Form.tsx"""
            
            rules = """- 'use client' on client components, server components by default
- Connect to NEXT_PUBLIC_API_URL (default http://localhost:8000)
- Implement COMPLETE auth flow: login → store JWT → include in all API calls → refresh on 401
- Apply design system tokens consistently to guarantee visual cohesion.
- NEVER truncate any component return statement. ALL components must be fully fleshed out.
- SWR for data fetching with proper keys and mutate calls referencing real backend API routes given above.
- NO static/mock data — ALL data from API
- Ensure all pages and routes defined in the PRD are fully coded and linked via Next.js <Link>.
- Next.js Link component MUST strictly be imported from 'next/link', NEVER import Link from 'next' directly. Example: import Link from 'next/link';"""

        elif frontend_framework == "react":
            tech = "React (Vite SPA), TypeScript, Tailwind CSS, Zustand/Redux, Axios, React Router Dom"
            if phase == "config":
                files_to_gen = """1. frontend/package.json — react@18, react-dom@18, react-router-dom@6, typescript, tailwindcss@3, zustand, axios, lucide-react.
2. frontend/tsconfig.json
3. frontend/vite.config.ts — proxy config
4. frontend/index.html — entry html
5. frontend/tailwind.config.js
6. frontend/src/main.tsx — main bootstrap
7. frontend/src/utils/api.ts — axios client
8. frontend/src/stores/useAuthStore.ts — auth store
9. frontend/src/components/ui/Button.tsx, Input.tsx, Card.tsx"""
            elif phase == "pages":
                files_to_gen = """1. frontend/src/App.tsx — routing setup, navbar, sidebar, theme wrappers
2. frontend/src/pages/Home.tsx — landing page
3. frontend/src/pages/Login.tsx — login page
4. frontend/src/pages/Register.tsx — signup page
5. frontend/src/pages/Dashboard.tsx — dashboard stats
6. FOR EACH ENTITY: frontend/src/pages/<Entity>Page.tsx — entity CRUD page"""
            else:
                files_to_gen = """1. frontend/package.json
2. frontend/tsconfig.json
3. frontend/vite.config.ts
4. frontend/index.html
5. frontend/tailwind.config.js
6. frontend/src/main.tsx
7. frontend/src/App.tsx
8. frontend/src/pages/Home.tsx
9. frontend/src/pages/Login.tsx
10. frontend/src/pages/Register.tsx
11. frontend/src/pages/Dashboard.tsx
12. FOR EACH ENTITY: frontend/src/pages/<Entity>Page.tsx
13. frontend/src/utils/api.ts
14. frontend/src/stores/useAuthStore.ts
15. frontend/src/components/ui/Button.tsx, Input.tsx, Card.tsx"""
            
            rules = """- Use standard Vite React SPA routing.
- Import standard React router links: import { Link } from 'react-router-dom';
- Connect to backend API.
- Write complete components."""

        elif frontend_framework == "angular":
            tech = "Angular, TypeScript, CSS/SCSS, RxJS"
            if phase == "config":
                files_to_gen = """1. frontend/package.json — @angular/core, @angular/router, etc.
2. frontend/angular.json — build configurations
3. frontend/src/main.ts — angular bootstrap
4. frontend/src/app/app.module.ts / app.config.ts
5. frontend/src/app/app-routing.module.ts
6. frontend/src/app/services/api.service.ts — Angular HttpClient service"""
            elif phase == "pages":
                files_to_gen = """1. frontend/src/app/app.component.ts & app.component.html
2. frontend/src/app/components/login/login.component.ts & .html
3. frontend/src/app/components/dashboard/dashboard.component.ts & .html
4. FOR EACH ENTITY: frontend/src/app/components/<entity>/<entity>.component.ts & .html"""
            else:
                files_to_gen = """1. frontend/package.json
2. frontend/angular.json
3. frontend/src/main.ts
4. frontend/src/app/app.module.ts / app.config.ts
5. frontend/src/app/app-routing.module.ts
6. frontend/src/app/app.component.ts & app.component.html
7. frontend/src/app/services/api.service.ts
8. frontend/src/app/components/login/login.component.ts & .html
9. frontend/src/app/components/dashboard/dashboard.component.ts & .html
10. FOR EACH ENTITY: frontend/src/app/components/<entity>/<entity>.component.ts & .html"""
            
            rules = """- Use standard Angular architecture (Services, Components, Routing).
- Inject HttpClient for backend communication."""

        elif frontend_framework == "vue":
            tech = "Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS"
            if phase == "config":
                files_to_gen = """1. frontend/package.json — vue@3, vue-router@4, pinia, axios, tailwindcss.
2. frontend/vite.config.ts
3. frontend/src/main.ts
4. frontend/src/router/index.ts
5. frontend/src/stores/auth.ts — Pinia auth store
6. frontend/src/components/ui/Button.vue, Card.vue"""
            elif phase == "pages":
                files_to_gen = """1. frontend/src/App.vue
2. frontend/src/views/Home.vue — landing view
3. frontend/src/views/Login.vue — login form
4. frontend/src/views/Dashboard.vue — dashboard
5. FOR EACH ENTITY: frontend/src/views/<Entity>View.vue — CRUD view"""
            else:
                files_to_gen = """1. frontend/package.json
2. frontend/vite.config.ts
3. frontend/src/main.ts
4. frontend/src/App.vue
5. frontend/src/router/index.ts
6. frontend/src/stores/auth.ts
7. frontend/src/views/Home.vue
8. frontend/src/views/Login.vue
9. frontend/src/views/Dashboard.vue
10. FOR EACH ENTITY: frontend/src/views/<Entity>View.vue
11. frontend/src/components/ui/Button.vue, Card.vue"""
            
            rules = """- Use Vue 3 Composition API with <script setup lang="ts">.
- Use Pinia for state management."""

        else:
            tech = f"{frontend_framework.capitalize()} frontend application"
            files_to_gen = """1. frontend/package.json
2. frontend/src/main.js
3. frontend/index.html"""
            rules = f"- Use {frontend_framework} for frontend."

        # Document context section
        doc_section = ""
        if doc_context:
            doc_section = f"""\nPROJECT DOCUMENTATION (SINGLE SOURCE OF TRUTH — ALL generated frontend MUST ALIGN exactly with these docs):
PRD: {doc_context['prd_summary']}
TRD: {doc_context['trd_summary']}
MRD: {doc_context['mrd_summary']}
Implementation Plan: {doc_context['implementation_plan']}

MINIMUM SCOPE REQUIREMENT: You MUST generate a production-ready frontend containing AT LEAST 5 major pages/modules/screens as described in the PRD (Dashboard, User Management, Analytics, Settings, Forms, etc.). Do not generate single-page toy apps. 
"""
        rule_list = [
            "Apply design system tokens consistently to guarantee visual cohesion.",
            "NEVER truncate any component return statement. ALL components must be fully fleshed out.",
            "Ensure all pages and routes defined in the PRD are fully coded and linked via Links."
        ]
        if gen_type == "frontend_only":
            rule_list.append("FRONTEND ONLY SIMULATION: Since there is no custom backend API server in this scope, you MUST implement fully functional mockup services, simulated data, or LocalStorage sync inside your stores/API hooks/utility files to ensure CRUD operations and auth login/signup flows are fully interactive. The app must run and be fully interactive without requesting or needing a backend server.")
        else:
            rule_list.append("NO static/mock data — ALL data from API")
            
        rule_directives = "\n".join(f"- {r}" for r in rule_list)

        if phase == "config":
            task_desc = f"Generate the CONFIGURATION files, Tailwind/postCSS config, utility services, client store hooks, and reusable UI components of the frontend codebase for \"{info['name']}\" using {frontend_framework.upper()} tech stack."
            rule_directives += "\n- Focus ONLY on generating setup, configurations, stores, helper functions, and base styled components. DO NOT generate individual page files or pages views yet."
        elif phase == "pages":
            task_desc = f"Generate the PAGES/VIEWS, layouts, and routing components of the frontend codebase for \"{info['name']}\" using {frontend_framework.upper()} tech stack."
            rule_directives += "\n- Focus ONLY on generating application views, routing pages, forms, lists, and layout shells that import the UI components and stores designed in the configuration phase."
        else:
            task_desc = f"Generate the COMPLETE frontend codebase for \"{info['name']}\" using {frontend_framework.upper()} tech stack."

        return f"""{task_desc}
Description: {info['description']}
{doc_section}
TECH: {tech}

BACKEND ENDPOINTS TO CONSUME (Strictly use these, do NOT invent missing ones):
{self._fmt_endpoints(endpoints)}

ENTITIES: {', '.join(entity_names)}

PAGES (Must generate AT LEAST 5 fully working interconnected pages):
{pages_text}

DESIGN SYSTEM & THEME (apply these consistently across ALL components):
COLOR PALETTE:
{colors_text}

TYPOGRAPHY SYSTEM:
{typography_text}

DARK/LIGHT MODE CONFIG:
{dark_mode_text}

COMPONENT STYLING RULES:
{component_styling_text}

SPACING & LAYOUT TOKENS:
Spacing: {spacing_text}
Layout: {layout_text}
Border Radius: {border_radius_text}
Shadows: {shadows_text}

BACKEND FILES (for reference to match types and routes exactly):
{self._fmt_file_list(backend_files)}

FILES TO GENERATE (COMPLETE code, NO placeholders or truncated components):
{files_to_gen}

CRITICAL RULES FOR PRODUCTION-READY FRONTEND:
{rules}
{rule_directives}

Return ONLY valid JSON:
{{
  "codebase": [
    {{"name":"file.tsx","path":"frontend/path/file.tsx","language":"typescript","content":"full code text"}}
  ]
}}"""

    # ---------- Phase 3: Infrastructure ----------

    def _build_infra_prompt(self, info: Dict, entities: List[Dict], db_type: str,
                            backend_files: List[Dict], frontend_files: List[Dict],
                            doc_context: Optional[Dict] = None, gen_type: str = "full_stack") -> str:
        entity_names = [e["name"] for e in entities]
        slug = info["name"].lower().replace(" ", "-").replace("_", "-")

        # Document context section
        doc_section = ""
        if doc_context:
            doc_section = f"""\nPROJECT DOCUMENTATION (use for README content, deployment notes, and test scenarios):
PRD: {doc_context['prd_summary']}
TRD: {doc_context['trd_summary']}
Implementation Plan: {doc_context['implementation_plan']}

MINIMUM SCOPE REQUIREMENT: Generate complete infrastructure ensuring tests, models, interfaces and deployments are fully connected and derived directly from the generated components. Do NOT leave missing links.
"""

        # Build list of files to generate based on gen_type
        files_to_generate = []
        if gen_type == "frontend_only":
            files_to_generate = [
                "1. README.md — comprehensive: description, features, tech stack, quick start, env vars, deployment (Frontend Only)",
                "2. .gitignore — Node.js + IDE",
                "3. .env.example — Frontend env vars with safe placeholders",
                "4. docker-compose.yml — frontend:3000",
                "5. frontend/Dockerfile — node:20-alpine multi-stage (build + standalone)",
                "6. Makefile — frontend dev, build, up, down, clean targets",
                "7. shared/types/index.ts — TypeScript interfaces matching the domain entities",
                "8. scripts/setup.sh — dev environment bootstrap"
            ]
        elif gen_type in ("backend_only", "microservice"):
            readme_label = "Microservice/Worker" if gen_type == "microservice" else "Backend Only"
            docker_services = "microservice:8000, async worker, redis:6379" if gen_type == "microservice" else ("backend:8000, " + ('postgres:5432' if db_type.lower() in ('postgresql','postgres') else 'mongodb:27017') + ", redis:6379")
            files_to_generate = [
                f"1. README.md — comprehensive: description, features, tech stack, quick start, API docs, env vars, deployment ({readme_label})",
                "2. .gitignore — Python + Docker + IDE",
                "3. .env.example — Backend/Microservice env vars with safe placeholders",
                f"4. docker-compose.yml — {docker_services}",
                "5. backend/Dockerfile — python:3.11-slim, install deps, uvicorn",
                "6. Makefile — dev, build, up, down, test, clean, migrate targets",
                "7. backend/tests/__init__.py",
                "8. backend/tests/conftest.py — pytest fixtures (test client, test DB, auth headers)",
                "9. backend/tests/test_auth.py — signup, login, refresh, protected route tests",
                "10. backend/tests/test_crud.py — CRUD tests for each entity fully implemented",
                "11. scripts/setup.sh — dev environment bootstrap"
            ]
        else: # full_stack
            files_to_generate = [
                "1. README.md — comprehensive: description, features, tech stack, quick start, API docs, env vars, deployment",
                "2. .gitignore — Python + Node.js + Docker + IDE",
                "3. .env.example — ALL env vars with safe placeholders",
                "4. docker-compose.yml — backend:8000, frontend:3000, " + ('postgres:5432' if db_type.lower() in ('postgresql','postgres') else 'mongodb:27017') + ", redis:6379",
                "5. docker-compose.prod.yml — production overrides",
                "6. backend/Dockerfile — python:3.11-slim, install deps, uvicorn",
                "7. frontend/Dockerfile — node:20-alpine multi-stage (build + standalone)",
                "8. Makefile — dev, build, up, down, test, clean, migrate targets",
                "9. shared/types/index.ts — TypeScript interfaces matching Python schemas EXACTLY",
                "10. shared/types/api.ts — API response types, error types",
                "11. backend/tests/__init__.py",
                "12. backend/tests/conftest.py — pytest fixtures (test client, test DB, auth headers)",
                "13. backend/tests/test_auth.py — signup, login, refresh, protected route tests",
                "14. backend/tests/test_crud.py — CRUD tests for each entity fully implemented",
                "15. scripts/setup.sh — dev environment bootstrap",
                "16. nginx/nginx.conf — reverse proxy /api→backend, /*→frontend (optional for prod)"
            ]

        files_to_generate_text = "\n".join(files_to_generate)

        return f"""Generate infrastructure, DevOps, testing, and integration files for "{info['name']}".

SLUG: {slug}
DATABASE: {db_type}
ENTITIES: {', '.join(entity_names)}
{doc_section}
EXISTING BACKEND FILES:
{self._fmt_file_list(backend_files)}

EXISTING FRONTEND FILES:
{self._fmt_file_list(frontend_files)}

FILES TO GENERATE:
{files_to_generate_text}

CRITICAL RULES FOR PRODUCTION-READY INFRASTRUCTURE:
- Docker services must use correct ports and env vars matching the code.
- README must have WORKING quick-start commands and detailed API instructions.
- shared/types must match backend Pydantic schemas field-for-field absolutely.
- Tests must have REAL assertions (not just pass) covering the real generated API routes. Ensure every test implements full setup, execution, and teardown where applicable.
- If DATABASE is mongodb, do NOT use or import SQLAlchemy or SQLite in backend/tests/conftest.py or other test files. Mock MongoDB or use Motor client fixtures, and only override the MongoDB client/db dependencies.
- No '...', 'TBD', or omitted steps.

Return ONLY valid JSON:
{{
  "codebase": [
    {{"name":"file","path":"path/to/file","language":"lang","content":"full content"}}
  ]
}}"""

    # ---------- Phase 4: Review & Self-Heal ----------

    def _build_review_prompt(self, all_files: List[Dict], info: Dict,
                             entities: List[Dict], endpoints: List[Dict]) -> str:
        # Include ALL imports and first 30 lines of each file for thorough review
        previews: List[str] = []
        for f in all_files[:80]:
            content = f.get("content", "")
            lines = content.split("\n")
            import_lines = [l for l in lines if l.strip().startswith(("import ", "from ", "require(", "export "))]
            preview_lines = lines[:30]
            combined = list(dict.fromkeys(import_lines + preview_lines))[:40]
            previews.append(f"--- {f['path']} ({len(lines)} lines) ---\n" + "\n".join(combined))
        files_text = "\n\n".join(previews)

        entity_names = [e["name"] for e in entities]
        return f"""Review the codebase for "{info['name']}" and FIX any issues.

ENTITIES: {', '.join(entity_names)}
ENDPOINTS:
{self._fmt_endpoints(endpoints, 25)}

ALL FILES AND THEIR IMPORTS:
{files_text}

VALIDATION CHECKLIST — fix ALL of these:
1. IMPORTS: Every 'from X import Y' / 'import X from "Y"' must resolve to a file that EXISTS above. Fix broken paths. Specifically, in Next.js, the 'Link' component MUST be imported from 'next/link', NOT from 'next'.
2. API CONTRACTS: Frontend fetch/axios URLs must EXACTLY match backend route paths. Fix mismatches.
3. TYPES: TypeScript interfaces in shared/types must match Python Pydantic schemas. Fix field name differences (snake_case ↔ camelCase).
4. AUTH FLOW: Login form → POST /auth/login → receive JWT → store in Zustand → attach to all API calls via Authorization header. Verify end-to-end.
5. MISSING FILES: If a file imports something that doesn't exist, generate that missing file.
6. ENV VARS: Every env var used in code must appear in .env.example.
7. PACKAGE.JSON: All imported npm packages must be in dependencies.
8. REQUIREMENTS.TXT: All imported Python packages must be listed.

Return ONLY files that need FIXING or are MISSING (not unchanged files):
{{
  "fixes_applied": ["fix description 1", "fix description 2"],
  "codebase": [
    {{"name":"file","path":"path","language":"lang","content":"COMPLETE fixed file content"}}
  ]
}}
If everything is correct: {{"fixes_applied":[],"codebase":[]}}"""

    # ──────────────────────────────────────────────────────────────
    # Synthesis Orchestration
    # ──────────────────────────────────────────────────────────────

    async def _run_phase(self, phase_name: str, prompt: str,
                         db: Any, project_id: str,
                         progress: int | float, step: str) -> List[Dict]:
        """Execute one synthesis phase via LLM with a 3-attempt self-healing feedback retry loop."""
        from app.services.workflow import broadcast_agent_progress
        from app.core.logger import SarthiConsoleLogger
        
        await broadcast_agent_progress(db, project_id, progress, step)
        await SarthiConsoleLogger.log_agent_start(db, project_id, f"CodeSynthesizer_{phase_name}", f"Starting synthesis phase '{phase_name}'")

        system = (
            f"You are Sarthi's CodeSynthesizer — a world-class AI code compiler. "
            f"Phase: {phase_name}.\n"
            "ABSOLUTE RULES:\n"
            "- Every file must contain COMPLETE, RUNNABLE, PRODUCTION-QUALITY code\n"
            "- NEVER truncate a file — write the FULL content\n"
            "- NO TODOs, NO placeholders, NO '...', NO 'implement here', NO 'add more'\n"
            "- ALL imports must resolve to real files in the project\n"
            "- Next.js Link component MUST strictly be imported from 'next/link', NEVER import Link from 'next' directly.\n"
            "- Use proper error handling, validation, and edge-case coverage\n"
            "- Return ONLY valid JSON — absolutely no markdown code fences"
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                raw = await get_llm_completion(
                    agent_name=f"CodeSynthesizer_{phase_name}",
                    messages=messages,
                    temperature=0.15,
                    max_tokens=100000,
                )
                data = parse_json_response(raw.strip())
                files = data.get("codebase", [])
                
                # Validate file structure
                valid_files = []
                for f in files:
                    if isinstance(f, dict) and f.get("path") and f.get("content"):
                        if not f.get("name"):
                            f["name"] = f["path"].split("/")[-1]
                        if not f.get("language"):
                            f["language"] = self._detect_language(f["path"])
                        valid_files.append(f)
                        
                logger.info(f"[CodeSynthesizer] Phase '{phase_name}': {len(valid_files)} files generated")
                for vf in valid_files:
                    logger.info(f"  📄 {vf['path']} ({len(vf.get('content',''))} chars)")
                
                await SarthiConsoleLogger.log_success(db, project_id, f"CodeSynthesizer_{phase_name}", f"Successfully synthesized {len(valid_files)} files for phase '{phase_name}'")
                return valid_files

            except Exception as e:
                err_msg = f"Attempt {attempt + 1}/{max_attempts} failed for phase '{phase_name}': {str(e)}"
                logger.warning(f"[CodeSynthesizer] {err_msg}")
                await SarthiConsoleLogger.log_healing(db, project_id, f"CodeSynthesizer_{phase_name}", f"Warning: {err_msg}")
                
                if attempt < max_attempts - 1:
                    # Capture assistant response or standard failure message
                    raw_response = locals().get("raw", "No response returned due to request error")
                    messages.append({"role": "assistant", "content": raw_response})
                    
                    correction_prompt = (
                        f"Your previous JSON output was invalid and could not be parsed.\n"
                        f"Error encountered: {type(e).__name__}: {str(e)}\n"
                        f"Please carefully analyze your previous output and correct it. Make sure you output the complete and valid JSON with double quotes correctly closed and standard delimiters present. Do not truncate any files."
                    )
                    messages.append({"role": "user", "content": correction_prompt})
                    
                    # Update progress and UI
                    retry_step = f"🩹 Healing: Retrying {phase_name} (Attempt {attempt + 2}/{max_attempts})..."
                    await broadcast_agent_progress(db, project_id, progress, retry_step)
                else:
                    logger.error(f"[CodeSynthesizer] All {max_attempts} attempts failed for phase '{phase_name}'")
                    await SarthiConsoleLogger.log_error(db, project_id, f"CodeSynthesizer_{phase_name}", f"All {max_attempts} attempts failed: {str(e)}")
                    return []

    @staticmethod
    def _detect_language(path: str) -> str:
        ext_map = {
            ".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".json": "json",
            ".css": "css", ".html": "html", ".md": "markdown",
            ".yml": "yaml", ".yaml": "yaml", ".toml": "toml",
            ".sh": "bash", ".sql": "sql", ".env": "plaintext",
            ".txt": "plaintext", ".ini": "ini", ".cfg": "ini",
            ".conf": "nginx",
        }
        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang
        return "plaintext"

    async def heal_codebase(self, project_doc: Dict, db: Any, project_id: str,
                            validation_errors: List[Dict], existing_codebase: List[Dict]) -> List[Dict]:
        """
        Targeted self-healing pass: takes files with errors and validation error logs,
        runs a focused LLM repair, and merges the repaired files back.
        """
        logger.info(f"[CodeSynthesizer] 🩺 Starting targeted dynamic healing for {len(validation_errors)} issues.")
        from app.services.workflow import broadcast_agent_progress
        await broadcast_agent_progress(db, project_id, 89, "🩺 Running dynamic healing on compilation/syntax errors...")
        
        # 1. Group errors by file
        errors_by_file: Dict[str, List[Dict]] = {}
        for err in validation_errors:
            file_path = err.get("file", "-")
            if file_path and file_path != "-":
                errors_by_file.setdefault(file_path, []).append(err)
                
        # 2. Extract contents of files with errors and related context files
        files_to_heal: Dict[str, str] = {}
        for file_path in errors_by_file:
            # Find in existing codebase
            file_content = ""
            for f in existing_codebase:
                if f.get("path") == file_path:
                    file_content = f.get("content", "")
                    break
            files_to_heal[file_path] = file_content
            
        # 3. If there are missing files, identify them
        missing_files = [err.get("file") for err in validation_errors if err.get("type") == "missing_file" and err.get("file")]
        for mf in missing_files:
            if mf not in files_to_heal:
                files_to_heal[mf] = ""
                
        if not files_to_heal:
            logger.warning("[CodeSynthesizer] Healing called but no specific files were mapped to errors. Healing main entrypoints.")
            for path in ["backend/app/main.py", "frontend/src/app/page.tsx"]:
                for f in existing_codebase:
                    if f.get("path") == path:
                        files_to_heal[path] = f.get("content", "")
                        
        # 4. Build prompt
        info = self._extract_project_info(project_doc)
        prompt = self._build_dynamic_healing_prompt(info, files_to_heal, errors_by_file, validation_errors)
        
        # 5. Run LLM
        healed_files = await self._run_phase("Healing", prompt, db, project_id, 91,
                                            "🩺 Applying targeted code repairs...")
                                            
        # 6. Merge healed files back into existing_codebase
        healed_paths = {f["path"] for f in healed_files}
        final_codebase = []
        for f in existing_codebase:
            path = f.get("path", "")
            if path in healed_paths:
                healed_f = next(hf for hf in healed_files if hf["path"] == path)
                final_codebase.append(healed_f)
                healed_paths.remove(path)
            else:
                final_codebase.append(f)
                
        # Append any newly created files
        for path in healed_paths:
            healed_f = next(hf for hf in healed_files if hf["path"] == path)
            final_codebase.append(healed_f)
            
        logger.info(f"[CodeSynthesizer] Dynamic healing applied {len(healed_files)} corrected files.")
        return final_codebase

    def _build_dynamic_healing_prompt(self, info: Dict, files_to_heal: Dict[str, str],
                                     errors_by_file: Dict[str, List[Dict]], all_errors: List[Dict]) -> str:
        files_section = ""
        for path, content in files_to_heal.items():
            errs = errors_by_file.get(path, [])
            err_desc = "\n".join([f"  - Line {e.get('line', 'N/A')}: [{e.get('type')}] {e.get('description')}" for e in errs])
            if not err_desc:
                err_desc = "  - File is missing or needs generation/refactoring to resolve global compilation issues."
            
            files_section += f"""
--- FILE PATH: {path} ---
ERRORS/ISSUES:
{err_desc}

CURRENT CODE CONTENT:
```
{content}
```
"""

        general_errors = [e for e in all_errors if e.get("file", "-") in ("-", "", None)]
        general_desc = ""
        if general_errors:
            general_desc = "\nGENERAL SYSTEM/COMPILATION ERRORS:\n" + "\n".join([
                f"  - [{e.get('type')}] {e.get('description')}" for e in general_errors
            ])

        return f"""You are Sarthi's Dynamic Healing Agent. Your task is to analyze and repair compilation, syntax, and import errors in the generated codebase.

Project Name: {info['name']}
Description: {info['description']}
Tech Stack: {json.dumps(info['tech_stack'])}

We have run compilation and code validation checks, and detected the following issues.

{general_desc}

FILES REQUIRING REPAIR:
{files_section}

CRITICAL REPAIR INSTRUCTIONS:
1. Fix all reported syntax, compile, and typechecking errors in the files.
2. Resolve broken imports. Ensure every import refers to a file that actually exists or is being created.
3. For Next.js/React, ensure 'Link' is imported from 'next/link', not 'next'.
4. Ensure all files returned contain COMPLETE, runnable code with no truncation, placeholders, or TODOs.
5. If a file was reported as missing, generate its initial complete implementation.

Return ONLY the files you have repaired or created in the following JSON format:
{{
  "codebase": [
    {{
      "name": "filename.ext",
      "path": "path/to/file.ext",
      "language": "programming-language",
      "content": "repaired full file content"
    }}
  ]
}}"""

    @staticmethod
    async def _store_intermediate(db: Any, project_id: str, files: List[Dict], phase: str) -> None:
        """Store intermediate codebase files in MongoDB to enable resume capability."""
        try:
            logger.info(f"[CodeSynthesizer] Storing intermediate codebase ({len(files)} files) for phase '{phase}'")
            await db.projects.update_one(
                {"_id": project_id},
                {"$set": {
                    "synthesized_codebase": files,
                    "last_synthesis_phase": phase
                }}
            )
        except Exception as e:
            logger.error(f"[CodeSynthesizer] Failed to store intermediate codebase: {e}")

    async def synthesize(self, project_doc: Dict, db: Any, project_id: str,
                         validation_errors: Optional[List[Dict]] = None,
                         existing_codebase: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Main entry point — multi-phase code synthesis.
        Returns [{name, path, language, content}].
        """
        if validation_errors and existing_codebase:
            return await self.heal_codebase(project_doc, db, project_id, validation_errors, existing_codebase)

        from app.services.project_assembler import detect_tech_stack
        stack = detect_tech_stack(project_doc)

        info = self._extract_project_info(project_doc)
        entities = self._extract_entities(project_doc)
        rels = self._extract_relationships(project_doc)
        endpoints = self._extract_endpoints(project_doc)
        pages = self._extract_pages(project_doc)
        tokens = self._extract_design_tokens(project_doc)
        auth = self._extract_auth_config(project_doc)
        stores = self._extract_stores(project_doc)
        db_type = self._get_db_type(project_doc)
        doc_context = self._extract_document_context(project_doc)
        
        gen_type = project_doc.get("generation_type", "full_stack")

        # ── Enforce minimum entities from features (Only if not frontend_only) ──
        if gen_type != "frontend_only":
            if not entities or len(entities) < 2:
                from app.services.project_assembler import _pascal_case, _pluralize, _snake_case
                for feat in info.get('features', [])[:8]:
                    if isinstance(feat, str):
                        entity_name = _pascal_case(feat)
                        route_name = _pluralize(_snake_case(entity_name)).replace("_", "-")
                        if entity_name and entity_name not in [e['name'] for e in entities]:
                            entities.append({
                                'name': entity_name,
                                'route': route_name,
                                'fields': [
                                    {'name': 'id', 'type': 'string', 'required': True, 'indexed': True},
                                    {'name': 'name', 'type': 'string', 'required': True, 'indexed': False},
                                    {'name': 'description', 'type': 'string', 'required': False, 'indexed': False},
                                    {'name': 'created_at', 'type': 'datetime', 'required': True, 'indexed': True},
                                    {'name': 'updated_at', 'type': 'datetime', 'required': False, 'indexed': False},
                                ],
                                'description': f'{feat} entity'
                            })
                logger.info(f"[CodeSynthesizer] Entities augmented from features: {[e['name'] for e in entities]}")

        # ── Enforce minimum pages/features (Only if not backend_only or microservice) ──
        if gen_type not in ("backend_only", "microservice"):
            min_features = max(5, len(info.get('features', [])))
            if len(pages) < 5:
                default_pages = [
                    {"name": "Dashboard", "route": "/dashboard", "protected": True},
                    {"name": "Login", "route": "/login", "protected": False},
                    {"name": "Register", "route": "/register", "protected": False},
                    {"name": "Settings", "route": "/settings", "protected": True},
                    {"name": "Profile", "route": "/profile", "protected": True},
                ]
                existing_routes = {p.get('route', '') for p in pages}
                for dp in default_pages:
                    if dp['route'] not in existing_routes and len(pages) < min_features:
                        pages.append(dp)
                logger.info(f"[CodeSynthesizer] Pages padded to minimum: {len(pages)} pages")

        logger.info("=" * 60)
        logger.info(f"[CodeSynthesizer] Starting synthesis for '{info['name']}' ({gen_type})")
        logger.info(f"  Entities : {[e['name'] for e in entities]}")
        logger.info(f"  Endpoints: {len(endpoints)}")
        logger.info(f"  Pages    : {len(pages)}")
        logger.info(f"  DB       : {db_type}")
        logger.info(f"  Backend  : {stack['backend']}")
        logger.info(f"  Frontend : {stack['frontend']}")
        logger.info(f"  PRD      : {'Available (' + str(len(doc_context['prd_summary'])) + ' chars)' if doc_context['prd_summary'] != 'No PRD available' else 'Not available'}")
        logger.info(f"  TRD      : {'Available (' + str(len(doc_context['trd_summary'])) + ' chars)' if doc_context['trd_summary'] != 'No TRD available' else 'Not available'}")
        logger.info(f"  MRD      : {'Available (' + str(len(doc_context['mrd_summary'])) + ' chars)' if doc_context['mrd_summary'] != 'No MRD available' else 'Not available'}")
        logger.info("=" * 60)

        all_files: List[Dict] = []

        # ── Phase 1: Backend ──
        backend_files = []
        if gen_type != "frontend_only":
            backend_prompt = self._build_backend_prompt(info, entities, rels, endpoints, auth, db_type, stack, doc_context)
            backend_files = await self._run_phase("Backend", backend_prompt, db, project_id, 62,
                                                  "🔧 Synthesizing Backend Code...")
            all_files.extend(backend_files)
            await self._store_intermediate(db, project_id, all_files, "phase_backend")

        # ── Phase 2A: Frontend Configuration & UI Components ──
        frontend_config_files = []
        if gen_type not in ("backend_only", "microservice"):
            frontend_config_prompt = self._build_frontend_prompt(info, entities, endpoints, pages,
                                                                 tokens, stores, backend_files, stack, doc_context, gen_type,
                                                                 phase="config")
            frontend_config_files = await self._run_phase("FrontendConfig", frontend_config_prompt, db, project_id, 70,
                                                          "🎨 Synthesizing Frontend Configuration & UI Components...")
            all_files.extend(frontend_config_files)
            await self._store_intermediate(db, project_id, all_files, "phase_frontend_config")

        # ── Phase 2B: Frontend Routing & Views ──
        frontend_pages_files = []
        if gen_type not in ("backend_only", "microservice"):
            frontend_pages_prompt = self._build_frontend_prompt(info, entities, endpoints, pages,
                                                                tokens, stores, backend_files, stack, doc_context, gen_type,
                                                                phase="pages")
            frontend_pages_files = await self._run_phase("FrontendPages", frontend_pages_prompt, db, project_id, 78,
                                                         "🎨 Synthesizing Frontend Routing & Views...")
            all_files.extend(frontend_pages_files)
            await self._store_intermediate(db, project_id, all_files, "phase_frontend_pages")

        frontend_files = frontend_config_files + frontend_pages_files

        # ── Phase 3: Infrastructure ──
        infra_prompt = self._build_infra_prompt(info, entities, db_type, backend_files, frontend_files, doc_context, gen_type)
        infra_files = await self._run_phase("Infrastructure", infra_prompt, db, project_id, 84,
                                            "🐳 Synthesizing Infrastructure & Tests...")
        all_files.extend(infra_files)
        await self._store_intermediate(db, project_id, all_files, "phase_infra")

        # ── Phase 4: Review & Self-Heal ──
        if all_files:
            review_prompt = self._build_review_prompt(all_files, info, entities, endpoints)
            fix_result = await self._run_phase("ReviewFix", review_prompt, db, project_id, 92,
                                               "🔍 Validating & Self-Healing Code...")
            if fix_result:
                existing_paths = {f["path"] for f in all_files}
                for fix_file in fix_result:
                    path = fix_file.get("path", "")
                    if path in existing_paths:
                        all_files = [f for f in all_files if f["path"] != path]
                    all_files.append(fix_file)
                logger.info(f"[CodeSynthesizer] Review applied {len(fix_result)} fixes")

        # ── Safety net: ensure minimum viable files ──
        if len(all_files) < (3 if gen_type in ("frontend_only", "backend_only", "microservice") else 5):
            logger.warning("[CodeSynthesizer] Too few files — injecting essential boilerplate")
            all_files = self._inject_essential_boilerplate(all_files, info, entities, db_type, stack, gen_type)

        # Deduplicate by path (keep latest)
        seen: Dict[str, Dict] = {}
        for f in all_files:
            seen[f.get("path", "")] = f
        all_files = list(seen.values())

        # ── Validation Step ──
        self._validate_synthesis_output(all_files, backend_files, frontend_files, stack, gen_type)

        logger.info("=" * 60)
        logger.info(f"[CodeSynthesizer] ✅ Synthesis complete — {len(all_files)} files")
        total_chars = sum(len(f.get("content", "")) for f in all_files)
        logger.info(f"  Total code size: {total_chars:,} characters")
        logger.info("=" * 60)

        return all_files

    def _validate_synthesis_output(self, all_files: List[Dict],
                                    backend_files: List[Dict],
                                    frontend_files: List[Dict],
                                    stack: Dict[str, Any],
                                    gen_type: str = "full_stack") -> None:
        """Post-synthesis validation — logs warnings but does not fail."""
        warnings: List[str] = []

        # Check total file count
        min_files = 6 if gen_type in ("frontend_only", "backend_only", "microservice") else 15
        if len(all_files) < min_files:
            warnings.append(f"Total files ({len(all_files)}) is below recommended minimum of {min_files}")

        # Check for required files based on stack
        all_paths = {f.get("path", "") for f in all_files}
        required_files = [("README.md", "Project documentation")]
        
        if stack["is_default"]:
            if gen_type != "frontend_only":
                required_files.extend([
                    ("backend/requirements.txt", "Python dependencies"),
                    ("backend/app/main.py", "FastAPI entrypoint"),
                ])
            if gen_type not in ("backend_only", "microservice"):
                required_files.append(("frontend/package.json", "Node.js dependencies"))
        else:
            if gen_type != "frontend_only":
                if stack["backend"] == "fastapi":
                    required_files.extend([
                        ("backend/requirements.txt", "Python dependencies"),
                        ("backend/app/main.py", "FastAPI entrypoint"),
                    ])
                elif stack["backend"] == "django":
                    required_files.append(("backend/manage.py" if any(f.startswith("backend/manage.py") for f in all_paths) else "manage.py", "Django manager"))
                elif stack["backend"] == "express":
                    required_files.append(("backend/package.json" if any(f.startswith("backend/package.json") for f in all_paths) else "package.json", "Express dependencies"))
                    
            if gen_type not in ("backend_only", "microservice"):
                if stack["frontend"] in ("nextjs", "react", "angular", "vue"):
                    required_files.append(("frontend/package.json", "Frontend dependencies"))

        for req_path, desc in required_files:
            if req_path not in all_paths:
                warnings.append(f"Missing required file: {req_path} ({desc})")

        if warnings:
            logger.warning("[CodeSynthesizer] ⚠️ Synthesis validation warnings:")
            for w in warnings:
                logger.warning(f"  - {w}")
        else:
            logger.info("[CodeSynthesizer] ✅ Synthesis validation passed — all checks OK")

    def _inject_essential_boilerplate(self, files: List[Dict], info: Dict,
                                     entities: List[Dict], db_type: str, stack: Dict[str, Any], gen_type: str = "full_stack") -> List[Dict]:
        existing = {f.get("path", "") for f in files}
        slug = info["name"].lower().replace(" ", "-")
        entity_names = [e["name"] for e in entities]

        boilerplate: List[Dict] = []
        
        if stack["is_default"]:
            if gen_type != "frontend_only" and "backend/requirements.txt" not in existing:
                boilerplate.append({
                    "name": "requirements.txt",
                    "path": "backend/requirements.txt",
                    "language": "plaintext",
                    "content": "fastapi>=0.104.0\nuvicorn[standard]>=0.24.0\nmotor>=3.3.0\npydantic>=2.5.0\npydantic-settings>=2.1.0\npython-jose[cryptography]>=3.3.0\npasslib[bcrypt]>=1.7.4\npython-multipart>=0.0.6\npython-dotenv>=1.0.0\nhttpx>=0.25.0\npytest>=7.4.0\npytest-asyncio>=0.21.0\n"
                })

            if gen_type != "frontend_only" and "backend/app/database.py" not in existing:
                db_content = ""
                if db_type == "mongodb":
                    db_content = '''import os
from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None

async def connect_db():
    global client, db
    mongo_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()

async def close_db():
    global client
    if client:
        client.close()
'''
                else:
                    db_content = '''async def connect_db():
    pass

async def close_db():
    pass
'''
                boilerplate.append({
                    "name": "database.py",
                    "path": "backend/app/database.py",
                    "language": "python",
                    "content": db_content
                })

            if gen_type != "frontend_only" and "backend/app/api/auth.py" not in existing:
                boilerplate.append({
                    "name": "auth.py",
                    "path": "backend/app/api/auth.py",
                    "language": "python",
                    "content": '''from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class AuthPayload(BaseModel):
    email: str
    password: str
    name: str = None

@router.post("/signup")
async def signup(payload: AuthPayload):
    return {"access_token": "dummy-token", "token_type": "bearer"}

@router.post("/login")
async def login(payload: AuthPayload):
    return {"access_token": "dummy-token", "token_type": "bearer"}
'''
                })

            if gen_type != "frontend_only":
                if "backend/app/api/__init__.py" not in existing:
                    boilerplate.append({
                        "name": "__init__.py",
                        "path": "backend/app/api/__init__.py",
                        "language": "python",
                        "content": ""
                    })
                if "backend/app/api/v1/__init__.py" not in existing:
                    boilerplate.append({
                        "name": "__init__.py",
                        "path": "backend/app/api/v1/__init__.py",
                        "language": "python",
                        "content": ""
                    })
                for e in entities:
                    route_name = e.get("route", e["name"].lower() + "s")
                    module_name = route_name.replace("-", "_")
                    ep_path = f"backend/app/api/v1/{module_name}.py"
                    if ep_path not in existing:
                        boilerplate.append({
                            "name": f"{module_name}.py",
                            "path": ep_path,
                            "language": "python",
                            "content": f'''from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_{module_name}():
    return {{"items": [{{"id": "smoke-id-123", "title": "Smoke item"}}]}}

@router.post("/")
async def create_{module_name}(data: dict):
    return {{"item": {{"id": "smoke-id-123", **data}}}}
'''
                        })

            if gen_type != "frontend_only" and "backend/app/main.py" not in existing:
                imports_list = []
                includes_list = []
                for e in entities:
                    route_name = e.get("route", e["name"].lower() + "s")
                    module_name = route_name.replace("-", "_")
                    imports_list.append(f"from app.api.v1 import {module_name}")
                    includes_list.append(f'app.include_router({module_name}.router, prefix="/api/v1/{route_name}", tags=["{e["name"]}s"])')
                imports_models = "\n".join(imports_list)
                includes = "\n".join(includes_list)
                boilerplate.append({
                    "name": "main.py",
                    "path": "backend/app/main.py",
                    "language": "python",
                    "content": f'''from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_db, close_db
from app.api import auth
{imports_models}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(title="{info['name']}", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
{includes}

@app.get("/api/v1/health")
async def health():
    return {{"status": "healthy"}}
'''
                })

            if gen_type not in ("backend_only", "microservice") and "frontend/package.json" not in existing:
                boilerplate.append({
                    "name": "package.json",
                    "path": "frontend/package.json",
                    "language": "json",
                    "content": json.dumps({
                        "name": slug,
                        "version": "0.1.0",
                        "private": True,
                        "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"},
                        "dependencies": {
                            "next": "14.2.0", "react": "^18.2.0", "react-dom": "^18.2.0",
                            "zustand": "^4.5.0", "swr": "^2.2.0", "framer-motion": "^11.0.0",
                            "lucide-react": "^0.300.0", "clsx": "^2.1.0", "zod": "^3.22.0",
                            "tailwind-merge": "^2.2.0",
                        },
                        "devDependencies": {
                            "typescript": "^5.3.0", "@types/react": "^18.2.0", "@types/node": "^20.10.0",
                            "tailwindcss": "^3.4.0", "postcss": "^8.4.0", "autoprefixer": "^10.4.0",
                        }
                    }, indent=2)
                })
        
        if "README.md" not in existing:
            boilerplate.append({
                "name": "README.md",
                "path": "README.md",
                "language": "markdown",
                "content": f"# {info['name']}\n\n{info['description']}\n\n## Quick Start\n\n```bash\ndocker-compose up --build\n```\n"
            })

        if "docker-compose.yml" not in existing:
            db_service_name = "mongodb" if stack["database"] == "mongodb" else "postgres"
            services_block = ""
            if gen_type == "frontend_only":
                services_block = f"""  frontend:
    build: ./frontend
    ports: ["3000:3000"]"""
            elif gen_type in ("backend_only", "microservice"):
                services_block = f"""  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [{db_service_name}]
  {db_service_name}:
    image: {"mongo:7" if db_service_name == "mongodb" else "postgres:15"}"""
            else:
                services_block = f"""  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [{db_service_name}]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  {db_service_name}:
    image: {"mongo:7" if db_service_name == "mongodb" else "postgres:15"}"""
                
            boilerplate.append({
                "name": "docker-compose.yml",
                "path": "docker-compose.yml",
                "language": "yaml",
                "content": f"""version: '3.8'
services:
{services_block}
"""
            })

        return files + boilerplate

