import time
import asyncio
from loguru import logger
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from google import genai
from google.genai import types
from app.core.config import settings
import contextvars
import os

# Context variable for LangGraph to inject feedback on retries
current_agent_feedback = contextvars.ContextVar("current_agent_feedback", default=None)
current_tech_stack = contextvars.ContextVar("current_tech_stack", default=None)
current_theme_palette = contextvars.ContextVar("current_theme_palette", default=None)
current_generation_type = contextvars.ContextVar("current_generation_type", default=None)



def map_google_model(model_name: str) -> str:
    """
    Map fictitious and placeholder Gemini model names to valid, existing Google Cloud Vertex AI / AI Studio model IDs.
    Returns comma-separated models for fallbacks where appropriate, keeping the original model as the first choice.
    """
    if not model_name:
        return ""
    
    model_name_lower = model_name.lower()
    
    # Map retired 2.0-flash to stable 2.5-flash or 3.5-flash
    if "gemini-2.0-flash" in model_name_lower:
        return "gemini-2.5-flash,gemini-3.5-flash,gemini-1.5-flash"
    
    # Map fictitious 3.1-pro/3-pro/2.5-pro to stable 2.5-pro or 1.5-pro fallback, preserving original first
    if any(m in model_name_lower for m in ["3.1-pro", "3-pro", "2.5-pro"]):
        fallback_list = [model_name, "gemini-2.5-pro", "gemini-1.5-pro"]
        unique_fallbacks = []
        for f in fallback_list:
            if f not in unique_fallbacks:
                unique_fallbacks.append(f)
        return ",".join(unique_fallbacks)
        
    # Map fictitious 3.5-flash/3-flash/2.5-flash to stable 3.5-flash, 2.5-flash or 1.5-flash fallback, preserving original first
    if any(m in model_name_lower for m in ["3.5-flash", "3-flash", "2.5-flash"]):
        fallback_list = [model_name, "gemini-3.5-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
        unique_fallbacks = []
        for f in fallback_list:
            if f not in unique_fallbacks:
                unique_fallbacks.append(f)
        return ",".join(unique_fallbacks)
        
    return model_name



# Core agent mapping to preferred (provider, model). Hackathon builds default to Gemini 3.
REASONING_MODEL = settings.GOOGLE_REASONING_MODEL or settings.GOOGLE_MODEL
FAST_MODEL = settings.GOOGLE_FAST_MODEL or settings.GOOGLE_MODEL

AGENT_ROUTE_MAPPING: Dict[str, Tuple[str, str]] = {
    # ---------------------------------------------------------
    # TIER 1: COMPLEX TASKS (Code Generation & Compilation)
    # Routed to Vertex AI / Gemini 3.1 Pro Preview
    # ---------------------------------------------------------
    "CodeGenerationPlannerAgent": ("gemini", REASONING_MODEL),
    "DatabaseModelGenerationAgent": ("gemini", FAST_MODEL),
    "BackendCodeGenerationAgent": ("gemini", FAST_MODEL),
    "APIImplementationAgent": ("gemini", FAST_MODEL),
    "FrontendCodeGenerationAgent": ("gemini", FAST_MODEL),
    "UIComponentGenerationAgent": ("gemini", FAST_MODEL),
    "StateImplementationAgent": ("gemini", FAST_MODEL),
    "IntegrationGenerationAgent": ("gemini", FAST_MODEL),
    "BuildCompilationAgent": ("gemini", FAST_MODEL),
    "ProjectExportAgent": ("gemini", FAST_MODEL),
    "CodebaseCompiler": ("gemini", REASONING_MODEL),
    "ValidationArchitectureAgent": ("gemini", FAST_MODEL),

    # ---------------------------------------------------------
    # TIER 2: CHAT, PLANNING & ARCHITECTURE TASKS
    # Routed to OpenRouter for chatting and document templates
    # ---------------------------------------------------------
    "ChatReply": ("openrouter", settings.OPENROUTER_MODEL),
    "CategoryClassifier": ("gemini", FAST_MODEL),
    "ProjectSuggestions": ("openrouter", settings.OPENROUTER_MODEL),
    "PlannerAgent": ("gemini", FAST_MODEL),
    "RequirementAnalyzerAgent": ("gemini", FAST_MODEL),
    "ErrorCorrectionAgent": ("gemini", REASONING_MODEL),
    
    # Architecture component agents
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
    "ThemeGeneratorAgent": ("gemini", FAST_MODEL),
    "DocumentGeneratorAgent": ("gemini", FAST_MODEL),
    "PRDGeneratorAgent": ("gemini", FAST_MODEL),
    "MRDGeneratorAgent": ("gemini", FAST_MODEL),
    "ResearchPlanningAgent": ("gemini", REASONING_MODEL),
    "CodeSynthesizer_Backend": ("gemini", REASONING_MODEL),
    "CodeSynthesizer_Frontend": ("gemini", REASONING_MODEL),
    "CodeSynthesizer_Infrastructure": ("gemini", FAST_MODEL),
    "CodeSynthesizer_ReviewFix": ("gemini", REASONING_MODEL),
    "TRDGeneratorAgent": ("gemini", REASONING_MODEL),
}

# Base global fallback (will be dynamically adjusted based on pref_provider)
FALLBACK_PROVIDERS = ["gemini", "openrouter", "nvidia"]


def get_provider_client(provider: str) -> Any:
    """Return configured client/API object for the requested provider."""
    provider = provider.lower()
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            return None
        return OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/prakhar-bip/Saarthi",
                "X-Title": "Sarthi",
            },
            timeout=120.0
        )
    
    elif provider in ("google", "gemini"):
        if settings.USE_VERTEX_AI:
            kwargs = {"vertexai": True}
            if settings.GCP_PROJECT_ID:
                kwargs["project"] = settings.GCP_PROJECT_ID
            if settings.GCP_LOCATION:
                kwargs["location"] = settings.GCP_LOCATION
            return genai.Client(**kwargs)
        if not settings.GOOGLE_API_KEY:
            return None
        return genai.Client(api_key=settings.GOOGLE_API_KEY)
        
    elif provider == "nvidia":
        if not settings.NVIDIA_API_KEY:
            return None
        return OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=settings.NVIDIA_API_KEY,
            timeout=120.0
        )
    
    return None


