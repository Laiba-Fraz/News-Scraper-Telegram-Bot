from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import crud

router = APIRouter()

class CookieSchema(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    expiry: Optional[int] = None
    secure: bool = False
    http_only: bool = False

@router.get("/cookies")
def get_cookies():
    return crud.get_all_cookies()

@router.post("/cookies")
def create_cookie(cookie: CookieSchema):
    created = crud.create_cookie(cookie)
    if not created:
        raise HTTPException(status_code=500, detail="Cookie creation failed")
    return created

@router.put("/cookies/{cookie_id}")
def update_cookie(cookie_id: str, cookie: CookieSchema):
    updated = crud.update_cookie(cookie_id, cookie)
    if not updated:
        raise HTTPException(status_code=404, detail="Update failed")
    return updated

@router.delete("/cookies/{cookie_id}")
def delete_cookie(cookie_id: str):
    deleted = crud.delete_cookie(cookie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Delete failed")
    return {"message": "Cookie deleted"}
