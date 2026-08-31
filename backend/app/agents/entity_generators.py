import json
import time
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.llm_router import get_llm_completion
from app.agents.context import build_agent_system_prompt, enrich_agent_output, parse_json_response


class BackendEntityGenerator:
    """
    Backend Entity Generator for Sarthi.
    Generates single-entity backend files for FastAPI, Django, Flask, Express, or Spring Boot.
    """

    def __init__(self) -> None:
        self.agent_name = "BackendEntityGenerator"

    async def generate(self, entity_contract: Dict[str, Any], relevant_dependencies: List[str], tech_stack: str = "fastapi", auth_architecture: Optional[Dict[str, Any]] = None, all_entity_names: Optional[List[str]] = None, sdlc_model: str = "agile", theme_styling: Optional[Dict[str, Any]] = None, realtime_architecture: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize backend modules for a single entity in isolation."""
        ename = entity_contract["name"]
        agent_inputs = {
            "entity_contract": entity_contract,
            "relevant_dependencies": relevant_dependencies,
            "tech_stack": tech_stack,
        }

        # Normalize stack name
        tech_stack_normalized = str(tech_stack).lower().strip()

        # Check for API keys
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(
                self._get_fallback_backend(entity_contract, tech_stack_normalized),
                self.agent_name,
                agent_inputs,
            )

        # Dynamic structure depending on normalized tech stack
        if tech_stack_normalized == "django":
            lang = "python"
            role_description = "Django Rest Framework (DRF) Engineer"
            instructions = (
                f"Generate models, serializers, views, and url patterns for '{ename}' using Django REST Framework.\n"
                "Do NOT use any placeholders. Write full Django code."
            )
            files_prompt = f"""
            1. models/{ename.lower()}.py — Django database model class
            2. serializers/{ename.lower()}.py — DRF serializers
            3. views/{ename.lower()}.py — DRF model ViewSet classes
            4. urls/{ename.lower()}.py — DRF URL routes and path registrations
            """
            example_file_path = f"backend/app/models/{ename.lower()}.py"
            example_code_snippet = f"from django.db import models\n\nclass {ename}(models.Model):\n    pass"

        elif tech_stack_normalized == "flask":
            lang = "python"
            role_description = "Flask Backend Engineer"
            instructions = (
                f"Generate Flask Blueprint, PyMongo-based models, and services for '{ename}'.\n"
                "Ensure standard Flask routing and JSON response utilities are fully coded without stubs."
            )
            files_prompt = f"""
            1. models/{ename.lower()}.py — Flask database schema or PyMongo driver helper
            2. blueprints/{ename.lower()}.py — Flask router blueprint and endpoints
            3. services/{ename.lower()}_service.py — business/CRUD execution logic
            """
            example_file_path = f"backend/app/blueprints/{ename.lower()}.py"
            example_code_snippet = f"from flask import Blueprint\n\n{ename.lower()}_bp = Blueprint('{ename.lower()}', __name__)"

        elif tech_stack_normalized == "express":
            lang = "javascript"
            role_description = "Express Node.js Backend Developer"
            instructions = (
                f"Generate Express.js router, controller, Mongoose model, and service/validation modules for '{ename}' in JavaScript.\n"
                "Return complete, beautifully written production-ready code with no placeholders."
            )
            files_prompt = f"""
            1. models/{ename.lower()}.js — Mongoose MongoDB model schema
            2. controllers/{ename.lower()}.js — Express handler functions for CRUD
            3. routes/{ename.lower()}.js — Express API endpoint routes
            4. services/{ename.lower()}_service.js — Business logic layer
            """
            example_file_path = f"backend/src/models/{ename.lower()}.js"
            example_code_snippet = "const mongoose = require('mongoose');\nconst schema = new mongoose.Schema({});"

        elif tech_stack_normalized in ["springboot", "spring"]:
            lang = "java"
            role_description = "Spring Boot Enterprise Java Developer"
            instructions = (
                f"Generate complete Spring Boot REST enterprise classes for '{ename}': JPA Entity, Spring Data Repository, Service layer, and REST controller.\n"
                "Ensure correct Spring annotations (@Entity, @RestController, @Service, @Autowired, @GetMapping, etc.) and complete logic."
            )
            files_prompt = f"""
            1. model/{ename}Entity.java — Spring Boot JPA entity class
            2. repository/{ename}Repository.java — Spring Data JPA Repository interface
            3. service/{ename}Service.java — business execution service layer
            4. controller/{ename}Controller.java — enterprise annotation-driven REST controller
            """
            example_file_path = f"backend/src/main/java/com/saarthi/model/{ename}Entity.java"
            example_code_snippet = "package com.saarthi.model;\nimport jakarta.persistence.*;\n\n@Entity\npublic class " + ename + "Entity {}"

        else:  # Default is fastapi
            lang = "python"
            role_description = "FastAPI Backend Specialist"
            instructions = (
                f"Write the COMPLETE and robust FastAPI backend modules specifically for the '{ename}' entity.\n"
                "Absolutely NO TODOs, placeholders, or ellipsis ('// ...'). Write clean, fully implemented, compilable code.\n"
                "Ensure correct imports, and use motor/pymongo for asynchronous database queries."
            )
            files_prompt = f"""
            1. models/{ename.lower()}.py — MongoDB database model class
            2. schemas/{ename.lower()}.py — Pydantic request/response validation schemas
            3. services/{ename.lower()}_service.py — business/CRUD execution logic
            4. api/{ename.lower()}.py — FastAPI endpoint routers
            5. validation/{ename.lower()}_validator.py — custom validation logic
            6. repository/{ename.lower()}_repository.py — database query interface
            """
            example_file_path = f"backend/app/models/{ename.lower()}.py"
            example_code_snippet = "from pydantic import BaseModel\nclass ModelName(BaseModel):\n    pass"

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                f"You are Sarthi's Senior {role_description}.\n"
                f"Your task is to write the COMPLETE and robust backend modules specifically for the '{ename}' entity.\n"
                f"Absolutely NO TODOs, placeholders, or ellipsis ('// ...'). Write clean, fully implemented, compilable code.\n\n"
                f"{instructions}"
            ),
        )

        # Build path prefix helper for Express / Spring Boot
        path_prefix = "backend/app/"
        if tech_stack_normalized == "express":
            path_prefix = "backend/src/"
        elif tech_stack_normalized in ["springboot", "spring"]:
            path_prefix = "backend/src/main/java/com/saarthi/"

        prompt_parts = [f"""
        Entity Contract: {json.dumps(entity_contract, indent=2)}
        Upstream Dependencies to Import/Reference: {json.dumps(relevant_dependencies)}

        Generate the following files for the '{ename}' entity:
        {files_prompt}

        Ensure files are saved under the correct path layout (e.g. prefix each relative path with '{path_prefix}').
        """]

        if auth_architecture:
            prompt_parts.append(f"\n\nAUTH STRATEGY:\n{json.dumps(auth_architecture.get('authentication_strategy', {}), default=str)[:1000]}")
        if all_entity_names:
            prompt_parts.append(f"\n\nALL PROJECT ENTITIES (for cross-references): {', '.join(all_entity_names)}")
        if sdlc_model:
            if sdlc_model == 'v_model':
                prompt_parts.append("\n\nSDLC: V-Model — generate comprehensive docstrings and include a test stub for every function.")
            elif sdlc_model == 'agile':
                prompt_parts.append("\n\nSDLC: Agile — add TODO comments for future sprint enhancements.")

        prompt_parts.append(f"""
        Return ONLY a JSON response in this exact format:
        {{
          "files": [
            {{
              "name": "{ename.lower()}.{ 'js' if lang == 'javascript' else ('java' if lang == 'java' else 'py') }",
              "path": "{example_file_path}",
              "language": "{lang}",
              "content": {json.dumps(example_code_snippet)}
            }}
          ]
        }}
        """)

        user_prompt = "".join(prompt_parts)


        try:
            t0 = time.time()
            response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            t1 = time.time()
            parsed = parse_json_response(response.strip())
            parsed["duration"] = t1 - t0
            return enrich_agent_output(parsed, self.agent_name, agent_inputs)
        except Exception as e:
            return enrich_agent_output(
                self._get_fallback_backend(entity_contract, tech_stack_normalized),
                self.agent_name,
                agent_inputs,
            )

    def _get_fallback_backend(self, entity_contract: Dict[str, Any], tech_stack: str = "fastapi") -> Dict[str, Any]:
        """Generate complete compilable fallback files if LLM synthesis fails."""
        ename = entity_contract["name"]
        l_name = ename.lower()
        tech_stack_normalized = str(tech_stack).lower().strip()

        if tech_stack_normalized == "django":
            model_code = f"""from django.db import models

class {ename}(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '{l_name}s'
"""
            serializer_code = f"""from rest_framework import serializers
from ..models.{l_name} import {ename}

class {ename}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {ename}
        fields = '__all__'
"""
            view_code = f"""from rest_framework import viewsets
from ..models.{l_name} import {ename}
from ..serializers.{l_name} import {ename}Serializer

class {ename}ViewSet(viewsets.ModelViewSet):
    queryset = {ename}.objects.all()
    serializer_class = {ename}Serializer
"""
            url_code = f"""from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.{l_name} import {ename}ViewSet

router = DefaultRouter()
router.register(r'{l_name}s', {ename}ViewSet, basename='{l_name}')

urlpatterns = [
    path('', include(router.urls)),
]
"""
            return {
                "files": [
                    {"name": f"{l_name}.py", "path": f"backend/app/models/{l_name}.py", "language": "python", "content": model_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/serializers/{l_name}.py", "language": "python", "content": serializer_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/views/{l_name}.py", "language": "python", "content": view_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/urls/{l_name}.py", "language": "python", "content": url_code.strip()},
                ]
            }

        elif tech_stack_normalized == "flask":
            model_code = f"""from datetime import datetime
from typing import Optional

class {ename}Model:
    @staticmethod
    def serialize(data: dict) -> dict:
        return {{
            "id": str(data.get("_id", "")),
            "name": data.get("name", ""),
            "created_at": data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
        }}
"""
            blueprint_code = f"""from flask import Blueprint, request, jsonify
from ..services.{l_name}_service import {ename}Service

{l_name}_bp = Blueprint('{l_name}', __name__)

@{l_name}_bp.route('/{l_name}s', methods=['GET'])
def list_items():
    items = {ename}Service.get_all()
    return jsonify(items)

@{l_name}_bp.route('/{l_name}s', methods=['POST'])
def create_item():
    data = request.get_json() or {{}}
    item = {ename}Service.create(data)
    return jsonify(item), 201
"""
            service_code = f"""from datetime import datetime
import uuid

# Dummy in-memory DB or PyMongo representation
_db_store = []

class {ename}Service:
    @staticmethod
    def get_all():
        return _db_store

    @staticmethod
    def create(data: dict):
        new_item = {{
            "id": str(uuid.uuid4()),
            "name": data.get("name", "Untitled"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }}
        _db_store.append(new_item)
        return new_item
"""
            return {
                "files": [
                    {"name": f"{l_name}.py", "path": f"backend/app/models/{l_name}.py", "language": "python", "content": model_code.strip()},
                    {"name": f"{l_name}_service.py", "path": f"backend/app/services/{l_name}_service.py", "language": "python", "content": service_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/blueprints/{l_name}.py", "language": "python", "content": blueprint_code.strip()},
                ]
            }

        elif tech_stack_normalized == "express":
            model_code = f"""const mongoose = require('mongoose');

const {ename}Schema = new mongoose.Schema({{
  name: {{ type: String, required: true }},
  createdAt: {{ type: Date, default: Date.now }},
  updatedAt: {{ type: Date, default: Date.now }}
}});

module.exports = mongoose.model('{ename}', {ename}Schema);
"""
            controller_code = f"""const Service = require('../services/{l_name}_service');

exports.getAll = async (req, res, next) => {{
  try {{
    const items = await Service.getAll();
    res.json(items);
  }} catch (err) {{
    res.status(500).json({{ error: err.message }});
  }}
}};

exports.create = async (req, res, next) => {{
  try {{
    const item = await Service.create(req.body);
    res.status(201).json(item);
  }} catch (err) {{
    res.status(400).json({{ error: err.message }});
  }}
}};
"""
            route_code = f"""const express = require('express');
const router = express.Router();
const controller = require('../controllers/{l_name}');

router.get('/{l_name}s', controller.getAll);
router.post('/{l_name}s', controller.create);

module.exports = router;
"""
            service_code = f"""const {ename} = require('../models/{l_name}');

exports.getAll = async () => {{
  return await {ename}.find();
}};

exports.create = async (data) => {{
  const item = new {ename}(data);
  return await item.save();
}};
"""
            return {
                "files": [
                    {"name": f"{l_name}.js", "path": f"backend/src/models/{l_name}.js", "language": "javascript", "content": model_code.strip()},
                    {"name": f"{l_name}_service.js", "path": f"backend/src/services/{l_name}_service.js", "language": "javascript", "content": service_code.strip()},
                    {"name": f"{l_name}.js", "path": f"backend/src/controllers/{l_name}.js", "language": "javascript", "content": controller_code.strip()},
                    {"name": f"{l_name}.js", "path": f"backend/src/routes/{l_name}.js", "language": "javascript", "content": route_code.strip()},
                ]
            }

        elif tech_stack_normalized in ["springboot", "spring"]:
            model_code = f"""package com.saarthi.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "{l_name}s")
public class {ename}Entity {{
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt = LocalDateTime.now();

    public Long getId() {{ return id; }}
    public void setId(Long id) {{ this.id = id; }}

    public String getName() {{ return name; }}
    public void setName(String name) {{ this.name = name; }}

    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public void setCreatedAt(LocalDateTime createdAt) {{ this.createdAt = createdAt; }}

    public LocalDateTime getUpdatedAt() {{ return updatedAt; }}
    public void setUpdatedAt(LocalDateTime updatedAt) {{ this.updatedAt = updatedAt; }}
}}
"""
            repo_code = f"""package com.saarthi.repository;

import com.saarthi.model.{ename}Entity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface {ename}Repository extends JpaRepository<{ename}Entity, Long> {{
}}
"""
            service_code = f"""package com.saarthi.service;

import com.saarthi.model.{ename}Entity;
import com.saarthi.repository.{ename}Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class {ename}Service {{
    @Autowired
    private {ename}Repository repository;

    public List<{ename}Entity> getAll() {{
        return repository.findAll();
    }}

    public {ename}Entity create({ename}Entity entity) {{
        return repository.save(entity);
    }}
}}
"""
            controller_code = f"""package com.saarthi.controller;

import com.saarthi.model.{ename}Entity;
import com.saarthi.service.{ename}Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1")
public class {ename}Controller {{
    @Autowired
    private {ename}Service service;

    @GetMapping("/{l_name}s")
    public List<{ename}Entity> getAll() {{
        return service.getAll();
    }}

    @PostMapping("/{l_name}s")
    public {ename}Entity create(@RequestBody {ename}Entity entity) {{
        return service.create(entity);
    }}
}}
"""
            return {
                "files": [
                    {"name": f"{ename}Entity.java", "path": f"backend/src/main/java/com/saarthi/model/{ename}Entity.java", "language": "java", "content": model_code.strip()},
                    {"name": f"{ename}Repository.java", "path": f"backend/src/main/java/com/saarthi/repository/{ename}Repository.java", "language": "java", "content": repo_code.strip()},
                    {"name": f"{ename}Service.java", "path": f"backend/src/main/java/com/saarthi/service/{ename}Service.java", "language": "java", "content": service_code.strip()},
                    {"name": f"{ename}Controller.java", "path": f"backend/src/main/java/com/saarthi/controller/{ename}Controller.java", "language": "java", "content": controller_code.strip()},
                ]
            }

        else: # Default fastapi fallback
            model_code = f"""from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class {ename}Model(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
"""
            schema_code = f"""from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class {ename}Create(BaseModel):
    name: str = Field(..., min_length=1)

class {ename}Update(BaseModel):
    name: Optional[str] = None

class {ename}Response(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
"""
            repo_code = f"""from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.{l_name} import {ename}Model

class {ename}Repository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["{l_name}s"]

    async def get_all(self) -> List[dict]:
        cursor = self.collection.find()
        return [doc async for doc in cursor]

    async def get_by_id(self, item_id: str) -> Optional[dict]:
        return await self.collection.find_one({{"_id": item_id}})

    async def create(self, data: dict) -> dict:
        result = await self.collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        return data
"""
            service_code = f"""from typing import List, Optional
from app.repository.{l_name}_repository import {ename}Repository

class {ename}Service:
    def __init__(self, repo: {ename}Repository):
        self.repo = repo

    async def fetch_all(self) -> List[dict]:
        return await self.repo.get_all()

    async def fetch_by_id(self, item_id: str) -> Optional[dict]:
        return await self.repo.get_by_id(item_id)

    async def create_item(self, data: dict) -> dict:
        return await self.repo.create(data)
"""
            api_code = f"""from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.{l_name} import {ename}Create, {ename}Response
from app.services.{l_name}_service import {ename}Service
from app.repository.{l_name}_repository import {ename}Repository
from app.db.mongodb import get_database

router = APIRouter()

def get_service() -> {ename}Service:
    db = get_database()
    repo = {ename}Repository(db)
    return {ename}Service(repo)

@router.get("/{l_name}s", response_model=List[{ename}Response])
async def list_items(service: {ename}Service = Depends(get_service)):
    return await service.fetch_all()

@router.post("/{l_name}s", response_model={ename}Response, status_code=status.HTTP_201_CREATED)
async def create_item(payload: {ename}Create, service: {ename}Service = Depends(get_service)):
    return await service.create_item(payload.dict())
"""
            validator_code = f"""from fastapi import HTTPException

class {ename}Validator:
    @staticmethod
    def validate_create(data: dict):
        if not data.get("name"):
            raise HTTPException(status_code=400, detail="Name field is required and cannot be empty.")
"""
            return {
                "files": [
                    {"name": f"{l_name}.py", "path": f"backend/app/models/{l_name}.py", "language": "python", "content": model_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/schemas/{l_name}.py", "language": "python", "content": schema_code.strip()},
                    {"name": f"{l_name}_repository.py", "path": f"backend/app/repository/{l_name}_repository.py", "language": "python", "content": repo_code.strip()},
                    {"name": f"{l_name}_service.py", "path": f"backend/app/services/{l_name}_service.py", "language": "python", "content": service_code.strip()},
                    {"name": f"{l_name}.py", "path": f"backend/app/api/{l_name}.py", "language": "python", "content": api_code.strip()},
                    {"name": f"{l_name}_validator.py", "path": f"backend/app/validation/{l_name}_validator.py", "language": "python", "content": validator_code.strip()},
                ]
            }


class FrontendEntityGenerator:
    """
    Frontend Entity Generator for Sarthi.
    Generates Next.js files: hook, Zustand store, Axios endpoint client, list page, form components.
    """

    def __init__(self) -> None:
        self.agent_name = "FrontendEntityGenerator"

    async def generate(self, entity_contract: Dict[str, Any], ui_contract: Dict[str, Any], api_contract: Dict[str, Any], auth_architecture: Optional[Dict[str, Any]] = None, all_entity_names: Optional[List[str]] = None, sdlc_model: str = "agile", theme_styling: Optional[Dict[str, Any]] = None, realtime_architecture: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize frontend components, pages, stores, and hooks for a single entity in isolation."""
        ename = entity_contract["name"]
        agent_inputs = {
            "entity_contract": entity_contract,
            "ui_contract": ui_contract,
            "api_contract": api_contract,
        }

        # Check for API keys
        if not (settings.NVIDIA_API_KEY or settings.OPENROUTER_API_KEY or settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
            return enrich_agent_output(
                self._get_fallback_frontend(entity_contract),
                self.agent_name,
                agent_inputs,
            )

        system_prompt = build_agent_system_prompt(
            self.agent_name,
            (
                "You are Sarthi's Senior Next.js/React Frontend UX Architect.\n"
                f"Write the COMPLETE and premium React/TypeScript code specifically for the '{ename}' entity.\n"
                "Use Tailwind CSS for stunning styling, SWR for API queries, and Zustand for global state.\n"
                "Absolutely NO TODOs, placeholders, or ellipsis ('// ...'). Write production-ready component code."
            ),
        )

        prompt_parts = [f"""
        Entity Contract: {json.dumps(entity_contract, indent=2)}
        UI Theme & Styling Tokens: {json.dumps(ui_contract, indent=2)}
        API Contract Endpoints: {json.dumps(api_contract, indent=2)}

        Generate the following frontend files for '{ename}':
        1. pages/{ename.lower()}/page.tsx — Dashboard list & grid view
        2. components/{ename.lower()}/{ename}Form.tsx — modal dialog form for create/edit
        3. hooks/use{ename}.ts — SWR React data fetching hook
        4. stores/{ename.lower()}Store.ts — Zustand state management store
        5. api/{ename.lower()}.ts — axios router client wrappers
        """]

        if auth_architecture:
            prompt_parts.append(f"\n\nAUTH STRATEGY:\n{json.dumps(auth_architecture.get('authentication_strategy', {}), default=str)[:1000]}")
        if all_entity_names:
            prompt_parts.append(f"\n\nALL PROJECT ENTITIES (for cross-references): {', '.join(all_entity_names)}")
        if sdlc_model:
            if sdlc_model == 'v_model':
                prompt_parts.append("\n\nSDLC: V-Model — generate comprehensive docstrings and include a test stub for every function.")
            elif sdlc_model == 'agile':
                prompt_parts.append("\n\nSDLC: Agile — add TODO comments for future sprint enhancements.")

        prompt_parts.append(f"""
        Return ONLY a JSON response in this exact format:
        {{
          "files": [
            {{
              "name": "page.tsx",
              "path": "frontend/src/app/dashboard/{ename.lower()}s/page.tsx",
              "language": "typescript",
              "content": "export default function Page() {{\\n    ..."
            }}
          ]
        }}
        """)

        user_prompt = "".join(prompt_parts)


        try:
            t0 = time.time()
            response = await get_llm_completion(
                agent_name=self.agent_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            t1 = time.time()
            parsed = parse_json_response(response.strip())
            parsed["duration"] = t1 - t0
            return enrich_agent_output(parsed, self.agent_name, agent_inputs)
        except Exception as e:
            return enrich_agent_output(
                self._get_fallback_frontend(entity_contract),
                self.agent_name,
                agent_inputs,
            )

    def _get_fallback_frontend(self, entity_contract: Dict[str, Any]) -> Dict[str, Any]:
        """Generate beautiful fallback TypeScript/Next.js components when LLM synthesis fails."""
        ename = entity_contract["name"]
        l_name = ename.lower()

        # api/item.ts
        api_code = f"""import axios from 'axios';

export interface {ename} {{
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}}

export const fetch{ename}s = async (): Promise<{ename}[]> => {{
  const res = await axios.get(`/api/v1/{l_name}s`);
  return res.data;
}};

export const create{ename} = async (name: string): Promise<{ename}> => {{
  const res = await axios.post(`/api/v1/{l_name}s`, {{ name }});
  return res.data;
}};
"""
        # stores/itemStore.ts
        store_code = f"""import {{ create }} from 'zustand';
import {{ {ename} }} from '../api/{l_name}';

interface {ename}State {{
  items: {ename}[];
  setItems: (items: {ename}[]) => void;
  addItem: (item: {ename}) => void;
}}

export const use{ename}Store = create<{ename}State>((set) => ({{
  items: [],
  setItems: (items) => set({{ items }}),
  addItem: (item) => set((state) => ({{ items: [...state.items, item] }})),
}}));
"""
        # hooks/useItem.ts
        hook_code = f"""import useSWR from 'swr';
import {{ fetch{ename}s }} from '../api/{l_name}';
import {{ use{ename}Store }} from '../stores/{l_name}Store';
import {{ useEffect }} from 'react';

export const use{ename} = () => {{
  const {{ data, error, mutate }} = useSWR(`/api/v1/{l_name}s`, fetch{ename}s);
  const setItems = use{ename}Store((state) => state.setItems);

  useEffect(() => {{
    if (data) {{
      setItems(data);
    }}
  }}, [data, setItems]);

  return {{
    items: use{ename}Store((state) => state.items),
    isLoading: !error && !data,
    isError: error,
    mutate,
  }};
}};
"""
        # components/item/Form.tsx
        form_code = f"""'use client';

import React, {{ useState }} from 'react';
import {{ create{ename} }} from '../../api/{l_name}';
import {{ use{ename}Store }} from '../../stores/{l_name}Store';

export function {ename}Form({{ onClose }}: {{ onClose: () => void }}) {{
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const addItem = use{ename}Store((state) => state.addItem);

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {{
      const newItem = await create{ename}(name);
      addItem(newItem);
      onClose();
    }} catch (err) {{
      console.error(err);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <form onSubmit={{handleSubmit}} className="bg-[#1A1F2C] border border-[#2D3748] rounded-2xl w-full max-w-md p-6 shadow-2xl animate-fade-in">
        <h2 className="text-xl font-bold text-white mb-4">Create New {ename}</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
            <input 
              type="text" 
              value={{name}}
              onChange={{(e) => setName(e.target.value)}}
              className="w-full bg-[#11141E] border border-[#2D3748] text-white rounded-xl px-4 py-3 focus:outline-none focus:border-[#4F46E5] transition" 
              placeholder="Enter name..."
              required
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={{onClose}} className="px-5 py-2.5 rounded-xl bg-gray-800 text-gray-300 hover:bg-gray-700 transition">Cancel</button>
          <button type="submit" disabled={{loading}} className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 font-medium transition flex items-center justify-center">
            {{loading ? 'Creating...' : 'Create'}}
          </button>
        </div>
      </form>
    </div>
  );
}}
"""
        # pages/item/page.tsx
        page_code = f"""'use client';

import React, {{ useState }} from 'react';
import {{ use{ename} }} from '../../../hooks/use{ename}';
import {{ {ename}Form }} from '../../../components/{l_name}/{ename}Form';

export default function {ename}Dashboard() {{
  const {{ items, isLoading }} = use{ename}();
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-white p-6 md:p-10">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">{ename} Management</h1>
            <p className="text-gray-400 mt-1">Surgically generated high-performance module</p>
          </div>
          <button 
            onClick={{() => setShowForm(true)}}
            className="bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 hover:shadow-indigo-500/40 transition-all duration-300 active:scale-95"
          >
            + Create {ename}
          </button>
        </div>

        {{isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {{items.length === 0 ? (
              <div className="col-span-full border border-dashed border-gray-800 rounded-2xl p-12 text-center text-gray-500">
                No items found. Create one to get started!
              </div>
            ) : (
              items.map((item) => (
                <div key={{item.id}} className="bg-[#141824] border border-[#232B3F] hover:border-indigo-500/50 rounded-2xl p-5 shadow-lg transition-all duration-300 hover:translate-y-[-4px]">
                  <h3 className="text-lg font-bold text-white mb-2">{{item.name}}</h3>
                  <div className="text-xs text-gray-500 space-y-1 mt-4 border-t border-gray-800 pt-3">
                    <div>ID: {{item.id}}</div>
                    <div>Created: {{new Date(item.createdAt).toLocaleDateString()}}</div>
                  </div>
                </div>
              ))
            )}}
          </div>
        )}}

        {{showForm && <{ename}Form onClose={{() => setShowForm(false)}} />}}
      </div>
    </div>
  );
}}
"""

        return {
            "files": [
                {"name": f"{l_name}.ts", "path": f"frontend/src/api/{l_name}.ts", "language": "typescript", "content": api_code.strip()},
                {"name": f"{l_name}Store.ts", "path": f"frontend/src/stores/{l_name}Store.ts", "language": "typescript", "content": store_code.strip()},
                {"name": f"use{ename}.ts", "path": f"frontend/src/hooks/use{ename}.ts", "language": "typescript", "content": hook_code.strip()},
                {"name": f"{ename}Form.tsx", "path": f"frontend/src/components/{l_name}/{ename}Form.tsx", "language": "typescript", "content": form_code.strip()},
                {"name": "page.tsx", "path": f"frontend/src/app/dashboard/{l_name}s/page.tsx", "language": "typescript", "content": page_code.strip()},
            ]
        }
