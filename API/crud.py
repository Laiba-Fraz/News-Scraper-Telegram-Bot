from API.database import supabase

TABLE_NAME = "apis"

def get_all_apis():
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        print("Fetched APIs:", response.data) 
        return response.data 
    except Exception as e:
        print("Error in get_all_apis:", e)
        return []

def update_api(api_id: int, name: str = None, url: str = None, token: str = None):
    try:
        data = {}
        if name: data["name"] = name
        if url: data["url"] = url
        if token: data["token"] = token
        response = supabase.table(TABLE_NAME).update(data).eq("id", api_id).execute()
        return response.data
    except Exception as e:
        print("Error in update_api:", e)
        return None

def delete_api(api_id: int):
    try:
        response = supabase.table(TABLE_NAME).delete().eq("id", api_id).execute()
        return response.data
    except Exception as e:
        print("Error in delete_api:", e)
        return None


# ---------- SOURCE SITES CRUD ----------
def get_all_source_sites():
    try:
        response = supabase.table("source_sites").select("*").execute()
        return response.data
    except Exception as e:
        print("Error in get_all_source_sites:", e)
        return []

def update_source_site(site_id: int, name: str = None, base_url: str = None, filters: str = None, is_active: bool = None):
    try:
        data = {}
        if name is not None: data["name"] = name
        if base_url is not None: data["base_url"] = base_url
        if filters is not None: data["filters"] = filters
        if is_active is not None: data["is_active"] = is_active

        response = supabase.table("source_sites").update(data).eq("id", site_id).execute()
        return response.data
    except Exception as e:
        print("Error in update_source_site:", e)
        return None

def delete_source_site(site_id: int):
    try:
        response = supabase.table("source_sites").delete().eq("id", site_id).execute()
        return response.data
    except Exception as e:
        print("Error in delete_source_site:", e)
        return None

# ---------- CHANNELS CRUD ----------

def get_all_channels():
    try:
        response = supabase.table("channels").select("*").execute()
        return response.data
    except Exception as e:
        print("Error in get_all_channels:", e)
        return []

def create_channel(channel):
    data = {
        "name": channel.name,
        "language": channel.language,
        "channel_url": channel.channel_url,
        "is_active": channel.is_active
    }
    response = supabase.table("channels").insert(data).execute()
    return response.data[0] if response.data else None

def update_channel(channel_id: int, name: str = None, language: str = None, is_active: bool = None, channel_url: str = None):
    try:
        data = {}
        if name is not None: data["name"] = name
        if language is not None: data["language"] = language
        if is_active is not None: data["is_active"] = is_active
        if channel_url is not None: data["channel_url"] = channel_url

        response = supabase.table("channels").update(data).eq("id", channel_id).execute()
        return response.data
    except Exception as e:
        print("Error in update_channel:", e)
        return None

def delete_channel(channel_id: int):
    try:
        response = supabase.table("channels").delete().eq("id", channel_id).execute()
        return response.data
    except Exception as e:
        print("Error in delete_channel:", e)
        return None

# ---------- POSTING HISTORY CRUD----------

