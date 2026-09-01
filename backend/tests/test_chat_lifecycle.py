import pytest
import os
import sys
from unittest.mock import patch

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.chats import update_chat
from tests.test_validation_backtrack import MockDatabase


@pytest.mark.asyncio
async def test_update_chat_with_temp_optimistic_id_does_not_404():
    """
    Ensure that when frontend sends an update with a temporary optimistic ID (e.g. 'chat-temp-123456'),
    the backend handles it gracefully without throwing a 404 error.
    """
    current_user = {"id": "user-1", "email": "test@sarthi.com"}
    res = await update_chat(
        chat_id="chat-temp-1740000000000",
        payload={"selected_project": {"name": "Test", "idea": "Test idea"}},
        current_user=current_user
    )
    assert res["status"] == "ignored"


@pytest.mark.asyncio
async def test_update_chat_with_real_id_updates_db():
    db = MockDatabase()
    chat_id = "real-chat-id-123"
    current_user = {"id": "user-1", "email": "test@sarthi.com"}

    await db.chats.insert_one({
        "_id": chat_id,
        "user_id": current_user["id"],
        "title": "Initial Chat",
        "category": "other"
    })

    with patch("app.api.chats.get_database", return_value=db):
        res = await update_chat(
            chat_id=chat_id,
            payload={"title": "Updated Chat Title", "category": "finance"},
            current_user=current_user
        )
        assert res["status"] == "success"

        updated = await db.chats.find_one({"_id": chat_id})
        assert updated["title"] == "Updated Chat Title"
        assert updated["category"] == "finance"
