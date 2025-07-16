from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import crud

router = APIRouter()

class CategoryKeywordCreate(BaseModel):
    category: str
    keywords: str
    quota_percentage: int = 0

@router.get("/category-keywords")
def get_all_categories():
    return crud.get_all_category_keywords()

@router.post("/category-keywords")
def create_category(category_keyword: CategoryKeywordCreate):
    new_category = crud.create_category_keyword(category_keyword)
    if not new_category:
        raise HTTPException(status_code=500, detail="Failed to create category")
    return new_category

@router.put("/category-keywords/{keyword_id}")
def update_category(keyword_id: int, category_keyword: CategoryKeywordCreate):
    updated = crud.update_category_keyword(
        keyword_id,
        category=category_keyword.category,
        keywords=category_keyword.keywords,
        quota_percentage=category_keyword.quota_percentage
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found or update failed")
    return updated

@router.delete("/category-keywords/{keyword_id}")
def delete_category(keyword_id: int):
    deleted = crud.delete_category_keyword(keyword_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found or delete failed")
    return {"message": "Category deleted"}