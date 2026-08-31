import json
import random
from typing import Dict, Any, List
from app.services.llm_router import get_llm_completion
from app.agents.context import parse_json_response

class DynamicCustomizationAgent:
    """
    DynamicCustomizationAgent applies styling changes, branding names, and unique student ID headers
    to codebase files dynamically before project export. This prevents plagiarism checks and makes 
    the project unique for every student.
    """
    def __init__(self):
        self.agent_name = "DynamicCustomizationAgent"

    async def customize_codebase(
        self,
        codebase: List[Dict[str, Any]],
        project_doc: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        
        # 1. Generate or extract dynamic brand name
        reqs = project_doc.get("requirements", {}) or {}
        idea = reqs.get("idea", "") or project_doc.get("name", "PlacementProject")
        
        # Call LLM to suggest branding attributes and colors
        system_prompt = (
            "You are a Creative Brand Architect in Sarthi.\n"
            "Your job is to generate a unique branding concept and color palette for a project "
            "so that it looks completely custom-designed. Your response must be in valid JSON format."
        )
        
        user_prompt = (
            f"Generate a custom brand concept for a project with this description:\n{idea}\n\n"
            "Provide:\n"
            "1. A unique brand name (e.g., instead of E-Shop use 'ZenCart' or 'SwiftBuy')\n"
            "2. A primary color hex code (harmonious, modern HSL or hex, e.g. '#3b82f6')\n"
            "3. A secondary color hex code\n"
            "4. A unique tagline\n\n"
            "Format your output EXACTLY as this JSON structure:\n"
            "{\n"
            '  "brand_name": "ZenCart",\n'
            '  "primary_color": "#4f46e5",\n'
            '  "secondary_color": "#10b981",\n'
            '  "tagline": "Seamless Commerce for Modern Teams"\n'
            "}"
        )
        
        try:
            raw_response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            brand_info = parse_json_response(raw_response)
        except Exception as e:
            brand_info = {
                "brand_name": "SaarthiProject_" + str(random.randint(100, 999)),
                "primary_color": "#3b82f6",
                "secondary_color": "#10b981",
                "tagline": "Enterprise Grade Solution"
            }

        brand_name = brand_info.get("brand_name", "SaarthiProject")
        primary_color = brand_info.get("primary_color", "#3b82f6")
        secondary_color = brand_info.get("secondary_color", "#10b981")
        tagline = brand_info.get("tagline", "Placement Verification App")
        
        # Create a unique Student Verification ID for anti-plagiarism headers
        random_id = f"PL-2026-{random.randint(1000, 9999)}-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
        
        
        customized_codebase = []
        for file in codebase:
            path = file.get("path", "")
            content = file.get("content", "")
            if not path or not content:
                customized_codebase.append(file)
                continue
                
            # Copy file records
            new_file = dict(file)
            
            # 2. Add verification header comments based on file type
            header = ""
            if path.endswith((".py", ".sh", ".ps1", "Dockerfile", "docker-compose.yml", ".yml", ".yaml")):
                header = (
                    f"# =========================================================================\n"
                    f"# Student ID: {random_id}\n"
                    f"# Project Brand: {brand_name} - {tagline}\n"
                    f"# Generated on: 2026-06-27\n"
                    f"# =========================================================================\n\n"
                )
            elif path.endswith((".js", ".jsx", ".ts", ".tsx", ".css")):
                header = (
                    f"/**\n"
                    f" * Student ID: {random_id}\n"
                    f" * Project Brand: {brand_name} - {tagline}\n"
                    f" * Generated on: 2026-06-27\n"
                    f" */\n\n"
                )
            elif path.endswith(".java"):
                header = (
                    f"/**\n"
                    f" * Student Verification ID: {random_id}\n"
                    f" * Module: {brand_name}\n"
                    f" */\n\n"
                )
            
            if header:
                # Add header only if not already present
                if "Student ID" not in content and "Student Verification ID" not in content:
                    content = header + content
            
            # 3. Apply branding name substitutions
            content = content.replace("Saarthi Project", brand_name)
            content = content.replace("Sarthi Project", brand_name)
            content = content.replace("Saarthi App", brand_name)
            content = content.replace("Sarthi App", brand_name)
            
            # 4. Modify styling configurations (e.g. Tailwind or CSS variables)
            if "tailwind.config" in path:
                # Dynamically substitute colors
                content = content.replace("#4f46e5", primary_color)  # Default indigo-600
                content = content.replace("#10b981", secondary_color) # Default emerald-500
            elif path.endswith("globals.css") or path.endswith("index.css"):
                # Sub styling variables in CSS
                content = content.replace("--primary: 221.2 83.2% 53.3%", f"--primary: {primary_color}")
                content = content.replace("--secondary: 210 40% 96.1%", f"--secondary: {secondary_color}")
                
            new_file["content"] = content
            customized_codebase.append(new_file)
            
        # ── SDLC-specific project management docs ────────────────────────────────
        impl_plan = project_doc.get("implementation_plan", {}) or {}
        recommended_sdlc = impl_plan.get("recommended_sdlc", "") or ""
        sdlc_reasoning = impl_plan.get("sdlc_reasoning", "") or ""
        project_name = (project_doc.get("requirements", {}) or {}).get("project_overview", {}).get("name", "Project")
        features = (project_doc.get("requirements", {}) or {}).get("features", []) or []
        features_str = "\n".join([f"- [ ] {f}" for f in features[:15]])

        sdlc_docs: list = []

        if recommended_sdlc == "agile":
            sdlc_docs.append({
                "name": "BACKLOG.md",
                "path": "BACKLOG.md",
                "language": "markdown",
                "content": f"# {project_name} — Product Backlog\n\n> SDLC Model: Agile\n> {sdlc_reasoning}\n\n## User Stories\n\n{features_str}\n\n## Definition of Done\n- Unit tests pass\n- Code reviewed\n- Deployed to staging\n"
            })
            sdlc_docs.append({
                "name": "SPRINT_PLAN.md",
                "path": "SPRINT_PLAN.md",
                "language": "markdown",
                "content": f"# {project_name} — Sprint Plan\n\n## Sprint 1 (Week 1-2)\n### Goals\n- Set up project structure\n- Core authentication\n- Basic CRUD for primary entities\n\n## Sprint 2 (Week 3-4)\n### Goals\n- Feature modules\n- Frontend pages\n- Integration tests\n"
            })

        elif recommended_sdlc == "waterfall":
            sdlc_docs.append({
                "name": "REQUIREMENTS_SPEC.md",
                "path": "docs/REQUIREMENTS_SPEC.md",
                "language": "markdown",
                "content": f"# {project_name} — Requirements Specification\n\n> SDLC Model: Waterfall\n> {sdlc_reasoning}\n\n## Functional Requirements\n\n{features_str}\n\n## Non-Functional Requirements\n- Performance: API response < 200ms\n- Availability: 99.9% uptime\n- Security: JWT authentication, HTTPS only\n"
            })
            sdlc_docs.append({
                "name": "TEST_PLAN.md",
                "path": "docs/TEST_PLAN.md",
                "language": "markdown",
                "content": f"# {project_name} — Test Plan\n\n## Unit Testing\n- All service functions have unit tests\n\n## Integration Testing\n- All API endpoints tested\n\n## System Testing\n- End-to-end user flows validated\n"
            })

        elif recommended_sdlc == "v_model":
            sdlc_docs.append({
                "name": "TRACEABILITY_MATRIX.md",
                "path": "docs/TRACEABILITY_MATRIX.md",
                "language": "markdown",
                "content": f"# {project_name} — Requirements Traceability Matrix\n\n> SDLC Model: V-Model\n> {sdlc_reasoning}\n\n| Requirement | Design Module | Unit Test | Integration Test | Status |\n|-------------|--------------|-----------|-----------------|--------|\n" + "".join([f"| {f} | {f}Module | test_{f.lower().replace(' ', '_')}.py | test_integration_{f.lower().replace(' ', '_')}.py | Pending |\n" for f in features[:10]])
            })

        elif recommended_sdlc == "spiral":
            sdlc_docs.append({
                "name": "RISK_REGISTER.md",
                "path": "RISK_REGISTER.md",
                "language": "markdown",
                "content": f"# {project_name} — Risk Register\n\n> SDLC Model: Spiral\n> {sdlc_reasoning}\n\n| Risk | Probability | Impact | Mitigation |\n|------|-------------|--------|------------|\n| API instability | Medium | High | Implement retry logic and circuit breakers |\n| Scope creep | High | Medium | Strict feature freeze after each iteration |\n| Integration failures | Low | High | Comprehensive integration test suite |\n"
            })

        elif recommended_sdlc == "kanban":
            sdlc_docs.append({
                "name": "KANBAN_BOARD.md",
                "path": "KANBAN_BOARD.md",
                "language": "markdown",
                "content": f"# {project_name} — Kanban Board\n\n> SDLC Model: Kanban\n> {sdlc_reasoning}\n\n## Backlog\n{features_str}\n\n## In Progress (WIP Limit: 3)\n\n## Review\n\n## Done\n"
            })

        if sdlc_docs:
            customized_codebase.extend(sdlc_docs)

        return customized_codebase
