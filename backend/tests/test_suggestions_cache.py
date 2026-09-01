import pytest
import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai import generate_project_suggestions, _SUGGESTIONS_CACHE


@pytest.mark.asyncio
async def test_suggestions_ttl_caching_and_deduplication():
    _SUGGESTIONS_CACHE.clear()

    mock_llm_suggestions = [
        {"name": "App 1", "idea": "Idea 1", "features": ["F1"], "tech_stack": "React, FastAPI"},
        {"name": "App 2", "idea": "Idea 2", "features": ["F2"], "tech_stack": "React, FastAPI"},
    ]

    with patch("app.core.config.settings.GOOGLE_API_KEY", "test-api-key"), \
         patch("app.services.ai.get_llm_completion", new_callable=AsyncMock) as mock_get_llm:
        mock_get_llm.return_value = str(mock_llm_suggestions).replace("'", '"')

        # First call: triggers LLM
        res1 = await generate_project_suggestions("finance")
        assert len(res1) == 2
        assert mock_get_llm.call_count == 1

        # Second call for same category: CACHE HIT (0 LLM calls!)
        res2 = await generate_project_suggestions("finance")
        assert len(res2) == 2
        assert mock_get_llm.call_count == 1  # Still 1 call!

        # Different category: triggers LLM
        res3 = await generate_project_suggestions("health")
        assert mock_get_llm.call_count == 2
