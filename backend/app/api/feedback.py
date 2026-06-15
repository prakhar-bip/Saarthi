from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.mongodb import get_database
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    category: str
    rating: int
    message: str
    email: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(payload: FeedbackCreate):
    try:
        db = get_database()
        feedback_id = f"feed-{uuid.uuid4().hex[:8]}"
        
        feedback_doc = {
            "_id": feedback_id,
            "category": payload.category,
            "rating": payload.rating,
            "message": payload.message,
            "email": payload.email,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.feedback.insert_one(feedback_doc)
        return {"status": "success", "id": feedback_id, "message": "Feedback logged successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )
