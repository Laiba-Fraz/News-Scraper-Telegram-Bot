# Import scraping functions from site scripts
from site1 import scrape_site1
from site2 import scrape_site2
from site3 import scrape_site3
from db_handler import insert_article  # Keep this as is, even if not used here
from db_handler import get_article_count, get_article_count_by_category, get_category_quota_percentage, increment_article_count

from telegram_selenium_sender import send_telegram_message_selenium
import schedule
import time
import random
import db_handler
import datetime


# Global counter to keep track of how many articles have been posted
total_posted_count = 0

import datetime
import time

# # def wait_until_10am_gmt3():
#     # Get the current time in GMT+3
#     # now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
#     now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4)))
    
#     # Calculate the time for the next 10:00 AM GMT+3
#     # target_time = now.replace(hour=10, minute=0, second=0, microsecond=0) 
#     target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
     
#     # If it's already past 10:00 AM today, make the first post immediately
#     if now >= target_time:
#         print("✅ It's already past 08:00 AM GMT+3. Posting the first article immediately.")
#         return  # Skip waiting, proceed with the first post
    
#     # If it's before 10:00 AM, calculate the time difference and wait
#     time_diff = target_time - now
#     print(f"⏳ Waiting for {time_diff} to post the first article at 10:00 AM GMT+3.")
    
#     # Sleep until 10:00 AM GMT+3
#     time.sleep(time_diff.total_seconds())

def wait_until_8am():
    now = datetime.datetime.now()

    # Create today’s 8:00 AM time
    target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)

    if now < target_time:
        # If current time is before 8 AM, wait until 8 AM today
        time_diff = target_time - now
        print(f"⏳ Waiting for {time_diff} to reach 8:00 AM local time.")
        time.sleep(time_diff.total_seconds())
    else:
        # If it's already 8 AM or later, post immediately
        print("✅ It's already past 8:00 AM. Posting immediately.")

def reset_article_count_if_needed():
    global total_posted_count
    if total_posted_count >= 100:
        print("✅ Resetting article counts for all categories...")

        # Reset article count to 0 for all categories
        db_handler.supabase.table("category_article_count").update({
            'article_count': 0  # Reset all article counts to 0
        }).execute()

        # Reset the global posted count
        total_posted_count = 0  # Reset the total post count

def scrape_all_sites():
    """
    Scrape data from all three websites sequentially.
    """
    before = get_article_count()
    print(f"✅ {before} existing entries.\n")

    all_new_articles = []

    print("Scraping Site 1...")
    articles1 = scrape_site1()  # returns only newly inserted articles
    all_new_articles.extend(articles1)
    print(f"Finished scraping Site 1. ✅ {len(articles1)} new articles.\n")

    # # Uncomment if needed
    print("Scraping Site 2...")
    articles2 = scrape_site2()
    all_new_articles.extend(articles2)
    print(f"Finished scraping Site 2. ✅ {len(articles2)} new articles.\n")

    print("Scraping Site 3...")
    articles3 = scrape_site3()
    all_new_articles.extend(articles3)
    print(f"Finished scraping Site 3. ✅ {len(articles3)} new articles.\n")

    after = get_article_count()
    added = after - before
    print(f"✅ {added} new articles added to the database.\n")
    print(f"✅ {after} updated entries.\n")
    
    return all_new_articles

# def post_articles_randomly(articles, max_posts=90, min_delay=30, max_delay=240):
#     """
#     Randomly select up to N articles and send them to Telegram with random delays.
#     """
#     if not articles:
#         print("❌ No new articles to post.\n")
#         return

#     random.shuffle(articles)
#     to_post = articles[:max_posts]

#     print(f"📤 Preparing to post {len(to_post)} articles with random delays...\n")

#     for i, article in enumerate(to_post, start=1):
#         print(f"📨 Posting article {i}/{len(to_post)}:")

#         # ✅ Check if the quota is exceeded for the article's category
#         category = article['category']
#         current_count = get_article_count_by_category(category)  # Get current count for category
#         quota_percentage = get_category_quota_percentage(category)  # Get the quota percentage for the category
        
