import json
import time
from typing import List, Dict, Any
from app.core.config import settings
from app.agents.context import build_compilation_context
from app.services.llm_router import get_llm_completion, stream_raw_llm_completion



async def generate_chat_reply(category: str, messages: List[Dict[str, str]], selected_project: dict = None) -> str:
    """
    Generate a reply using the LLM Router.
    Converts list of messages into Chat Completions.
    """
    start_time = time.perf_counter()
    try:
        if selected_project:
            system_prompt = (
                f"You are **Sarthi**, an expert AI development partner for the '{category}' domain. You adapt dynamically to the user's state of mind.\n\n"
                f"## Active Project Context\n"
                f"- **Project Name**: {selected_project.get('name')}\n"
                f"- **Core Idea**: {selected_project.get('idea')}\n"
                f"- **Key Features**: {', '.join(selected_project.get('features', []))}\n"
                f"- **Tech Stack**: {selected_project.get('tech_stack')}\n\n"
                "## Mindset & Semantic Routing\n"
                "Analyze the user's intent semantically across messages:\n"
                "1. **Casual/General Chat**: Talk naturally and warmly. Do not force technical jargon, templates, or blueprint blocks.\n"
                "2. **Learning/Concept Q&A**: Explain clearly with code snippets and markdown formatting, focusing on the specific question.\n"
                "3. **Refining & Brainstorming**: Discuss ideas as a co-founder. Suggest features gradually and listen to feedback. Do not dump complete structures immediately.\n\n"
                "## Blueprint Block (Locking in Configuration)\n"
                "ONLY append the `<blueprint>` block at the very end of your message if the user has EXPLICITLY requested to save, finalize, update, or compile the project blueprint, OR if they agree on a specific feature set configuration. Otherwise, chat normally without any blocks.\n"
                "Format of the block when requested:\n"
                "<blueprint>\n"
                "{\n"
                "  \"name\": \"Updated Project Name\",\n"
                "  \"idea\": \"Core Idea/Description\",\n"
                "  \"features\": [\"Feature 1\", \"Feature 2\", \"Feature 3\"],\n"
                "  \"tech_stack\": \"Flask, HTML, CSS\",\n"
                "  \"category\": \"web\"  // 'web', 'agent', 'mobile', or 'backend'\n"
                "}\n"
                "</blueprint>"
            )
        else:
            system_prompt = (
                f"You are **Sarthi**, an expert AI development partner for the '{category}' domain. You adapt dynamically to the user's state of mind.\n\n"
                "## Your Role & Vibe\n"
                "You are an empathetic, intelligent, and conversational co-pilot. Listen carefully, analyze the user's mindset, and build context step-by-step over the chat history.\n\n"
                "## Mindset & Semantic Routing\n"
                "Analyze the user's intent semantically across messages:\n"
                "1. **Casual/General Chat**: Talk naturally, enthusiastically, and warmly. Do not force templates or project planning.\n"
                "2. **Learning/Concept Q&A**: Provide clear, direct, and well-commented code snippets with concise explanations.\n"
                "3. **Brainstorming Project Ideas**: Engage in active, friendly brainstorming. Suggest 1-2 creative directions rather than overloading the user. Build on their ideas.\n\n"
                "## Blueprint Block (Locking in Configuration)\n"
                "ONLY append the `<blueprint>` block at the very end of your message if the user has EXPLICITLY requested to finalize, save, or compile a project blueprint. Do NOT output this block for greetings, casual chat, brainstorming, or normal Q&A.\n"
                "Format of the block when requested:\n"
                "<blueprint>\n"
                "{\n"
                "  \"name\": \"Project Name\",\n"
                "  \"idea\": \"Core Idea/Description\",\n"
                "  \"features\": [\"Feature 1\", \"Feature 2\", \"Feature 3\"],\n"
                "  \"tech_stack\": \"Flask, HTML, CSS\",\n"
                "  \"category\": \"web\"  // 'web', 'agent', 'mobile', or 'backend'\n"
                "}\n"
                "</blueprint>"
            )
        
        chat_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            chat_messages.append({"role": role, "content": msg["text"]})

        reply = await get_llm_completion(
            agent_name="ChatReply",
            messages=chat_messages,
            temperature=0.7,
            max_tokens=2048
        )
        return reply
    except Exception as e:
        duration = time.perf_counter() - start_time
        return get_fallback_chat_reply(category, messages[-1]["text"] if messages else "", selected_project)


async def stream_chat_reply(category: str, messages: List[Dict[str, str]], selected_project: dict = None):
    """
    Generate a reply using the LLM Router stream completion.
    Yields chunks of text.
    """
    try:
        if selected_project:
            system_prompt = (
                f"You are **Sarthi**, an expert AI development partner for the '{category}' domain. You adapt dynamically to the user's state of mind.\n\n"
                f"## Active Project Context\n"
                f"- **Project Name**: {selected_project.get('name')}\n"
                f"- **Core Idea**: {selected_project.get('idea')}\n"
                f"- **Key Features**: {', '.join(selected_project.get('features', []))}\n"
                f"- **Tech Stack**: {selected_project.get('tech_stack')}\n\n"
                "## Mindset & Semantic Routing\n"
                "Analyze the user's intent semantically across messages:\n"
                "1. **Casual/General Chat**: Talk naturally and warmly. Do not force technical jargon, templates, or blueprint blocks.\n"
                "2. **Learning/Concept Q&A**: Explain clearly with code snippets and markdown formatting, focusing on the specific question.\n"
                "3. **Refining & Brainstorming**: Discuss ideas as a co-founder. Suggest features gradually and listen to feedback. Do not dump complete structures immediately.\n\n"
                "## Blueprint Block (Locking in Configuration)\n"
                "ONLY append the `<blueprint>` block at the very end of your message if the user has EXPLICITLY requested to save, finalize, update, or compile the project blueprint, OR if they agree on a specific feature set configuration. Otherwise, chat normally without any blocks.\n"
                "Format of the block when requested:\n"
                "<blueprint>\n"
                "{\n"
                "  \"name\": \"Updated Project Name\",\n"
                "  \"idea\": \"Core Idea/Description\",\n"
                "  \"features\": [\"Feature 1\", \"Feature 2\", \"Feature 3\"],\n"
                "  \"tech_stack\": \"Flask, HTML, CSS\",\n"
                "  \"category\": \"web\"  // 'web', 'agent', 'mobile', or 'backend'\n"
                "}\n"
                "</blueprint>"
            )
        else:
            system_prompt = (
                f"You are **Sarthi**, an expert AI development partner for the '{category}' domain. You adapt dynamically to the user's state of mind.\n\n"
                "## Your Role & Vibe\n"
                "You are an empathetic, intelligent, and conversational co-pilot. Listen carefully, analyze the user's mindset, and build context step-by-step over the chat history.\n\n"
                "## Mindset & Semantic Routing\n"
                "Analyze the user's intent semantically across messages:\n"
                "1. **Casual/General Chat**: Talk naturally, enthusiastically, and warmly. Do not force templates or project planning.\n"
                "2. **Learning/Concept Q&A**: Provide clear, direct, and well-commented code snippets with concise explanations.\n"
                "3. **Brainstorming Project Ideas**: Engage in active, friendly brainstorming. Suggest 1-2 creative directions rather than overloading the user. Build on their ideas.\n\n"
                "## Blueprint Block (Locking in Configuration)\n"
                "ONLY append the `<blueprint>` block at the very end of your message if the user has EXPLICITLY requested to finalize, save, or compile a project blueprint. Do NOT output this block for greetings, casual chat, brainstorming, or normal Q&A.\n"
                "Format of the block when requested:\n"
                "<blueprint>\n"
                "{\n"
                "  \"name\": \"Project Name\",\n"
                "  \"idea\": \"Core Idea/Description\",\n"
                "  \"features\": [\"Feature 1\", \"Feature 2\", \"Feature 3\"],\n"
                "  \"tech_stack\": \"Flask, HTML, CSS\",\n"
                "  \"category\": \"web\"  // 'web', 'agent', 'mobile', or 'backend'\n"
                "}\n"
                "</blueprint>"
            )
        
        chat_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            chat_messages.append({"role": role, "content": msg["text"]})

        async for chunk in stream_raw_llm_completion(
            agent_name="ChatReply",
            messages=chat_messages,
            temperature=0.7,
            max_tokens=2048
        ):
            yield chunk
    except Exception as e:
        # Yield fallback reply
        fallback = get_fallback_chat_reply(category, messages[-1]["text"] if messages else "", selected_project)
        yield fallback



async def auto_identify_category(blueprint: dict, messages: List[Dict[str, str]]) -> str:
    """
    Analyze the project blueprint and chat conversation history to identify the most fitting category:
    'startup', 'finance', 'health', 'education', 'productivity', 'sustainability', or 'other'.
    """
    try:
        # Format conversation context
        conv_text = ""
        for m in messages[-8:]:
            sender = m.get("sender", "user")
            text = m.get("text", "")
            conv_text += f"{sender.capitalize()}: {text}\n"

        blueprint_text = json.dumps(blueprint, indent=2, default=str)

        prompt = (
            "You are Sarthi's category classification assistant.\n"
            "Given the following project blueprint details and recent chat conversation history, "
            "classify the project into exactly one of these 7 categories:\n"
            "'startup', 'finance', 'health', 'education', 'productivity', 'sustainability', 'other'.\n\n"
            f"Blueprint Context:\n{blueprint_text}\n\n"
            f"Conversation History:\n{conv_text}\n\n"
            "Reply with ONLY the category name in lowercase, with no punctuation or additional text. Example: finance"
        )

        chat_messages = [
            {"role": "system", "content": "You are a precise classifier. Return only one of the allowed category words in lowercase."},
            {"role": "user", "content": prompt}
        ]

        reply = await get_llm_completion(
            agent_name="CategoryClassifier",
            messages=chat_messages,
            temperature=0.1,
            max_tokens=10
        )
        category = reply.strip().lower()
        allowed_categories = {"startup", "finance", "health", "education", "productivity", "sustainability", "other"}
        if category in allowed_categories:
            return category
    except Exception as e:
    
    # Simple keyword fallback detection
        pass
    idea_text = (blueprint.get("idea") or "").lower()
    name_text = (blueprint.get("name") or "").lower()
    combined = f"{name_text} {idea_text}"
    if any(k in combined for k in ["startup", "saas", "mvp", "pitch", "business", "product", "client", "customer", "revenue", "monetize", "funding", "marketing", "b2b"]):
        return "startup"
    if any(k in combined for k in ["finance", "budget", "money", "invest", "crypto", "stock", "wallet", "expense", "transaction", "pay", "payment", "bank", "saving", "tax"]):
        return "finance"
    if any(k in combined for k in ["health", "wellness", "fitness", "gym", "workout", "routine", "exercise", "breath", "meditat", "doctor", "medical", "diet", "food", "nutrition", "sleep"]):
        return "health"
    if any(k in combined for k in ["education", "learn", "study", "quiz", "course", "school", "teach", "note", "flashcard", "memory", "repetition", "student", "class", "practice"]):
        return "education"
    if any(k in combined for k in ["productivity", "task", "todo", "schedule", "calendar", "timeline", "manage", "organize", "time", "focus", "work", "efficient", "habit"]):
        return "productivity"
    if any(k in combined for k in ["sustainability", "carbon", "eco", "green", "recycle", "nature", "emission", "climate", "environment", "waste", "energy", "solar"]):
        return "sustainability"
    
    return "other"

