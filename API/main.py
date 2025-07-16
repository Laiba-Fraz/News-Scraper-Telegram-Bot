from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import API.crud as crud
from pydantic import BaseModel
from .routes import source_sites
from fastapi.responses import HTMLResponse
import os
from .routes import channels, posting_history
from .routes import cookies
from .routes import category_keywords
from API.database import supabase

app = FastAPI()
app.include_router(channels.router)
app.include_router(posting_history.router)
app.include_router(cookies.router)
app.include_router(category_keywords.router)



# from fastapi.middleware.cors import CORSMiddleware

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # allow all for now; you can restrict later
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# Serve static files like CSS/JS from API/static folder
#app.mount("/static", StaticFiles(directory="API/static"), name="static")

app.include_router(source_sites.router)

class ApiIn(BaseModel):
    name: str
    url: str
    token: str | None = None

class ApiUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    token: str | None = None

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = Path(__file__).parent / "index.html"
    return index_path.read_text()


@app.get("/apis-list", response_class=HTMLResponse)
async def get_apis_page():
    try:
        apis_page_path = Path(__file__).parent / "apis.html"  # Adjust the path if needed
        return apis_page_path.read_text()  # Serve the HTML content of apis.html
    except Exception as e:
        print("Error in GET:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/apis-data")
def get_apis_list():
    apis = crud.get_all_apis()  # Fetch the API data from the database
    if not apis:
        raise HTTPException(status_code=404, detail="No APIs found")
    return apis


# @app.post("/apis-data")
# def create_api(api: ApiIn):
#     new_api = crud.create_api(api)
#     if new_api:
#         return new_api
#     raise HTTPException(status_code=400, detail="Failed to create API record")

@app.put("/apis-data/{api_id}")
def update_api(api_id: int, api: ApiUpdate):
    updated_api = crud.update_api(
        api_id,
        name=api.name,
        url=api.url,
        token=api.token
    )
    if updated_api:
        return updated_api
    raise HTTPException(status_code=400, detail="Failed to update API record")

@app.delete("/apis-data/{api_id}")
def delete_api(api_id: int):
    deleted = crud.delete_api(api_id)
    if deleted:
        return {"detail": "API record deleted successfully"}
    raise HTTPException(status_code=400, detail="Failed to delete API record")


@app.get("/articles")
def get_articles():
    try:
        response = supabase.table("articles").select("id", "url").execute()
        return response.data
    except Exception as e:
        print("Error fetching articles:", e)
        return []



@app.get("/source_sites", response_class=HTMLResponse)
def get_source_sites_page():
    with open(os.path.join("API", "source_sites.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/channels-page", response_class=HTMLResponse)
def channels_page():
    with open(os.path.join("API", "channels.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/posting_history_page", response_class=HTMLResponse)
def get_posting_history_page():
    with open(os.path.join("API", "posting_history.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

    
@app.get("/cookies-page", response_class=HTMLResponse)
def cookies_page():
    with open(os.path.join("API", "cookies.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/category_keywords", response_class=HTMLResponse)
def get_category_keywords_page():
    with open(os.path.join("API", "category_keywords.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/category_keywords", response_class=HTMLResponse)
def get_category_keywords_page():
    with open(os.path.join("API", "category_keywords.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)