#         allowed_count = (max_posts * quota_percentage) // 100  # Calculate the allowed count based on quota percentage
        
#         # If the current count exceeds the allowed count based on the quota, skip this article
#         if current_count >= allowed_count:
#             print(f"⚠️ Skipping article '{article['title']}' due to quota limit exceeded for category: {category}")
#             continue  # Skip this article

#         # ✅ Updated message formatting
#         message = (
#             f"📰 *{article['title']}*\n"
#             f"🔗 {article['url']}\n"
#             f"🕒 {article['timestamp']}\n\n"
#             f"{article['content']}\n\n"
#             f"🌐 Source: {article['base_url']}"
#         )

#         # Send article to Telegram
#         send_telegram_message_selenium(message, article["id"], base_url=article["base_url"])

#         # ✅ Increment article count for the category after posting
#         increment_article_count(article['category'])

#         # Check if we need to reset the counts after posting this article
#         reset_article_count_if_needed()

#         if i < len(to_post):
#             delay = random.randint(min_delay, max_delay)
#             print(f"⏱ Waiting {delay} seconds ({delay//60}m {delay%60}s) before next post...\n")
#             time.sleep(delay)

def post_articles_randomly(articles, max_posts=90, min_delay=3600, max_delay=6000):
    """
    Randomly select up to N articles and send them to Telegram with random delays.
    """
    # ✅ Check daily post limit first
    from db_handler import get_daily_post_count
    
    daily_limit = 8
    today_posts = get_daily_post_count()
    
    print(f"📊 Daily posts so far: {today_posts}/{daily_limit}")
    
    if today_posts >= daily_limit:
        print(f"🚫 Daily limit of {daily_limit} posts already reached. Skipping posting.")
        return
    
    # Calculate remaining posts allowed today
    remaining_posts = daily_limit - today_posts
    max_posts = min(max_posts, remaining_posts)
    print(f"📝 Will post maximum {max_posts} articles today")

    if not articles:
        print("❌ No new articles to post.\n")
        return

    random.shuffle(articles)
    to_post = articles[:max_posts]

    print(f"📤 Preparing to post {len(to_post)} articles with random delays...\n")

    for i, article in enumerate(to_post, start=1):
        print(f"📨 Posting article {i}/{len(to_post)}:")

        # ✅ Check if the quota is exceeded for the article's category
        category = article['category']
        current_count = get_article_count_by_category(category)  # Get current count for category
        quota_percentage = get_category_quota_percentage(category)  # Get the quota percentage for the category
        
        # allowed_count = (max_posts * quota_percentage) // 100  # Calculate the allowed count based on quota percentage
        allowed_count = (100 * quota_percentage) // 100  # Out of 100 total posts
        
        # If the current count exceeds the allowed count based on the quota, skip this article
        if current_count >= allowed_count:
            print(f"⚠️ Skipping article '{article['title']}' due to quota limit exceeded for category: {category}")
            continue  # Skip this article

        # ✅ Updated message formatting
        message = (
            f"📰 *{article['title']}*\n"
            f"🔗 {article['url']}\n"
            f"🕒 {article['timestamp']}\n\n"
            f"{article['content']}\n\n"
            f"🌐 Source: {article['base_url']}"
        )

        # Send article to Telegram
        send_telegram_message_selenium(message, article["id"], base_url=article["base_url"])

        # ✅ Increment article count for the category after posting
        increment_article_count(article['category'])

        # Check if we need to reset the counts after posting this article
        reset_article_count_if_needed()

        if i < len(to_post):
            delay = random.randint(min_delay, max_delay)
            print(f"⏱ Waiting {delay} seconds ({delay//60}m {delay%60}s) before next post...\n")
            time.sleep(delay)

def job():
    print("Starting scheduled scraping...")
    new_articles = scrape_all_sites()
    post_articles_randomly(new_articles, max_posts=90)
    print("Scraping job completed.\n")

if __name__ == "__main__":
    # Wait until 10:00 AM GMT+3 for the first post (if before 10:00 AM)
    wait_until_8am()
    print("Scheduler started. Scraping every 60 minutes.")
    job()  # Run once immediately before scheduling

    schedule.every(60).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
