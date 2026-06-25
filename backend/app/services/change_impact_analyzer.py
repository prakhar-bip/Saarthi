import os
import re
import hashlib
from typing import Dict, Any, List, Set, Tuple
from loguru import logger

class ChangeImpactAnalyzer:
    """
    Statically analyzes source code file changes, resolves file-level dependency graphs,
    and determines targeted validation scopes and verification tiers.
    """
    
    # Regex patterns for static import discovery
    PY_IMPORT_RE = re.compile(r'^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.,\t ]+))', re.MULTILINE)
    TS_IMPORT_RE = re.compile(r'(?:import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]|import\s*[\'"]([^\'"]+)[\'"]|require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\))')

    @classmethod
    def compute_sha256(cls, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @classmethod
    def identify_changed_files(cls, current_files: List[Dict[str, Any]], previous_hashes: Dict[str, str]) -> List[str]:
        """Compares current files against baseline hashes to identify modified files."""
        changed = []
        for file_rec in current_files:
            path = file_rec.get("path", "")
            if not path:
                continue
            content = file_rec.get("content", "")
            curr_hash = cls.compute_sha256(content)
            prev_hash = previous_hashes.get(path)
            if curr_hash != prev_hash:
                changed.append(path)
        return changed

    @classmethod
    def parse_imports(cls, file_path: str, content: str) -> List[str]:
        """Extracts relative and absolute workspace imports from file contents."""
        imports = []
        ext = os.path.splitext(file_path)[1]
        
        if ext == ".py":
            for match in cls.PY_IMPORT_RE.finditer(content):
                module = match.group(1) or match.group(2)
                if module:
                    # Clean up multiple imports or spaces
                    cleaned = [m.strip() for m in module.split(",") if m.strip()]
                    for c in cleaned:
                        imports.append(c)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            for match in cls.TS_IMPORT_RE.finditer(content):
                imp = match.group(1) or match.group(2) or match.group(3)
                if imp:
                    imports.append(imp)
        return imports

    @classmethod
    def build_dependency_graph(cls, files: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Builds a bidirectional dependency graph:
        - import_map: file -> list of files it imports
        - dependent_map: file -> list of files that import it
        """
        import_map: Dict[str, List[str]] = {}
        dependent_map: Dict[str, List[str]] = {}
        
        file_paths = {f["path"] for f in files}
        file_contents = {f["path"]: f.get("content", "") for f in files}
        
        for path in file_paths:
            import_map[path] = []
            if path not in dependent_map:
                dependent_map[path] = []

        for path, content in file_contents.items():
            discovered = cls.parse_imports(path, content)
            for imp in discovered:
                # Resolve relative or package names to physical workspace files
                resolved_path = cls._resolve_import_to_file(path, imp, file_paths)
                if resolved_path and resolved_path in file_paths:
                    import_map[path].append(resolved_path)
                    if resolved_path not in dependent_map:
                        dependent_map[resolved_path] = []
                    dependent_map[resolved_path].append(path)
                    
        return import_map, dependent_map

    @classmethod
    def _resolve_import_to_file(cls, current_file: str, import_str: str, file_paths: Set[str]) -> str:
        """Heuristically matches an import path string to a file in the workspace."""
        if import_str.startswith("."):
            # Node/TS relative import
            dir_name = os.path.dirname(current_file)
            candidate = os.path.normpath(os.path.join(dir_name, import_str)).replace("\\", "/")
            for ext in [".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx"]:
                if candidate + ext in file_paths:
                    return candidate + ext
                if candidate.endswith(ext) and candidate in file_paths:
                    return candidate
        else:
            # Python absolute package style or node absolute path aliases (e.g. @/components/...)
            norm_imp = import_str.replace(".", "/").replace("@/", "")
            for f in file_paths:
                if norm_imp in f:
                    return f
        return ""

    @classmethod
    def get_affected_files(cls, changed_files: List[str], dependent_map: Dict[str, List[str]]) -> Set[str]:
        """Recursively traces downstream dependent files affected by the changed files."""
        affected = set(changed_files)
        queue = list(changed_files)
        
        while queue:
            curr = queue.pop(0)
            dependents = dependent_map.get(curr, [])
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    queue.append(dep)
        return affected

    @classmethod
    def determine_validation_scope(cls, affected_files: Set[str]) -> str:
        """Determines if changes are backend, frontend, or full_stack."""
        has_backend = any("backend/" in f for f in affected_files)
        has_frontend = any("frontend/" in f for f in affected_files)
        
        if has_backend and has_frontend:
            return "full_stack"
        elif has_frontend:
            return "frontend"
        else:
            return "backend"

    @classmethod
    def build_validation_plan(cls, current_files: List[Dict[str, Any]], previous_hashes: Dict[str, str]) -> Dict[str, Any]:
        """Main orchestrator computing changed files, dependents, scope, and recommended start tier."""
        changed = cls.identify_changed_files(current_files, previous_hashes)
        if not changed:
            logger.info("[ChangeImpact] No changed files detected compared to baseline.")
            return {
                "changed_files": [],
                "affected_files": [],
                "scope": "full_stack",
                "recommended_tier": 6 # run full verification on initial/empty baseline
            }
            
        import_map, dependent_map = cls.build_dependency_graph(current_files)
        affected = cls.get_affected_files(changed, dependent_map)
        scope = cls.determine_validation_scope(affected)
        
        # Heuristically determine start tier (e.g., config changes require full compile, view-only is Tier 1/2)
        has_config_change = any("package.json" in f or "requirements" in f or "config" in f for f in changed)
        recommended_tier = 5 if has_config_change else 1
        
        logger.info(f"[ChangeImpact] Identified {len(changed)} changed files, affecting {len(affected)} total files. Scope={scope}. Start Tier={recommended_tier}")
        return {
            "changed_files": changed,
            "affected_files": list(affected),
            "scope": scope,
            "recommended_tier": recommended_tier
        }
