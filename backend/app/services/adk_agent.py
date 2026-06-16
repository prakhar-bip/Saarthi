from loguru import logger
from typing import List, Dict, Any, Optional
from google.genai.types import Content, Part

from app.core.config import settings
from app.services.ai import generate_theme_suggestions, stream_chat_reply

# Check if google-adk is installed
HAS_ADK = False
try:
    from google.adk.agents.llm_agent import Agent
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.agents.run_config import RunConfig
    HAS_ADK = True
except (ImportError, ModuleNotFoundError):
    logger.warning("google-adk package is not installed. Root ADK Agent chat will cascade to LangGraph fallback.")
    Agent = None
    Runner = None
    InMemorySessionService = None
    RunConfig = None

# If ADK is present, restrict it to production environment and verify credentials.
if settings.ENVIRONMENT != "production":
    logger.info("google-adk disabled in development mode.")
    HAS_ADK = False
elif HAS_ADK and settings.USE_VERTEX_AI:
    try:
        import google.auth
        google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    except Exception as e:
        logger.warning(f"Vertex AI credentials check failed: {e}. Sarthi ADK Agent chat disabled (bypassing deadlock).")
        HAS_ADK = False


# 1. Define custom Python tools first for ADK
def get_design_theme_suggestions_tool(project_name: str, category: str, features: List[str], tech_stack: str, custom_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate design themes and color palettes for the project.
    
    Args:
        project_name: Name of the project.
        category: Project category (e.g., finance, health, startup).
        features: List of project features.
        tech_stack: Tech stack of the project.
        custom_prompt: Optional user customization prompt for styling.
    """
    try:
        import asyncio
        blueprint = {
            "name": project_name,
            "category": category,
            "features": features,
            "tech_stack": tech_stack
        }
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            
        themes = asyncio.run(generate_theme_suggestions(blueprint, custom_prompt=custom_prompt))
        return themes
    except Exception as e:
        logger.error(f"Error in get_design_theme_suggestions_tool: {e}")
        return []

platform_info = "Google Cloud Vertex AI (via IAM Service Account)" if settings.USE_VERTEX_AI else "Google AI Studio (via Developer API Key)"

# 2. Initialize the Root ADK Agent
sarthi_agent = None
session_service = None
runner = None

if HAS_ADK:
    from app.services.llm_router import map_google_model
    mapped_model = map_google_model(settings.GOOGLE_FAST_MODEL or settings.GOOGLE_MODEL)
    adk_model = mapped_model.split(",")[0].strip() if mapped_model else (settings.GOOGLE_FAST_MODEL or settings.GOOGLE_MODEL)
    sarthi_agent = Agent(
        name="Sarthi",
        model=adk_model,
        instruction=(
            "You are **Sarthi**, an expert AI development companion built for hackathon project planning and software engineering. "
            f"Currently, you are executing on the {platform_info} platform. If the user asks which platform or API route you are using, answer with this platform name.\n\n"
            "You are optimized for the Building Agents for Real-World Challenges hackathon using Gemini, Google Cloud Agent Builder style orchestration, and the MongoDB partner MCP server.\n\n"
            "## Core Capabilities\n"
            "1. **General Assistant**: Answer ANY question thoroughly — coding doubts, debugging, algorithms, system design, tech concepts, career advice, etc. Respond like a knowledgeable senior developer.\n"
            "2. **Project Brainstorming**: When the user discusses a project idea, help them refine it — suggest features, architecture patterns, UX workflows, database schemas, and tech stack choices.\n"
            "3. **Blueprint Generation**: When project details are discussed, output a structured blueprint block that auto-populates the project form.\n\n"
            "## Response Rules\n"
            "- **Dynamic Brainstorming**: When the user shares a project idea, DO NOT just passively accept it. Act as a dynamic tech co-founder. Discuss their idea, suggest 2-3 innovative, modern features they might not have thought of, and ask for their feedback. Make it clear that everything is customizable.\n"
            "- For hackathon project discussions, prefer agentic products that take action through tools, database state, workflows, generated deliverables, and human approval checkpoints.\n"
            "- Mention that Sarthi will package generated apps with README, MIT license, .env example, PRD/MRD/TRD, MongoDB MCP evidence, and a Devpost-ready submission checklist.\n"
            "- For **general questions** (coding, debugging, concepts): Provide clear, accurate answers with code examples where relevant. Do NOT mention project compilation or blueprints.\n"
            "- For **project discussions**: Engage naturally. Ask clarifying questions. Suggest improvements. Append the blueprint block dynamically so the right panel updates, but let them know they can modify it anytime.\n"
            "- Use **markdown formatting**: headings, bullet lists, code blocks with language tags, bold for emphasis.\n"
            "- Keep responses conversational, enthusiastic, and direct — not robotic.\n\n"
            "## Blueprint Block Format\n"
            "ONLY when the user is discussing their project idea, features, or tech stack, append this block at the END of your response:\n"
            "<blueprint>\n"
            "{\n"
            "  \"name\": \"Project Name\",\n"
            "  \"idea\": \"Clear one-line description of what the project does\",\n"
            "  \"features\": [\"Feature 1 with brief detail\", \"Feature 2 with brief detail\", \"Feature 3\"],\n"
            "  \"tech_stack\": \"Flask, HTML, CSS, JavaScript\",\n"
            "  \"category\": \"web\"  // 'web', 'agent', 'mobile', or 'backend'\n"
            "}\n"
            "</blueprint>\n\n"
            "Do NOT include blueprint blocks for general questions, greetings, or non-project conversations."
        ),
        tools=[get_design_theme_suggestions_tool]
    )

    # Instantiate Session service and Runner for ADK
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="SarthiApp",
        agent=sarthi_agent,
        session_service=session_service
    )

# 3. LangGraph Fallback Orchestration Setup
try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict
    
    class FallbackState(TypedDict):
        category: str
        messages: List[Dict[str, Any]]
        selected_project: Optional[Dict[str, Any]]
        response: str
        
    async def call_llm_node(state: FallbackState) -> Dict[str, Any]:
        """Node for querying the Gemini model using standard Sarthi API completion."""
        from app.services.ai import generate_chat_reply
        reply = await generate_chat_reply(
            category=state.get("category", "general"),
            messages=state.get("messages", []),
            selected_project=state.get("selected_project")
        )
        return {"response": reply}
        
    # Compile the fallback workflow
    workflow = StateGraph(FallbackState)
    workflow.add_node("call_llm", call_llm_node)
    workflow.set_entry_point("call_llm")
    workflow.add_edge("call_llm", END)
    
    fallback_app = workflow.compile()
except Exception as init_err:
    logger.error(f"Failed to initialize LangGraph fallback workflow: {init_err}")
    fallback_app = None

async def run_langgraph_fallback(
    category: str,
    messages: List[Dict[str, Any]],
    selected_project: Optional[Dict[str, Any]] = None
) -> str:
    """
    Fallback chat completion runner using LangGraph workflow.
    """
    if not fallback_app:
        from app.services.ai import generate_chat_reply
        return await generate_chat_reply(category, messages, selected_project)
        
    try:
        initial_state = {
            "category": category,
            "messages": messages,
            "selected_project": selected_project,
            "response": ""
        }
        result = await fallback_app.ainvoke(initial_state)
        return result.get("response", "")
    except Exception as e:
        logger.error(f"Error executing LangGraph fallback runner: {e}")
        from app.services.ai import generate_chat_reply
        return await generate_chat_reply(category, messages, selected_project)

async def run_adk_chat(
    chat_id: str,
    user_id: str,
    messages: List[Dict[str, Any]],
    selected_project: Optional[Dict[str, Any]] = None
) -> str:
    """
    Executes the chat session using the Google Cloud ADK agent platform when Vertex AI is active.
    Falls back to LangGraph workflow if Vertex AI is not used or if it fails.
    """
    if settings.ENVIRONMENT == "production" and settings.USE_VERTEX_AI and HAS_ADK:
        try:
            # Find the last user message
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("sender") == "user":
                    last_user_message = msg.get("text", "")
                    break
            
            if last_user_message:
                logger.info(f"🔌 [ADK CHAT RUNNER] Invoking Sarthi root agent via ADK for session {chat_id}...")
                
                # Get or create session
                session = await session_service.get_session(
                    app_name="SarthiApp", 
                    user_id=user_id, 
                    session_id=chat_id
                )
                if not session:
                    session = await session_service.create_session(
                        app_name="SarthiApp", 
                        user_id=user_id, 
                        session_id=chat_id
                    )
                
                user_message = Content(role="user", parts=[Part.from_text(text=last_user_message)])
                run_config = RunConfig(response_modalities=["TEXT"])
                
                # Run ADK agent runner
                events = runner.run(
                    user_id=session.user_id,
                    session_id=session.id,
                    new_message=user_message,
                    run_config=run_config
                )
                
                response_text = ""
                for event in events:
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_text += part.text
                                
                if response_text:
                    logger.info(f"✅ [ADK CHAT RUNNER] Successfully generated chat reply via ADK.")
                    return response_text
                    
        except Exception as adk_err:
            logger.warning(f"⚠️ [ADK CHAT RUNNER] Failed: {adk_err}. Cascading to LangGraph Fallback...")

    # Fallback path (LangGraph)
    category = "general"
    for msg in messages:
        if msg.get("category"):
            category = msg.get("category")
            break
            
    return await run_langgraph_fallback(
        category=category,
        messages=messages,
        selected_project=selected_project
    )


async def stream_adk_chat(
    chat_id: str,
    user_id: str,
    messages: List[Dict[str, Any]],
    selected_project: Optional[Dict[str, Any]] = None
):
    """
    Asynchronously streams the chat session response.
    Cascades to stream_chat_reply as fallback.
    """
    if settings.ENVIRONMENT == "production" and settings.USE_VERTEX_AI and HAS_ADK:
        try:
            # Find the last user message
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("sender") == "user":
                    last_user_message = msg.get("text", "")
                    break
            
            if last_user_message:
                logger.info(f"🌐 [ADK CHAT RUNNER] Invoking Sarthi root agent via ADK for session {chat_id} (Streaming)...")
                
                # Get or create session
                session = await session_service.get_session(
                    app_name="SarthiApp", 
                    user_id=user_id, 
                    session_id=chat_id
                )
                if not session:
                    session = await session_service.create_session(
                        app_name="SarthiApp", 
                        user_id=user_id, 
                        session_id=chat_id
                    )
                
                user_message = Content(role="user", parts=[Part.from_text(text=last_user_message)])
                run_config = RunConfig(response_modalities=["TEXT"])
                
                # Run ADK agent runner
                events = runner.run(
                    user_id=session.user_id,
                    session_id=session.id,
                    new_message=user_message,
                    run_config=run_config
                )
                
                has_yielded = False
                for event in events:
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                has_yielded = True
                                yield part.text
                                
                if has_yielded:
                    logger.info(f"✅ [ADK CHAT RUNNER] Successfully generated chat reply via ADK streaming.")
                    return
                    
        except Exception as adk_err:
            logger.warning(f"⚠️ [ADK CHAT RUNNER] Streaming failed: {adk_err}. Cascading to stream_chat_reply...")

    # Fallback path (streaming chat reply)
    category = "general"
    for msg in messages:
        if msg.get("category"):
            category = msg.get("category")
            break
            
    async for chunk in stream_chat_reply(
        category=category,
        messages=messages,
        selected_project=selected_project
    ):
        yield chunk

