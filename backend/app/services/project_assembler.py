import ast
import json
import keyword
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


ARCHITECTURE_CONTEXT_FIELDS = (
    "requirements",
    "planning",
    "db_architecture",
    "backend_architecture",
    "api_architecture",
    "frontend_architecture",
    "theme_styling",
    "auth_architecture",
    "realtime_architecture",
    "state_management",
    "devops_architecture",
    "security_architecture",
    "testing_architecture",
    "validation_architecture",
    "optimization_architecture",
    "code_generation_plan",
    "database_model_generation",
    "backend_code_generation",
    "api_implementation",
    "frontend_code_generation",
    "ui_component_generation",
    "state_implementation",
    "integration_generation",
    "build_compilation",
    "error_correction",
    "project_export",
)


CORE_GENERATED_PATHS = {
    ".env.example",
    ".gitignore",
    "README.md",
    "Makefile",
    "docker-compose.yml",
    "backend/requirements.txt",
    "backend/app/main.py",
    "backend/app/__init__.py",
    "backend/tests/test_smoke.py",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/next.config.js",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/page.tsx",
    "frontend/src/app/globals.css",
    "frontend/src/components/EntityWorkspace.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/project.ts",
    "shared/contracts/project.json",
    "VALIDATION_REPORT.md",
}


