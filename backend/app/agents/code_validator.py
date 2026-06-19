"""
CodeValidatorAgent for Sarthi.

Performs structural validation on the synthesized codebase to catch issues
that the LLM might have introduced:
  - Broken import paths
  - Frontend ↔ Backend API contract mismatches
  - Missing required files
  - Placeholder / TODO code
  - Missing env var declarations
  - Missing package dependencies

Returns a list of issues, each with type, severity, file, and description.
"""

import re
from loguru import logger
from typing import Any, Dict, List, Set


class CodeValidatorAgent:

    def __init__(self) -> None:
        self.agent_name = "CodeValidatorAgent"

    def validate(self, codebase: List[Dict], architecture_context: Dict = None) -> List[Dict]:
        """
        Run all validation checks. Returns a list of issues:
        [{type, severity, file, line, description}]
        """
        issues: List[Dict] = []
        issues.extend(self._check_placeholders(codebase))
        issues.extend(self._check_python_imports(codebase))
        issues.extend(self._check_typescript_imports(codebase))
        issues.extend(self._check_required_files(codebase, architecture_context))
        issues.extend(self._check_api_contracts(codebase))
        issues.extend(self._check_env_consistency(codebase))
        issues.extend(self._check_package_deps(codebase))
        issues.extend(self._check_empty_files(codebase))
        issues.extend(self._check_minimum_codebase(codebase, architecture_context))
        if architecture_context:
            issues.extend(self._check_entity_endpoint_alignment(codebase, architecture_context))

        if issues:
            logger.warning(f"[CodeValidator] Found {len(issues)} issues:")
            for i in issues[:20]:
                logger.warning(f"  [{i['severity']}] {i['type']} in {i.get('file','-')}: {i['description']}")
        else:
            logger.info("[CodeValidator] ✅ No issues found — codebase passes validation")

        return issues

    # ──────────────────────────────────────────────────────────────
    # Placeholder Detection
    # ──────────────────────────────────────────────────────────────

    _PLACEHOLDER_PATTERNS = [
        (r'\bTODO\b', "Contains TODO comment"),
        (r'\bFIXME\b', "Contains FIXME comment"),
        (r'\bHACK\b', "Contains HACK comment"),
        (r'\.{3}', "Contains ellipsis placeholder '...'"),
        (r'pass\s*$', "Contains bare 'pass' statement"),
        (r'#\s*implement\s', "Contains '# implement' comment"),
        (r'//\s*implement\s', "Contains '// implement' comment"),
        (r'placeholder', "Contains 'placeholder' text"),
        (r'add\s+more\s+here', "Contains 'add more here'"),
        (r'your[\s_-]*(code|logic|implementation)\s*here', "Contains 'your code here'"),
    ]

    def _check_placeholders(self, codebase: List[Dict]) -> List[Dict]:
        issues: List[Dict] = []
        for f in codebase:
            content = f.get("content", "")
            path = f.get("path", "")
            if path.endswith(".md"):
                continue  # Skip markdown files
            for line_num, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                # Skip empty lines and pure comments explaining architecture
                if not stripped:
                    continue
                for pattern, desc in self._PLACEHOLDER_PATTERNS:
                    if re.search(pattern, stripped, re.IGNORECASE):
                        # Skip false positives — legitimate uses
                        if pattern == r'pass\s*$' and ('class ' in line or 'except' in content.split("\n")[max(0,line_num-2)]):
                            continue
                        if pattern == r'\.{3}' and ('Pydantic' in content or 'BaseModel' in content):
                            # Pydantic uses ... for required fields
                            if 'Field(' in line or '=' in line:
                                continue
                        issues.append({
                            "type": "placeholder",
                            "severity": "warning",
                            "file": path,
                            "line": line_num,
                            "description": f"{desc}: '{stripped[:80]}'",
                        })
                        break
        return issues

    # ──────────────────────────────────────────────────────────────
    # Python Import Checking
    # ──────────────────────────────────────────────────────────────

    _PY_IMPORT_RE = re.compile(
        r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
    )

    def _check_python_imports(self, codebase: List[Dict]) -> List[Dict]:
        # Build set of project module paths
        py_modules: Set[str] = set()
        for f in codebase:
            path = f.get("path", "")
            if path.endswith(".py"):
                # Convert path to module: backend/app/models/user.py -> app.models.user
                mod = path.replace("\\", "/")
                if mod.startswith("backend/"):
                    mod = mod[len("backend/"):]
                mod = mod.replace("/", ".").removesuffix(".py")
                if mod.endswith(".__init__"):
                    mod = mod[:-len(".__init__")]
                py_modules.add(mod)
                # Also add parent packages
                parts = mod.split(".")
                for i in range(1, len(parts)):
                    py_modules.add(".".join(parts[:i]))

        # Standard library and common third-party modules to skip
        stdlib_and_deps = {
            "os", "sys", "json", "re", "typing", "datetime", "asyncio", "uuid",
            "pathlib", "hashlib", "secrets", "functools", "collections", "enum",
            "contextlib", "abc", "io", "logging", "time", "copy", "math",
            "fastapi", "pydantic", "pydantic_settings", "motor", "pymongo",
            "jose", "jwt", "passlib", "dotenv", "httpx", "redis", "celery",
            "sqlalchemy", "alembic", "asyncpg", "aiosqlite",
            "starlette", "bson", "loguru", "openai",
            "google", "pytest", "unittest", "mock",
        }

        issues: List[Dict] = []
        for f in codebase:
            path = f.get("path", "")
            if not path.endswith(".py"):
                continue
            content = f.get("content", "")
            for line_num, line in enumerate(content.split("\n"), 1):
                m = self._PY_IMPORT_RE.match(line)
                if not m:
                    continue
                mod = m.group(1) or m.group(2)
                if not mod:
                    continue
                root = mod.split(".")[0]
                if root in stdlib_and_deps:
                    continue
                # Check if any prefix of the import path is in our modules
                parts = mod.split(".")
                found = False
                for i in range(len(parts), 0, -1):
                    candidate = ".".join(parts[:i])
                    if candidate in py_modules:
                        found = True
                        break
                if not found:
                    issues.append({
                        "type": "broken_import",
                        "severity": "error",
                        "file": path,
                        "line": line_num,
                        "description": f"Cannot resolve import '{mod}' — no matching file in codebase",
                    })
        return issues

    # ──────────────────────────────────────────────────────────────
    # TypeScript/JS Import Checking
    # ──────────────────────────────────────────────────────────────

    _TS_IMPORT_RE = re.compile(
        r'''(?:import|from)\s+.*?['"](@/[^'"]+|\.\.?/[^'"]+)['"]'''
    )

    def _check_typescript_imports(self, codebase: List[Dict]) -> List[Dict]:
        ts_files: Dict[str, str] = {}
        for f in codebase:
            path = f.get("path", "").replace("\\", "/")
            if any(path.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx")):
                # Normalize: frontend/src/utils/api.ts -> src/utils/api
                norm = path
                if norm.startswith("frontend/"):
                    norm = norm[len("frontend/"):]
                for ext in (".tsx", ".ts", ".jsx", ".js"):
                    if norm.endswith(ext):
                        norm = norm[:-len(ext)]
                        break
                ts_files[norm] = path
                # Also with /index
                ts_files[norm.rstrip("/index")] = path

        issues: List[Dict] = []
        for f in codebase:
            path = f.get("path", "").replace("\\", "/")
            if not any(path.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx")):
                continue
            content = f.get("content", "")
            for line_num, line in enumerate(content.split("\n"), 1):
                for m in self._TS_IMPORT_RE.finditer(line):
                    import_path = m.group(1)
                    
                    # Catch incorrect Next.js Link imports: 'import Link from "next"' instead of 'next/link'
                    if import_path == "next" and "Link" in line:
                        issues.append({
                            "type": "incorrect_next_link_import",
                            "severity": "error",
                            "file": path,
                            "line": line_num,
                            "description": "Incorrect Next.js Link import. Link component MUST be imported from 'next/link', NOT from 'next'.",
                        })
                        continue

                    if import_path.startswith("@/"):
                        # @/ alias → src/
                        resolved = "src/" + import_path[2:]
                    elif import_path.startswith("."):
                        # Relative import — resolve from file's directory
                        file_dir = "/".join(path.replace("\\", "/").split("/")[:-1])
                        if file_dir.startswith("frontend/"):
                            file_dir = file_dir[len("frontend/"):]
                        parts = import_path.split("/")
                        dir_parts = file_dir.split("/")
                        for p in parts:
                            if p == "..":
                                dir_parts = dir_parts[:-1] if dir_parts else []
                            elif p == ".":
                                continue
                            else:
                                dir_parts.append(p)
                        resolved = "/".join(dir_parts)
                    else:
                        continue

                    # Check if resolved path exists
                    if resolved not in ts_files:
                        # Also try with /index
                        if resolved + "/index" not in ts_files:
                            issues.append({
                                "type": "broken_ts_import",
                                "severity": "warning",
                                "file": path,
                                "line": line_num,
                                "description": f"Cannot resolve import '{import_path}' (resolved: {resolved})",
                            })
        return issues

    # ──────────────────────────────────────────────────────────────
    # Required Files Check
    # ──────────────────────────────────────────────────────────────

    def _check_required_files(self, codebase: List[Dict], architecture_context: Dict = None) -> List[Dict]:
        from app.services.project_assembler import detect_tech_stack
        
        project_doc = {}
        if architecture_context:
            project_doc["requirements"] = architecture_context.get("requirements", {})
            project_doc["blueprint"] = architecture_context.get("blueprint", {})
            
        stack = detect_tech_stack(project_doc)
        existing = {f.get("path", "").replace("\\", "/") for f in codebase}
        issues: List[Dict] = []
        
        gen_type = architecture_context.get("generation_type", "full_stack") if architecture_context else "full_stack"
        
        required = ["README.md"]
        if stack["is_default"]:
            if gen_type != "frontend_only":
                required.extend([
                    "backend/requirements.txt",
                    "backend/app/main.py",
                ])
            if gen_type not in ("backend_only", "microservice"):
                required.append("frontend/package.json")
        else:
            if gen_type != "frontend_only":
                if stack["backend"] == "fastapi":
                    required.extend(["backend/requirements.txt", "backend/app/main.py"])
                elif stack["backend"] == "django":
                    django_root = "backend/" if any(f.startswith("backend/manage.py") for f in existing) else ""
                    required.append(django_root + "manage.py")
                elif stack["backend"] == "flask":
                    flask_root = "backend/" if any(f.startswith("backend/app.py") for f in existing) else ""
                    required.append(flask_root + "app.py")
                elif stack["backend"] == "express":
                    express_root = "backend/" if any(f.startswith("backend/package.json") for f in existing) else ""
                    required.append(express_root + "package.json")
                elif stack["backend"] == "springboot":
                    pom_root = "backend/" if any(f.startswith("backend/pom.xml") for f in existing) else ""
                    if any(f.startswith(pom_root + "build.gradle") for f in existing):
                        required.append(pom_root + "build.gradle")
                    else:
                        required.append(pom_root + "pom.xml")
                        
            if gen_type not in ("backend_only", "microservice"):
                if stack["frontend"] in ("nextjs", "react", "angular", "vue"):
                    required.append("frontend/package.json")

        for req in required:
            if req not in existing:
                issues.append({
                    "type": "missing_file",
                    "severity": "error",
                    "file": req,
                    "line": 0,
                    "description": f"Required file '{req}' is missing from codebase",
                })
        return issues

    # ──────────────────────────────────────────────────────────────
    # API Contract Check
    # ──────────────────────────────────────────────────────────────

    def _check_api_contracts(self, codebase: List[Dict]) -> List[Dict]:
        """Check that frontend API calls reference endpoints that exist in backend."""
        # Extract backend route paths
        backend_routes: Set[str] = set()
        route_re = re.compile(r'@(?:router|app)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
        for f in codebase:
            if f.get("path", "").startswith("backend/"):
                for m in route_re.finditer(f.get("content", "")):
                    backend_routes.add(m.group(2))

        if not backend_routes:
            return []  # Can't validate without backend routes

        # Extract frontend API call paths
        api_call_re = re.compile(r'''(?:fetch|axios\.\w+|api\.\w+)\(\s*[`"']([^`"'\s]+/api/[^`"'\s]+)[`"']''')
        issues: List[Dict] = []
        for f in codebase:
            path = f.get("path", "")
            if not path.startswith("frontend/"):
                continue
            content = f.get("content", "")
            for line_num, line in enumerate(content.split("\n"), 1):
                for m in api_call_re.finditer(line):
                    api_path = m.group(1)
                    # Strip base URL parts
                    if "/api/" in api_path:
                        api_path = "/api/" + api_path.split("/api/", 1)[1]
                    # Remove template literals
                    api_path = re.sub(r'\$\{[^}]+\}', '{id}', api_path)
                    # Check if any backend route matches (prefix match for parameterized routes)
                    matched = any(
                        api_path.startswith(r.rstrip("/")) or r.startswith(api_path.rstrip("/"))
                        for r in backend_routes
                    )
                    if not matched and api_path not in ("/api/health",):
                        issues.append({
                            "type": "api_contract_mismatch",
                            "severity": "warning",
                            "file": path,
                            "line": line_num,
                            "description": f"Frontend calls '{api_path}' but no matching backend route found",
                        })
        return issues

    # ──────────────────────────────────────────────────────────────
    # Env Var Consistency Check
    # ──────────────────────────────────────────────────────────────

    def _check_env_consistency(self, codebase: List[Dict]) -> List[Dict]:
        """Check that env vars used in code are declared in .env.example."""
        env_example_vars: Set[str] = set()
        for f in codebase:
            if f.get("path", "").endswith(".env.example") or f.get("path", "").endswith(".env"):
                for line in f.get("content", "").split("\n"):
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        var = line.split("=", 1)[0].strip()
                        if var:
                            env_example_vars.add(var)

        if not env_example_vars:
            return []  # No .env.example found

        # Find env var references in code
        env_ref_re = re.compile(r'''(?:os\.(?:environ|getenv)\(\s*["\']|process\.env\.)([A-Z_][A-Z0-9_]+)''')
        issues: List[Dict] = []
        seen_warnings: Set[str] = set()
        for f in codebase:
            path = f.get("path", "")
            if path.endswith((".md", ".env", ".env.example", ".gitignore")):
                continue
            content = f.get("content", "")
            for m in env_ref_re.finditer(content):
                var = m.group(1)
                if var not in env_example_vars and var not in seen_warnings:
                    seen_warnings.add(var)
                    issues.append({
                        "type": "missing_env_var",
                        "severity": "info",
                        "file": path,
                        "line": 0,
                        "description": f"Env var '{var}' used in code but not declared in .env.example",
                    })
        return issues

    # ──────────────────────────────────────────────────────────────
    # Package Dependency Check
    # ──────────────────────────────────────────────────────────────

    def _check_package_deps(self, codebase: List[Dict]) -> List[Dict]:
        """Check that imported npm packages are in package.json."""
        # Parse package.json dependencies
        pkg_deps: Set[str] = set()
        for f in codebase:
            if f.get("path", "").endswith("package.json"):
                try:
                    pkg = __import__("json").loads(f.get("content", "{}"))
                    for section in ("dependencies", "devDependencies", "peerDependencies"):
                        pkg_deps.update(pkg.get(section, {}).keys())
                except Exception:
                    pass

        if not pkg_deps:
            return []

        # Packages that don't need explicit listing
        builtin_modules = {"react", "react-dom", "next", "fs", "path", "crypto", "url", "stream"}
        pkg_deps.update(builtin_modules)

        # Find npm imports in frontend files
        npm_import_re = re.compile(r'''(?:import|from)\s+.*?['"]((?!\.\.?/|@/)[\w@][\w/-]*)['"]''')
        issues: List[Dict] = []
        seen: Set[str] = set()
        for f in codebase:
            path = f.get("path", "")
            if not path.startswith("frontend/") or not any(path.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx")):
                continue
            content = f.get("content", "")
            for m in npm_import_re.finditer(content):
                pkg = m.group(1)
                # Get root package name (e.g., @radix-ui/react-dialog -> @radix-ui/react-dialog)
                if pkg.startswith("@"):
                    parts = pkg.split("/")
                    root = "/".join(parts[:2]) if len(parts) >= 2 else pkg
                else:
                    root = pkg.split("/")[0]
                if root not in pkg_deps and root not in seen:
                    seen.add(root)
                    issues.append({
                        "type": "missing_npm_dep",
                        "severity": "info",
                        "file": path,
                        "line": 0,
                        "description": f"Package '{root}' imported but not in package.json",
                    })
        return issues

    # ──────────────────────────────────────────────────────────────
    # Empty / Trivial File Detection
    # ──────────────────────────────────────────────────────────────

    def _check_empty_files(self, codebase: List[Dict]) -> List[Dict]:
        """Detect files with no meaningful content."""
        issues: List[Dict] = []
        for f in codebase:
            path = f.get("path", "")
            content = f.get("content", "")
            stripped = content.strip()
            
            if path.endswith((".md", ".txt", ".gitignore", ".env.example", ".env", "__init__.py")):
                continue
                
            if len(stripped) == 0:
                issues.append({
                    "type": "empty_file",
                    "severity": "error",
                    "file": path,
                    "line": 0,
                    "description": f"File is completely empty — must contain runnable code",
                })
            elif len(stripped) < 30 and not path.endswith(("__init__.py", ".json", ".yaml", ".yml", ".toml", ".cfg")):
                issues.append({
                    "type": "trivial_file",
                    "severity": "warning",
                    "file": path,
                    "line": 0,
                    "description": f"File has only {len(stripped)} chars — likely incomplete or placeholder",
                })
        return issues

    # ──────────────────────────────────────────────────────────────
    # Minimum Codebase Size Validation
    # ──────────────────────────────────────────────────────────────

    def _check_minimum_codebase(self, codebase: List[Dict], architecture_context: Dict = None) -> List[Dict]:
        """Ensure the generated codebase meets minimum production requirements."""
        issues: List[Dict] = []
        
        total_files = len(codebase)
        backend_files = [f for f in codebase if f.get("path", "").startswith("backend/")]
        frontend_files = [f for f in codebase if f.get("path", "").startswith("frontend/")]
        
        gen_type = architecture_context.get("generation_type", "full_stack") if architecture_context else "full_stack"
        
        min_files = 15 if gen_type == "full_stack" else 7
        if total_files < min_files:
            issues.append({
                "type": "insufficient_files",
                "severity": "error",
                "file": "-",
                "line": 0,
                "description": f"Only {total_files} total files — production projects need at least {min_files} files",
            })
        
        if gen_type != "frontend_only" and len(backend_files) < 5:
            issues.append({
                "type": "insufficient_backend",
                "severity": "warning",
                "file": "-",
                "line": 0,
                "description": f"Only {len(backend_files)} backend files — need at least 5 (main, config, models, routes, services)",
            })
        
        if gen_type not in ("backend_only", "microservice") and len(frontend_files) < 5:
            issues.append({
                "type": "insufficient_frontend",
                "severity": "warning",
                "file": "-",
                "line": 0,
                "description": f"Only {len(frontend_files)} frontend files — need at least 5 (layout, pages, components, stores, utils)",
            })
        
        # Check total code volume
        total_chars = sum(len(f.get("content", "")) for f in codebase)
        min_chars = 5000 if gen_type == "full_stack" else 2500
        if total_chars < min_chars:
            issues.append({
                "type": "insufficient_code",
                "severity": "error",
                "file": "-",
                "line": 0,
                "description": f"Total code size is only {total_chars:,} chars — production projects need substantially more code",
            })
        
        return issues

    # ──────────────────────────────────────────────────────────────
    # Entity-Endpoint Cross-Reference Validation
    # ──────────────────────────────────────────────────────────────

    def _check_entity_endpoint_alignment(self, codebase: List[Dict], architecture_context: Dict) -> List[Dict]:
        """Verify that DB entities have corresponding API endpoints."""
        issues: List[Dict] = []
        
        db_arch = architecture_context.get("db_architecture", {}) or {}
        entities = db_arch.get("entities", [])
        
        api_arch = architecture_context.get("api_architecture", {}) or {}
        endpoints = api_arch.get("endpoints", [])
        
        if not entities or not endpoints:
            return issues
        
        # Extract entity names
        entity_names = set()
        for e in entities:
            if isinstance(e, dict):
                name = e.get("entity_name", e.get("name", ""))
                if name:
                    entity_names.add(name.lower())
            elif isinstance(e, str):
                entity_names.add(e.lower())
        
        # Extract endpoint paths
        endpoint_paths = set()
        for ep in endpoints:
            if isinstance(ep, dict):
                path = ep.get("path", "").lower()
                if path:
                    endpoint_paths.add(path)
        
        # Check each entity has at least one related endpoint
        for entity in entity_names:
            has_endpoint = any(
                entity in path or entity + "s" in path
                for path in endpoint_paths
            )
            if not has_endpoint:
                issues.append({
                    "type": "missing_entity_endpoint",
                    "severity": "warning",
                    "file": "-",
                    "line": 0,
                    "description": f"Entity '{entity}' has no corresponding API endpoint — add CRUD routes for this entity",
                })
        
        return issues
