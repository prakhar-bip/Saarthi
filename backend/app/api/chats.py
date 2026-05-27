from fastapi import APIRouter, Depends, HTTPException, status
from app.models.chat import ChatSessionResponse, ChatSessionCreate, MessageSchema
from app.db.mongodb import get_database
from app.api.auth import get_current_user
from app.services.ai import generate_chat_reply, generate_theme_suggestions
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.get("", response_model=list[ChatSessionResponse])
async def list_chats(current_user: dict = Depends(get_current_user)):
    db = get_database()
    cursor = db.chats.find({"user_id": current_user["id"]}).sort("created_at_dt", -1)
    chats = []
    async for doc in cursor:
        chats.append(ChatSessionResponse(
            id=doc["_id"],
            title=doc["title"],
            category=doc["category"],
            messages=doc.get("messages", []),
            created=doc.get("created", ""),
            user_id=doc["user_id"],
            selected_project=doc.get("selected_project"),
            is_confirmed=doc.get("is_confirmed", False),
            project_id=doc.get("project_id")
        ))
    return chats

@router.post("", response_model=ChatSessionResponse)
async def create_chat(payload: ChatSessionCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    chat_id = f"chat-{uuid.uuid4().hex[:8]}"
    created_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    
    initial_messages = []
    if payload.selected_project:
        time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
        features_list = "\n".join([f"- {f}" for f in payload.selected_project.features])
        initial_messages.append({
            "id": f"m-{uuid.uuid4().hex[:8]}",
            "sender": "ai",
            "text": f"Welcome! I have loaded the blueprint for **{payload.selected_project.name}**.\n\n"
                   f"**Core Idea:** {payload.selected_project.idea}\n\n"
                   f"**Proposed Features:**\n{features_list}\n\n"
                   f"**Tech Stack:** {payload.selected_project.tech_stack}\n\n"
                   f"Let's discuss it! What adjustments or additions would you like to make? When you are ready, click **Confirm & Compile** on the right side pane to generate the codebase.",
            "timestamp": time_str
        })
        
    new_chat = {
        "_id": chat_id,
        "title": payload.title,
        "category": payload.category,
        "messages": initial_messages,
        "created": created_str,
        "created_at_dt": datetime.now(timezone.utc),
        "user_id": current_user["id"],
        "selected_project": payload.selected_project.dict() if payload.selected_project else None,
        "is_confirmed": False,
        "project_id": None
    }
    await db.chats.insert_one(new_chat)
    
    return ChatSessionResponse(
        id=chat_id,
        title=new_chat["title"],
        category=new_chat["category"],
        messages=new_chat["messages"],
        created=new_chat["created"],
        user_id=new_chat["user_id"],
        selected_project=new_chat["selected_project"],
        is_confirmed=new_chat["is_confirmed"],
        project_id=new_chat["project_id"]
    )

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    result = await db.chats.delete_one({"_id": chat_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat session not found")
    # Also delete associated projects
    await db.projects.delete_many({"chat_id": chat_id, "user_id": current_user["id"]})
    return {"status": "success", "message": "Chat and related projects deleted successfully"}

@router.post("/{chat_id}/messages")
async def send_message(chat_id: str, message: dict, current_user: dict = Depends(get_current_user)):
    db = get_database()
    chat = await db.chats.find_one({"_id": chat_id, "user_id": current_user["id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    user_msg_text = message.get("text", "")
    if not user_msg_text:
        raise HTTPException(status_code=400, detail="Message text is required")
        
    # Append user message
    time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    user_msg = {
        "id": f"m-{uuid.uuid4().hex[:8]}",
        "sender": "user",
        "text": user_msg_text,
        "timestamp": time_str
    }
    
    await db.chats.update_one(
        {"_id": chat_id},
        {"$push": {"messages": user_msg}}
    )
    
    # Refresh chat object
    updated_chat = await db.chats.find_one({"_id": chat_id})
    
    # Generate AI response
    ai_reply_text = await generate_chat_reply(
        updated_chat["category"], 
        updated_chat["messages"],
        selected_project=updated_chat.get("selected_project")
    )
    
    # Append AI message
    ai_time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    ai_msg = {
        "id": f"m-{uuid.uuid4().hex[:8]}",
        "sender": "ai",
        "text": ai_reply_text,
        "timestamp": ai_time_str
    }
    
    await db.chats.update_one(
        {"_id": chat_id},
        {"$push": {"messages": ai_msg}}
    )
    
    return {"user_message": user_msg, "ai_message": ai_msg}

@router.put("/{chat_id}/messages/{message_id}")
async def edit_message(chat_id: str, message_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    db = get_database()
    chat = await db.chats.find_one({"_id": chat_id, "user_id": current_user["id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    new_text = payload.get("text", "")
    if not new_text:
        raise HTTPException(status_code=400, detail="Text is required")
        
    # Update the specific message item in the array matching the id
    result = await db.chats.update_one(
        {"_id": chat_id, "messages.id": message_id},
        {"$set": {"messages.$.text": new_text}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
        
    return {"status": "success", "text": new_text}

@router.get("/{chat_id}/themes")
async def get_chat_themes(chat_id: str, prompt: str = None, current_user: dict = Depends(get_current_user)):
    db = get_database()
    chat = await db.chats.find_one({"_id": chat_id, "user_id": current_user["id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    blueprint = chat.get("selected_project")
    if not blueprint:
        # Fallback to general info if chat doesn't have a selected blueprint yet
        blueprint = {
            "name": chat.get("title") or "Workspace Project",
            "category": chat.get("category") or "other",
            "features": [],
            "tech_stack": "React, Tailwind, Node.js"
        }
        
    themes = await generate_theme_suggestions(blueprint, custom_prompt=prompt)
    return themes
