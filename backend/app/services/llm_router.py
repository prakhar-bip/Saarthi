import time
import logging
import json
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

# Core agent mapping to preferred (provider, model). Hackathon builds default to Gemini 3.
REASONING_MODEL = settings.GOOGLE_REASONING_MODEL or settings.GOOGLE_MODEL
FAST_MODEL = settings.GOOGLE_FAST_MODEL or settings.GOOGLE_MODEL

AGENT_ROUTE_MAPPING: Dict[str, Tuple[str, str]] = {
    # High-reasoning and planning agents → gemini-2.5-pro
    "PlannerAgent": ("gemini", REASONING_MODEL),
    "RequirementAnalyzerAgent": ("gemini", REASONING_MODEL),
    "CodeGenerationPlannerAgent": ("gemini", REASONING_MODEL),
    "ErrorCorrectionAgent": ("gemini", REASONING_MODEL),

    # Code generation agents → gemini-2.5-flash (fast + capable)
    "DatabaseModelGenerationAgent": ("gemini", FAST_MODEL),
    "BackendCodeGenerationAgent": ("gemini", FAST_MODEL),
    "APIImplementationAgent": ("gemini", FAST_MODEL),
    "FrontendCodeGenerationAgent": ("gemini", FAST_MODEL),
    "UIComponentGenerationAgent": ("gemini", FAST_MODEL),
    "StateImplementationAgent": ("gemini", FAST_MODEL),
    "IntegrationGenerationAgent": ("gemini", FAST_MODEL),
    "BuildCompilationAgent": ("gemini", FAST_MODEL),
    "ProjectExportAgent": ("gemini", FAST_MODEL),
    "ValidationArchitectureAgent": ("gemini", FAST_MODEL),

    # Architecture component agents → gemini-2.5-flash
    "FrontendArchitectureAgent": ("gemini", FAST_MODEL),
    "BackendArchitectureAgent": ("gemini", FAST_MODEL),
    "DatabaseArchitectureAgent": ("gemini", FAST_MODEL),
    "DevOpsArchitectureAgent": ("gemini", FAST_MODEL),
    "RealtimeArchitectureAgent": ("gemini", FAST_MODEL),
    "StateManagementAgent": ("gemini", FAST_MODEL),
    "AuthArchitectureAgent": ("gemini", FAST_MODEL),
    "SecurityArchitectureAgent": ("gemini", FAST_MODEL),
    "APIAgent": ("gemini", FAST_MODEL),

    # Fast agents / Optimization / Testing / Styling
    "UIUXArchitectAgent": ("gemini", FAST_MODEL),
    "OptimizationArchitectureAgent": ("gemini", FAST_MODEL),
    "TestingArchitectureAgent": ("gemini", FAST_MODEL),

    # App core utilities / features — fastest path
    "ChatReply": ("gemini", FAST_MODEL),
    "CategoryClassifier": ("gemini", FAST_MODEL),
    "ProjectSuggestions": ("gemini", FAST_MODEL),
    "CodebaseCompiler": ("gemini", REASONING_MODEL),
    "ThemeGeneratorAgent": ("gemini", FAST_MODEL),
    "DocumentGeneratorAgent": ("gemini", FAST_MODEL),
}

# Fallback sequence: try Groq first (fast & reliable), then OpenRouter, then Nvidia
FALLBACK_PROVIDERS = ["gemini", "groq", "openrouter", "nvidia"]


def get_provider_client(provider: str) -> Any:
    """Return configured client/API object for the requested provider."""
    provider = provider.lower()
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            return None
        return OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            timeout=30.0
        )
    
    elif provider == "groq":
        if not settings.GROQ_API_KEY:
            return None
        return OpenAI(
            base_url=settings.GROQ_BASE_URL,
            api_key=settings.GROQ_API_KEY,
            timeout=30.0
        )
    
    elif provider in ("google", "gemini"):
        if settings.GCP_PROJECT_ID:
            return genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_LOCATION
            )
        if not settings.GOOGLE_API_KEY:
            return None
        return genai.Client(api_key=settings.GOOGLE_API_KEY)
        
    elif provider == "nvidia":
        if not settings.NVIDIA_API_KEY:
            return None
        return OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=settings.NVIDIA_API_KEY,
            timeout=30.0
        )
    
    return None


