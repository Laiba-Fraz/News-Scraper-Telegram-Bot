from supabase import create_client, Client

# Replace with your actual Supabase URL and anon key
url = "https://wnueyrkedgvddmpxiqol.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWV5cmtlZGd2ZGRtcHhpcW9sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5MzU5MDMsImV4cCI6MjA2NDUxMTkwM30.23nMoIlF89fC2XYzdVGCeiZLHgLrvDFjkILdE75_Lmw"

supabase: Client = create_client(url, key)

def insert_article(article_data):
    # Include the category in the record dictionary
    record = {
        'title': article_data.get('title'),
        'url': article_data.get('url'),
        'published_at': article_data.get('timestamp'),
        'description': article_data.get('content'),
        'category': article_data.get('category')  # Add category field to the record
    }

    try:
        # Insert the article into the 'articles' table
        response = supabase.table('articles').insert([record]).execute()

        if response.data:
            print("✅ Inserted article:", record['title'])
            return response.data[0]  # Return the inserted article dict
        else:
            print("⚠️ Possibly duplicate or failed insert:", record['title'])
            return None

    except Exception as e:
        # Handle duplicate key errors and other exceptions
        if "duplicate key value violates unique constraint" in str(e):
            print("⏩ Duplicate article skipped:", record['title'])
            return None
        else:
            print("❌ Error inserting article:", e)
            return None

# FUNCTION TO COUNT ARTICLES
def get_article_count():
    try:
        response = supabase.table("articles").select("id", count="exact").execute()
        return response.count
    except Exception as e:
        print("Error fetching article count:", e)
        return 0

def get_filters_for_url(base_url):
    try:
        result = supabase.table("source_sites").select("filters").eq("base_url", base_url).execute()
        if result.data and result.data[0]["filters"]:
            return result.data[0]["filters"]
        else:
            print(f"⚠️ No filters found for {base_url}. Using default empty list.")
            return []  # Fallback to no filters
    except Exception as e:
        print(f"❌ Error fetching filters for {base_url}: {e}")
        return []

# FUNCTION TO FETCH CATEGORIES AND KEYWORDS DYNAMICALLY
def get_categories_and_keywords():
    categories = {}

    # Query to get categories and keywords from Supabase
    response = supabase.table('category_keywords').select('category, keywords').execute()  # Change 'keyword' to 'keywords'

    if response.data:
        # Process each row and build the categories dictionary
        for row in response.data:
            category, keyword_list = row['category'], row['keywords']
            keywords = keyword_list.split(",")  # Split keywords if stored as comma-separated
            categories[category] = keywords
    
    return categories

def get_article_count_by_category(category):
    """Fetch the current article count for a specific category."""
    try:
        response = supabase.table("category_article_count").select("article_count").eq("category", category).execute()
        if response.data:
            return response.data[0]['article_count']  # Return the count of articles for the category
        return 0
    except Exception as e:
        print(f"❌ Error fetching article count for category {category}: {e}")
        return 0


def increment_article_count(category):
    try:
        # Increment article count for the given category
        response = supabase.table("category_article_count").select("article_count").eq("category", category).execute()

        if response.data:
            # Increment the current count
            current_count = response.data[0]["article_count"]
            new_count = current_count + 1

            # Update the article count for the category
            update_response = supabase.table("category_article_count").update({
                "article_count": new_count
            }).eq("category", category).execute()

            if update_response.data:
                print(f"✅ Successfully incremented article count for category: {category}. New count: {new_count}")
            else:
                print(f"❌ Failed to update article count for category: {category}")
        else:
            print(f"❌ No entry found for category: {category}")

    except Exception as e:
        print(f"❌ Error incrementing article count for category {category}: {e}")


def get_category_quota_percentage(category):
    """Get the quota percentage for a specific category."""
    try:
        response = supabase.table("category_article_count").select("quota_percentage").eq("category", category).execute()
        if response.data:
            return response.data[0]['quota_percentage']  # Return the quota percentage for the category
        return 0
    except Exception as e:
        print(f"❌ Error fetching quota percentage for category {category}: {e}")
        return 0

def get_total_articles_posted():
    try:
        # Fetch all category counts and sum them up
        response = supabase.table("category_article_count").select("article_count").execute()
        
        if response.data:
            total_posted = sum([row["article_count"] for row in response.data])
            return total_posted
        else:
            return 0  # If no data, total articles posted is 0

    except Exception as e:
        print(f"❌ Error fetching total posted articles: {e}")
        return 0

# Reset all article counts for each category
def reset_article_counts():
    try:
        # Reset article count to 0 for all categories
        response = supabase.table("category_article_count").update({
            'article_count': 0  # Reset all article counts to 0
        }).execute()
        
        print("✅ All article counts have been reset.")
        return response
    except Exception as e:
        print(f"❌ Error resetting article counts: {e}")
        return None

# Get the count of posts made today (or for a specific date).
def get_daily_post_count(date=None):
    from datetime import datetime  
    if date is None:
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
    else:
        today = date   
    try:
        # Count posts from posting_history where posted_at date equals today
        result = supabase.table("posting_history").select("id", count="exact").gte("posted_at", f"{today} 00:00:00").lt("posted_at", f"{today} 23:59:59").execute()
        
        return result.count if result.count else 0
    except Exception as e:
        print(f"Error getting daily post count: {e}")
        return 0