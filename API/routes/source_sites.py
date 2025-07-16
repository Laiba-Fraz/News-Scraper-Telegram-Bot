from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import crud

router = APIRouter()

class SourceSiteCreate(BaseModel):
    name: str
    base_url: str
    filters: Optional[str] = None
    is_active: bool = True

@router.get("/source-sites")
def get_all_sites():
    return crud.get_all_source_sites()

# @router.post("/source-sites")
# def create_site(site: SourceSiteCreate):
#     new_site = crud.create_source_site(site)
#     if not new_site:
#         raise HTTPException(status_code=500, detail="Failed to create site")
#     return new_site

@router.put("/source-sites/{site_id}")
def update_site(site_id: int, site: SourceSiteCreate):
    updated = crud.update_source_site(
        site_id,
        name=site.name,
        base_url=site.base_url,
        filters=site.filters,
        is_active=site.is_active
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Site not found or update failed")
    return updated

@router.delete("/source-sites/{site_id}")
def delete_site(site_id: int):
    deleted = crud.delete_source_site(site_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Site not found or delete failed")
    return {"message": "Site deleted"}
