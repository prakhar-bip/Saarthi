import json
from datetime import datetime, timezone
from typing import Any, Dict, List


MIT_LICENSE_TEXT = """MIT License

Copyright (c) 2026 Sarthi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def build_env_example(metadata: Dict[str, Any] | None = None) -> str:
    metadata = metadata or {}
    return "\n".join(
        [
            "# Sarthi generated hackathon project environment",
            "FLASK_ENV=development",
            "FLASK_DEBUG=1",
            "PORT=5000",
            "MONGODB_URI=mongodb://localhost:27017",
            "DATABASE_NAME=sarthi_generated_project",
            "GOOGLE_API_KEY=your_google_api_key_here",
            f"GOOGLE_MODEL={metadata.get('primary_model', 'gemini-3-pro-preview')}",
            "PARTNER_TRACK=MongoDB",
            "PARTNER_MCP_SERVER=mongodb-mcp-server@latest",
            "MONGODB_MCP_READ_ONLY=true",
            "",
        ]
    )


def build_submission_markdown(
    project_name: str,
    metadata: Dict[str, Any] | None = None,
    evidence: Dict[str, Any] | None = None,
) -> str:
    metadata = metadata or {}
    evidence = evidence or {}
    checklist = metadata.get("submission_checklist") or [
        "Hosted project URL",
        "Public open-source repository URL",
        "Root LICENSE file",
        "Approximately 3 minute demo video",
        "Selected MongoDB partner track",
        "Completed Devpost form",
    ]
    pipeline = metadata.get("sub_agent_pipeline") or []
    pipeline_lines = [
        f"- {agent.get('name', 'Agent')}: {agent.get('role', '')}"
        for agent in pipeline
        if isinstance(agent, dict)
    ]
    tool_names = evidence.get("available_tools") or []

    return f"""# Hackathon Submission Guide - {project_name}

## Challenge Fit

- Challenge: {metadata.get('challenge', 'Building Agents for Real-World Challenges')}
- Partner track: {metadata.get('partner_track', 'MongoDB')}
- Partner MCP server: {metadata.get('partner_mcp_server', 'mongodb-mcp-server@latest')}
- Model/runtime: {metadata.get('primary_model', 'Gemini 3')} with Agent Builder compatible orchestration

## What The Agent Does

Sarthi moves beyond chat by turning an idea into requirements documents, a multi-agent architecture plan, MongoDB MCP evidence, and a runnable Flask prototype package.

## Human Oversight

{chr(10).join(f"- {item}" for item in metadata.get('human_oversight', [])) or "- User reviews and confirms each major generation phase."}

## MongoDB MCP Evidence

- MCP mode: {(evidence.get('mcp_status') or {}).get('mode', 'unknown')}
- Connected: {(evidence.get('mcp_status') or {}).get('connected', False)}
- Read only: {(evidence.get('mcp_status') or {}).get('read_only', True)}
- Tools seen: {', '.join(tool_names[:12]) if tool_names else 'Tools exposed through /api/mcp/tools'}

## Sub-Agent Pipeline

{chr(10).join(pipeline_lines) if pipeline_lines else '- See sarthi-internal/AI_AgentContext.json in the generated ZIP.'}

## Devpost Checklist

{chr(10).join(f"- [ ] {item}" for item in checklist)}

## Demo Video Flow

1. Start Sarthi and sign in.
2. Describe a real-world problem.
3. Show the blueprint, theme, PRD/MRD/TRD review, and Proceed to Build Codebase action.
4. Open the generated files, MCP evidence JSON, and run the Flask prototype.
5. Show the partner track selection as MongoDB and explain how MCP gives database context to Sarthi's agents.

Generated at {datetime.now(timezone.utc).isoformat()}.
"""


def build_hackathon_files(
    project_name: str,
    metadata: Dict[str, Any] | None = None,
    evidence: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    metadata = metadata or {}
    evidence = evidence or {}
    return [
        {
            "name": "LICENSE",
            "path": "LICENSE",
            "language": "plaintext",
            "content": MIT_LICENSE_TEXT,
        },
        {
            "name": ".env.example",
            "path": ".env.example",
            "language": "dotenv",
            "content": build_env_example(metadata),
        },
        {
            "name": "HACKATHON_SUBMISSION.md",
            "path": "HACKATHON_SUBMISSION.md",
            "language": "markdown",
            "content": build_submission_markdown(project_name, metadata, evidence),
        },
        {
            "name": "MCP_EVIDENCE.json",
            "path": "sarthi-internal/MCP_EVIDENCE.json",
            "language": "json",
            "content": json.dumps(evidence, indent=2),
        },
        {
            "name": "HACKATHON_METADATA.json",
            "path": "sarthi-internal/HACKATHON_METADATA.json",
            "language": "json",
            "content": json.dumps(metadata, indent=2),
        },
    ]


def merge_hackathon_files(
    codebase: List[Dict[str, Any]],
    project_name: str,
    metadata: Dict[str, Any] | None = None,
    evidence: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    existing_paths = {file.get("path") for file in codebase}
    for file in build_hackathon_files(project_name, metadata, evidence):
        if file["path"] not in existing_paths:
            codebase.append(file)
            existing_paths.add(file["path"])
    return codebase