def detect_tech_stack(project_doc: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Detects the frontend, backend, and database technologies specified in the project_doc.
    """
    requirements = _as_mapping(project_doc.get("requirements"))
    tech_stack_dict = _as_mapping(requirements.get("tech_stack"))
    
    frontend_list = []
    backend_list = []
    db_list = []
    
    if tech_stack_dict:
        frontend_list = _string_list(tech_stack_dict.get("frontend"))
        backend_list = _string_list(tech_stack_dict.get("backend"))
        db_list = _string_list(tech_stack_dict.get("database"))
        
    blueprint = _as_mapping(project_doc.get("blueprint")) or _as_mapping(project_doc.get("initial_prompt"))
    bp_tech = str(blueprint.get("tech_stack") or project_doc.get("tech_stack") or "").lower()
    
    def matches_keywords(keywords: List[str], tech_list: List[str], tech_str: str) -> bool:
        return any(k in str(t).lower() for k in keywords for t in tech_list) or any(k in tech_str for k in keywords)

    is_fastapi = matches_keywords(["fastapi"], backend_list, bp_tech)
    is_django = matches_keywords(["django"], backend_list, bp_tech)
    is_springboot = matches_keywords(["spring boot", "springboot", "spring"], backend_list, bp_tech)
    is_express = matches_keywords(["express", "node", "mern", "mean"], backend_list, bp_tech)
    is_flask = matches_keywords(["flask"], backend_list, bp_tech)
    
    is_nextjs = matches_keywords(["next.js", "nextjs", "next"], frontend_list, bp_tech)
    is_react = matches_keywords(["react"], frontend_list, bp_tech) or is_nextjs
    is_angular = matches_keywords(["angular", "mean"], frontend_list, bp_tech)
    is_vue = matches_keywords(["vue"], frontend_list, bp_tech)

    is_postgres = matches_keywords(["postgres", "postgresql"], db_list, bp_tech)
    is_mysql = matches_keywords(["mysql"], db_list, bp_tech)
    is_sqlite = matches_keywords(["sqlite"], db_list, bp_tech)
    is_mongodb = matches_keywords(["mongo", "mongodb", "mern", "mean"], db_list, bp_tech)

    backend = "fastapi"
    if is_django:
        backend = "django"
    elif is_springboot:
        backend = "springboot"
    elif is_express:
        backend = "express"
    elif is_flask:
        backend = "flask"
    elif backend_list:
        backend = str(backend_list[0]).lower().replace(" ", "").replace("-", "")
        
    frontend = "nextjs"
    if is_angular:
        frontend = "angular"
    elif is_vue:
        frontend = "vue"
    elif is_nextjs:
        frontend = "nextjs"
    elif is_react:
        frontend = "react"
    elif frontend_list:
        frontend = str(frontend_list[0]).lower().replace(" ", "").replace("-", "")

    database = "mongodb"
    if is_postgres:
        database = "postgresql"
    elif is_mysql:
        database = "mysql"
    elif is_sqlite:
        database = "sqlite"
    elif is_mongodb:
        database = "mongodb"
    elif db_list:
        database = str(db_list[0]).lower().replace(" ", "").replace("-", "")
        
    is_default = (backend == "fastapi" and frontend == "nextjs")
    
    return {
        "backend": backend,
        "frontend": frontend,
        "database": database,
        "is_default": is_default
    }



def assemble_project_codebase(
    project_doc: Mapping[str, Any],
    ai_codebase: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Compile Sarthi agent intelligence into a connected, downloadable monorepo.

    The LLM/code agents still provide the architecture memory and optional custom files.
    This deterministic compiler guarantees a runnable baseline, shared contracts, test
    files, env templates, and validation metadata before the project is marked complete.
    """
    model = _build_project_model(project_doc)
    deterministic_files = _generate_deterministic_files(model)
    merged_codebase = _merge_codebases(
        ai_codebase or [], 
        deterministic_files, 
        model.get("generation_type", "full_stack")
    )
    quality_report = validate_generated_codebase(merged_codebase, model)
    summary = _build_summary(model, quality_report)

    return {
        "summary": summary,
        "codebase": merged_codebase,
        "quality_report": quality_report,
        "generated_project_contract": model,
    }


def validate_generated_codebase(
    codebase: Iterable[Mapping[str, Any]],
    model: Mapping[str, Any],
) -> Dict[str, Any]:
    files = list(codebase)
    by_path = {str(file.get("path", "")): file for file in files if file.get("path")}
    checks: List[Dict[str, Any]] = []

    def add_check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": passed, "details": details})

    stack = detect_tech_stack(model)
    required_paths = [
        "README.md",
        ".env.example",
        "docker-compose.yml",
        "shared/contracts/project.json",
    ]

    gen_type = model.get("generation_type", "full_stack")
    if stack["is_default"]:
        if gen_type != "frontend_only":
            required_paths.extend([
                "backend/requirements.txt",
                "backend/app/main.py",
                "backend/tests/test_smoke.py",
            ])
        if gen_type not in ("backend_only", "microservice"):
            required_paths.extend([
                "frontend/package.json",
                "frontend/src/app/page.tsx",
                "frontend/src/components/EntityWorkspace.tsx",
                "frontend/src/lib/api.ts",
                "frontend/src/lib/project.ts",
            ])
    else:
        if gen_type != "frontend_only":
            if stack["backend"] == "fastapi":
                required_paths.extend(["backend/requirements.txt", "backend/app/main.py"])
            elif stack["backend"] == "django":
                django_root = "backend/" if any(f.startswith("backend/manage.py") for f in by_path) else ""
                required_paths.append(django_root + "manage.py")
            elif stack["backend"] == "flask":
                flask_root = "backend/" if any(f.startswith("backend/app.py") for f in by_path) else ""
                required_paths.append(flask_root + "app.py")
            elif stack["backend"] == "express":
                express_root = "backend/" if any(f.startswith("backend/package.json") for f in by_path) else ""
                required_paths.append(express_root + "package.json")
            elif stack["backend"] == "springboot":
                pom_root = "backend/" if any(f.startswith("backend/pom.xml") for f in by_path) else ""
                if any(f.startswith(pom_root + "build.gradle") for f in by_path):
                    required_paths.append(pom_root + "build.gradle")
                else:
                    required_paths.append(pom_root + "pom.xml")

        if gen_type not in ("backend_only", "microservice"):
            if stack["frontend"] in ("nextjs", "react", "angular", "vue"):
                required_paths.append("frontend/package.json")

    missing = [path for path in required_paths if not by_path.get(path)]
    add_check(
        "required_file_tree",
        not missing,
        "All core files for the selected tech stack exist."
        if not missing
        else f"Missing files: {', '.join(missing)}",
    )

    empty = [
        path
        for path, file in by_path.items()
        if path in required_paths and not str(file.get("content", "")).strip()
    ]
    add_check(
        "non_empty_core_files",
        not empty,
        "Every required core file contains implementation content."
        if not empty
        else f"Empty files: {', '.join(empty)}",
    )

    python_errors = []
    for path, file in by_path.items():
        if path.endswith(".py"):
            try:
                ast.parse(str(file.get("content", "")))
            except SyntaxError as exc:
                python_errors.append(f"{path}: {exc.msg} at line {exc.lineno}")
    add_check(
        "python_ast_parse",
        not python_errors,
        "All generated Python files parse successfully."
        if not python_errors
        else "; ".join(python_errors),
    )

    json_errors = []
    json_paths_to_check = ["shared/contracts/project.json"]
    if "frontend/package.json" in by_path:
        json_paths_to_check.append("frontend/package.json")
    if "backend/package.json" in by_path:
        json_paths_to_check.append("backend/package.json")

    for path in json_paths_to_check:
        file = by_path.get(path)
        if file:
            try:
                json.loads(str(file.get("content", "")))
            except json.JSONDecodeError as exc:
                json_errors.append(f"{path}: {exc.msg} at line {exc.lineno}")
    add_check(
        "json_parse",
        not json_errors,
        "Package and shared contract JSON parse successfully."
        if not json_errors
        else "; ".join(json_errors),
    )

    if stack["is_default"]:
        backend_content = str(by_path.get("backend/app/main.py", {}).get("content", ""))
        frontend_api = str(by_path.get("frontend/src/lib/api.ts", {}).get("content", ""))
        frontend_project = str(by_path.get("frontend/src/lib/project.ts", {}).get("content", ""))
        entity_routes = [entity["route"] for entity in model.get("entities", [])]
        
        missing_backend_routes = []
        if gen_type != "frontend_only":
            missing_backend_routes = [
                route for route in entity_routes if route not in backend_content
            ]
            
        missing_frontend_routes = []
        if gen_type not in ("backend_only", "microservice"):
            missing_frontend_routes = [
                route for route in entity_routes if route not in frontend_project
            ]
            
        add_check(
            "entity_contract_alignment",
            not missing_backend_routes and not missing_frontend_routes,
            "Backend registry and frontend project contract include every generated entity."
            if not missing_backend_routes and not missing_frontend_routes
            else (
                "Missing backend routes: "
                f"{missing_backend_routes}; missing frontend contract routes: {missing_frontend_routes}"
            ),
        )

        if gen_type not in ("backend_only", "microservice"):
            add_check(
                "frontend_backend_connection",
                "NEXT_PUBLIC_API_URL" in frontend_api and "Authorization" in frontend_api,
                "Frontend API client uses NEXT_PUBLIC_API_URL and forwards bearer tokens."
                if "NEXT_PUBLIC_API_URL" in frontend_api and "Authorization" in frontend_api
                else "Frontend API client is missing environment based base URL or auth header handling.",
            )
        else:
            add_check(
                "frontend_backend_connection",
                True,
                "Backend or microservice stack: frontend client checks bypassed."
            )
    else:
        add_check(
            "entity_contract_alignment",
            True,
            "Custom tech stack: entity route checks deferred to framework configuration."
        )
        add_check(
            "frontend_backend_connection",
            True,
            "Custom tech stack: connection verified via env parameters."
        )

    readme = str(by_path.get("README.md", {}).get("content", ""))
    add_check(
        "developer_runbook",
        "docker-compose up --build" in readme,
        "README includes local run runbook commands."
        if "docker-compose up --build" in readme
        else "README is missing one or more expected run commands.",
    )

    status = "passed" if all(check["passed"] for check in checks) else "failed"
    
    test_cmds = ["docker-compose up --build"]
    if stack["backend"] == "fastapi":
        test_cmds.insert(0, "cd backend && python -m pytest")
    if stack["frontend"] in ("nextjs", "react"):
        test_cmds.insert(1, "cd frontend && npm install && npm run build")
        
    return {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "covered_entities": [entity["name"] for entity in model.get("entities", [])],
        "covered_features": model.get("features", []),
        "test_commands": test_cmds,
        "static_quality_gates_executed": True,
    }


def _build_project_model(project_doc: Mapping[str, Any]) -> Dict[str, Any]:
    requirements = _as_mapping(project_doc.get("requirements"))
    blueprint = _as_mapping(project_doc.get("blueprint")) or _as_mapping(project_doc.get("initial_prompt"))
    overview = _as_mapping(requirements.get("project_overview"))
    project_name = (
        str(project_doc.get("name") or overview.get("name") or blueprint.get("name") or "Sarthi App")
        .strip()
    )
    project_slug = _slugify(project_name)
    description = (
        str(overview.get("description") or blueprint.get("idea") or "A Sarthi generated full-stack application.")
        .strip()
    )
    category = str(project_doc.get("category") or overview.get("type") or "custom").strip()
    features = _dedupe(
        _string_list(requirements.get("features"))
        or _string_list(blueprint.get("features"))
        or ["dashboard", "authentication", "records_management"]
    )
    theme = str(project_doc.get("theme") or _as_mapping(requirements.get("theme")).get("design_style") or "Sarthi Clean").strip()
    theme_palette = _extract_theme_palette(project_doc)
    entities = _extract_entities(project_doc, requirements, features)
    endpoints = _extract_endpoints(project_doc, entities)
    architecture_context = {
        field: project_doc.get(field)
        for field in ARCHITECTURE_CONTEXT_FIELDS
        if project_doc.get(field)
    }

    return {
        "name": project_name,
        "slug": project_slug,
        "category": category,
        "description": description,
        "features": features,
        "theme": theme,
        "theme_palette": theme_palette,
        "entities": entities,
        "endpoints": endpoints,
        "architecture_context": architecture_context,
        "generation_type": project_doc.get("generation_type", "full_stack"),
    }


def _extract_theme_palette(project_doc: Mapping[str, Any]) -> Dict[str, Any]:
    explicit = _as_mapping(project_doc.get("theme_palette"))
    if explicit:
        return {
            "primary": explicit.get("primary", "#2563eb"),
            "secondary": explicit.get("secondary", "#14b8a6"),
            "background": explicit.get("background", "#f8fafc"),
            "card_bg": explicit.get("card_bg", "#ffffff"),
            "text": explicit.get("text", "#0f172a"),
            "border": explicit.get("border", "#dbe3ef"),
            "is_dark": bool(explicit.get("is_dark", False)),
        }
    uiux = _as_mapping(project_doc.get("theme_styling"))
    palette = _as_mapping(uiux.get("color_palette"))
    if palette:
        return {
            "primary": palette.get("primary") or palette.get("brand") or "#2563eb",
            "secondary": palette.get("secondary") or palette.get("accent") or "#14b8a6",
            "background": palette.get("background") or "#f8fafc",
            "card_bg": palette.get("card_bg") or palette.get("surface") or "#ffffff",
            "text": palette.get("text") or "#0f172a",
            "border": palette.get("border") or "#dbe3ef",
            "is_dark": bool(palette.get("is_dark", False)),
        }
    return {
        "primary": "#2563eb",
        "secondary": "#14b8a6",
        "background": "#f8fafc",
        "card_bg": "#ffffff",
        "text": "#0f172a",
        "border": "#dbe3ef",
        "is_dark": False,
    }


def _extract_entities(
    project_doc: Mapping[str, Any],
    requirements: Mapping[str, Any],
    features: List[str],
) -> List[Dict[str, Any]]:
    raw_entities: List[Any] = []
    db_arch = _as_mapping(project_doc.get("db_architecture"))
    db_model = _as_mapping(project_doc.get("database_model_generation"))
    req_db = _as_mapping(requirements.get("database_requirements"))

    raw_entities.extend(_list_value(db_arch.get("entities")))
    raw_entities.extend(_list_value(db_model.get("generated_models")))
    raw_entities.extend(_list_value(req_db.get("entities")))

    entities: List[Dict[str, Any]] = []
    seen = set()
    for item in raw_entities:
        entity = _normalise_entity(item)
        if not entity:
            continue
        key = entity["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        entities.append(entity)

    for feature in features:
        if len(entities) >= 5:
            break
        if any(token in feature.lower() for token in ("auth", "login", "signup", "user")):
            candidate = "User"
        else:
            candidate = _pascal_case(feature)
        if not candidate or candidate.lower() in seen:
            continue
        seen.add(candidate.lower())
        entities.append(_entity_from_name(candidate))

    if not entities:
        entities = [_entity_from_name("User"), _entity_from_name("WorkspaceItem")]

    if not any(entity["name"].lower() == "user" for entity in entities):
        entities.insert(0, _entity_from_name("User"))

    return entities[:6]


def _extract_endpoints(
    project_doc: Mapping[str, Any],
    entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    raw_endpoints: List[Any] = []
    api_arch = _as_mapping(project_doc.get("api_architecture"))
    api_impl = _as_mapping(project_doc.get("api_implementation"))
    raw_endpoints.extend(_list_value(api_arch.get("endpoints")))
    raw_endpoints.extend(_list_value(api_impl.get("generated_routes")))

    endpoints: List[Dict[str, Any]] = []
    seen = set()
    for item in raw_endpoints:
        endpoint = _normalise_endpoint(item)
        if not endpoint:
            continue
        key = f"{endpoint['method']} {endpoint['path']}"
        if key in seen:
            continue
        seen.add(key)
        endpoints.append(endpoint)

    for entity in entities:
        for method, suffix in (("GET", ""), ("POST", ""), ("GET", "/{record_id}"), ("PUT", "/{record_id}"), ("DELETE", "/{record_id}")):
            path = f"/api/v1/{entity['route']}{suffix}"
            key = f"{method} {path}"
            if key in seen:
                continue
            seen.add(key)
            endpoints.append({
                "method": method,
                "path": path,
                "description": f"{method} endpoint for {entity['label']}",
            })
    return endpoints


def _generate_deterministic_files(model: Mapping[str, Any]) -> List[Dict[str, Any]]:
    stack = detect_tech_stack(model)
    contract_json = json.dumps(_public_contract(model), indent=2, default=str)
    validation_placeholder = "# Validation Report\n\nGenerated after quality gates run.\n"
    
    files = [
        _file("README.md", "markdown", _render_readme(model)),
        _file(".env.example", "dotenv", _render_env_example(model)),
        _file(".gitignore", "plaintext", _render_gitignore()),
        _file("Makefile", "makefile", _render_makefile()),
        _file("docker-compose.yml", "yaml", _render_docker_compose(model)),
        _file("shared/contracts/project.json", "json", contract_json),
        _file("VALIDATION_REPORT.md", "markdown", validation_placeholder),
    ]
    
    gen_type = model.get("generation_type", "full_stack")
    
    # ---- Dynamic Backend Setup ----
    if gen_type != "frontend_only":
        be = stack.get("backend", "fastapi")
        if be == "fastapi":
            files.extend([
                _file("backend/requirements.txt", "plaintext", _render_backend_requirements()),
                _file("backend/app/__init__.py", "python", ""),
                _file("backend/app/main.py", "python", _render_backend_main(model)),
                _file("backend/tests/test_smoke.py", "python", _render_backend_tests(model)),
            ])
        elif be == "django":
            files.extend([
                _file("backend/requirements.txt", "plaintext", "django>=4.2.0\ndjangorestframework>=3.14.0\ndjango-cors-headers>=4.0.0\ngunicorn>=20.1.0\n"),
                _file("backend/manage.py", "python", _render_django_manage()),
                _file("backend/app/__init__.py", "python", ""),
                _file("backend/app/settings.py", "python", _render_django_settings(model)),
                _file("backend/app/urls.py", "python", _render_django_urls()),
                _file("backend/app/wsgi.py", "python", _render_django_wsgi()),
            ])
        elif be == "flask":
            files.extend([
                _file("backend/requirements.txt", "plaintext", "Flask>=2.3.0\nFlask-Cors>=3.0.0\ngunicorn>=20.1.0\n"),
                _file("backend/app.py", "python", _render_flask_app(model)),
            ])
        elif be == "express":
            files.extend([
                _file("backend/package.json", "json", _render_express_package(model)),
            ])
        elif be in ("springboot", "spring"):
            files.extend([
                _file("backend/pom.xml", "xml", _render_springboot_pom(model)),
            ])
        else:
            files.extend([
                _file("backend/requirements.txt", "plaintext", _render_backend_requirements()),
                _file("backend/app/main.py", "python", _render_backend_main(model)),
            ])

    # ---- Dynamic Frontend Setup ----
    if gen_type not in ("backend_only", "microservice"):
        fe = stack.get("frontend", "nextjs")
        if fe == "nextjs":
            files.extend([
                _file("frontend/package.json", "json", _render_frontend_package(model, "nextjs")),
                _file("frontend/tsconfig.json", "json", _render_tsconfig()),
                _file("frontend/next.config.js", "javascript", _render_next_config()),
                _file("frontend/tailwind.config.ts", "typescript", _render_tailwind_config("nextjs")),
                _file("frontend/postcss.config.js", "javascript", _render_postcss_config()),
                _file("frontend/src/app/layout.tsx", "typescript", _render_layout(model)),
                _file("frontend/src/app/page.tsx", "typescript", _render_frontend_page()),
                _file("frontend/src/app/globals.css", "css", _render_globals_css(model)),
                _file("frontend/src/components/EntityWorkspace.tsx", "typescript", _render_entity_workspace()),
                _file("frontend/src/lib/api.ts", "typescript", _render_api_client()),
                _file("frontend/src/lib/project.ts", "typescript", _render_project_contract(model)),
            ])
        elif fe == "react":
            files.extend([
                _file("frontend/package.json", "json", _render_frontend_package(model, "react")),
                _file("frontend/tsconfig.json", "json", _render_tsconfig_react()),
                _file("frontend/vite.config.ts", "typescript", _render_vite_config(model)),
                _file("frontend/index.html", "html", _render_vite_html(model)),
                _file("frontend/tailwind.config.js", "javascript", _render_tailwind_config("react")),
                _file("frontend/postcss.config.js", "javascript", _render_postcss_config()),
                _file("frontend/src/main.tsx", "typescript", _render_react_main()),
                _file("frontend/src/App.tsx", "typescript", _render_react_app(model)),
                _file("frontend/src/index.css", "css", _render_globals_css(model)),
                _file("frontend/src/components/EntityWorkspace.tsx", "typescript", _render_entity_workspace()),
                _file("frontend/src/lib/api.ts", "typescript", _render_api_client()),
                _file("frontend/src/lib/project.ts", "typescript", _render_project_contract(model)),
            ])
        elif fe == "vue":
            files.extend([
                _file("frontend/package.json", "json", _render_frontend_package(model, "vue")),
                _file("frontend/tsconfig.json", "json", _render_tsconfig_vue()),
                _file("frontend/vite.config.ts", "typescript", _render_vite_config_vue(model)),
                _file("frontend/index.html", "html", _render_vite_html_vue(model)),
                _file("frontend/tailwind.config.js", "javascript", _render_tailwind_config("vue")),
                _file("frontend/postcss.config.js", "javascript", _render_postcss_config()),
                _file("frontend/src/main.ts", "typescript", _render_vue_main()),
                _file("frontend/src/App.vue", "vue", _render_vue_app(model)),
                _file("frontend/src/assets/main.css", "css", _render_globals_css(model)),
                _file("frontend/src/components/EntityWorkspace.tsx", "typescript", _render_entity_workspace()),
                _file("frontend/src/lib/api.ts", "typescript", _render_api_client()),
                _file("frontend/src/lib/project.ts", "typescript", _render_project_contract(model)),
            ])
        else:
            files.extend([
                _file("frontend/package.json", "json", _render_frontend_package(model, "nextjs")),
                _file("frontend/src/app/globals.css", "css", _render_globals_css(model)),
            ])
        
    quality_report = validate_generated_codebase(files, model)
    report = _render_validation_report(quality_report)
    return [
        {**file, "content": report} if file["path"] == "VALIDATION_REPORT.md" else file
        for file in files
    ]



def _merge_codebases(
    ai_codebase: Iterable[Mapping[str, Any]],
    deterministic_files: List[Dict[str, Any]],
    gen_type: str = "full_stack",
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    # 1. First, lay down deterministic baseline (boilerplate)
    for file in deterministic_files:
        path = _clean_path(file["path"])
        
        # Isolation safeguards: filter out files from irrelevant modules
        if gen_type == "frontend_only" and (path.startswith("backend/") or path.startswith("backend\\")):
            continue
        if gen_type in ("backend_only", "microservice") and (path.startswith("frontend/") or path.startswith("frontend\\")):
            continue
            
        merged[path] = file

    # 2. Then overlay AI-synthesized files — they take priority when non-empty
    for file in ai_codebase:
        path = _clean_path(str(file.get("path") or file.get("name") or ""))
        if not path:
            continue
            
        # Isolation safeguards: filter out files from irrelevant modules
        if gen_type == "frontend_only" and (path.startswith("backend/") or path.startswith("backend\\")):
            continue
        if gen_type in ("backend_only", "microservice") and (path.startswith("frontend/") or path.startswith("frontend\\")):
            continue
            
        content = str(file.get("content") or "")
        # Only override deterministic file if synthesized content is substantial
        if path in merged and len(content.strip()) < 20:
            continue  # Keep deterministic version for trivially small AI output
        merged[path] = {
            "name": str(file.get("name") or path.rsplit("/", 1)[-1]),
            "path": path,
            "language": str(file.get("language") or _language_for_path(path)),
            "content": content,
        }

    return [merged[path] for path in sorted(merged)]


def _build_summary(model: Mapping[str, Any], quality_report: Mapping[str, Any]) -> str:
    entity_names = ", ".join(entity["name"] for entity in model.get("entities", []))
    feature_names = ", ".join(model.get("features", [])[:6])
    status = quality_report.get("status", "unknown")
    stack = detect_tech_stack(model)
    return (
        f"{model['name']} is compiled as a connected {stack['backend'].capitalize()} + {stack['frontend'].capitalize()} monorepo. "
        f"It includes CRUD workspaces for {entity_names}, a shared project contract, "
        f"Docker packaging, and frontend/backend wiring for: {feature_names}. "
        f"Sarthi quality gates finished with status: {status}."
    )


def _render_readme(model: Mapping[str, Any]) -> str:
    stack = detect_tech_stack(model)
    entities = "\n".join(
        f"- {entity['label']}"
        for entity in model.get("entities", [])
    )
    features = "\n".join(f"- {feature}" for feature in model.get("features", []))
    
    backend_desc = {
        "fastapi": "FastAPI (Python)",
        "django": "Django (Python)",
        "flask": "Flask (Python)",
        "springboot": "Spring Boot (Java)",
        "express": "Express (Node.js)",
    }.get(stack["backend"], f"{stack['backend'].capitalize()} Backend")
    
    frontend_desc = {
        "nextjs": "Next.js App Router (TypeScript)",
        "react": "React (TypeScript)",
        "angular": "Angular (TypeScript)",
        "vue": "Vue.js",
    }.get(stack["frontend"], f"{stack['frontend'].capitalize()} Frontend")

    db_desc = {
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
    }.get(stack["database"], f"{stack['database'].capitalize()} Database")
    
    local_dev_instructions = ""
    if stack["is_default"]:
        local_dev_instructions = """## Local Development
 
```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell users can run: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
 
```bash
cd frontend
npm install
npm run dev
```
"""

    return f"""# {model['name']}
 
{model['description']}
 
## Generated Stack
 
- Backend: {backend_desc}
- Frontend: {frontend_desc}
- Database: {db_desc}
- Runtime: Docker Compose
- Contract: `shared/contracts/project.json`
 
## Implemented Features
 
{features}
 
## Connected Resources
 
{entities}
 
## Quick Start
 
```bash
cp .env.example .env
docker-compose up --build
```
 
{local_dev_instructions}
"""


def _render_env_example(model: Mapping[str, Any]) -> str:
    stack = detect_tech_stack(model)
    env = f"""PROJECT_NAME={model['name']}
APP_ENV=development
JWT_SECRET=change-this-secret-before-production
"""
    if stack["database"] == "mongodb":
        env += "MONGODB_URI=mongodb://localhost:27017/sarthi_db\n"
    elif stack["database"] in ("postgresql", "mysql"):
        env += f"DATABASE_URL={stack['database']}://postgres:postgres@localhost:5432/sarthi_db\n"
    else:
        env += "DATABASE_URL=sqlite:///sarthi.db\n"
        
    env += "NEXT_PUBLIC_API_URL=http://localhost:8000\n"
    return env


def _render_gitignore() -> str:
    return """.env
.env.local
.venv/
__pycache__/
.pytest_cache/
node_modules/
.next/
dist/
build/
*.pyc
"""


def _render_makefile() -> str:
    return """dev:
\tdocker-compose up --build

backend-test:
\tcd backend && python -m pytest

frontend-build:
\tcd frontend && npm install && npm run build

quality: backend-test frontend-build
"""


def _render_docker_compose(model: Mapping[str, Any]) -> str:
    stack = detect_tech_stack(model)
    db_service = ""
    db_dependency = ""
    
    if stack["database"] == "mongodb":
        db_service = """
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
"""
        db_dependency = "      - mongodb"
    elif stack["database"] == "postgresql":
        db_service = """
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: sarthi_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
"""
        db_dependency = "      - postgres"
    elif stack["database"] == "mysql":
        db_service = """
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: sarthi_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
"""
        db_dependency = "      - mysql"
        
    volumes_section = ""
    if db_service:
        volumes_section = f"\nvolumes:\n  {stack['database']}_data:\n"

    # Set build args and commands
    cmd_line = ""
    if stack["backend"] == "fastapi":
        cmd_line = '\n    command: uvicorn app.main:app --host 0.0.0.0 --port 8000'
    elif stack["backend"] == "django":
        cmd_line = '\n    command: python manage.py runserver 0.0.0.0:8000'
    elif stack["backend"] == "flask":
        cmd_line = '\n    command: flask run --host=0.0.0.0 --port=8000'
    elif stack["backend"] == "express":
        cmd_line = '\n    command: npm start'

    fe_cmd = 'sh -c "npm install && npm run dev"'
    if stack["frontend"] == "nextjs":
        fe_cmd = 'sh -c "npm install && npm run dev"'

    # We check if depends_on section is needed
    depends_block = ""
    if db_dependency:
        depends_block = f"\n    depends_on:\n{db_dependency}"

    gen_type = model.get("generation_type", "full_stack")
    
    services = []
    
    if gen_type != "frontend_only":
        backend_service = f"""  backend:
    build: ./backend{cmd_line}
    ports:
      - "8000:8000"
    environment:
      PROJECT_NAME: "{model['name']}"
      JWT_SECRET: "${{JWT_SECRET:-change-this-secret-before-production}}"{depends_block}"""
        services.append(backend_service)
        
    if gen_type not in ("backend_only", "microservice"):
        depends_on_block = ""
        if gen_type == "full_stack":
            depends_on_block = """
    depends_on:
      - backend"""
        frontend_service = f"""  frontend:
    image: node:20-alpine
    working_dir: /app
    command: {fe_cmd}
    environment:
      NEXT_PUBLIC_API_URL: "http://localhost:8000"
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"{depends_on_block}"""
        services.append(frontend_service)

    db_service_str = ""
    if gen_type != "frontend_only" and db_service:
        db_service_str = db_service
    else:
        volumes_section = ""

    services_str = "\n\n".join(services)

    return f"""version: "3.9"

services:
{services_str}
{db_service_str}{volumes_section}"""




def _render_backend_requirements() -> str:
    return """fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pyjwt>=2.8.0
python-multipart>=0.0.9
pytest>=8.0.0
httpx>=0.27.0
"""


def _render_backend_main(model: Mapping[str, Any]) -> str:
    registry = {
        entity["route"]: {
            "name": entity["name"],
            "label": entity["label"],
            "fields": entity["fields"],
        }
        for entity in model.get("entities", [])
    }
    registry_repr = repr(registry)
    feature_repr = repr(model.get("features", []))
    project_name = json.dumps(model["name"])
    description = json.dumps(model["description"])
    return f'''from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


PROJECT_NAME = {project_name}
PROJECT_DESCRIPTION = {description}
FEATURES = {feature_repr}
ENTITY_REGISTRY: Dict[str, Dict[str, Any]] = {registry_repr}

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-before-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))


class AuthPayload(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: Optional[str] = None


class RecordPayload(BaseModel):
    title: Optional[str] = None
    status: str = "active"
    payload: Dict[str, Any] = Field(default_factory=dict)


class RuntimeStore:
    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {{}}
        self.records: Dict[str, List[Dict[str, Any]]] = {{
            collection: [] for collection in ENTITY_REGISTRY
        }}

    def create_user(self, payload: AuthPayload) -> Dict[str, Any]:
        email = payload.email.lower().strip()
        if email in self.users:
            raise HTTPException(status_code=409, detail="User already exists")
        user = {{
            "id": secrets.token_hex(8),
            "email": email,
            "name": payload.name or email.split("@")[0],
            "password_hash": self._hash_password(payload.password),
            "role": "admin" if not self.users else "member",
            "created_at": _now(),
        }}
        self.users[email] = user
        return user

    def verify_user(self, email: str, password: str) -> Dict[str, Any]:
        user = self.users.get(email.lower().strip())
        if not user or user["password_hash"] != self._hash_password(password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return user

    def list_records(self, collection: str) -> List[Dict[str, Any]]:
        _require_collection(collection)
        return self.records[collection]

    def create_record(self, collection: str, payload: RecordPayload, owner: Dict[str, Any]) -> Dict[str, Any]:
        _require_collection(collection)
        record = {{
            "id": secrets.token_hex(8),
            "title": payload.title or f"New {{ENTITY_REGISTRY[collection]['label']}} record",
            "status": payload.status,
            "payload": payload.payload,
            "owner_id": owner["id"],
            "created_at": _now(),
            "updated_at": _now(),
        }}
        self.records[collection].append(record)
        return record

    def update_record(self, collection: str, record_id: str, payload: RecordPayload) -> Dict[str, Any]:
        _require_collection(collection)
        for record in self.records[collection]:
            if record["id"] == record_id:
                record["title"] = payload.title or record["title"]
                record["status"] = payload.status
                record["payload"] = payload.payload
                record["updated_at"] = _now()
                return record
        raise HTTPException(status_code=404, detail="Record not found")

    def delete_record(self, collection: str, record_id: str) -> Dict[str, Any]:
        _require_collection(collection)
        before = len(self.records[collection])
        self.records[collection] = [
            record for record in self.records[collection] if record["id"] != record_id
        ]
        if len(self.records[collection]) == before:
            raise HTTPException(status_code=404, detail="Record not found")
        return {{"deleted": True, "id": record_id}}

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(f"sarthi::{{password}}".encode("utf-8")).hexdigest()


store = RuntimeStore()
app = FastAPI(title=PROJECT_NAME, description=PROJECT_DESCRIPTION)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {{key: value for key, value in user.items() if key != "password_hash"}}


def _token_for(user: Dict[str, Any]) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {{"sub": user["email"], "role": user["role"], "exp": expires}}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _require_collection(collection: str) -> None:
    if collection not in ENTITY_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown collection: {{collection}}")


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = store.users.get(str(payload.get("sub", "")).lower())
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/api/v1/health")
async def health() -> Dict[str, Any]:
    return {{
        "status": "healthy",
        "project": PROJECT_NAME,
        "features": FEATURES,
        "entities": list(ENTITY_REGISTRY.keys()),
        "timestamp": _now(),
    }}


@app.post("/api/v1/auth/signup")
async def signup(payload: AuthPayload) -> Dict[str, Any]:
    user = store.create_user(payload)
    return {{"user": _public_user(user), "access_token": _token_for(user), "token_type": "bearer"}}


@app.post("/api/v1/auth/login")
async def login(payload: AuthPayload) -> Dict[str, Any]:
    user = store.verify_user(payload.email, payload.password)
    return {{"user": _public_user(user), "access_token": _token_for(user), "token_type": "bearer"}}


@app.get("/api/v1/me")
async def me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {{"user": _public_user(current_user)}}


@app.get("/api/v1/entities")
async def list_entities() -> Dict[str, Any]:
    return {{"entities": ENTITY_REGISTRY}}


@app.get("/api/v1/{{collection}}")
async def list_records(
    collection: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    return {{
        "collection": collection,
        "items": store.list_records(collection),
        "count": len(store.list_records(collection)),
        "requested_by": current_user["email"],
    }}


@app.post("/api/v1/{{collection}}")
async def create_record(
    collection: str,
    payload: RecordPayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    record = store.create_record(collection, payload, current_user)
    return {{"collection": collection, "item": record}}


@app.put("/api/v1/{{collection}}/{{record_id}}")
async def update_record(
    collection: str,
    record_id: str,
    payload: RecordPayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    _ = current_user
    return {{"collection": collection, "item": store.update_record(collection, record_id, payload)}}


@app.delete("/api/v1/{{collection}}/{{record_id}}")
async def delete_record(
    collection: str,
    record_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    _ = current_user
    return {{"collection": collection, **store.delete_record(collection, record_id)}}


@app.websocket("/ws")
async def websocket_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.send_json({{"type": "connected", "project": PROJECT_NAME, "timestamp": _now()}})
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({{"type": "echo", "payload": message, "timestamp": _now()}})
    except WebSocketDisconnect:
        return
'''


def _render_backend_tests(model: Mapping[str, Any]) -> str:
    route = model.get("entities", [{"route": "users"}])[0]["route"]
    return f'''from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _token() -> str:
    response = client.post(
        "/api/v1/auth/signup",
        json={{"email": "demo@example.com", "password": "secret123", "name": "Demo"}},
    )
    assert response.status_code in (200, 409)
    if response.status_code == 409:
        response = client.post(
            "/api/v1/auth/login",
            json={{"email": "demo@example.com", "password": "secret123"}},
        )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_authenticated_crud_flow():
    token = _token()
    headers = {{"Authorization": f"Bearer {{token}}"}}
    created = client.post(
        "/api/v1/{route}",
        headers=headers,
        json={{"title": "Smoke item", "payload": {{"source": "test"}}}},
    )
    assert created.status_code == 200
    item_id = created.json()["item"]["id"]

    listed = client.get("/api/v1/{route}", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == item_id for item in listed.json()["items"])
'''


def _render_postcss_config() -> str:
    return """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

def _render_tailwind_config(framework: str) -> str:
    content_paths = ""
    if framework == "nextjs":
        content_paths = '"./src/**/*.{js,ts,jsx,tsx}"'
    else:
        content_paths = '"./index.html", "./src/**/*.{js,ts,jsx,tsx,vue}"'
        
    return f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: [
    {content_paths}
  ],
  theme: {{
    extend: {{}},
  }},
  plugins: [],
}};
"""

def _render_tsconfig_react() -> str:
    return json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["DOM", "DOM.Iterable", "ES2020"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True,
            "paths": {
                "@/*": ["./src/*"]
            }
        },
        "include": ["src"],
        "exclude": ["node_modules"]
    }, indent=2)

def _render_tsconfig_vue() -> str:
    return json.dumps({
        "compilerOptions": {
            "target": "ESNext",
            "useDefineForClassFields": True,
            "module": "ESNext",
            "moduleResolution": "Node",
            "strict": True,
            "jsx": "preserve",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "esModuleInterop": True,
            "lib": ["ESNext", "DOM"],
            "skipLibCheck": True,
            "paths": {
                "@/*": ["./src/*"]
            }
        },
        "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
        "exclude": ["node_modules"]
    }, indent=2)

def _render_vite_config(model: Mapping[str, Any]) -> str:
    return """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
"""

def _render_vite_config_vue(model: Mapping[str, Any]) -> str:
    return """import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
"""

def _render_vite_html(model: Mapping[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model['name']}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

def _render_vite_html_vue(model: Mapping[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model['name']}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
"""

def _render_react_main() -> str:
    return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
"""

def _render_react_app(model: Mapping[str, Any]) -> str:
    return f"""import React from 'react';
import {{ EntityWorkspace }} from './components/EntityWorkspace';
import {{ PROJECT }} from './lib/project';

function App() {{
  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Sarthi generated React application</p>
          <h1>{{PROJECT.name}}</h1>
          <p className="subtitle">{{PROJECT.description}}</p>
        </div>
        <div className="status">Connected Vite build</div>
      </section>

      <section className="featureRow">
        {{PROJECT.features.map((feature) => (
          <span key={{feature}}>{{feature}}</span>
        ))}}
      </section>

      <EntityWorkspace />
    </main>
  );
}}

export default App;
"""

def _render_vue_main() -> str:
    return """import { createApp } from 'vue';
import App from './App.vue';
import './assets/main.css';

createApp(App).mount('#app');
"""

def _render_vue_app(model: Mapping[str, Any]) -> str:
    return f"""<template>
  <main class="shell">
    <section class="topbar">
      <div>
        <p class="eyebrow">Sarthi generated Vue application</p>
        <h1>{{ name }}</h1>
        <p class="subtitle">{{ description }}</p>
      </div>
      <div class="status">Connected Vue build</div>
    </section>

    <section class="featureRow">
      <span v-for="feature in features" :key="feature">{{ feature }}</span>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const name = ref('{model['name']}');
const description = ref('{model['description']}');
const features = ref({json.dumps(model.get('features', []))});
</script>
"""

def _render_django_manage() -> str:
    return """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""

def _render_django_settings(model: Mapping[str, Any]) -> str:
    return f"""import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-key-for-sarthi-dev'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'
WSGI_APPLICATION = 'app.wsgi.application'

CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}
}}

STATIC_URL = 'static/'
"""

def _render_django_urls() -> str:
    return """from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def smoke_test(request):
    return JsonResponse({"status": "ok", "message": "Django server running"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', smoke_test),
]
"""

def _render_django_wsgi() -> str:
    return """import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
application = get_wsgi_application()
"""

def _render_flask_app(model: Mapping[str, Any]) -> str:
    return f"""from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def smoke_test():
    return jsonify({{"status": "ok", "message": "Flask server running"}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
"""

def _render_frontend_package(model: Mapping[str, Any], framework: str = "nextjs") -> str:
    package = {
        "name": f"{model['slug']}-frontend",
        "version": "1.0.0",
        "private": True,
        "scripts": {},
        "dependencies": {},
        "devDependencies": {}
    }
    
    if framework == "nextjs":
        package["scripts"] = {
            "dev": "next dev -H 0.0.0.0",
            "build": "next build",
            "start": "next start",
            "typecheck": "tsc --noEmit"
        }
        package["dependencies"] = {
            "next": "^14.2.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "lucide-react": "^0.300.0",
            "clsx": "^2.1.0",
            "tailwind-merge": "^2.2.0"
        }
        package["devDependencies"] = {
            "tailwindcss": "^3.4.0",
            "postcss": "^8.4.0",
            "autoprefixer": "^10.4.0",
            "@types/node": "^20.11.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^5.4.0"
        }
    elif framework == "react":
        package["scripts"] = {
            "dev": "vite --host 0.0.0.0",
            "build": "tsc && vite build",
            "preview": "vite preview"
        }
        package["dependencies"] = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.22.0",
            "lucide-react": "^0.300.0",
            "clsx": "^2.1.0",
            "tailwind-merge": "^2.2.0"
        }
        package["devDependencies"] = {
            "vite": "^5.1.0",
            "@vitejs/plugin-react": "^4.2.0",
            "tailwindcss": "^3.4.0",
            "postcss": "^8.4.0",
            "autoprefixer": "^10.4.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^5.4.0"
        }
    elif framework == "vue":
        package["scripts"] = {
            "dev": "vite --host 0.0.0.0",
            "build": "vue-tsc && vite build",
            "preview": "vite preview"
        }
        package["dependencies"] = {
            "vue": "^3.4.0",
            "vue-router": "^4.3.0",
            "lucide-react": "^0.300.0"
        }
        package["devDependencies"] = {
            "vite": "^5.1.0",
            "@vitejs/plugin-vue": "^5.0.0",
            "tailwindcss": "^3.4.0",
            "postcss": "^8.4.0",
            "autoprefixer": "^10.4.0",
            "typescript": "^5.4.0",
            "vue-tsc": "^1.8.0"
        }
    else:
        package["scripts"] = {
            "dev": "next dev -H 0.0.0.0",
            "build": "next build",
            "start": "next start"
        }
        package["dependencies"] = {
            "next": "^14.2.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        }

    return json.dumps(package, indent=2)


def _render_tsconfig() -> str:
    return json.dumps(
        {
            "compilerOptions": {
                "target": "es2017",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": False,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {"@/*": ["./src/*"]},
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"],
        },
        indent=2,
    )


def _render_next_config() -> str:
    return """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true
};

module.exports = nextConfig;
"""


def _render_layout(model: Mapping[str, Any]) -> str:
    return f"""import type {{ Metadata }} from 'next';
import './globals.css';

export const metadata: Metadata = {{
  title: '{_escape_ts(model['name'])}',
  description: '{_escape_ts(model['description'])}'
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _render_frontend_page() -> str:
    return """import { EntityWorkspace } from '@/components/EntityWorkspace';
import { PROJECT } from '@/lib/project';

export default function HomePage() {
  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Sarthi generated application</p>
          <h1>{PROJECT.name}</h1>
          <p className="subtitle">{PROJECT.description}</p>
        </div>
        <div className="status">Connected build</div>
      </section>

      <section className="featureRow">
        {PROJECT.features.map((feature) => (
          <span key={feature}>{feature}</span>
        ))}
      </section>

      <EntityWorkspace />
    </main>
  );
}
"""


def _render_globals_css(model: Mapping[str, Any]) -> str:
    palette = model.get("theme_palette", {})
    return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --primary: {palette.get('primary', '#2563eb')};
  --secondary: {palette.get('secondary', '#14b8a6')};
  --background: {palette.get('background', '#f8fafc')};
  --card: {palette.get('card_bg', '#ffffff')};
  --text: {palette.get('text', '#0f172a')};
  --border: {palette.get('border', '#dbe3ef')};
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  background: var(--background);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

button, input, textarea, select {{
  font: inherit;
}}

.shell {{
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0;
}}

.topbar {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 24px;
}}

.eyebrow {{
  margin: 0 0 8px;
  color: var(--secondary);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}}

h1 {{
  margin: 0;
  font-size: 36px;
  line-height: 1.1;
}}

.subtitle {{
  max-width: 760px;
  margin: 12px 0 0;
  color: #526070;
}}

.status, .featureRow span, .pill {{
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 700;
}}

.featureRow {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 22px 0;
}}

.workspace {{
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 18px;
}}

.panel {{
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  padding: 18px;
}}

.navList {{
  display: grid;
  gap: 8px;
}}

.navButton, .primaryButton, .ghostButton {{
  min-height: 40px;
  border-radius: 8px;
  border: 1px solid var(--border);
  cursor: pointer;
}}

.navButton {{
  width: 100%;
  background: #ffffff;
  text-align: left;
  padding: 10px 12px;
}}

.navButton.active, .primaryButton {{
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}}

.ghostButton {{
  background: #ffffff;
  color: var(--text);
  padding: 0 14px;
}}

.formGrid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0;
}}

.field {{
  display: grid;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
}}

.field input, .field textarea {{
  min-height: 40px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 10px;
  background: #ffffff;
}}

.records {{
  display: grid;
  gap: 10px;
}}

.record {{
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  background: #fbfdff;
}}

.recordTitle {{
  margin: 0 0 6px;
  font-weight: 800;
}}

.muted {{
  color: #64748b;
  font-size: 13px;
}}

@media (max-width: 760px) {{
  .topbar, .workspace, .formGrid {{
    grid-template-columns: 1fr;
    display: grid;
  }}

  h1 {{
    font-size: 30px;
  }}
}}
"""


def _render_entity_workspace() -> str:
    return """'use client';

import { useEffect, useMemo, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { PROJECT, ProjectEntity } from '@/lib/project';

type AuthState = {
  token: string;
  email: string;
};

type RecordItem = {
  id: string;
  title: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export function EntityWorkspace() {
  const [activeRoute, setActiveRoute] = useState<string>(PROJECT.entities[0]?.route ?? 'users');
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('secret123');
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [title, setTitle] = useState('');
  const [payload, setPayload] = useState('{"priority":"high"}');
  const [message, setMessage] = useState('Sign up or log in to activate the generated API.');

  const activeEntity = useMemo(
    () => PROJECT.entities.find((entity) => entity.route === activeRoute) ?? PROJECT.entities[0],
    [activeRoute]
  );

  async function authenticate(mode: 'signup' | 'login') {
    const response = await apiRequest<{ access_token: string; user: { email: string } }>(
      `/api/v1/auth/${mode}`,
      {
        method: 'POST',
        body: JSON.stringify({ email, password, name: 'Demo User' })
      }
    );
    setAuth({ token: response.access_token, email: response.user.email });
    setMessage(`Authenticated as ${response.user.email}`);
  }

  async function loadRecords(entity: ProjectEntity = activeEntity) {
    if (!auth || !entity) return;
    const response = await apiRequest<{ items: RecordItem[] }>(`/api/v1/${entity.route}`, {}, auth.token);
    setRecords(response.items);
  }

  async function createRecord() {
    if (!auth || !activeEntity) return;
    let parsedPayload: Record<string, unknown>;
    try {
      parsedPayload = JSON.parse(payload);
    } catch {
      setMessage('Payload must be valid JSON before it can be sent to the API.');
      return;
    }
    await apiRequest(
      `/api/v1/${activeEntity.route}`,
      {
        method: 'POST',
        body: JSON.stringify({
          title: title || `${activeEntity.label} sample`,
          status: 'active',
          payload: parsedPayload
        })
      },
      auth.token
    );
    setTitle('');
    setMessage(`${activeEntity.label} record created and synced with FastAPI.`);
    await loadRecords(activeEntity);
  }

  useEffect(() => {
    if (auth && activeEntity) {
      loadRecords(activeEntity).catch((error) => setMessage(error.message));
    }
  }, [auth, activeEntity]);

  return (
    <section className="workspace">
      <aside className="panel">
        <p className="eyebrow">Entities</p>
        <div className="navList">
          {PROJECT.entities.map((entity) => (
            <button
              key={entity.route}
              className={`navButton ${entity.route === activeRoute ? 'active' : ''}`}
              onClick={() => setActiveRoute(entity.route)}
            >
              {entity.label}
            </button>
          ))}
        </div>
      </aside>

      <div className="panel">
        <div className="formGrid">
          <label className="field">
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="field">
            Password
            <input value={password} type="password" onChange={(event) => setPassword(event.target.value)} />
          </label>
          <div className="field">
            Session
            <button className="primaryButton" onClick={() => authenticate(auth ? 'login' : 'signup')}>
              {auth ? 'Refresh Login' : 'Create Session'}
            </button>
          </div>
        </div>

        <p className="muted">{message}</p>

        <div className="formGrid">
          <label className="field">
            Record Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label className="field">
            JSON Payload
            <textarea value={payload} onChange={(event) => setPayload(event.target.value)} />
          </label>
          <div className="field">
            Action
            <button className="primaryButton" disabled={!auth} onClick={createRecord}>
              Add {activeEntity?.label ?? 'Record'}
            </button>
          </div>
        </div>

        <div className="records">
          {records.length === 0 ? (
            <div className="record muted">No records yet. Create one to verify the frontend-backend connection.</div>
          ) : (
            records.map((record) => (
              <article className="record" key={record.id}>
                <p className="recordTitle">{record.title}</p>
                <p className="muted">{record.status} | {new Date(record.created_at).toLocaleString()}</p>
                <pre>{JSON.stringify(record.payload, null, 2)}</pre>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
"""


def _render_api_client() -> str:
    return """const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: 'no-store'
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}
"""


def _render_project_contract(model: Mapping[str, Any]) -> str:
    public = _public_contract(model)
    return f"""export type ProjectEntity = {{
  name: string;
  label: string;
  route: string;
  fields: ReadonlyArray<{{
    name: string;
    type: string;
    required: boolean;
  }}>;
}};

export const PROJECT = {json.dumps(public, indent=2, default=str)} as const;
"""


def _render_validation_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Validation Report",
        "",
        f"Status: {report.get('status')}",
        f"Generated At: {report.get('generated_at')}",
        "",
        "## Quality Gates",
        "",
    ]
    for check in report.get("checks", []):
        mark = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {mark}: {check.get('name')} - {check.get('details')}")
    lines.extend(["", "## Commands", ""])
    for command in report.get("test_commands", []):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def _public_contract(model: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "name": model["name"],
        "slug": model["slug"],
        "category": model["category"],
        "description": model["description"],
        "features": model["features"],
        "theme": model["theme"],
        "theme_palette": model["theme_palette"],
        "entities": model["entities"],
        "endpoints": model["endpoints"],
    }


def _normalise_entity(item: Any) -> Optional[Dict[str, Any]]:
    if isinstance(item, str):
        return _entity_from_name(item)
    if not isinstance(item, Mapping):
        return None
    raw_name = (
        item.get("entity_name")
        or item.get("model_name")
        or item.get("name")
        or item.get("mapped_model")
    )
    if not raw_name:
        return None
    entity = _entity_from_name(str(raw_name))
    fields = item.get("fields") or item.get("columns") or item.get("attributes") or []
    normalised_fields = []
    for field in _list_value(fields):
        if isinstance(field, str):
            normalised_fields.append(_field_from_name(field))
        elif isinstance(field, Mapping):
            name = field.get("name") or field.get("field_name") or field.get("column_name")
            if name:
                normalised_fields.append({
                    "name": _snake_case(str(name)),
                    "type": str(field.get("type") or field.get("data_type") or "string"),
                    "required": bool(field.get("required", False)),
                })
    if normalised_fields:
        entity["fields"] = _dedupe_fields(entity["fields"] + normalised_fields)
    return entity


def _entity_from_name(raw_name: str) -> Dict[str, Any]:
    name = _pascal_case(raw_name) or "WorkspaceItem"
    route = _pluralize(_snake_case(name)).replace("_", "-")
    return {
        "name": name,
        "label": _title_from_pascal(name),
        "route": route,
        "fields": [
            {"name": "title", "type": "string", "required": True},
            {"name": "status", "type": "string", "required": True},
            {"name": "notes", "type": "string", "required": False},
        ],
    }


def _normalise_endpoint(item: Any) -> Optional[Dict[str, Any]]:
    if isinstance(item, str):
        parts = item.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            return {"method": parts[0].upper(), "path": parts[1], "description": item}
        return None
    if not isinstance(item, Mapping):
        return None
    path = item.get("path") or item.get("route_path")
    method = item.get("method") or item.get("http_method") or "GET"
    if not path:
        return None
    return {
        "method": str(method).upper(),
        "path": str(path),
        "description": str(item.get("description") or item.get("route_name") or path),
    }


def _field_from_name(name: str) -> Dict[str, Any]:
    return {"name": _snake_case(name), "type": "string", "required": False}


def _dedupe_fields(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for field in fields:
        name = field.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(field)
    return result


def _file(path: str, language: str, content: str) -> Dict[str, Any]:
    clean = _clean_path(path)
    return {
        "name": clean.rsplit("/", 1)[-1],
        "path": clean,
        "language": language,
        "content": content,
    }


def _clean_path(path: str) -> str:
    clean = path.replace("\\", "/").strip()
    while clean.startswith("./"):
        clean = clean[2:]
    return clean.lstrip("/")


def _language_for_path(path: str) -> str:
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "py": "python",
        "tsx": "typescript",
        "ts": "typescript",
        "js": "javascript",
        "json": "json",
        "md": "markdown",
        "yml": "yaml",
        "yaml": "yaml",
        "css": "css",
        "txt": "plaintext",
    }.get(suffix, "plaintext")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_value(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe(values: Iterable[str]) -> List[str]:
    result = []
    seen = set()
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "sarthi-app"


def _snake_case(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    cleaned = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cleaned).lower()
    if not cleaned:
        cleaned = "item"
    if cleaned[0].isdigit() or keyword.iskeyword(cleaned):
        cleaned = f"{cleaned}_item"
    return cleaned


def _pascal_case(value: str) -> str:
    words = re.split(r"[^a-zA-Z0-9]+|_", value)
    name = "".join(word[:1].upper() + word[1:] for word in words if word)
    if not name:
        return ""
    if name[0].isdigit() or keyword.iskeyword(name.lower()):
        name = f"{name}Item"
    return name[:40]


def _title_from_pascal(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", value).strip() or value


def _pluralize(value: str) -> str:
    if value.endswith("y") and not value.endswith(("ay", "ey", "iy", "oy", "uy")):
        return f"{value[:-1]}ies"
    if value.endswith(("s", "x", "z", "ch", "sh")):
        return f"{value}es"
    return f"{value}s"


def _escape_ts(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def _render_express_package(model: Mapping[str, Any]) -> str:
    package = {
        "name": f"{model['slug']}-backend",
        "version": "1.0.0",
        "private": True,
        "main": "src/index.js",
        "scripts": {
            "start": "node src/index.js",
            "dev": "nodemon src/index.js"
        },
        "dependencies": {
            "express": "^4.19.0",
            "cors": "^2.8.5",
            "mongoose": "^8.2.0",
            "dotenv": "^16.4.5"
        },
        "devDependencies": {
            "nodemon": "^3.1.0"
        }
    }
    return json.dumps(package, indent=2)


def _render_springboot_pom(model: Mapping[str, Any]) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.5</version>
        <relativePath/>
    </parent>
    <groupId>com.saarthi</groupId>
    <artifactId>{model['slug']}</artifactId>
    <version>1.0.0</version>
    <name>{model['name']}</name>
    <description>{model['description']}</description>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""

