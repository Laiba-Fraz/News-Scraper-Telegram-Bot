from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import crud

router = APIRouter()

from typing import Optional

class PostingHistorySchema(BaseModel):
    article_id: int
    channel_id: int
    article_url: Optional[str] = None


@router.get("/posting-history")
def get_history():
    return crud.get_all_posting_history()

@router.post("/posting-history")
def add_history(entry: PostingHistorySchema):
    added = crud.add_posting_history(entry)
    if not added:
        raise HTTPException(status_code=500, detail="Failed to record posting")
    return added
