import logging
from typing import List, Dict, Any, Optional
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents.run_config import RunConfig
from google.genai.types import Content, Part

from app.core.config import settings
from app.services.ai import generate_theme_suggestions

logger = logging.getLogger(__name__)

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

# 2. Initialize the Root ADK Agent
sarthi_agent = Agent(
    name="Sarthi",
    model=settings.GOOGLE_MODEL or "gemini-2.5-flash",
    instruction=(
        "You are Sarthi, an expert AI development partner for hackathons specializing in software architecture and code compilation.\n"
        "First, analyze the user's message to determine their specific intent (e.g. brainstorming, refining features, writing code, technical layout discussion).\n"
        "Maintain continuity with prior chat messages: restate relevant confirmed decisions, update assumptions when the user changes direction, and keep the blueprint internally consistent for the compiler agents.\n"
        "When the user proposes a change, translate it into concrete feature, data, API, UI, auth, realtime, or deployment implications.\n"
        "Decide the most suitable response format based on your analysis:\n"
        "- Use clean, conversational paragraphs for explanations and feedback.\n"
        "- Use bullet points / numbered lists for step-by-step guides, checklists, or pros/cons.\n"
        "- Use code blocks for code snippets, commands, or data formats.\n"
        "- CRITICAL: Do NOT use markdown tables to respond to general queries, questions, or refinements. Only use tables if the user explicitly requests structured tabular data.\n\n"
        "Keep your responses concise, friendly, and structured. End with a note suggesting to confirm and compile the codebase when ready."
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
    
    class FallbackState(Dict[str, Any]):
        category: str
        messages: List[Dict[str, str]]
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
    workflow = StateGraph(dict)
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
    Executes a chat message session using the Google ADK runner.
    Falls back to LangGraph orchestration in case of failure.
    """
    # Extract category for fallback routing
    category = "general"
    for msg in messages:
        if msg.get("category"):
            category = msg.get("category")
            break
            
    try:
        session_id = chat_id
        
        # Ensure session exists
        try:
            session = session_service.get_session(app_name="SarthiApp", session_id=session_id)
        except Exception:
            session = session_service.create_session(app_name="SarthiApp", user_id=user_id, session_id=session_id)
            
        # Extract the latest message from the user
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("sender") == "user":
                last_user_msg = msg.get("text", "")
                break
                
        if not last_user_msg:
            return "Hello! How can I help you with your project today?"

        # We construct the content to pass to the runner including blueprint context
        blueprint_ctx = ""
        if selected_project:
            blueprint_ctx = (
                f"\n\n[Active Project Blueprint Context]\n"
                f"Name: {selected_project.get('name')}\n"
                f"Core Idea: {selected_project.get('idea')}\n"
                f"Key Features: {', '.join(selected_project.get('features', []))}\n"
                f"Suggested Tech Stack: {selected_project.get('tech_stack')}\n"
            )
            
        full_prompt = f"{last_user_msg}{blueprint_ctx}"
        
        # Prepare message in Vertex/Gemini schema
        user_message = Content(role="user", parts=[Part.from_text(text=full_prompt)])
        run_config = RunConfig(response_modalities=["TEXT"])
        
        # Run ADK Agent
        events = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
            run_config=run_config
        )
        
        # Collect response text
        response_text = ""
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                        
        if not response_text:
            raise ValueError("No response returned from ADK agent runner")
            
        return response_text
        
    except Exception as e:
        logger.error(f"Error running ADK Agent: {e}. Falling back to LangGraph orchestration...")
        return await run_langgraph_fallback(
            category=category,
            messages=messages,
            selected_project=selected_project
        )