def get_default_model(provider: str) -> str:
    """Get the default model string configured for a provider."""
    provider = provider.lower()
    if provider == "openrouter":
        return settings.OPENROUTER_MODEL
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


def _inject_platform_instruction(messages: List[Dict[str, str]]):
    """Inject active platform information into system messages for self-awareness."""
    platform_info = "Google Cloud Vertex AI (via IAM Service Account)" if settings.USE_VERTEX_AI else "Google AI Studio (via Developer API Key)"
    platform_instruction = f"\n\n[SYSTEM CONFIGURATION: You are executing on the {platform_info} platform. If the user asks which platform or API route you are using, answer with this platform name.]"
    
    system_msg = None
    for msg in messages:
        if msg.get("role") == "system":
            system_msg = msg
            break
            
    if system_msg:
        if "[SYSTEM CONFIGURATION:" not in system_msg.get("content", ""):
            system_msg["content"] = system_msg.get("content", "") + platform_instruction
    else:
        messages.insert(0, {"role": "system", "content": f"You are a helpful assistant.{platform_instruction}"})


async def get_raw_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 8000
) -> str:
    """
    Standard direct API client completion call without ADK or LangGraph wrapping.
    """
    _inject_platform_instruction(messages)
    # Feedback injection moved to the top of get_llm_completion to cover all code paths

    # Determine preferred provider and model
    has_google = settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GEMINI_API_KEY")
    if settings.ENVIRONMENT == "production":
        pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
            agent_name, ("gemini", settings.GOOGLE_MODEL)
        )
        if agent_name == "ChatReply":
            # ChatReply uses OpenRouter as primary, fallback to Gemini
            fallback_sequence = ["gemini"]
        else:
            # All other tasks in production MUST strictly use Vertex AI and NOT openrouter
            fallback_sequence = []
    else:  # development
        pref_provider = "openrouter"
        pref_model = settings.OPENROUTER_MODEL
        fallback_sequence = ["gemini", "nvidia"]
    
    # Sequence of providers to try (preferred first, then cascade through fallbacks)
    seen = set()
    providers_to_try = []
    
    for p in [pref_provider] + fallback_sequence:
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
        if provider in ("google", "gemini"):
            model = map_google_model(model)
        models = [m.strip() for m in model.split(",") if m.strip()] if model else []
        if not models:
            continue
            
        start_time = time.perf_counter()
        last_model_error = None
        
        break_provider = False
        for model_item in models:
            if break_provider:
                break
            max_retries = 3
            for retry_attempt in range(max_retries):
                try:
                    reply = None
                    logger.info(f"🌐 [{agent_name}] Attempting call on {provider.upper()} using model {model_item}...")
                    
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
                        
                        response = await client.aio.models.generate_content(
                            model=model_item,
                            contents=contents,
                            config=config
                        )
                        reply = response.text
                    else:
                        completion = await asyncio.to_thread(
                            client.chat.completions.create,
                            model=model_item,
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
                        model=model_item,
                        latency=latency,
                        input_len=input_str_len,
                        output_len=len(reply),
                        status="SUCCESS"
                    )
                    return reply
                    
                except Exception as e:
                    is_retryable = any(keyword in str(e).lower() for keyword in [
                        'rate_limit', 'resource_exhausted', '429', '503', 'timeout',
                        'deadline', 'unavailable', 'overloaded', 'quota'
                    ])
                    if is_retryable and retry_attempt < max_retries - 1:
                        wait_time = (2 ** retry_attempt) * 1.5  # 1.5s, 3s, 6s
                        logger.warning(f"⏳ Retryable error for {agent_name} on {model_item} (attempt {retry_attempt+1}/{max_retries}). Waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    last_model_error = e
                    logger.warning(f"⚠️ Model {model_item} failed on {provider.upper()}: {e}")
                    if "credentials" in str(e).lower() or "default credentials" in str(e).lower():
                        logger.error(f"❌ Credentials/Auth error on {provider.upper()}. Skipping remaining models.")
                        break_provider = True
                    break
                
        # If we exhausted all models for this provider
        latency = time.perf_counter() - start_time
        last_error = f"[{provider.upper()} Error] {last_model_error}"
        log_llm_call(
            agent_name=agent_name,
            provider=provider,
            model=model,
            latency=latency,
            input_len=input_str_len,
            output_len=0,
            status="FAILED",
            error=str(last_model_error)
        )
        logger.warning(f"⚠️ Provider {provider.upper()} failed for {agent_name}. Cascading to fallback...")
        continue
            
    raise RuntimeError(f"All LLM providers failed for agent '{agent_name}'. Last error: {last_error}")


async def stream_raw_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 4000
):
    """
    Standard direct API client completion call with streaming enabled.
    Yields chunks of generated text.
    """
    _inject_platform_instruction(messages)
    # Determine preferred provider and model
    if settings.ENVIRONMENT == "production":
        pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
            agent_name, ("gemini", settings.GOOGLE_MODEL)
        )
        if agent_name == "ChatReply":
            # ChatReply uses OpenRouter as primary, fallback to Gemini
            fallback_sequence = ["gemini"]
        else:
            # All other tasks in production MUST strictly use Vertex AI and NOT openrouter
            fallback_sequence = []
    else:  # development
        pref_provider = "openrouter"
        pref_model = settings.OPENROUTER_MODEL
        fallback_sequence = ["gemini", "nvidia"]
    
    seen = set()
    providers_to_try = []

    for p in [pref_provider] + fallback_sequence:
        norm_p = "google" if p in ("google", "gemini") else p
        if norm_p not in seen:
            seen.add(norm_p)
            providers_to_try.append(p)
    
    last_error = None
    
    for provider in providers_to_try:
        client = get_provider_client(provider)
        if not client:
            continue
            
        model = pref_model if provider == pref_provider else get_default_model(provider)
        if provider in ("google", "gemini"):
            model = map_google_model(model)
        models = [m.strip() for m in model.split(",") if m.strip()] if model else []
        if not models:
            continue
            
        last_model_error = None
        stream_started = False
        
        for model_item in models:
            try:
                logger.info(f"🌐 [{agent_name}] Attempting streaming call on {provider.upper()} using model {model_item}...")
                
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
                    
                    response_stream = await client.aio.models.generate_content_stream(
                        model=model_item,
                        contents=contents,
                        config=config
                    )
                    async for chunk in response_stream:
                        if chunk.text:
                            stream_started = True
                            yield chunk.text
                    return
                    
                else:
                    completion_stream = client.chat.completions.create(
                        model=model_item,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                    for chunk in completion_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            stream_started = True
                            yield chunk.choices[0].delta.content
                    return
                    
            except Exception as e:
                last_model_error = e
                logger.warning(f"⚠️ Model {model_item} streaming failed on {provider.upper()}: {e}")
                if stream_started:
                    logger.error(f"❌ Streaming failed mid-stream for model {model_item}. Cannot fallback.")
                    raise e
                continue
                
        last_error = f"[{provider.upper()} Error] {last_model_error}"
        logger.warning(f"⚠️ Provider {provider.upper()} streaming failed for {agent_name}. Cascading to fallback: {last_model_error}")
        continue
            
    raise RuntimeError(f"All LLM providers failed for streaming agent '{agent_name}'. Last error: {last_error}")



async def get_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 8000
) -> str:
    """
    Primary wrapper for all agents.
    """
    # Extract feedback context from previous attempt if present (enables self-healing globally)
    feedback = current_agent_feedback.get()
    if feedback:
        logger.info(f"[{agent_name}] Injecting retry feedback into prompt at the top of get_llm_completion.")
        if messages:
            messages = [dict(m) for m in messages]
            last_msg = messages[-1]
            last_msg["content"] += f"\n\n--- IMPORTANT FEEDBACK FROM PREVIOUS ATTEMPT ---\n{feedback}\nPlease ensure your JSON output is complete and not truncated."

    has_google = settings.USE_VERTEX_AI or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GEMINI_API_KEY")
    if settings.ENVIRONMENT == "production":
        pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
            agent_name, ("gemini", settings.GOOGLE_MODEL)
        )
    else:  # development
        pref_provider = "openrouter"
        pref_model = settings.OPENROUTER_MODEL
    
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

    # Robust feedback injection before passing to ADK runner or direct API
    if feedback:
        feedback_str = f"\n\n--- IMPORTANT FEEDBACK FROM PREVIOUS ATTEMPT ---\n{feedback}\nPlease ensure your JSON output is complete and not truncated."
        if user_prompt and feedback_str not in user_prompt:
            user_prompt += feedback_str
        if system_instruction and feedback_str not in system_instruction:
            system_instruction += feedback_str

    # 1. Primary path: Google Cloud ADK Agent Runner (Only for Gemini)
    if pref_provider in ("google", "gemini"):
        try:
            # Cleanly skip ADK if credentials are missing to avoid noisy thread stack traces
            if not settings.USE_VERTEX_AI and not settings.GOOGLE_API_KEY and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.environ.get("GEMINI_API_KEY"):
                logger.info(f"⏭️ [ADK RUNNER] Skipping ADK for {agent_name} (No Google Credentials found). Deferring to Fallback.")
                raise ValueError("Google Credentials missing for local dev.")

            if settings.USE_VERTEX_AI:
                try:
                    import google.auth
                    google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                except Exception as credentials_err:
                    logger.info(f"⏭️ [ADK RUNNER] Skipping ADK for {agent_name} (Vertex AI default credentials not found: {credentials_err}). Deferring to Fallback.")
                    raise ValueError("Vertex AI credentials not configured.")

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
            agent_tools = [mongodb_mcp_tool] if agent_name in mcp_enabled_agents else []

            mapped_pref_model = map_google_model(pref_model)
            adk_model = mapped_pref_model.split(",")[0].strip() if mapped_pref_model else pref_model
            adk_agent = ADKAgent(
                name=agent_name,
                model=adk_model,
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
            
            events = await asyncio.to_thread(
                runner.run,
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
            logger.warning(f"⚠️ [ADK RUNNER] Failed for {agent_name}: {adk_err}. Falling back to direct API...")

    # 2. Direct API call (removed wasteful LangGraph StateGraph wrapper)
    return await get_raw_llm_completion(agent_name, messages, temperature, max_tokens)