def inject_boilerplate_files(codebase: List[Dict[str, Any]], project_name: str, architecture_context: dict = None) -> List[Dict[str, Any]]:
    project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
    existing_paths = {f.get("path") for f in codebase}
    
    # 1. backend/requirements.txt
    if "backend/requirements.txt" not in existing_paths and "requirements.txt" not in existing_paths:
        codebase.append({
            "name": "requirements.txt",
            "path": "backend/requirements.txt",
            "language": "plaintext",
            "content": (
                "fastapi>=0.100.0\n"
                "uvicorn[standard]>=0.22.0\n"
                "motor>=3.1.0\n"
                "pymongo>=4.3.3\n"
                "pydantic>=2.0\n"
                "python-jose[cryptography]>=3.3.0\n"
                "passlib[bcrypt]>=1.7.4\n"
                "python-multipart>=0.0.6\n"
                "google-genai>=0.1.0\n"
                "pymupdf>=1.22.0\n"
                "pillow>=9.5.0\n"
                "python-dotenv>=1.0.0\n"
            )
        })

    # 2. backend/app/main.py (FastAPI core backend)
    if "backend/app/main.py" not in existing_paths and "app.py" not in existing_paths:
        endpoints = []
        entities = []
        if architecture_context:
            api_arch = architecture_context.get("api_architecture") or {}
            endpoints = api_arch.get("endpoints", [])
            if not endpoints:
                api_impl = architecture_context.get("api_implementation") or {}
                endpoints = api_impl.get("endpoints", [])
            
            db_arch = architecture_context.get("db_architecture") or {}
            entities = db_arch.get("entities", [])
            if not entities:
                db_model = architecture_context.get("database_model_generation") or {}
                entities = db_model.get("entities", [])

        # Build FastAPI routes
        routes_code = []
        added_paths = set()
        
        for ep in endpoints:
            if not isinstance(ep, dict):
                continue
            path = ep.get("path", "")
            method = ep.get("method", "GET").upper()
            desc = ep.get("description", "Sarthi API route.")
            if not path or (path, method) in added_paths:
                continue
            added_paths.add((path, method))
            
            func_name = path.strip("/").replace("/", "_").replace("{", "").replace("}", "").replace("-", "_").replace(".", "_")
            func_name = f"{method.lower()}_{func_name}" if func_name else f"{method.lower()}_root"
            
            # Map parameters in FastAPI path format
            fastapi_path = path
            
            if method in ["POST", "PUT"]:
                routes_code.append(
                    f"# {desc}\n"
                    f"@router.{method.lower()}('{fastapi_path}')\n"
                    f"async def {func_name}(payload: dict = None, db = Depends(get_db)):\n"
                    f"    payload = payload or {{}}\n"
                    f"    return {{\"status\": \"success\", \"message\": \"Processed {path} successfully\", \"data\": payload}}\n"
                )
            else:
                routes_code.append(
                    f"# {desc}\n"
                    f"@router.{method.lower()}('{fastapi_path}')\n"
                    f"async def {func_name}(db = Depends(get_db)):\n"
                    f"    return {{\"status\": \"success\", \"message\": \"Fetched data from {path}\"}}\n"
                )
            
        if not routes_code and entities:
            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                ent_name = ent.get("entity_name", "Item")
                ent_lower = ent_name.lower()
                
                routes_code.append(
                    f"@router.get('/api/v1/{ent_lower}s')\n"
                    f"async def get_{ent_lower}s(db = Depends(get_db)):\n"
                    f"    cursor = db['{ent_lower}s'].find({{}})\n"
                    f"    items = await cursor.to_list(length=100)\n"
                    f"    for item in items: item['_id'] = str(item['_id'])\n"
                    f"    return {{\"status\": \"success\", \"{ent_lower}s\": items}}\n"
                )
                routes_code.append(
                    f"@router.post('/api/v1/{ent_lower}s')\n"
                    f"async def create_{ent_lower}(payload: dict, db = Depends(get_db)):\n"
                    f"    result = await db['{ent_lower}s'].insert_one(payload)\n"
                    f"    payload['_id'] = str(result.inserted_id)\n"
                    f"    return {{\"status\": \"success\", \"message\": \"{ent_name} created successfully.\", \"data\": payload}}\n"
                )

        if not routes_code:
            routes_code.append(
                "@router.get('/api/v1/health')\n"
                "async def health_check():\n"
                "    return {\"status\": \"healthy\", \"service\": \"" + project_name + "\"}\n"
            )

        routes_str = "\n".join(routes_code)
        
        main_py_content = f"""from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import fitz # PyMuPDF
from google import genai
from google.genai import types

app = FastAPI(title="{project_name} Production API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Client Initialization
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/app_db")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()

async def get_db():
    return db

router = APIRouter()

# Real Document Ingestion Endpoint using Gemini SDK & PyMuPDF
@router.post("/api/v1/documents/ingest")
async def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_bytes = await file.read()
    
    # Run heavy processing inside BackgroundTasks to avoid timeouts
    background_tasks.add_task(async_document_processing, file_bytes, file.filename)
    return {{"status": "processing", "message": "Document queued for background parsing and vector indexing"}}

async def async_document_processing(file_bytes: bytes, filename: str):
    try:
        # Extract text via PyMuPDF (fitz)
        text_content = ""
        if filename.endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_content = "\\n".join([page.get_text() for page in doc])
            
        # Parse using Gemini Pro
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and text_content:
            ai_client = genai.Client(api_key=api_key)
            response = ai_client.models.generate_content(
                model='gemini-2.5-pro',
                contents=f"Extract structured details from this doc:\\n{{text_content}}"
            )
            # Log results to MongoDB
            await db["ingested_documents"].insert_one({{
                "filename": filename,
                "parsed_text": text_content,
                "analysis": response.text,
                "status": "APPROVED" if "total" in response.text.lower() else "FLAGGED_FOR_REVIEW"
            }})
    except Exception as e:
        print(f"Async ingestion failed: {{e}}")

{routes_str}

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"""
        codebase.append({
            "name": "main.py",
            "path": "backend/app/main.py",
            "language": "python",
            "content": main_py_content
        })

    # 3. frontend/package.json
    if "frontend/package.json" not in existing_paths:
        codebase.append({
            "name": "package.json",
            "path": "frontend/package.json",
            "language": "json",
            "content": f"""{{
  "name": "{project_slug}-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }},
  "dependencies": {{
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "next": "^15.0.0",
    "lucide-react": "^0.300.0"
  }},
  "devDependencies": {{
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0"
  }}
}}"""
        })

    # 4. frontend/src/app/page.tsx
    if "frontend/src/app/page.tsx" not in existing_paths:
        codebase.append({
            "name": "page.tsx",
            "path": "frontend/src/app/page.tsx",
            "language": "typescript",
            "content": f"""'use client';

import React, {{ useState }} from 'react';
import {{ Play, CheckCircle, AlertTriangle, ShieldCheck, Database }} from 'lucide-react';

export default function Dashboard() {{
  const [healthResult, setHealthResult] = useState<string | null>(null);
  const [jsonText, setJsonText] = useState('{{"total_amount": 6200, "vendor": "Mock Vendor"}}');
  const [jsonError, setJsonError] = useState<string | null>(null);

  const checkHealth = async () => {{
    setHealthResult('Contacting backend...');
    try {{
      const res = await fetch('http://localhost:8000/api/v1/health');
      const data = await res.json();
      setHealthResult(JSON.stringify(data, null, 2));
    }} catch (err: any) {{
      setHealthResult(`Error: Failed to contact backend. Make sure FastAPI server is running on port 8000.`);
    }}
  }};

  const handleJsonChange = (text: string) => {{
    setJsonText(text);
    try {{
      JSON.parse(text);
      setJsonError(null);
    }} catch (e: any) {{
      setJsonError(`Invalid JSON format: ${{e.message}}`);
    }}
  }};

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      <header className="bg-white border-b border-slate-200/80 px-8 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-indigo-600 tracking-tight">{project_name}</h1>
        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full border border-emerald-100">Production Ready</span>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-white border border-slate-200/60 rounded-3xl p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Backend Health & API Status</h2>
            <p className="text-xs text-slate-500">FastAPI backend provides REST routes and database connections asynchronously.</p>
            <div className="flex gap-4">
              <button 
                onClick={{checkHealth}}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition-all cursor-pointer shadow-sm flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5" /> Run Backend Health Check
              </button>
            </div>
            {{healthResult && (
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto max-h-[200px]">
                {{healthResult}}
              </pre>
            )}}
          </div>

          <div className="bg-white border border-slate-200/60 rounded-3xl p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Secure JSON Validation Editor</h2>
            <textarea
              value={{jsonText}}
              onChange={{(e) => handleJsonChange(e.target.value)}}
              className="w-full h-32 bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            {{jsonError ? (
              <div className="flex items-center gap-1.5 text-xs text-rose-500 font-semibold bg-rose-50 border border-rose-100 p-3 rounded-xl">
                <AlertTriangle className="w-4 h-4" /> {{jsonError}}
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold bg-emerald-50 border border-emerald-100 p-3 rounded-xl">
                <ShieldCheck className="w-4 h-4" /> JSON format is fully valid.
              </div>
            )}}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200/60 rounded-3xl p-6 shadow-sm space-y-4 h-full flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Interactive Document Preview</h2>
              <p className="text-xs text-slate-500 mt-1">Native browser iframe renders live PDFs dynamically with toolbar suppression.</p>
              <div className="mt-4 border border-slate-150 rounded-2xl h-80 bg-slate-50 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-indigo-950/5 flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <Database className="w-8 h-8 text-indigo-500" />
                  <span className="text-xs text-slate-700 font-semibold">Native PDF/Doc Preview Stream</span>
                  <span className="text-[10px] text-slate-400 max-w-[240px]">Real PDF uploads are processed asynchronously via PyMuPDF and stored in MongoDB Atlas.</span>
                </div>
              </div>
            </div>
            
            <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
              <button className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-semibold rounded-xl">
                Reject Document
              </button>
              <button className="px-4 py-2 bg-indigo-950 hover:bg-indigo-900 text-white text-xs font-semibold rounded-xl">
                Approve & Index
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}}"""
        })

    # 5. docker-compose.yml
    if "docker-compose.yml" not in existing_paths:
        codebase.append({
            "name": "docker-compose.yml",
            "path": "docker-compose.yml",
            "language": "yaml",
            "content": f"""version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/sarthi_db
      - GEMINI_API_KEY=mock-api-key
    depends_on:
      - mongodb

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
"""
        })

    # 6. start.sh
    if "start.sh" not in existing_paths:
        codebase.append({
            "name": "start.sh",
            "path": "start.sh",
            "language": "bash",
            "content": (
                "#!/bin/bash\n"
                "echo \"Starting Sarthi Production Stack (FastAPI + React)...\"\n"
                "docker-compose up --build\n"
            )
        })

    # 7. start.bat
    if "start.bat" not in existing_paths:
        codebase.append({
            "name": "start.bat",
            "path": "start.bat",
            "language": "batch",
            "content": (
                "@echo off\n"
                "echo Starting Sarthi Production Stack (FastAPI + React)...\n"
                "docker-compose up --build\n"
                "pause\n"
            )
        })

    return codebase


