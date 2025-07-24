from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import crud

router = APIRouter()

class ChannelSchema(BaseModel):
    name: str
    language: Optional[str] = None
    channel_url: Optional[str] = None  
    is_active: bool = True

@router.get("/channels")
def get_channels():
    return crud.get_all_channels()

@router.post("/channels")
def create_channel(channel: ChannelSchema):
    created = crud.create_channel(channel)
    if not created:
        raise HTTPException(status_code=500, detail="Channel creation failed")
    return created

@router.put("/channels/{channel_id}")
def update_channel(channel_id: int, channel: ChannelSchema):
    updated = crud.update_channel(
        channel_id,
        name=channel.name,
        language=channel.language,
        channel_url=channel.channel_url,  
        is_active=channel.is_active
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Update failed")
    return updated

@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int):
    deleted = crud.delete_channel(channel_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Delete failed")
    return {"message": "Channel deleted"}
