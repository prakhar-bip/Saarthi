import asyncio
import os
import sys

# Ensure backend/app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_router import get_llm_completion
from app.agents.requirement_analyzer import RequirementAnalyzerAgent

async def main():
    print("Testing get_llm_completion fallback logic...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Respond with the word 'SUCCESS' and nothing else."},
        {"role": "user", "content": "Confirm you are working."}
    ]
    try:
        reply = await get_llm_completion(
            agent_name="RequirementAnalyzerAgent",
            messages=messages,
            temperature=0.1
        )
        print("Reply received:", reply)
    except Exception as e:
        print("Failed to get completion:", e)

    print("\nTesting RequirementAnalyzerAgent...")
    try:
        agent = RequirementAnalyzerAgent()
        blueprint = {
            "name": "Todo App",
            "idea": "I want to build a simple Todo app in Flask with MongoDB.",
            "features": ["Create todo", "Update todo status", "Delete todo"],
            "tech_stack": "Flask, MongoDB"
        }
        result = await agent.analyze(blueprint)
        import json
        print("Agent analysis result keys:", list(result.keys()))
        print("Handoff details:", result.get("agent_handoff", {}).get("agent"))
    except Exception as e:
        print("Agent failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