def get_default_model(provider: str) -> str:
    """Get the default model string configured for a provider."""
    provider = provider.lower()
    if provider == "openrouter":
        return settings.OPENROUTER_MODEL
    elif provider == "groq":
        return settings.GROQ_MODEL
    elif provider in ("google", "gemini"):
        return settings.GOOGLE_MODEL
    elif provider == "nvidia":
        return settings.NVIDIA_MODEL
    return ""


def log_llm_call(
    agent_name: str, 
    provider: str, 
    model: str, 
    latency: float, 
    input_len: int, 
    output_len: int, 
    status: str, 
    error: str = None
):
    """Log LLM call details beautifully with emojis and token approximations."""
    est_prompt_tokens = int(input_len / 4)
    est_completion_tokens = int(output_len / 4)
    
    logger.info("==================================================")
    if status == "SUCCESS":
        logger.info(f"🔌 [LLM API CALL SUCCESS] Agent: {agent_name}")
        logger.info(f"🔹 Provider: {provider.upper()} | Model: {model}")
        logger.info(f"🔹 Latency: {latency:.2f}s")
        logger.info(f"🔹 Est. Tokens: Prompt {est_prompt_tokens} | Completion {est_completion_tokens} | Total {est_prompt_tokens + est_completion_tokens}")
    else:
        logger.info(f"❌ [LLM API CALL FAILED] Agent: {agent_name}")
        logger.info(f"🔹 Provider: {provider.upper()} | Model: {model}")
        logger.info(f"🔹 Latency: {latency:.2f}s")
        logger.info(f"🔹 Error Detail: {error}")
    logger.info("==================================================")


async def get_raw_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 3000
) -> str:
    """
    Standard direct API client completion call without ADK or LangGraph wrapping.
    """
    # Determine preferred provider and model
    pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
        agent_name, ("gemini", settings.GOOGLE_MODEL)
    )
    
    # Sequence of providers to try (preferred first, then cascade through fallbacks)
    seen = set()
    providers_to_try = []
    for p in [pref_provider] + FALLBACK_PROVIDERS:
        norm_p = "google" if p in ("google", "gemini") else p
        if norm_p not in seen:
            seen.add(norm_p)
            providers_to_try.append(p)
    
    last_error = None
    input_str_len = sum(len(m.get("content", "")) for m in messages)
    
    for provider in providers_to_try:
        client = get_provider_client(provider)
        if not client:
            continue
            
        model = pref_model if provider == pref_provider else get_default_model(provider)
        start_time = time.perf_counter()
        
        try:
            logger.info(f"🌐 [{agent_name}] Attempting call on {provider.upper()} using model {model}...")
            
            if provider in ("google", "gemini"):
                system_instruction = None
                contents = []
                
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    if role == "system":
                        system_instruction = content
                    else:
                        role_mapped = "model" if role == "assistant" else "user"
                        contents.append(
                            types.Content(
                                role=role_mapped,
                                parts=[types.Part.from_text(text=content)]
                            )
                        )
                
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                reply = response.text
                
            else:
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                reply = completion.choices[0].message.content
                
            if not reply:
                raise ValueError("Received empty or null response content")
                
            latency = time.perf_counter() - start_time
            log_llm_call(
                agent_name=agent_name,
                provider=provider,
                model=model,
                latency=latency,
                input_len=input_str_len,
                output_len=len(reply),
                status="SUCCESS"
            )
            return reply
            
        except Exception as e:
            latency = time.perf_counter() - start_time
            last_error = f"[{provider.upper()} Error] {e}"
            log_llm_call(
                agent_name=agent_name,
                provider=provider,
                model=model,
                latency=latency,
                input_len=input_str_len,
                output_len=0,
                status="FAILED",
                error=str(e)
            )
            logger.warning(f"⚠️ Provider {provider.upper()} failed for {agent_name}. Cascading to fallback...")
            continue
            
    raise RuntimeError(f"All LLM providers failed for agent '{agent_name}'. Last error: {last_error}")


