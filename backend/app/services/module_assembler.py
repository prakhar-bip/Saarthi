import re
from typing import Dict, Any, List, Optional
from loguru import logger
from app.services.project_assembler import detect_tech_stack


class ModuleAssembler:
    """
    Module Assembler for Sarthi.
    Gathers generated independent entity module files and weaves them into a unified project file tree.
    Enforces deterministic router mappings, export tables, and shared import paths.
    """

    def __init__(self, db: Any, project_id: str) -> None:
        self.db = db
        self.project_id = project_id

    async def assemble(
        self,
        project_doc: Dict[str, Any],
        synthesized_modules: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Collect all modular entities and combine them into a single runnable codebase."""
        logger.info("[ModuleAssembler] Starting codebase assembly sequence...")
        
        assembled_files: List[Dict[str, Any]] = []
        entity_names = list(synthesized_modules.keys())

        # 1. Gather all entity files
        for name, modules in synthesized_modules.items():
            logger.info(f"[ModuleAssembler] Module: {name} - Gathering files...")
            backend_files = modules.get("backend", []) or []
            frontend_files = modules.get("frontend", []) or []
            
            # Append each file cleanly
            assembled_files.extend(backend_files)
            assembled_files.extend(frontend_files)

        # 2. Dynamic Backend Routing and Wiring
        tech_stack = detect_tech_stack(project_doc)
        backend_tech = tech_stack.get("backend", "fastapi")
        
        if backend_tech == "django":
            # Assemble a central backend/app/urls.py registering DRF routers
            url_imports = []
            url_registrations = []
            for name in entity_names:
                l_name = name.lower()
                url_imports.append(f"from .views.{l_name} import {name}ViewSet")
                url_registrations.append(f"router.register(r'{l_name}s', {name}ViewSet, basename='{l_name}')")

            django_urls_py = f"""from django.urls import path, include
from rest_framework.routers import DefaultRouter
{chr(10).join(url_imports)}

router = DefaultRouter()
{chr(10).join(url_registrations)}

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
"""
            assembled_files.append({
                "name": "urls.py",
                "path": "backend/app/urls.py",
                "language": "python",
                "content": django_urls_py.strip(),
            })

        elif backend_tech == "flask":
            # Assemble a central backend/app/main.py registering Blueprints
            blueprint_imports = []
            blueprint_registrations = []
            for name in entity_names:
                l_name = name.lower()
                blueprint_imports.append(f"from app.blueprints.{l_name} import {l_name}_bp")
                blueprint_registrations.append(f"app.register_blueprint({l_name}_bp, url_prefix='/api/v1')")

            flask_main_py = f"""from flask import Flask
from flask_cors import CORS
{chr(10).join(blueprint_imports)}

app = Flask(__name__)
CORS(app)

{chr(10).join(blueprint_registrations)}

@app.route('/health', methods=['GET'])
def health():
    return {{"status": "healthy"}}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""
            assembled_files.append({
                "name": "main.py",
                "path": "backend/app/main.py",
                "language": "python",
                "content": flask_main_py.strip(),
            })

        elif backend_tech == "express":
            # Assemble a central backend/src/index.js requiring routes
            route_requires = []
            route_usages = []
            for name in entity_names:
                l_name = name.lower()
                route_requires.append(f"const {l_name}Routes = require('./routes/{l_name}');")
                route_usages.append(f"app.use('/api/v1', {l_name}Routes);")

            express_index_js = f"""const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');

{chr(10).join(route_requires)}

const app = express();
app.use(cors());
app.use(express.json());

{chr(10).join(route_usages)}

app.get('/health', (req, res) => {{
  res.json({{ status: 'healthy' }});
}});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {{
  console.log(`Server is running on port ${{PORT}}`);
}});
"""
            assembled_files.append({
                "name": "index.js",
                "path": "backend/src/index.js",
                "language": "javascript",
                "content": express_index_js.strip(),
            })

        elif backend_tech in ["springboot", "spring"]:
            # Spring Boot controllers are automatically discovered by @SpringBootApplication annotation,
            # so we only need to write a standard central Application.java class.
            spring_app_java = f"""package com.saarthi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SaarthiApplication {{
    public static void main(String[] args) {{
        SpringApplication.run(SaarthiApplication.class, args);
    }}
}}
"""
            assembled_files.append({
                "name": "SaarthiApplication.java",
                "path": "backend/src/main/java/com/saarthi/SaarthiApplication.java",
                "language": "java",
                "content": spring_app_java.strip(),
            })

        else: # fastapi (Default)
            import_statements = []
            router_registrations = []
            for name in entity_names:
                l_name = name.lower()
                import_statements.append(f"from app.api.{l_name} import router as {l_name}_router")
                router_registrations.append(f"app.include_router({l_name}_router, prefix='/api/v1', tags=['{name}'])")

            base_main_py = f"""import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

{chr(10).join(import_statements)}

app = FastAPI(title=settings.PROJECT_NAME, version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

{chr(10).join(router_registrations)}

@app.get('/health', tags=['Health'])
def health_check():
    return {{'status': 'healthy'}}
"""
            assembled_files.append({
                "name": "main.py",
                "path": "backend/app/main.py",
                "language": "python",
                "content": base_main_py.strip(),
            })

        # 3. Dynamic Frontend State and Route Imports/Exports
        # For React / Next.js, let's assemble a global stores/index.ts that bundles all Zustand stores
        store_exports = []
        for name in entity_names:
            l_name = name.lower()
            store_exports.append(f"export * from './{l_name}Store';")

        assembled_files.append({
            "name": "index.ts",
            "path": "frontend/src/stores/index.ts",
            "language": "typescript",
            "content": "\n".join(store_exports),
        })

        # Also add a central axios fetch wrapper if needed or general api clients index
        api_exports = []
        for name in entity_names:
            l_name = name.lower()
            api_exports.append(f"export * from './{l_name}';")

        assembled_files.append({
            "name": "index.ts",
            "path": "frontend/src/api/index.ts",
            "language": "typescript",
            "content": "\n".join(api_exports),
        })

        logger.info(f"[ModuleAssembler] Codebase compiled successfully with {len(assembled_files)} total files.")
        return assembled_files