async def generate_codebase(
    project_name: str, 
    category: str, 
    chat_history: List[Dict[str, str]], 
    theme: str = None,
    blueprint: dict = None,
    theme_palette: dict = None,
    architecture_context: dict = None,
    hackathon_metadata: dict = None,
    mcp_evidence: dict = None
) -> Dict[str, Any]:
    """
    Generate files for a project using Nvidia NIM.
    Should return a dictionary containing 'summary' and 'codebase' (list of CodeFiles).
    """
    start_time = time.perf_counter()
    context = "\n".join([f"{m['sender'].upper()}: {m['text']}" for m in chat_history])
    if not (settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or settings.OPENROUTER_API_KEY or settings.NVIDIA_API_KEY):
        return get_fallback_codebase(project_name, category, theme, blueprint, theme_palette, architecture_context, hackathon_metadata, mcp_evidence)

    blueprint_prompt = ""
    if blueprint:
        blueprint_prompt = f"\n\nConfirmed Project Blueprint (JSON):\n{json.dumps(blueprint, indent=2, default=str)}"

    theme_palette_prompt = ""
    if theme_palette:
        theme_palette_prompt = f"\n\nSelected Theme Palette (JSON):\n{json.dumps(theme_palette, indent=2, default=str)}"

    theme_prompt = f"\nThe user selected the design theme: '{theme}'. Please apply this theme's color palette, design styles, and dark/light configuration in the styling of the generated components using Tailwind CSS classes." if theme else ""

    architecture_context_prompt = ""
    if architecture_context:
        compiled_context = build_compilation_context(architecture_context)
        architecture_context_prompt = (
            "\n\nConnected Sarthi Agent Architecture Context (compact JSON):\n"
            f"{json.dumps(compiled_context, indent=2, default=str)}"
        )

    hackathon_prompt = ""
    if hackathon_metadata:
        hackathon_prompt = f"\n\nHackathon Metadata & Constraints:\n{json.dumps(hackathon_metadata, indent=2, default=str)}"

    mcp_prompt = ""
    if mcp_evidence:
        mcp_prompt = f"\n\nMCP Evidence Data:\n{json.dumps(mcp_evidence, indent=2, default=str)}"

    db_name = "MongoDB"
    if architecture_context:
        db_arch = architecture_context.get("db_architecture", {}) or {}
        db_strat = db_arch.get("database_strategy", {}) or {}
        primary_db = db_strat.get("primary_database")
        if primary_db:
            db_name = primary_db

    if db_name.lower() in ["postgresql", "postgres", "sqlite", "mysql", "mariadb", "sql"]:
        db_instructions = (
            f"- Use {db_name} as the relational database. Use SQLAlchemy (or SQLModel) declarative base models with async engine mappings.\n"
            f"- Include real {db_name} connection client code using SQLAlchemy and appropriate async drivers (e.g., asyncpg for PostgreSQL, aiosqlite for SQLite).\n"
            f"- Do NOT use MongoDB queries or syntax; use standard SQL or ORM operations."
        )
        reqs_example = "fastapi\\nuvicorn\\nsqlalchemy\\nasyncpg\\naiosqlite\\npydantic\\npython-jose[cryptography]\\npasslib[bcrypt]\\ngoogle-genai\\npython-multipart\\npython-dotenv"
    else:
        db_instructions = (
            "- Use MongoDB as the document database. Include real MongoDB connection client code using motor.\n"
            "- Do not use MongoDB `$search` since it is not supported on standard local MongoDB docker instances. For local search, use `$text` or standard regex queries, or use `$vectorSearch` with Atlas embeddings if and only if Atlas is configured."
        )
        reqs_example = "fastapi\\nuvicorn\\nmotor\\npydantic\\npython-jose[cryptography]\\npasslib[bcrypt]\\ngoogle-genai\\npython-multipart\\npython-dotenv"

    prompt = f"""
You are Sarthi AI compiler. You need to generate a high-fidelity production-ready codebase for a project using FastAPI (Python) for the backend and React/Next.js (TypeScript) for the frontend, with {db_name} as the database.
Project Name: {project_name}
Category: {category}{theme_prompt}{blueprint_prompt}{theme_palette_prompt}{architecture_context_prompt}{hackathon_prompt}{mcp_prompt}
Context/Chat History:
{context}

Generate a complete, fully functional, multi-file codebase structure separating backend (FastAPI) and frontend (Next.js/React).
Honor the Connected Sarthi Agent Architecture Context as the source of truth:
- Create backend files in `backend/` directory (e.g., `backend/requirements.txt`, `backend/app/main.py`, `backend/app/database.py`, `backend/app/models.py`, routes, etc.).
- Create frontend files in `frontend/` directory (e.g., `frontend/package.json`, `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, components, utilities).
- Use declared entities, endpoints, pages, theme tokens, auth rules, and validation notes when present.
- Keep names consistent across README, requirements, components, and routes.
- Implement JWT authentication verification and role checks where required.
{db_instructions}
- Include a real PDF viewer panel component and a secure JSON editor with client-side validation on the frontend.
- When generating backend endpoints that call Gemini, use the new official `google-genai` SDK and call a valid, existing model like `gemini-2.5-flash` or `gemini-2.5-pro` (DO NOT use deprecated `google-generativeai` or fake models like `gemini-3.5-flash`). Example:
  ```python
  from google import genai
  client = genai.Client()
  response = client.models.generate_content(model="gemini-2.5-flash", contents="...")
  ```
- Ensure the frontend connects to the backend API endpoints (with authentication headers where required) instead of using static placeholder data.
- Ensure there is an auth UI/page (like `/login` and `/signup` routes or modals) on the frontend that obtains the JWT token and uses it to authenticate subsequent API calls.

Return your output ONLY as a valid JSON object. Do not include markdown code block syntax (like ```json ... ```). Just return the raw JSON.
The JSON must follow this exact schema:
{{
  "summary": "A concise paragraph describing what the project does, key features, and instructions on how to use it.",
  "codebase": [
    {{
      "name": "README.md",
      "path": "README.md",
      "language": "markdown",
      "content": "# MarkDown content here..."
    }},
    {{
      "name": "requirements.txt",
      "path": "backend/requirements.txt",
      "language": "plaintext",
      "content": "{reqs_example}"
    }},
    {{
      "name": "main.py",
      "path": "backend/app/main.py",
      "language": "python",
      "content": "Full FastAPI application with routing, database client setup and routers..."
    }},
    {{
      "name": "package.json",
      "path": "frontend/package.json",
      "language": "json",
      "content": "Next.js frontend package.json dependencies..."
    }},
    {{
      "name": "page.tsx",
      "path": "frontend/src/app/page.tsx",
      "language": "typescript",
      "content": "Fully functional React page rendering the dashboard and fetching backend API data..."
    }}
  ]
}}

Generate at least 5 files including: README.md, backend/requirements.txt, backend/app/main.py, frontend/package.json, and frontend/src/app/page.tsx. Make sure the files are fully integrated and provide a cohesive, complete, functioning application without any TODO comments.
"""
    try:
        content = await get_llm_completion(
            agent_name="CodebaseCompiler",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Sarthi's final compiler. Generate cohesive FastAPI (Python) backend files "
                        "and React/Next.js (TypeScript) frontend files from the chat, blueprint, selected theme, and connected architecture-agent context. "
                        "Return only valid JSON."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=6000
        )
        raw_content = content.strip()
        # Strip code blocks if LLM included them despite instructions
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
            
        data = json.loads(raw_content)
        duration = time.perf_counter() - start_time
        
        # Structured terminal logging
        for f in data.get('codebase', []):
        
            pass
        if "summary" in data and "codebase" in data:
            data["codebase"] = inject_boilerplate_files(data["codebase"], project_name, architecture_context)
            return data
        else:
            raise ValueError("Invalid JSON structure returned by NIM model")
    except Exception as e:
        duration = time.perf_counter() - start_time
        return get_fallback_codebase(project_name, category, theme, blueprint, theme_palette, architecture_context)