def get_all_posting_history():
    try:
        response = (
            supabase
            .table("posting_history")
            .select("*")
            .order("posted_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print("Error in get_all_posting_history:", e)
        return []

def add_posting_history(history):
    try:
        # Prepare data for insertion, including article_title and channel_name
        data = {
            "article_id": history.article_id,
            "channel_id": history.channel_id,
            "article_url": history.article_url,  
            "article_title": history.article_title,  
            "channel_name": history.channel_name 
        }

        # Insert data into posting_history table
        response = supabase.table("posting_history").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print("Error in add_posting_history:", e)
        return None

def log_posting(article_id: int, channel_ids: list[int]):
    try:
        # Fetch the article URL and title from the articles table using article_id
        article_data = supabase.table("articles").select("url", "title").eq("id", article_id).execute()
        article_url = article_data.data[0]["url"] if article_data.data else None
        article_title = article_data.data[0]["title"] if article_data.data else "Unknown"

        # Prepare the records to insert, including article_url, article_title, and channel_name
        records = []
        for ch_id in channel_ids:
            # Fetch the channel name from the channels table using channel_id
            channel_data = supabase.table("channels").select("name").eq("id", ch_id).execute()
            channel_name = channel_data.data[0]["name"] if channel_data.data else "Unknown"

            # Add the record with all required fields
            records.append({
                "article_id": article_id,
                "article_url": article_url,
                "article_title": article_title,
                "channel_id": ch_id,
                "channel_name": channel_name
            })
        
        # Insert the records into posting_history table
        supabase.table("posting_history").insert(records).execute()

    except Exception as e:
        print("Error in log_posting:", e)


# ---------- COOKIES CRUD ----------

def get_all_cookies():
    try:
        response = supabase.table("telegram_cookies").select("*").execute()
        return response.data
    except Exception as e:
        print("Error in get_all_cookies:", e)
        return []

def create_cookie(cookie):
    try:
        data = {
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "expiry": cookie.expiry,
            "secure": cookie.secure,
            "http_only": cookie.http_only,
        }
        response = supabase.table("telegram_cookies").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print("Error in create_cookie:", e)
        return None

def update_cookie(cookie_id: str, cookie):
    try:
        data = {
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "expiry": cookie.expiry,
            "secure": cookie.secure,
            "http_only": cookie.http_only,
        }
        response = supabase.table("telegram_cookies").update(data).eq("id", cookie_id).execute()
        return response.data
    except Exception as e:
        print("Error in update_cookie:", e)
        return None

def delete_cookie(cookie_id: str):
    try:
        response = supabase.table("telegram_cookies").delete().eq("id", cookie_id).execute()
        return response.data
    except Exception as e:
        print("Error in delete_cookie:", e)
        return None


# ---------- CATEGORY KEYWORDS CRUD ----------
def get_all_category_keywords():
    try:
        # Get all category keywords
        keywords_response = supabase.table("category_keywords").select("*").execute()
        
        if not keywords_response.data:
            return []
        
        result = []
        for item in keywords_response.data:
            # Get quota_percentage for this category from category_article_count table
            quota_response = supabase.table("category_article_count").select("quota_percentage").eq("category", item["category"]).execute()
            
            quota = 0  # Default value
            if quota_response.data:
                quota = quota_response.data[0]["quota_percentage"]
            
            result.append({
                "id": item["id"],
                "category": item["category"],
                "keywords": item["keywords"],
                "quota_percentage": quota
            })
        
        return result
    except Exception as e:
        print("Error in get_all_category_keywords:", e)
        return []

def create_category_keyword(category_keyword):
    try:
        # Insert into category_keywords table
        keywords_data = {
            "category": category_keyword.category,
            "keywords": category_keyword.keywords
        }
        keywords_response = supabase.table("category_keywords").insert(keywords_data).execute()
        
        # Check if category exists in category_article_count, if not create it
        existing_count = supabase.table("category_article_count").select("*").eq("category", category_keyword.category).execute()
        
        if not existing_count.data:
            count_data = {
                "category": category_keyword.category,
                "quota_percentage": getattr(category_keyword, 'quota_percentage', 0),
                "article_count": 0
            }
            supabase.table("category_article_count").insert(count_data).execute()
        
        return keywords_response.data[0] if keywords_response.data else None
    except Exception as e:
        print("Error in create_category_keyword:", e)
        return None

def update_category_keyword(keyword_id: int, category: str = None, keywords: str = None, quota_percentage: int = None):
    try:
        # Get current category name
        current = supabase.table("category_keywords").select("category").eq("id", keyword_id).execute()
        if not current.data:
            return None
        
        current_category = current.data[0]["category"]
        
        # Update category_keywords table
        keywords_data = {}
        if category is not None: keywords_data["category"] = category
        if keywords is not None: keywords_data["keywords"] = keywords
        
        if keywords_data:
            supabase.table("category_keywords").update(keywords_data).eq("id", keyword_id).execute()
        
        # Update quota_percentage in category_article_count table
        if quota_percentage is not None:
            target_category = category if category is not None else current_category
            supabase.table("category_article_count").update({"quota_percentage": quota_percentage}).eq("category", target_category).execute()
        
        return {"success": True}
    except Exception as e:
        print("Error in update_category_keyword:", e)
        return None

def delete_category_keyword(keyword_id: int):
    try:
        response = supabase.table("category_keywords").delete().eq("id", keyword_id).execute()
        return response.data
    except Exception as e:
        print("Error in delete_category_keyword:", e)
        return None