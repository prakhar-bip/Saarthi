# 🛡️ Sarthi — AI-Powered Project Charioteer

An enterprise-grade, action-oriented multi-agent pipeline that transforms your raw ideas into fully documented, compiled, and deployable software codebases.

<div align="center">

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Gemini%203.5%20%26%203.1-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Google ADK](https://img.shields.io/badge/Google-Agent%20Development%20Kit-EA4335?style=for-the-badge&logo=google-cloud&logoColor=white)](https://google.github.io/adk-docs/)
[![MongoDB MCP](https://img.shields.io/badge/MongoDB-MCP%20Server-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://github.com/mongodb-js/mongodb-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**[🌐 Live App](https://sarthi-gtu3eysx6q-uc.a.run.app) · [🔌 Deployed API](https://sarthi-backend-gtu3eysx6q-uc.a.run.app) · [🏛️ Architecture](#-system-architecture) · [🛠️ Setup Guide](#-quick-start) · [🔌 MCP Evidence](#-mongodb-mcp-verification)**

</div>

---

## 🌟 What is Sarthi?

Inspired by the concept of a **Sarthi** (a divine guide/charioteer), this platform is **not another simple AI wrapper or chatbot**. It is a **fully automated software engineering workspace** powered by Google Cloud Vertex AI, Google Agent Development Kit (ADK), and MongoDB MCP.

Instead of writing code snippet-by-snippet, you converse with Sarthi to brainstorm your idea. Once finalized, Sarthi orchestrates a **hierarchical pipeline of 28 specialized AI agents** that work in parallel and sequence to architect, generate, test, repair, compile, and bundle your application.

> **💡 The Result:** A downloadable zip containing a complete backend/frontend repository (e.g., FastAPI + Next.js), structured database models, JWT authentication, deployment configurations, a full PRD/MRD/TRD package, and a Devpost-ready submission checklist.

---

## 🚀 Active Cloud Run Endpoints
*   **Frontend Service**: [https://sarthi-gtu3eysx6q-uc.a.run.app](https://sarthi-gtu3eysx6q-uc.a.run.app)
*   **Backend API Service**: [https://sarthi-backend-gtu3eysx6q-uc.a.run.app](https://sarthi-backend-gtu3eysx6q-uc.a.run.app)

---

## ✨ Key Capabilities

*   🧠 **Dynamic Brainstorming & Co-Founding**: Actively suggests features, database schemas, styling themes, and stacks.
*   🏗️ **28-Agent Assembly Line**: Specialized subagents design and validate every single layer—from APIs and authorization flows to DevOps scripts and error correction.
*   🔌 **MongoDB Model Context Protocol (MCP)**: Utilizes the official `mongodb-mcp-server` to inspect active collections, pull database contexts, and validate queries dynamically.
*   ⚡ **Google Cloud Vertex AI (IAM-based)**: Fully migrated to Vertex AI for enterprise reliability, authenticating automatically via Service Account Application Default Credentials (ADC) without exposing cleartext API keys.
*   🔄 **WebSocket Progress Engine**: Stream real-time agent execution logs, step progressions, and compilation outputs directly to a console UI.

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    User(["👤 Developer / User"]) --> Chat["💬 Sarthi Chat\nBrainstorming & Concept Design"]
    Chat --> Blueprint["📋 Project Blueprint\n(JSON Specification)"]
    Blueprint --> Pipeline
 
    subgraph Pipeline["🏗️ 28-Agent Architecture Pipeline"]
        direction TB
        RA["1. Requirement Analyzer"] --> PL["2. Blueprint Planner"]
        PL --> DB["3. Database Architect"]
        DB --> BA["4. Backend Architect"]
        BA --> API["5. API Contract Designer"]
        API --> FA["6. Frontend Architect"]
        FA --> UX["7. UI/UX & Theme Designer"]
        UX --> Auth["8. Auth & Security Architect"]
        Auth --> CG["9. Code Generator"]
        CG --> Build["10. Build & Compiler Service"]
        Build --> EC["11. AI Error Correction"]
        EC --> Export["12. Project Bundler & Exporter"]
    end

    subgraph MCP["🔌 MongoDB MCP Bridge"]
        direction LR
        MCPServer["mongodb-mcp-server"] --> Tools["list-collections\nfind\naggregate\ncount\nrun-command"]
    end

    Pipeline --> MCP
    Pipeline --> Output["📦 Complete Deployable App\n- Next.js / FastAPI Code\n- PRD, MRD, TRD Docs\n- Docker & Deploy Scripts"]

    subgraph LLM["🧠 LLM & Orchestration Layer"]
        direction LR
        ADK["Google ADK\nAgent SDK"] --> Gemini["Gemini 3.5 Flash & 3.1 Pro\nvia Vertex AI"]
    end

    Pipeline --> LLM
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16 (Turbopack), React 19, Tailwind CSS, Framer Motion |
| **Backend** | FastAPI, Uvicorn, Python 3.11+, Motor (async MongoDB driver) |
| **Orchestration** | Google Agent Development Kit (ADK), LangGraph |
| **Models** | `gemini-3.5-flash` (Fast tasks/Chat), `gemini-3.1-pro-preview` (Reasoning & Code Compilation) |
| **Database** | MongoDB Atlas, Redis (Celery backend routing) |
| **MCP** | `mongodb-mcp-server@latest` (Stdio bridge) |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB instance (local or Atlas)
- Google Cloud SDK (`gcloud` CLI)

### 1. Local Credentials Authentication (Vertex AI)
To run Sarthi locally without exposing cleartext API keys, authenticate your local terminal with GCP Application Default Credentials:
```bash
gcloud auth application-default login
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

pip install -r requirements.txt
cp .env.example .env  # Configure your settings (no API keys required!)
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** to launch your local charioteer.

---

## 🔌 MongoDB MCP Verification
For hackathon evaluation and technical audits, Sarthi exposes system integration endpoints that prove live MongoDB MCP operation:

*   **System Health & MCP Status**: `GET /api/health`
*   **MCP Connection Details**: `GET /api/mcp/status`
*   **Available MCP Tools**: `GET /api/mcp/tools`
*   **MCP Proof Evidence Bundle**: `GET /api/mcp/evidence`

### Quick Verification Curl
```bash
# Check MCP status
curl https://sarthi-backend-gtu3eysx6q-uc.a.run.app/api/health

# Fetch MCP judging evidence
curl https://sarthi-backend-gtu3eysx6q-uc.a.run.app/api/mcp/evidence
```

---

## 📂 Repository Structure
```
Sarthi/
├── backend/
│   ├── app/
│   │   ├── agents/          # 28 specialized pipeline agents
│   │   ├── api/             # FastAPI routers (auth, chats, projects, mcp)
│   │   ├── core/            # Configs (Vertex AI & global settings)
│   │   ├── db/              # MongoDB & Redis adapters
│   │   └── services/        # ADK agent wrappers, LLM router, MCP bridge
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app routes
│   │   ├── components/      # UI components (chat, console, viewer)
│   │   └── context/         # React Context state
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── deploy.ps1               # PowerShell Deployment Script
└── README.md
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Built with ❤️ for the <b>Building Agents for Real-World Challenges</b> Hackathon — MongoDB Partner Track
</div>