async def get_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 3000
) -> str:
    """
    Primary wrapper for all agents. 
    Attempts ADK Agent runner first, falls back to LangGraph workflow, 
    and finally cascades to the standard direct LLM completion client.
    """
    pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
        agent_name, ("gemini", settings.GOOGLE_MODEL)
    )
    
    # Extract system and user contents
    system_instruction = ""
    user_prompt = ""
    for m in messages:
        if m.get("role") == "system":
            system_instruction = m.get("content", "")
        elif m.get("role") == "user":
            user_prompt = m.get("content", "")
            
    # If user prompt is empty, join all user messages or use system instructions
    if not user_prompt:
        user_prompt = "\n".join([m.get("content", "") for m in messages if m.get("role") == "user"])
    if not user_prompt:
        user_prompt = "Perform action according to instructions."

    # 1. Primary path: Google Cloud ADK Agent Runner
    try:
        from google.adk.agents.llm_agent import Agent as ADKAgent
        from google.adk.runners import Runner as ADKRunner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.adk.agents.run_config import RunConfig
        from google.genai.types import Content, Part
        from app.services.mcp_service import mcp_client
        import json
        
        logger.info(f"🔌 [ADK RUNNER] Invoking {agent_name}...")
        
        async def mongodb_mcp_tool(tool_name: str, arguments_json: str = "{}") -> str:
            """
            Query the MongoDB database via the MCP protocol. 
            Use this tool to inspect schemas, read user data, or update records to accomplish real-world tasks.
            """
            try:
                args = json.loads(arguments_json) if arguments_json else {}
                return await mcp_client.execute_tool(tool_name, args)
            except Exception as e:
                return f"Failed to execute MongoDB MCP tool: {e}"
        
        # Inject MCP superpowers into planning, architecture, generation, build, and export agents.
        mcp_enabled_agents = [
            "PlannerAgent",
            "RequirementAnalyzerAgent",
            "DatabaseArchitectureAgent",
            "BackendArchitectureAgent",
            "APIAgent",
            "CodeGenerationPlannerAgent",
            "DatabaseModelGenerationAgent",
            "BackendCodeGenerationAgent",
            "APIImplementationAgent",
            "BuildCompilationAgent",
            "ProjectExportAgent",
            "CodebaseCompiler",
        ]
        agent_tools = [mongodb_mcp_tool] if agent_name in mcp_enabled_agents else None

        adk_agent = ADKAgent(
            name=agent_name,
            model=pref_model,
            instruction=system_instruction or "You are a helpful software compiler agent.",
            tools=agent_tools
        )
        session_service = InMemorySessionService()
        runner = ADKRunner(
            app_name=f"{agent_name}App",
            agent=adk_agent,
            session_service=session_service
        )
        session = await session_service.create_session(app_name=f"{agent_name}App", user_id="system_user")
        user_message = Content(role="user", parts=[Part.from_text(text=user_prompt)])
        run_config = RunConfig(response_modalities=["TEXT"])
        
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
                        
        if not response_text:
            raise ValueError("ADK runner returned empty response")
            
        logger.info(f"✅ [ADK RUNNER] Completed {agent_name} successfully.")
        return response_text
        
    except Exception as adk_err:
        logger.warning(f"⚠️ [ADK RUNNER] Failed for {agent_name}: {adk_err}. Cascading to LangGraph Fallback...")

    # 2. Secondary path: LangGraph StateGraph Workflow
    try:
        from langgraph.graph import StateGraph, END
        
        logger.info(f"🔌 [LANGGRAPH FALLBACK] Orchestrating {agent_name}...")
        
        async def call_router_fallback(state: dict) -> dict:
            res = await get_raw_llm_completion(agent_name, messages, temperature, max_tokens)
            return {"response": res}
            
        workflow = StateGraph(dict)
        workflow.add_node("call_llm", call_router_fallback)
        workflow.set_entry_point("call_llm")
        workflow.add_edge("call_llm", END)
        fallback_app = workflow.compile()
        
        result = await fallback_app.ainvoke({"messages": messages})
        response_text = result.get("response", "")
        if not response_text:
            raise ValueError("LangGraph fallback returned empty response")
            
        logger.info(f"✅ [LANGGRAPH FALLBACK] Completed {agent_name} successfully.")
        return response_text
        
    except Exception as lg_err:
        logger.warning(f"⚠️ [LANGGRAPH FALLBACK] Failed for {agent_name}: {lg_err}. Cascading to raw API call...")

    # 3. Tertiary path: Direct Raw Fallback
    return await get_raw_llm_completion(agent_name, messages, temperature, max_tokens)