FALLBACK_PROJECTS = {
    "startup": [
        {
            "name": "SaaS Growth CRM & Lead Engager",
            "idea": "A comprehensive B2B lead management and pipeline engagement platform tailored for early-stage startups. It centralizes customer communications, optimizes sales pipelines with real-time status reporting, handles dynamic contact action queues, and automates email sequence workflows to maximize user acquisition efficiency.",
            "features": [
                "Interactive Kanban Sales Pipeline: Drag-and-drop opportunity cards with instant value aggregates.",
                "Automated Outreach Sequence Builder: Configure multi-step email cadences triggered by client sign-up states.",
                "Realtime Notification Center: Pushes browser alerts whenever high-value leads perform target page events.",
                "Customer Activity Timeline: Chronological audit log tracking touchpoints, meetings, and support tickets.",
                "Growth Metrics Graph Dashboard: Analytics widget summarizing MRR, Churn Rate, LTV, and CAC inputs."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand Stores, FastAPI Backend, MongoDB Database, Redis Caching"
        },
        {
            "name": "AI-Powered Slide Deck Architect",
            "idea": "An interactive slide deck planner and narrative builder that leverages generative intelligence to structure business proposals. It parses raw product descriptions, configures responsive visual templates, maps slide-by-slide hierarchies, and provides AI content assistant widgets to bootstrap startup investor pitches.",
            "features": [
                "Markdown-to-Slide Compiler: Automatically transform bulleted outlines into structured slide layout blocks.",
                "Drag-and-Drop Narrative Sequencer: Rearrange pitch modules with auto-saving state validation.",
                "Nvidia NIM AI Copilot Sidebar: Real-time contextual content suggestions and copy improvements.",
                "Responsive Layout Previewer: Inspect presentation slides in mobile, tablet, and desktop aspect ratios.",
                "Universal JSON Export: Download clean schema metadata for custom player integrations."
            ],
            "tech_stack": "Next.js Framework, Tailwind CSS, Framer Motion, FastAPI Backend, SQLite relational storage, Nvidia NIM API"
        },
        {
            "name": "SaaS Billing & Metrics Aggregator",
            "idea": "A high-fidelity metrics dashboard built to track MRR growth and calculate transaction metrics. It offers mock Stripe integration, aggregates revenue numbers, provides scenario-modeling sandboxes, and logs churn rates to guide funding rounds and financial presentations.",
            "features": [
                "Simulated Stripe Sync Pipeline: Webhook listeners logging mock payment status upgrades.",
                "Scenarios Forecasting Sandbox: Interactive range sliders to simulate price adjustments impact on MRR.",
                "Financial PDF Report Exporter: Automated document generation detailing cash flow balances.",
                "Custom Alert Thresholds: Send webhook notifications when MRR milestones or churn rates cross set limits.",
                "Unified Cohort Retention Chart: Matrix representation of active subscribers over time."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Graphics, FastAPI, PostgreSQL Relational Database, Redis Broker"
        },
        {
            "name": "No-Code API Mocking & Webhook Server",
            "idea": "A modular visual backend designer that allows hackathon developers to configure mock JSON REST endpoints, simulate dynamic delay latency, inspect incoming OAuth bearer headers, and trigger test webhooks without writing server code.",
            "features": [
                "Visual Endpoint Constructor: Map HTTP methods to custom JSON response templates.",
                "Latency Simulator: Inject artificial delays to test client-side loading spinners.",
                "Incoming Request Log: Inspect header tokens and body structures in real-time."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Node.js Express, MongoDB, Socket.io"
        },
        {
            "name": "Subscription Optimizer & Churn Forecaster",
            "idea": "A simulation control panel designed for SaaS startups to model pricing tier impacts and churn risk. It aggregates active user profiles, evaluates usage indicators, predicts drop-off trends, and recommends target promo offers to retain subscribers.",
            "features": [
                "Pricing Scenarios Modeler: Simulates user conversion rates when shifting pricing tiers.",
                "Risk Analytics Engine: Flags accounts with declining login frequencies.",
                "Discount Promos Generator: Tailors promo discounts based on customer churn profiles."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Graphing, FastAPI, Python Scikit-learn"
        }
    ],
    "finance": [
        {
            "name": "Micro-Savings Companion",
            "idea": "An automated micro-deposit and financial goal ledger that securely saves transaction round-ups. It connects to mock banking data stream models, calculates residual change, and allocates fractional savings to specific long-term target goals via custom user rules.",
            "features": [
                "Automated Round-Up Engine: Multi-account ledger computing transaction margins for savings.",
                "Tiered Goal Allocation Framework: Split saved fractions across custom investment buckets dynamically.",
                "Interactive Savings Milestones: Visual progress ring with milestone badges and notification alerts.",
                "Smart Recurrence Scheduler: Form controllers defining daily, weekly, or monthly transfer rules.",
                "Projected Compound Calculator: Analytics forecasting growth trends over selectable year periods."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand Stores, Node.js Express, MongoDB, localForage storage"
        },
        {
            "name": "Crypto Asset Tracker & Modeler",
            "idea": "A real-time cryptocurrency portfolio tracker and scenario planning simulator. It maps active token holdings, fetches mock coin rates, logs transaction entries, and visualizes profits, losses, and historical values using interactive analytics widgets.",
            "features": [
                "Mock Pricing Live Simulator: Simulates fluctuations in coin valuations with connection heartbeat controls.",
                "Transaction Entry Ledger: Multi-currency records supporting buy, sell, transfer, and swap entries.",
                "Portfolio Allocation Charts: Interactive pie and radar graphs detailing asset distribution percentages.",
                "Price Threshold Webhook Alerts: Configure automatic notifications on sudden valuation shifts.",
                "Profit/Loss Projection Timeline: Historical performance curve chart tracking balance changes."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Library, Node.js Express, Redis cache stores, SQLite relational db"
        },
        {
            "name": "Split-Bill Ledger & Settlements",
            "idea": "A shared expense ledger utility built for group expense tracking and bill splitting. It logs shared payments, runs balance reconciliation math to minimize transfer loops, and manages transaction histories and reminder logs.",
            "features": [
                "Dynamic Split Ratio Calculator: Split bills by percentages, shares, or unequal item amounts.",
                "Optimized Balance Reconciler: Minimize transactions needed to settle debts across group members.",
                "Mock Settlement Payment Gate: Simulates immediate paybacks with instant state confirmation.",
                "Recurring Expense Scheduler: Creates recurring items for utility bills and shared subscriptions.",
                "Group Activity Ledger: Auditable chronology detailing added expenses and settlements."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, FastAPI Backend, PostgreSQL Relational Database, JWT middleware guards"
        },
        {
            "name": "AI Tax Planner & Deductions Locator",
            "idea": "An automated micro-tax tracker that monitors freelancer income and detects deductible business expenses. It parses digital transaction records, matches vendor categories against local tax guidelines, and aggregates year-end estimates.",
            "features": [
                "Receipt Text Parser: Extract vendor and totals from uploaded documents.",
                "Deduction Matching Engine: Flags tax write-off opportunities automatically.",
                "Estimated Quarterly Calculator: Forecasts federal and state tax liabilities in real-time."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Python Flask, PostgreSQL, Tesseract OCR"
        },
        {
            "name": "Gamified Investor Sandbox & Stock Simulator",
            "idea": "A risk-free investment learning dashboard built for amateur investors. It provides mock currency credentials, updates asset prices using simulated live feeds, tracks portfolio values, and hosts group leaderboard trading challenges.",
            "features": [
                "Paper Trading Sandbox: Buy and sell options using mock cash balances.",
                "Dynamic Market Simulator: Fluctuates stock valuations based on news sentiment indicators.",
                "Peer Leaderboard Challenges: Real-time competitor standings and reward badges."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts Graphics, Node.js Express, MongoDB"
        }
    ],
    "health": [
        {
            "name": "CalmPath Breathing Guide",
            "idea": "An interactive wellness application featuring a real-time paced breathing visualizer. It provides Inhale/Hold/Exhale guidance, tracks breathing sessions, logs stress indicators, and displays wellness trends on a modern dashboard to help users maintain mindfulness.",
            "features": [
                "Paced Breathing Ring: Expanding and contracting Framer Motion visualizer with customizable tempos.",
                "Stress Score Mood Logger: Form-based logger to record daily anxiety levels and write notes.",
                "Audio Guidance Synthesis: Dynamic sound tones playing in sync with breathing phase transitions.",
                "Weekly Wellness Analytics: Recharts line visualization charting logged stress scores over time.",
                "Local Session Cache: LocalStorage persistence allowing complete offline-first breathing guides."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Framer Motion, Zustand Stores, LocalStorage APIs"
        },
        {
            "name": "Hydration Tracker & Fluid Log",
            "idea": "A high-fidelity water intake tracker designed to optimize daily hydration goals. It sets custom targets based on body metrics, handles fluid logs, reminds users using in-app banners, and displays intake grids to visualize milestones.",
            "features": [
                "Fluid Logging Widget: Log water, tea, or coffee inputs with instant hydration multiplier calculations.",
                "Custom Intake Goal Configurator: Form computing recommended intake using user weight and activity logs.",
                "Hourly Reminder Notification Engine: Websocket-backed prompts driving in-app notifications.",
                "Intake History Calendar Grid: Grid visualization charting hydration performance over weeks.",
                "Interactive Water Milestone Badges: Gamified goals rewarding consistent compliance."
            ],
            "tech_stack": "Next.js SPA Mode, Tailwind CSS, localForage, Service Workers, FastAPI, PostgreSQL"
        },
        {
            "name": "Workout Routine Builder & Timer",
            "idea": "A modern workout customizer and interval countdown timer designed for training sessions. It allows users to build routine sets, customize rest buffers, manage timed countdown triggers, and review history logs on a unified user panel.",
            "features": [
                "Workout Plan Creator: Form builder supporting custom names, sets, reps, and time caps.",
                "Responsive Interval Timer: Clean visual countdown with audio alerts for workout and rest states.",
                "Exercise Library Manager: Customizable database of default card movements and guidelines.",
                "Performance History Analytics: Graph dashboards displaying active training duration averages.",
                "Active Share Sheet: Export workout routines as structured JSON configurations."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Node.js Express, MongoDB database"
        },
        {
            "name": "NutriLog Food Scanner & Macro Tracker",
            "idea": "A meal tracking assistant that helps users log food items and monitor macro goals. It uses mock photo scanner tools, evaluates nutrient densities, and visualizes weekly calorie balances.",
            "features": [
                "Appliance Macro Registry: Log protein, fat, and carb ratios easily.",
                "Daily Calorie Score: Live counts tracking consumption against base limits.",
                "Appliance Photo Simulator: Simulates image recognition to identify ingredients."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Node.js, MongoDB database"
        },
        {
            "name": "Sleep Phase Analyzer & Alarm Pacer",
            "idea": "A sleep hygiene logging dashboard and timed alarm controller. It tracks user-reported sleep stages, logs caffeine intake triggers, maps daily sleep efficiency scores, and suggests paced routines to optimize recovery.",
            "features": [
                "Sleep Quality Log: Form recording sleep duration and morning fatigue levels.",
                "Caffeine Decay Tracker: Calculates remaining caffeine levels in body based on time.",
                "Paced Wind-Down Guides: Timed notifications prompting screen-free habits."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, LocalStorage APIs, Recharts, Zustand Stores"
        }
    ],
    "education": [
        {
            "name": "Spaced Repetition Flashcards",
            "idea": "An interactive flashcard study assistant powered by spaced repetition learning models. It manages user-created study decks, logs retention scores, and schedules cards for review based on difficulty ratings to accelerate knowledge retention.",
            "features": [
                "Deck Builder & Card Editor: Rich-text card creator supporting markdown prompts and code blocks.",
                "Spaced Repetition Scheduler: Algorithm-driven scheduling queue displaying weaker cards more frequently.",
                "Interactive Quiz Workspace: Double-sided card flip animations with self-grading controls.",
                "Study Session Analytics: Progress bar charts logging daily card review counts and accuracy scores.",
                "Shared Study Pool: Search and import community-shared card decks from global repository structures."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Framer Motion, FastAPI Backend, MongoDB Database, Redis Cache"
        },
        {
            "name": "Pomodoro Focus Study Log",
            "idea": "A productivity dashboard combining Pomodoro work-break timers with task list tracking. It helps students partition study intervals, block distractions, log completed tasks, and view focus time metrics.",
            "features": [
                "Pomodoro Cycle Timer: Adjustable focus/short break/long break intervals with audio alarms.",
                "Focus Task Board: List management widget linking active tasks directly to the running timer.",
                "Daily Focus Log Chart: Recharts bar timeline tracking total daily focus minutes.",
                "In-App Distraction Shield: Configurable browser notifications block toggle during active sessions.",
                "Streak Milestone Tracker: Tracks consecutive study days with motivation prompts."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Zustand Stores, LocalStorage persistence"
        },
        {
            "name": "Skill Tree Learner & Roadmap",
            "idea": "A visual mapping application that structures educational subjects into interactive learning trees. It organizes complex topics into step-by-step nodes, tracks progress checkbox milestones, and suggests resources for each item.",
            "features": [
                "Interactive Skill Tree Graph: Visual Node Graph rendering dependent learning paths.",
                "Resources Database: Link resource tutorials, videos, and exercises to skill nodes.",
                "Concept Checkpoint Quizzes: In-app mini quizzes validating knowledge before unlocking nodes.",
                "Progress Milestone Tracker: Real-time progress bar computing overall subject completion.",
                "Custom Pathway Builder: Drag-and-drop node tool enabling teachers to design roadmaps."
            ],
            "tech_stack": "React Flow Library, Tailwind CSS, Framer Motion, FastAPI, SQLite Relational Database"
        },
        {
            "name": "Collaborative Study Lobby & Shared Notes",
            "idea": "A real-time workspace for study groups to share notes and solve quizzes. It provides shared markdown editors, syncs group study timer clocks, and aggregates collective study statistics.",
            "features": [
                "Shared Markdown Pad: Simultaneous group note editing with user markers.",
                "Group Focus Timer: Synchronized Pomodoro clock matching timers across group members.",
                "Peer Study Leaderboard: Logs total active study minutes per student group."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, WebSockets, Node.js Express, Redis cache stores"
        },
        {
            "name": "Code Quiz Sandbox & Technical Practice",
            "idea": "An interactive platform for learning programming syntax and core algorithms. It provides structured language challenges, compiles code inputs locally in-browser, and charts syntax accuracy over time.",
            "features": [
                "Code Sandbox Console: Write JavaScript or Python snippets inside a Monaco editor.",
                "Instant Syntax Validator: Client-side validator testing outputs against default conditions.",
                "Coding Streaks Tracker: Visual calendar grid displaying consecutive daily practice sessions."
            ],
            "tech_stack": "React Flow Library, Monaco Editor, Tailwind CSS, localForage storage"
        }
    ],
    "productivity": [
        {
            "name": "Milestone Board & Sprint Tracker",
            "idea": "A drag-and-drop project management board tailored for sprint tracking. It coordinates tasks across pipeline columns (To Do, In Progress, Review, Done), calculates progress bars, and filters tasks by priority and assignment metrics.",
            "features": [
                "Drag-and-Drop Task Columns: Interactive board mapping tasks to workflow columns.",
                "Sprint Milestone Calculator: Progress bar tracking completed story points vs target values.",
                "Resource Allocation Manager: Assign tasks to team members with workload balance checks.",
                "Project Activity Feed: Chronological stream logging drag updates and task completions.",
                "Task Priority Matrix: Color-coded tags filtering tasks by urgency and impact criteria."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand client stores, Node.js Express, MongoDB"
        },
        {
            "name": "Eisenhower Priority Matrix",
            "idea": "A task prioritizer utilizing the Eisenhower Matrix model. It organizes todos into four quadrants (Do First, Schedule, Delegate, Eliminate), supports drag re-ordering, and structures task checklists to maximize daily efficiency.",
            "features": [
                "Quadrant Visual Grid: Clean 2x2 grid representing urgent/important prioritization splits.",
                "Quick-Add Task Bar: Inline text field enabling immediate task addition to active quadrants.",
                "Task Archive Vault: Toggle panels displaying historical completed tasks by date.",
                "Daily Planning Prompts: Short morning alerts prompting users to clear Quadrant 4 tasks.",
                "State Recovery Engine: Auto-saving data layers preventing data loss on window closes."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Framer Motion, LocalStorage APIs, React Context"
        },
        {
            "name": "Standup Notes & Hook Builder",
            "idea": "A team coordination portal that captures daily standup notes and triggers notification hooks. It logs yesterday's accomplishments, today's goals, and active blockers, and supports exporting logs to team channels.",
            "features": [
                "Standup Template Form: Text areas structured for completed tasks, goals, and blockers.",
                "Mock Slack Webhook Trigger: Simulate publishing formatted logs to team channels.",
                "Historical Standup Ledger: Database tracking past standup submissions by team members.",
                "Active Blockers Dashboard: Banner panel highlighting critical issues blocking progress.",
                "Clipboard Copy Formatter: Format updates as clean markdown bullet points for quick copies."
            ],
            "tech_stack": "Next.js SPA, Tailwind CSS, FastAPI Backend, SQLite relational storage, Redis pub/sub"
        },
        {
            "name": "Digital Habit Builder & Streak Ledger",
            "idea": "A habit formation assistant that logs daily checklists and tracks streaks. It allows users to set daily habits, configure notification reminders, and visualize check-in frequencies.",
            "features": [
                "Habit Check-In List: Simple list of daily tasks with checkbox completions.",
                "Streak Calendar Matrix: Visualizes consecutive check-in streaks over months.",
                "Appliance Webhook Hooks: Integrates with custom webhook routes on habit completions."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Zustand client stores, LocalStorage persistence"
        },
        {
            "name": "Meeting Minutes Summarizer & Task Finder",
            "idea": "An interactive coordination board that organizes team meeting transcripts and highlights task items. It takes raw meeting inputs, highlights key takeaways, and creates todo task cards.",
            "features": [
                "Transcript Text Parser: Extracts bulleted action items from transcripts.",
                "Action Tasks Exporter: Single click button creating workspace board tickets.",
                "Meeting Outcomes Dashboard: Displays meeting summaries, dates, and organizers."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, FastAPI, SQLite relational db"
        }
    ],
    "sustainability": [
        {
            "name": "Carbon Calculator & Offset Log",
            "idea": "A sustainability calculator that computes commuting carbon footprints and logs offset activities. It guides users through daily transport inputs, performs carbon math, and lists eco-friendly actions to balance emissions.",
            "features": [
                "Commuting Footprint Slider: Interactive commuter forms computing CO2 emissions instantly.",
                "Carbon Offset Catalog: Directory detailing offset actions like planting trees or recycling.",
                "Monthly Carbon Breakdown Chart: Recharts pie representation displaying emissions by source.",
                "Community Green Leaderboard: Gamified standings page tracking offset scores.",
                "Eco-Tips Recommendation Engine: Tailored notification cards prompting custom energy saving guides."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Recharts, FastAPI Backend, MongoDB Database, JWT auth"
        },
        {
            "name": "Waste Sorting & Recycling Guide",
            "idea": "An educational guide identifying recyclable, compostable, and trash items. It features a fast fuzzy-matching catalog search, displays detailed item sheets with disposal rules, and lists nearby center drop-offs.",
            "features": [
                "Fuzzy Material Search Bar: Real-time filter sorting items by material composition.",
                "Item Classification Details: Visual detail cards detailing local sorting regulations.",
                "Mock Recycling Centers Map: Mapbox dashboard displaying nearby collection points.",
                "Custom Disposal Checklist: In-app organizer helping users log waste sorting events.",
                "Sorting Milestone Badges: Digital rewards for logging correct sorting practices."
            ],
            "tech_stack": "Next.js SPA, Tailwind CSS, Mapbox GL UI, SQLite Database, FastAPI Backend"
        },
        {
            "name": "Energy Saver Utility Hub",
            "idea": "A smart home utility logger that monitors appliance power consumption and computes energy scores. It tracks appliance ratings, charts daily usage history, and suggests optimization steps to lower carbon outputs.",
            "features": [
                "Appliance Power Registry: Form tracker logging appliances and wattage rates.",
                "Usage Duration Log: Time inputs recording hourly appliance activation stats.",
                "Daily Energy Score: Algorithm computing household efficiency ratings out of 100.",
                "Consumptions Column Chart: Recharts columns charting power usage patterns by hour.",
                "Smart Saving Workflows: Push notifications prompting users to turn off heavy appliances."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, ChartJS, Node.js Express, MongoDB, Redis cache"
        },
        {
            "name": "Local Farmers Market Locator & Eco-Shop",
            "idea": "A directory and map visualizer for local farmers markets and eco-friendly shops. It features category sorting, drop-off guidelines, and catalogs seasonal local produce items.",
            "features": [
                "Eco Map Dashboard: Visual Mapbox dashboard displaying farmers market pins.",
                "Seasonal Produce Guide: Matrix grid highlighting local fruits/veggies in season.",
                "Green Shop Reviews: Community reviews detailing sustainable shop practices."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Mapbox GL UI, FastAPI, PostgreSQL"
        },
        {
            "name": "Water Conservation Monitor & Audit",
            "idea": "An indoor water tracking application that logs household water consumption and schedules audit checks. It tracks appliance water flows, suggests conservation steps, and logs leak alerts.",
            "features": [
                "Appliance Flow Registry: Log kitchen, bathroom, and garden water usage inputs.",
                "Consumptions Column Chart: Visualizes water use patterns by day and source.",
                "Conservation Checklist: Interactive tasks detailing steps to lower home water bills."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, Recharts, FastAPI Backend, MongoDB Database"
        }
    ],
    "other": [
        {
            "name": "API Sandbox & JSON Console",
            "idea": "An interactive API tester and JSON syntax formatter. It allows developers to configure mock requests, test status outputs, format payloads, and inspect authorization headers in a unified web console.",
            "features": [
                "Request Builder Console: Input URL, select HTTP verbs, and write JSON payloads.",
                "Status Code Mock Selector: Test response renderings for success, validation, and auth error states.",
                "Monaco JSON Code Editor: Code console with syntax checks and formatting tools.",
                "Headers Inspection Panel: Check authorization tokens and response metadata in tab views.",
                "Mock API Endpoints Pool: Simulated responses dashboard for testing client fetch functions."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Monaco Editor, Express, LocalStorage APIs"
        },
        {
            "name": "WebSocket Mock Loopback Chat",
            "idea": "A local chat client simulating server loopbacks using client-side WebSockets. It enables testing group channel joins, chat history rendering, message dispatching, and connection status alerts.",
            "features": [
                "Active Channel Sidebar: Switch workspaces and group chat channels dynamically.",
                "Message Box Scroll View: Automatic auto-scroll messaging interface with sender tags.",
                "Status Connection Banner: Displays connection state changes (connecting, active, closed).",
                "Loopback Message Simulator: Automatically responds with simulated AI answers."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, WebSockets, Node.js, Redis cached logs"
        },
        {
            "name": "Custom SVG Icons Editor & Code Compiler",
            "idea": "An interactive SVG graphics editor and path compiler. It allows users to write custom SVG paths, adjust viewbox dimensions, inspect raw node hierarchies, and compile optimized XML code formats.",
            "features": [
                "Interactive Path Canvas: Render path edits dynamically with grid overlays.",
                "SVG Node Tree Inspector: View tag hierarchies in collapsible tree panels.",
                "Code Export Dialog: Quick copy options for React, Vue, or raw SVG formats."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Monaco Editor, LocalStorage APIs"
        },
        {
            "name": "Markdown Blog Compiler & Static Previewer",
            "idea": "A lightweight static markdown compiler designed for writers. It supports writing posts in markdown syntax, renders preview blocks in real-time, and generates static HTML package exports.",
            "features": [
                "Markdown Split-Screen Editor: Synchronized editor and markdown renderer views.",
                "Blog Metadata Configurator: Form editor defining tags, authors, and cover image files.",
                "Static Package Bundle Builder: Download static HTML/CSS template assets as a ZIP."
            ],
            "tech_stack": "React (Vite SPA), Tailwind CSS, Node.js Express, localForage"
        },
        {
            "name": "Local Host DNS Mock & Redirect Panel",
            "idea": "A local host routing manager and mockup portal. It configures target redirects, matches paths against local mock services, and prints debugging log streams.",
            "features": [
                "Redirect Router Table: Add source domain and redirect target address rows.",
                "Path Matcher Engine: Custom regex matching rules for dynamic endpoint URLs.",
                "Active Traffic Logs: Scroll view console detailing routed request methods and timestamps."
            ],
            "tech_stack": "TypeScript, Tailwind CSS, React Context, Node.js, SQLite"
        }
    ]
}

def parse_json_array_response(raw_content: str) -> List[Any]:
    raw_content = raw_content.strip()
    
    # Extract candidate block between first '[' and last ']'
    start_idx = raw_content.find("[")
    end_idx = raw_content.rfind("]")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = raw_content[start_idx:end_idx+1]
    else:
        cleaned = raw_content
        
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
        
    # Attempt json_repair
    try:
        from json_repair import repair_json
        repaired = repair_json(cleaned, return_objects=True)
        if isinstance(repaired, list):
            return repaired
    except Exception:
        pass
        
    raise ValueError("Failed to parse valid JSON array from raw content")

async def generate_project_suggestions(category: str) -> List[Dict[str, Any]]:
    """
    Generate exactly 5 project suggestions in JSON format using Nvidia NIM / Google fallback,
    or fall back to the structured fallback lists.
    """
    category_lower = category.lower()
    if not (settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or settings.OPENROUTER_API_KEY or settings.NVIDIA_API_KEY):
        return FALLBACK_PROJECTS.get(category_lower, FALLBACK_PROJECTS["other"])
    
    prompt = f"""
You are Sarthi, an expert AI partner. Generate exactly 5 project suggestions for a hackathon under the category '{category}'.
Each suggestion must represent a detailed blueprint that can flow cleanly through Sarthi's connected agent pipeline.
For each suggestion, provide:
1. name (Project Name)
2. idea (A concise description of the application's vision - between 40 to 60 words)
3. features (List of descriptive system features/modules - generate as many as necessary to cover the project's requirements, minimum 3 - under 25 words each)
4. tech_stack (Suggested Tech Stack, e.g. "React, Tailwind CSS, FastAPI, MongoDB")

CRITICAL: Return your output ONLY as a valid JSON array of objects.
- NO trailing commas.
- Escape all quotes inside strings.
- Do not wrap in markdown code blocks. Just raw JSON.
The JSON must match this structure exactly:
[
  {{
    "name": "Project Name",
    "idea": "Concise core idea description...",
    "features": [
      "Feature 1 description...",
      "Feature 2 description...",
      "Feature 3 description..."
    ],
    "tech_stack": "React, FastAPI, MongoDB"
  }}
]
"""
    try:
        content = await get_llm_completion(
            agent_name="ProjectSuggestions",
            messages=[
                {
                    "role": "system",
                    "content": "You are Sarthi's blueprint ideation agent. You must output ONLY strict, valid JSON. No conversational text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        data = parse_json_array_response(content)
        if isinstance(data, list) and len(data) > 0:
            return data
        else:
            raise ValueError("Invalid suggestions format returned by model")
    except Exception as e:
        return FALLBACK_PROJECTS.get(category_lower, FALLBACK_PROJECTS["other"])

async def generate_single_project_suggestion(idea: str, generation_type: str = "full_stack") -> Dict[str, Any]:
    """
    Generate a single project suggestion/blueprint in JSON format based on user's custom idea and scope.
    """
    if not (settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or settings.OPENROUTER_API_KEY or settings.NVIDIA_API_KEY):
        # Local fallback if no LLM key, tailored to scope
        if generation_type == "frontend_only":
            return {
                "name": "Custom Frontend Prototype",
                "idea": f"[Frontend Only] {idea}",
                "features": [
                    "High-fidelity interactive UI with responsive layout",
                    "Client-side state management & local mock data integration",
                    "Polished glassmorphism dashboard and widgets"
                ],
                "tech_stack": "React, Tailwind CSS, Lucide Icons, Framer Motion"
            }
        elif generation_type == "backend_only":
            return {
                "name": "Custom Backend Core",
                "idea": f"[Backend Only] {idea}",
                "features": [
                    "RESTful API design with clean endpoint routing",
                    "Pydantic data schemas and strict validation rules",
                    "Database integration with robust repository patterns"
                ],
                "tech_stack": "FastAPI, Python, Pydantic, PostgreSQL, SQLAlchemy"
            }
        elif generation_type == "microservice":
            return {
                "name": "Custom Microservice Engine",
                "idea": f"[Microservice] {idea}",
                "features": [
                    "Ultra-lightweight API service or async background worker",
                    "High-performance message broker queue with Redis",
                    "Dockerized infrastructure container with built-in health-checks"
                ],
                "tech_stack": "FastAPI, Redis, Celery, Docker, Pydantic"
            }
        else:
            return {
                "name": "Custom Full Stack App",
                "idea": idea,
                "features": [
                    "Interactive React frontend with responsive glassmorphism modules",
                    "High-performance FastAPI backend server supporting endpoints",
                    "Secure database management with streamlined schemas"
                ],
                "tech_stack": "React, Tailwind CSS, FastAPI, MongoDB"
            }

    scope_guidance = ""
    if generation_type == "frontend_only":
        scope_guidance = (
            "CRITICAL: The generation scope is FRONTEND ONLY. No real backend exists. "
            "Focus completely on modern, highly interactive UI features, client-side React logic, local mock data state, and sleek user experience aesthetics. "
            "The suggested tech_stack must be purely frontend focused (e.g. React, Tailwind CSS, etc.)."
        )
    elif generation_type == "backend_only":
        scope_guidance = (
            "CRITICAL: The generation scope is BACKEND ONLY. No frontend UI exists. "
            "Focus completely on server-side architecture, robust RESTful APIs, request-response schemas, database management, and service layers. "
            "The suggested tech_stack must be purely backend focused (e.g. FastAPI, PostgreSQL, etc.)."
        )
    elif generation_type == "microservice":
        scope_guidance = (
            "CRITICAL: The generation scope is MICROSERVICE. It is a highly-focused backend-only service or background worker. "
            "Focus on lightweight endpoints, message queues (Redis/Celery), high performance, single-responsibility logic, API endpoints, and containerized deployment structures. "
            "The suggested tech_stack must be suited for a microservice (e.g. FastAPI, Redis, Celery, Docker, etc.)."
        )
    else:
        scope_guidance = (
            "The generation scope is FULL STACK. Deliver both a modern, interactive web frontend dashboard "
            "and a robust server-side REST API/backend."
        )

    prompt = f"""
You are Sarthi, an expert AI partner. The user wants to build a project with this core idea: "{idea}".
{scope_guidance}

Create a detailed project blueprint matching this idea. Generate exactly:
1. name (A catchy, highly unique, innovative, and creative Project Name. Do NOT use generic names like 'Taskflow', 'Trackify', 'Personal Finance App', 'Travel Planner'. Brainstorm something distinct and premium.)
2. idea (A refined, professional, and detailed description of the application's vision - between 40 to 60 words)
3. features (List of highly detailed system features/modules matching the selected scope. Generate as many as necessary to cover the project's requirements, minimum 4. Each feature should have a detailed explanation of its function and value - under 25 words each.)
4. tech_stack (Suggested Tech Stack, matching the selected scope, e.g. "React, Tailwind CSS, FastAPI, MongoDB" for full stack, "React, Tailwind CSS, Framer Motion" for frontend, "FastAPI, PostgreSQL, SQLAlchemy" for backend, "FastAPI, Redis, Celery, Docker" for microservice)

CRITICAL: Return your output ONLY as a valid JSON object.
- NO trailing commas.
- Escape all quotes inside strings.
- Do not wrap in markdown code blocks. Just raw JSON.
The JSON must match this structure:
{{
  "name": "Project Name",
  "idea": "Refined core idea description...",
  "features": [
    "Feature description 1...",
    "Feature description 2..."
  ],
  "tech_stack": "React, FastAPI, MongoDB"
}}
"""
    try:
        content = await get_llm_completion(
            agent_name="ProjectSuggestions",
            messages=[
                {
                    "role": "system",
                    "content": "You are Sarthi's blueprint ideation agent. You must output ONLY strict, valid JSON. No conversational text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        raw_content = content.strip()
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
        
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as decode_err:
            try:
                repaired = raw_content.rstrip(", \n\t")
                if not repaired.endswith('"') and not repaired.endswith('}') and not repaired.endswith(']'):
                    repaired += '"'
                if not repaired.endswith('}'):
                    repaired += '}'
                data = json.loads(repaired)
            except Exception:
                raise ValueError(f"Could not parse JSON. Original error: {decode_err}")

        if isinstance(data, dict) and "name" in data and "idea" in data:
            return data
        else:
            raise ValueError("Invalid single suggestion format returned by model")
    except Exception as e:
        if generation_type == "frontend_only":
            return {
                "name": "Custom Frontend App",
                "idea": idea,
                "features": [
                    "Responsive client-side dashboard",
                    "Mock data controller hooks",
                    "Beautiful UI components and navigation"
                ],
                "tech_stack": "React, Tailwind CSS, Framer Motion"
            }
        elif generation_type == "backend_only":
            return {
                "name": "Custom API Service",
                "idea": idea,
                "features": [
                    "RESTful endpoints and path routers",
                    "SQLAlchemy/MongoDB model schemas",
                    "Pydantic validation layer"
                ],
                "tech_stack": "FastAPI, Python, Pydantic, SQLite"
            }
        elif generation_type == "microservice":
            return {
                "name": "Custom Worker/API Service",
                "idea": idea,
                "features": [
                    "Lightweight FastAPI service routing",
                    "Async Redis queue integration",
                    "Dockerized config and health monitor"
                ],
                "tech_stack": "FastAPI, Python, Redis, Docker"
            }
        else:
            return {
                "name": f"Project Idea MVP",
                "idea": idea,
                "features": [
                    "Responsive dashboard layouts",
                    "Advanced action tracking modules",
                    "Settings and profile panels"
                ],
                "tech_stack": "React, Tailwind CSS, FastAPI, MongoDB"
            }


def get_fallback_chat_reply(category: str, user_text: str, selected_project: dict = None) -> str:
    category_lower = category.lower()
    text_lower = user_text.lower()
    
    if selected_project:
        return (
            f"Understood. Let's discuss refinement of the blueprint for **{selected_project.get('name')}**. "
            f"Regarding your query '{user_text}', we can structure this component dynamically. What specific database fields or page animations do you want to add?"
        )

    responses: Dict[str, str] = {
        "startup": f"I can help construct a startup pitch draft and MVP architecture for '{user_text}'. I suggest creating a modular dashboard file containing SaaS growth metrics.",
        "finance": f"I can help construct a financial companion framework for '{user_text}'. I suggest creating a modular dashboard file containing calculation states and transactional lists.",
        "health": f"That sounds like a helpful health project. I have structured React widgets for mood tracking and deep breathing cycles. Let's build a codebase prototype for '{user_text}'.",
        "education": f"For this learning system, I recommend generating an interactive Flashcard quiz layout using standard React hooks. It will help test user retention rates.",
        "productivity": f"I will build a virtual Chief of Staff workspace template. We can compile check-lists and priority tags to help developers coordinate milestones.",
        "sustainability": f"An essential idea. I'll design a Carbon calculator layout with commuting values, carbon conversion weights, and simple suggestions.",
        "other": f"Understood. I will prepare custom interactive modules to bootstrap your hackathon pitch. Let's configure the structure."
    }
    reply = responses.get(category_lower, "I'll compile the custom modules for your workspace based on your specifications.")
    return f"{reply}\n\nType a name for your compiled codebase project below and click 'Generate' to initialize the software development pipeline!"

def get_fallback_codebase(
    name: str,
    category: str,
    theme: str = None,
    blueprint: dict = None,
    theme_palette: dict = None,
    architecture_context: dict = None,
    hackathon_metadata: dict = None,
    mcp_evidence: dict = None
) -> Dict[str, Any]:
    capital_name = name.capitalize()
    normalized_category = category.lower()
    
    theme_lower = (theme or "").lower()
    
    # Default color styles
    theme_color = "indigo"
    if "emerald" in theme_lower or "sage" in theme_lower or "green" in theme_lower:
        theme_color = "emerald"
    elif "synthwave" in theme_lower or "dark" in theme_lower or "cyber" in theme_lower or "neon" in theme_lower:
        theme_color = "pink"
    elif "warm" in theme_lower or "sunrise" in theme_lower or "orange" in theme_lower:
        theme_color = "orange"

    blueprint_json_str = json.dumps(blueprint, indent=2, default=str) if blueprint else "None"
    theme_palette_json_str = json.dumps(theme_palette, indent=2, default=str) if theme_palette else "None"
    compiled_architecture_context = build_compilation_context(architecture_context or {}) if architecture_context else {}
    architecture_context_json_str = json.dumps(compiled_architecture_context, indent=2, default=str) if compiled_architecture_context else "None"

    readme = {
        "name": "README.md",
        "path": "README.md",
        "language": "markdown",
        "content": f"""# {capital_name} ({category.upper()} category)

Welcome to your Sarthi production-ready codebase!

## Confirmed Project Configuration

### Selected Design Theme
* Theme Name: **{theme or 'Slate Minimal'}**

### Theme Palette (JSON)
```json
{theme_palette_json_str}
```

### Confirmed Blueprint (JSON)
```json
{blueprint_json_str}
```

### Connected Agent Context (JSON)
```json
{architecture_context_json_str}
```

## Tech Stack
- **Backend:** FastAPI (Python) with Motor async MongoDB driver, JWT Auth, and Gemini Pro integrations.
- **Frontend:** React / Next.js with TypeScript and Tailwind CSS.
- **Database:** MongoDB Atlas (Vector Search ready).
- **Deployment:** Docker Compose (local development & production configs).

## Getting Started

### Local Development (using Docker Compose)
Simply run the startup script:
```bash
./start.sh
```
Or on Windows:
```cmd
start.bat
```
This will spin up:
- FastAPI Backend on `http://localhost:8000`
- React Frontend on `http://localhost:3000`
- MongoDB Database on `mongodb://localhost:27017`
"""
    }

    codebase = [readme]
    return {
        "summary": f"This is a production-grade FastAPI and Next.js React codebase workspace for {capital_name} generated dynamically based on design requirements.",
        "codebase": inject_boilerplate_files(codebase, name, architecture_context)
    }

async def generate_theme_suggestions(blueprint: dict, custom_prompt: str = None, chat_history: str = None) -> List[Dict[str, Any]]:
    """
    Generate exactly 3 custom color/style themes for the selected project blueprint using Gemini / fallback LLM,
    or fall back to the structured category-specific lists.
    """
    if not (settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or settings.OPENROUTER_API_KEY or settings.NVIDIA_API_KEY):
        return get_fallback_theme_suggestions(blueprint, custom_prompt, chat_history)

    custom_guideline = f"\nCRITICAL: The user has requested custom themes matching this preference: '{custom_prompt}'. Please generate themes that specifically match this style/preference (e.g. naming, descriptions, and color choices matching '{custom_prompt}')." if custom_prompt else ""
    chat_context = f"\nReference Chat Conversation History (contains user preferences, target audience, specific features, and design discussions):\n{chat_history}" if chat_history else ""

    prompt = f"""
    You are Sarthi, an expert AI partner. Suggest exactly 3 custom design themes matching the styling requirements of this project blueprint:
    Blueprint Name: {blueprint.get('name')}
    Core Idea: {blueprint.get('idea')}
    Key Features: {', '.join(blueprint.get('features', []))}
    Suggested Tech Stack: {blueprint.get('tech_stack')}{custom_guideline}{chat_context}
    
    CRITICAL: Analyze the project's domain, target audience (inferred from the chat history and blueprint), and key features to suggest color palettes that are contextually relevant. Do NOT suggest random or generic colors.
    For example:
    - FinTech / Finance: Trustworthy blues, emerald greens, and high-quality stone/slate tones.
    - Healthcare / Medicine: Sterile mint greens, calming teals, and clean soft background tones.
    - Kids / Education / Gaming: Energetic sunsets, warm amber, playful rose/pink, and colorful accents.
    - Developer tools / Technical utilities: High-contrast dark modes, terminal obsidian background, and neon highlights (emerald/purple).
    
    For each design theme, provide:
    1. name (Theme Name)
    2. description (Brief explanation of design choices, mood, typography, spacing, and styling aesthetic - keeping it strictly under 15 words to prevent response truncation)
    3. palette (ThemePalette object matching this JSON structure:
       {{
         "primary": "Hex color code",
         "secondary": "Hex color code",
         "background": "Hex color code",
         "card_bg": "Hex color code",
         "text": "Hex color code",
         "border": "Hex color code",
         "is_dark": true/false
       }}
      )
    
    Return your output ONLY as a valid JSON array of objects. Do not include markdown code block syntax (like ```json ... ```). Just return the raw JSON.
    The JSON must match this structure:
    [
      {{
        "name": "Theme Name",
        "description": "Theme Description",
        "palette": {{
          "primary": "#...",
          "secondary": "#...",
          "background": "#...",
          "card_bg": "#...",
          "text": "#...",
          "border": "#...",
          "is_dark": false
        }}
      }}
    ]
    """
    try:
        from app.services.llm_router import get_llm_completion
        content = await get_llm_completion(
            agent_name="ThemeGeneratorAgent",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        if not content:
            raise ValueError("LLM returned an empty or null theme suggestions response")
        data = parse_json_array_response(content)
        if isinstance(data, list) and len(data) == 3:
            return data
        else:
            raise ValueError("Theme suggestion JSON structure was not an array of 3 themes")
    except Exception as e:
        return get_fallback_theme_suggestions(blueprint, custom_prompt, chat_history)


def get_fallback_theme_suggestions(blueprint: dict, custom_prompt: str = None, chat_history: str = None) -> List[Dict[str, Any]]:
    name = blueprint.get("name", "Workspace Project")
    category = blueprint.get("category", "other").lower()

    if custom_prompt:
        cp_lower = custom_prompt.lower()
        if "dark" in cp_lower or "black" in cp_lower or "night" in cp_lower:
            return [
                {
                    "name": f"Custom Dark Mode",
                    "description": f"A dark theme generated matching '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#3b82f6",
                        "secondary": "#1d4ed8",
                        "background": "#090d16",
                        "card_bg": "#111827",
                        "text": "#f3f4f6",
                        "border": "#1f2937",
                        "is_dark": True
                    }
                },
                {
                    "name": f"Midnight Neon",
                    "description": f"Vibrant custom tones matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#f43f5e",
                        "secondary": "#a855f7",
                        "background": "#030712",
                        "card_bg": "#0f172a",
                        "text": "#f9fafb",
                        "border": "#1e293b",
                        "is_dark": True
                    }
                },
                {
                    "name": f"Obsidian Theme",
                    "description": f"Sleek obsidian monochrome tones matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#10b981",
                        "secondary": "#047857",
                        "background": "#0b0f19",
                        "card_bg": "#161b22",
                        "text": "#e6edf3",
                        "border": "#30363d",
                        "is_dark": True
                    }
                }
            ]
        elif "light" in cp_lower or "white" in cp_lower or "clean" in cp_lower:
            return [
                {
                    "name": f"Clean Light Workspace",
                    "description": f"Ultra-clean light theme matching '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#4f46e5",
                        "secondary": "#c7d2fe",
                        "background": "#fafaf9",
                        "card_bg": "#ffffff",
                        "text": "#1c1917",
                        "border": "#e7e5e4",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Soft Ivory",
                    "description": f"Warm ivory white background matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#d97706",
                        "secondary": "#fef3c7",
                        "background": "#fdfbf7",
                        "card_bg": "#ffffff",
                        "text": "#451a03",
                        "border": "#f5eebc",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Minimalist White",
                    "description": f"Sleek monochrome light theme matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#000000",
                        "secondary": "#e5e5e5",
                        "background": "#ffffff",
                        "card_bg": "#f9f9f9",
                        "text": "#111111",
                        "border": "#e5e5e5",
                        "is_dark": False
                    }
                }
            ]
        else:
            return [
                {
                    "name": f"Dynamic {custom_prompt.title()}",
                    "description": f"A dynamic theme generated matching style preference '{custom_prompt}' for {name}.",
                    "palette": {
                        "primary": "#6366f1",
                        "secondary": "#e0e7ff",
                        "background": "#f8fafc",
                        "card_bg": "#ffffff",
                        "text": "#0f172a",
                        "border": "#e2e8f0",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Accent {custom_prompt.title()}",
                    "description": f"Alternate accents generated matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#db2777",
                        "secondary": "#fce7f3",
                        "background": "#fff1f2",
                        "card_bg": "#ffffff",
                        "text": "#4c0519",
                        "border": "#ffe4e6",
                        "is_dark": False
                    }
                },
                {
                    "name": f"Dark {custom_prompt.title()}",
                    "description": f"A dark variation matching '{custom_prompt}'.",
                    "palette": {
                        "primary": "#f59e0b",
                        "secondary": "#78350f",
                        "background": "#111827",
                        "card_bg": "#1f2937",
                        "text": "#f9fafb",
                        "border": "#374151",
                        "is_dark": True
                    }
                }
            ]

    if category == "health" or "wellness" in name.lower() or "breathe" in name.lower():
        return [
            {
                "name": "Tranquil Sage",
                "description": f"A soft, nature-inspired palette designed to keep users of {name} focused and calm during breathing cycles.",
                "palette": {
                    "primary": "#059669",
                    "secondary": "#a7f3d0",
                    "background": "#f0fdf4",
                    "card_bg": "#ffffff",
                    "text": "#064e3b",
                    "border": "#d1fae5",
                    "is_dark": False
                }
            },
            {
                "name": "Ocean Serenity",
                "description": f"Cool blue gradients to evoke relaxation and trust, perfect for logging wellness habits.",
                "palette": {
                    "primary": "#0284c7",
                    "secondary": "#bae6fd",
                    "background": "#f0f9ff",
                    "card_bg": "#ffffff",
                    "text": "#0369a1",
                    "border": "#e0f2fe",
                    "is_dark": False
                }
            },
            {
                "name": "Midnight Breathe",
                "description": f"A soothing dark mode option with indigo accents, designed to reduce eye strain during nighttime sleep tracking.",
                "palette": {
                    "primary": "#6366f1",
                    "secondary": "#c7d2fe",
                    "background": "#0f172a",
                    "card_bg": "#1e293b",
                    "text": "#f1f5f9",
                    "border": "#334155",
                    "is_dark": True
                }
            }
        ]
    elif category == "finance" or "save" in name.lower() or "budget" in name.lower() or "invest" in name.lower() or "crypto" in name.lower():
        return [
            {
                "name": "Vibrant Mint",
                "description": f"Fresh green accent tones and a clean white background representing cash flow and financial growth for {name}.",
                "palette": {
                    "primary": "#10b981",
                    "secondary": "#d1fae5",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#0f172a",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Slate Corporate",
                "description": f"Trustworthy steel blue accents and structured layouts for institutional accuracy.",
                "palette": {
                    "primary": "#1e3a8a",
                    "secondary": "#93c5fd",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#0f172a",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Dark Gold Ledger",
                "description": f"A rich graphite dark mode theme with warm gold highlights for high-end investor vibes.",
                "palette": {
                    "primary": "#d97706",
                    "secondary": "#fde68a",
                    "background": "#121212",
                    "card_bg": "#1e1e1e",
                    "text": "#f5f5f5",
                    "border": "#2c2c2c",
                    "is_dark": True
                }
            }
        ]
    else:
        return [
            {
                "name": "Cyber Synthwave",
                "description": f"A retro neon dark mode built for developer tools and high-fidelity prototype dashboard layouts.",
                "palette": {
                    "primary": "#ec4899",
                    "secondary": "#a855f7",
                    "background": "#0f172a",
                    "card_bg": "#1e293b",
                    "text": "#f8fafc",
                    "border": "#334155",
                    "is_dark": True
                }
            },
            {
                "name": "Minimalist Clean",
                "description": f"Ultra-clean typography with cool grey accents and slate borders to emphasize content layout.",
                "palette": {
                    "primary": "#4f46e5",
                    "secondary": "#c7d2fe",
                    "background": "#f8fafc",
                    "card_bg": "#ffffff",
                    "text": "#1e293b",
                    "border": "#e2e8f0",
                    "is_dark": False
                }
            },
            {
                "name": "Sunrise Warmth",
                "description": f"Energizing orange-red primary accents on cream and beige, ideal for creative work.",
                "palette": {
                    "primary": "#f97316",
                    "secondary": "#ffedd5",
                    "background": "#fafaf9",
                    "card_bg": "#ffffff",
                    "text": "#292524",
                    "border": "#e7e5e4",
                    "is_dark": False
                }
            }
        ]

async def generate_prd_mrd_trd(
    project_name: str,
    prompt: str,
    generation_type: str = "full_stack",
    theme: str = None,
    theme_palette: dict = None,
    chat_history: str = None,
    exclude_prd_mrd: bool = False
) -> Dict[str, str]:
    """
    Generate high-quality PRD, MRD, and TRD markdown files in parallel.
    """
    import asyncio
    
    # Construct context instructions for themes and chat history
    context_directives = ""
    if theme:
        context_directives += f"\n- Confirmed Styling Theme Name: {theme}"
    if theme_palette:
        context_directives += (
            f"\n- Confirmed Styling Color Palette: Primary={theme_palette.get('primary')}, "
            f"Secondary={theme_palette.get('secondary')}, Background={theme_palette.get('background')}, "
            f"Text={theme_palette.get('text')}, Border={theme_palette.get('border')}, DarkMode={theme_palette.get('is_dark')}"
        )
    if chat_history:
        context_directives += f"\n- Reference Chat Conversation History (contains user preferences, target audience, specific features, and design discussions):\n{chat_history}"
        
    prompt = (
        f"{prompt}\n\n"
        f"STRICT SPECIFICATION GENERATION INSTRUCTIONS:\n"
        f"1. You must align all UI/UX layouts, component descriptions, and visual/interactive styling recommendations in the document with the confirmed Theme and Color Palette:\n"
        f"{context_directives}\n"
        f"2. You must incorporate all specific user preferences, target audience demographics, functional constraints, and requirements discussed in the Chat Conversation History.\n"
        f"3. Make sure the technical requirement decisions dynamically adapt to these parameters."
    )
    
    if generation_type == "frontend_only":
        # 1. PRD Prompt (Frontend Only)
        prd_system = (
            "You are an expert Principal Product Manager. Your task is to generate a comprehensive, high-fidelity Product Requirement Document (PRD) "
            "in Markdown format for the proposed FRONTEND ONLY project."
        )
        prd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed PRD containing the following sections:
        # Product Requirement Document (PRD) - {project_name} (Frontend Only)
        ## 1. Executive Summary & Objectives
        What user-facing problem are we solving? What are the core client-side goals and frontend metrics of this product?
        ## 2. Target Audience & User Personas
        Who are the target client-side users? Detail at least two user personas.
        ## 3. Product Scope & Out of Scope
        What are the minimum viable frontend features (MVP)? What UI features are deferred to V2? NOTE: Server-side database management and custom API development are explicitly Out of Scope.
        ## 4. Key Functional Features (Frontend)
        Detail user flows, frontend client routing, mock data interactions, and UI component specifications for each core feature.
        ## 5. Non-Functional Requirements (Frontend)
        Usability, accessibility (WCAG compliance), responsive layouts (mobile, tablet, desktop), web performance parameters (Lighthouse scores, FCP, LCP).
        ## 6. Success Metrics & Key Performance Indicators (KPIs)
        What does frontend success look like? What user interaction/retention metrics should we track?
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Product Requirement Document'.
        """

        # 2. MRD Prompt (Frontend Only)
        mrd_system = (
            "You are an expert Director of Product Marketing. Your task is to generate a comprehensive, high-fidelity Market Requirement Document (MRD) "
            "in Markdown format for a Frontend-focused / Client-focused product."
        )
        mrd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed MRD containing the following sections:
        # Market Requirement Document (MRD) - {project_name} (Frontend Only)
        ## 1. Market Opportunity & Size
        Define the target addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM) for this user interface.
        ## 2. Competitor Landscape & User Experience Differentiation
        Identify at least three competitors (direct and indirect). What is our unique selling proposition (USP) regarding user experience, design, accessibility, and interaction design?
        ## 3. Positioning & Messaging
        How will we position the product in the market? Include key brand/design pillars.
        ## 4. Go-To-Market (GTM) Strategy
        What marketing channels, content strategies, and acquisition tactics for client-facing apps?
        ## 5. Pricing & Monetization Model
        How will the product generate revenue? Describe subscription tiers or client-side ad-integration/in-app purchase models.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Market Requirement Document'.
        """

        # 3. TRD Prompt (Frontend Only)
        trd_system = (
            "You are a Principal Software Architect. Your task is to generate a comprehensive, high-fidelity Technical Requirement Document (TRD) "
            "in Markdown format for a FRONTEND ONLY project."
        )
        trd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed TRD containing the following sections:
        # Technical Requirement Document (TRD) - {project_name} (Frontend Only)
        ## 1. Architectural Overview & Frontend System Design
        Describe the high-level frontend architecture, state management patterns (Zustand/SWR/Redux), client-side routing, and folder structure.
        ## 2. Tech Stack & Dependencies
        What frontend libraries, frameworks (React/Next.js/Vite), styling tools (Tailwind/CSS modules), and client-side utilities are required? Explain why.
        ## 3. Client State & Mock Data Models
        Detail the client-side state schema and JSON structures for mock/local storage data models. NOTE: No database schemas or server-side DB models.
        ## 4. Client Routing & Inter-component Communication
        Define router paths, query parameters, page components, and context/props flow.
        ## 5. Security & Client-Side Verification
        Local storage safety, input sanitization, front-end auth logic/routing guards.
        ## 6. Deployment & Build Pipeline
        Static hosting configuration (Vercel/Netlify/S3), asset optimization, build optimization (tree shaking, code splitting), and CI/CD steps.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Technical Requirement Document'.
        """

    elif generation_type == "backend_only":
        # 1. PRD Prompt (Backend Only)
        prd_system = (
            "You are an expert Principal Product Manager. Your task is to generate a comprehensive, high-fidelity Product Requirement Document (PRD) "
            "in Markdown format for the proposed BACKEND ONLY (API-first/Headless) project."
        )
        prd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed PRD containing the following sections:
        # Product Requirement Document (PRD) - {project_name} (Backend Only)
        ## 1. Executive Summary & Objectives
        What system-level or API-level problem are we solving? What are the core goals and metrics of this backend system?
        ## 2. Target Audience & System Personas
        Who are the target consumers (e.g., frontend developers, third-party systems, admin scripts)? Detail at least two personas.
        ## 3. Product Scope & Out of Scope
        What are the minimum viable backend APIs and services (MVP)? What features are deferred to V2? NOTE: UI development, frontend pages, layouts, and web styling are explicitly Out of Scope.
        ## 4. Key Functional Features (Backend)
        Detail system workflows, data processing logic, background jobs, and API functionalities.
        ## 5. Non-Functional Requirements (Backend)
        System scalability, latency parameters, uptime SLAs, rate limits, performance parameters, and data integrity constraints.
        ## 6. Success Metrics & Key Performance Indicators (KPIs)
        What does backend success look like? What backend performance metrics (API response times, error rates, server utilization) should we track?
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Product Requirement Document'.
        """

        # 2. MRD Prompt (Backend Only)
        mrd_system = (
            "You are an expert Director of Product Marketing. Your task is to generate a comprehensive, high-fidelity Market Requirement Document (MRD) "
            "in Markdown format for a Backend/API-first/Headless product."
        )
        mrd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed MRD containing the following sections:
        # Market Requirement Document (MRD) - {project_name} (Backend Only)
        ## 1. Market Opportunity & Size
        Define the target addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM) for headless/API-first platforms or enterprise backends.
        ## 2. Competitor Landscape & API-First Differentiation
        Identify at least three competitors (direct and indirect). What is our unique selling proposition (USP) regarding system efficiency, reliability, API developer experience, or processing capabilities?
        ## 3. Positioning & Messaging
        How will we position this backend product? Include brand/developer pillars.
        ## 4. Go-To-Market (GTM) Strategy & Developer Relations (DevRel)
        What strategies will we use to acquire backend consumers? Documentation, developer kits, sandboxes, and API portals.
        ## 5. Pricing & Monetization Model
        How will the product generate revenue? Describe API usage pricing tiers (pay-per-request, rate-limited tiers, data volume limits).
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Market Requirement Document'.
        """

        # 3. TRD Prompt (Backend Only)
        trd_system = (
            "You are a Principal Software Architect. Your task is to generate a comprehensive, high-fidelity Technical Requirement Document (TRD) "
            "in Markdown format for a BACKEND ONLY project."
        )
        trd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed TRD containing the following sections:
        # Technical Requirement Document (TRD) - {project_name} (Backend Only)
        ## 1. Architectural Overview & Backend Design
        Describe the high-level server architecture, patterns (MVC, Repository, clean architecture), and database-server interaction.
        ## 2. Tech Stack & Backend Dependencies
        What backend frameworks (FastAPI/Express/Django), database engines, caching solutions (Redis), and third-party APIs are required? Explain why.
        ## 3. Database Schema & Data Models
        Provide a detailed database schema. List entities, properties, data types, migrations, index strategies, and relationships.
        ## 4. API Endpoints & Payload Contracts
        Define REST/WebSocket routes (methods, paths, request bodies, response payloads, error payloads, query params).
        ## 5. Security, Authentication & Access Control
        JWT validation, session management, OAuth2 scopes, rate limiting, hashing, encryption at rest/transit.
        ## 6. Deployment, Infrastructure & CI/CD
        Docker configurations, Dockerfiles, caching layers (Redis), cloud VM/serverless configs, and automated pipeline steps.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Technical Requirement Document'.
        """

    elif generation_type == "microservice":
        # 1. PRD Prompt (Microservice)
        prd_system = (
            "You are an expert Principal Product Manager. Your task is to generate a comprehensive, high-fidelity Product Requirement Document (PRD) "
            "in Markdown format for the proposed MICROSERVICE-based project."
        )
        prd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed PRD containing the following sections:
        # Product Requirement Document (PRD) - {project_name} (Microservice Architecture)
        ## 1. Executive Summary & Objectives
        What distributed system-level problem are we solving? What are the core scalability goals of this product?
        ## 2. Target Audience & System Personas
        Who are the target consumers? Detail at least two personas (developers, devops engineers, internal clients).
        ## 3. Product Scope & Out of Scope
        What is the scope of the microservices MVP? What features or services are deferred to V2?
        ## 4. Key Functional Features (Distributed Workflows)
        Detail user/system workflows that span multiple microservices. Explain distributed transaction patterns.
        ## 5. Non-Functional Requirements
        High availability, fault tolerance (circuit breakers, retries), eventual consistency window, latency overhead, and inter-service latency.
        ## 6. Success Metrics & Key Performance Indicators (KPIs)
        What does success look like? What metrics (distributed trace times, service uptime, message queue lag, scaling speed) should we track?
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Product Requirement Document'.
        """

        # 2. MRD Prompt (Microservice)
        mrd_system = (
            "You are an expert Director of Product Marketing. Your task is to generate a comprehensive, high-fidelity Market Requirement Document (MRD) "
            "in Markdown format for a Scalable Microservice Platform."
        )
        mrd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed MRD containing the following sections:
        # Market Requirement Document (MRD) - {project_name} (Microservice Architecture)
        ## 1. Market Opportunity & Size
        TAM, SAM, SOM for highly scalable enterprise systems.
        ## 2. Competitor Landscape & Cloud-Native Differentiation
        Competitors, USP regarding extreme scalability, independence of service scaling, high availability, and modularity.
        ## 3. Positioning & Messaging
        How will we position this platform? Modularity, resiliency, speed.
        ## 4. Go-To-Market (GTM) Strategy
        B2B sales, open-source community plays, developer evangelism.
        ## 5. Pricing & Monetization Model
        Enterprise licensing, consumption-based pricing, resource-allocated plans.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Market Requirement Document'.
        """

        # 3. TRD Prompt (Microservice)
        trd_system = (
            "You are a Principal Software Architect. Your task is to generate a comprehensive, high-fidelity Technical Requirement Document (TRD) "
            "in Markdown format for a MICROSERVICE architecture project."
        )
        trd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed TRD containing the following sections:
        # Technical Requirement Document (TRD) - {project_name} (Microservice Architecture)
        ## 1. Distributed Architectural Overview & Services Layout
        Describe the service layout, communication boundaries, and architectural patterns (API Gateway, Event-driven, Database-per-service).
        ## 2. Tech Stack, Message Brokers & Protocols
        What technologies are chosen for each service? Explain message brokers (Kafka/RabbitMQ/Redis PubSub) and inter-service communication protocols (gRPC/HTTP REST).
        ## 3. Databases per Service & Schema
        Provide schemas for each individual service's database. Explain how data synchronization and eventual consistency are achieved.
        ## 4. Inter-service APIs & Event Schemas
        Define REST/gRPC endpoints and message queue topic structures/event payloads.
        ## 5. Distributed Security, Auth & Service-to-Service Auth
        Centralized OAuth2/JWT gateway verification, service-to-service auth (mTLS, API Keys).
        ## 6. Infrastructure, Orchestration, CI/CD & Tracing
        Kubernetes configurations, Helm charts, Docker Compose, distributed tracing (Jaeger/OpenTelemetry), and centralized logging.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Technical Requirement Document'.
        """

    else:
        # 1. PRD Prompt (Full Stack)
        prd_system = (
            "You are an expert Principal Product Manager. Your task is to generate a comprehensive, high-fidelity Product Requirement Document (PRD) "
            "in Markdown format for the proposed project."
        )
        prd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed PRD containing the following sections:
        # Product Requirement Document (PRD) - {project_name}
        ## 1. Executive Summary & Objectives
        What problem are we solving? What are the core goals and metrics of this product?
        ## 2. Target Audience & User Personas
        Who are the target users? Detail at least two user personas.
        ## 3. Product Scope & Out of Scope
        What are the minimum viable features (MVP)? What features are deferred to V2?
        ## 4. Key Functional Features
        Detail user flows, requirements, and specifications for each core feature.
        ## 5. Non-Functional Requirements
        Usability, accessibility, responsiveness, performance parameters.
        ## 6. Success Metrics & Key Performance Indicators (KPIs)
        What does success look like? What metrics should we track?
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Product Requirement Document'.
        """

        # 2. MRD Prompt (Full Stack)
        mrd_system = (
            "You are an expert Director of Product Marketing. Your task is to generate a comprehensive, high-fidelity Market Requirement Document (MRD) "
            "in Markdown format for the proposed project."
        )
        mrd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed MRD containing the following sections:
        # Market Requirement Document (MRD) - {project_name}
        ## 1. Market Opportunity & Size
        Define the target addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM).
        ## 2. Competitor Landscape & Differentiation
        Identify at least three competitors (direct and indirect). What is our unique selling proposition (USP)?
        ## 3. Positioning & Messaging
        How will we position the product in the market? Include key brand pillars.
        ## 4. Go-To-Market (GTM) Strategy
        What marketing channels, content strategies, and acquisition tactics will we employ?
        ## 5. Pricing & Monetization Model
        How will the product generate revenue? Describe subscription tiers or transaction models.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Market Requirement Document'.
        """

        # 3. TRD Prompt (Full Stack)
        trd_system = (
            "You are a Principal Software Architect. Your task is to generate a comprehensive, high-fidelity Technical Requirement Document (TRD) "
            "in Markdown format for the proposed project."
        )
        trd_user = f"""
        Project Name: {project_name}
        Project Core Idea/Description: {prompt}
        
        Write a detailed TRD containing the following sections:
        # Technical Requirement Document (TRD) - {project_name}
        ## 1. Architectural Overview & System Design
        Describe the high-level system architecture, client-server models, and design patterns.
        ## 2. Tech Stack & Dependencies
        What frontend libraries, backend frameworks, databases, and third-party APIs are required? Explain why.
        ## 3. Database Schema & Data Models
        Provide a detailed database schema. List entities, properties, data types, and relations.
        ## 4. API Endpoints & Payload Contracts
        Define REST/WebSocket routes (methods, paths, request bodies, response payloads).
        ## 5. Security, Authentication & Compliance
        JWT policies, rate limiting, encryption at rest/transit, GDPR/compliance notes.
        ## 6. Deployment, Infrastructure & CI/CD
        Docker configurations, cloud providers, caching layers (Redis), and pipeline steps.
        
        Return ONLY the markdown document. Do not wrap in extra commentary or extra code blocks. Just start with '# Technical Requirement Document'.
        """

    async def run_prd():
        try:
            return await get_llm_completion(
                agent_name="PRDGeneratorAgent",
                messages=[
                    {"role": "system", "content": prd_system},
                    {"role": "user", "content": prd_user}
                ],
                temperature=0.3,
                max_tokens=3500
            )
        except Exception as e:
            return f"# PRD - {project_name}\\n\\nFailed to generate Product Requirement Document: {e}"

    async def run_mrd():
        try:
            return await get_llm_completion(
                agent_name="MRDGeneratorAgent",
                messages=[
                    {"role": "system", "content": mrd_system},
                    {"role": "user", "content": mrd_user}
                ],
                temperature=0.3,
                max_tokens=3500
            )
        except Exception as e:
            return f"# MRD - {project_name}\\n\\nFailed to generate Market Requirement Document: {e}"

    async def run_trd():
        try:
            return await get_llm_completion(
                agent_name="TRDGeneratorAgent",
                messages=[
                    {"role": "system", "content": trd_system},
                    {"role": "user", "content": trd_user}
                ],
                temperature=0.3,
                max_tokens=3500
            )
        except Exception as e:
            return f"# TRD - {project_name}\\n\\nFailed to generate Technical Requirement Document: {e}"

    if exclude_prd_mrd:
        trd_doc = await run_trd()
        prd_doc = ""
        mrd_doc = ""
    else:
        prd_doc, mrd_doc, trd_doc = await asyncio.gather(run_prd(), run_mrd(), run_trd())
    
    def clean_doc(doc: str) -> str:
        d = doc.strip()
        if d.startswith("```"):
            lines = d.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            d = "\\n".join(lines).strip()
        return d
        
    return {
        "prd": clean_doc(prd_doc),
        "mrd": clean_doc(mrd_doc),
        "trd": clean_doc(trd_doc)
    }

