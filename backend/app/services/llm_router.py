import time
import logging
import json
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

# Core agent mapping to preferred (provider, model)
AGENT_ROUTE_MAPPING: Dict[str, Tuple[str, str]] = {
    # High-reasoning and planning agents
    "PlannerAgent": ("openrouter", "google/gemini-2.0-flash-001"),
    "RequirementAnalyzerAgent": ("openrouter", "google/gemini-flash-1.5"),
    "CodeGenerationPlannerAgent": ("openrouter", "google/gemini-2.0-flash-001"),
    "ValidationArchitectAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "DatabaseModelGenerationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "BackendCodeGenerationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "APIImplementationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "FrontendCodeGenerationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "UIComponentGenerationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "StateImplementationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "IntegrationGenerationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "BuildCompilationAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "ErrorCorrectionAgent": ("google", "gemini-1.5-flash"),
    "ProjectExportAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),

    # Code generation and architectural component agents
    "FrontendArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "BackendArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "DbArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "DevOpsArchitectAgent": ("nvidia", "google/gemma-2-27b-it"),
    "RealtimeArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "StateArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "AuthArchitectAgent": ("openrouter", "openai/gpt-oss-120b:free"),
    "SecurityArchitectAgent": ("nvidia", "meta/llama-3.3-70b-instruct"),
    "ApiAgent": ("openrouter", "openai/gpt-oss-120b:free"),

    # Fast agents / Optimization / Testing
    "UiUxArchitectAgent": ("nvidia", "google/gemma-2-9b-it"),
    "OptimizationArchitectAgent": ("groq", "llama-3.3-70b-versatile"),
    "TestingArchitectureAgent": ("groq", "llama-3.3-70b-versatile"),

    # App core utilities
    "ChatReply": ("groq", "llama-3.3-70b-versatile"),
    "ProjectSuggestions": ("nvidia", "google/gemma-2-9b-it"),
    "CodebaseCompiler": ("openrouter", "openai/gpt-oss-120b:free"),
}

# Fallback sequence to try other providers if preferred fails or is not configured
FALLBACK_PROVIDERS = ["groq", "nvidia", "openrouter", "google"]


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
    
    elif provider == "google":
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
    elif provider == "google":
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


async def get_llm_completion(
    agent_name: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 3000
) -> str:
    """
    Routes an LLM completion call dynamically based on the calling agent.
    Implements cascading fallbacks and transparent logging.
    """
    # 1. Determine preferred provider and model
    pref_provider, pref_model = AGENT_ROUTE_MAPPING.get(
        agent_name, ("openrouter", settings.OPENROUTER_MODEL)
    )
    
    # Sequence of providers to try (preferred first, then cascade through fallbacks)
    providers_to_try = [pref_provider] + [p for p in FALLBACK_PROVIDERS if p != pref_provider]
    
    last_error = None
    input_str_len = sum(len(m.get("content", "")) for m in messages)
    
    for provider in providers_to_try:
        client = get_provider_client(provider)
        if not client:
            # Skip if key is not configured
            continue
            
        model = pref_model if provider == pref_provider else get_default_model(provider)
        start_time = time.perf_counter()
        
        try:
            logger.info(f"🌐 [{agent_name}] Attempting call on {provider.upper()} using model {model}...")
            
            if provider == "google":
                # Convert messages format to Google GenAI SDK format
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
                
                # Setup model configuration
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
                # OpenAI-compatible completions format (Nvidia, Groq, OpenRouter)
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
            
    # If all providers failed
    raise RuntimeError(f"All LLM providers failed for agent '{agent_name}'. Last error: {last_error}")
