import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import feedparser
from bs4 import BeautifulSoup
import time
from db_handler import insert_article, get_categories_and_keywords 
from telegram_selenium_sender import send_telegram_message_selenium


def categorize_article(title, content):
    # Get categories and keywords dynamically from the database
    categories = get_categories_and_keywords()

    # Convert title and content to lowercase for case-insensitive matching
    title = title.lower()
    content = content.lower()

    # Check each category's keywords in the title/content
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title or keyword in content:
                return category

    return "Uncategorized"  # If no match, categorize as "Uncategorized"

def get_full_article_content_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Scroll down slowly to bottom to trigger any lazy loading
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # wait for loading
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    try:
        content_element = driver.find_element(By.CSS_SELECTOR, 'div.post__content-wrapper > div.post-content')
        html_content = content_element.get_attribute('innerHTML')
    except Exception:
        driver.quit()
        return "Content not found"

    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')
    full_text = '\n'.join(soup.stripped_strings)

    return full_text if full_text else "Content not found"

def scrape_site1(base_url='https://cointelegraph.com'):
    rss_url = f'{base_url}/rss'
    articles = []

    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        title = entry.title
        url = entry.link
        timestamp = entry.published if 'published' in entry else 'No timestamp'
        author = entry.get('author', None)

        full_content = get_full_article_content_selenium(url)

        # Get the category for the article based on keywords
        category = categorize_article(title, full_content)

        article_data = {
            'url': url,
            'title': title,
            'timestamp': timestamp,
            'author': author,
            'content': full_content,
            'base_url': "https://cointelegraph.com",
            'category': category  
        }

        # Debug print to check the scraped article data before passing it to insert_article
        print(f"Scraping article: {title}")
        print(f"URL: {url}")
        print(f"Timestamp: {timestamp}")
        print(f"Content: {full_content[:1000]}...")  # Only print first 1000 chars of content
        print(f"Category: {category}")
        print('-' * 50)

        # Insert article into database
        inserted = insert_article(article_data)
        if inserted:
            article_data["id"] = inserted["id"]
            articles.append(article_data)
            break

    return articles

if __name__ == '__main__':
    articles = scrape_site1()

    for i, article in enumerate(articles[:3], start=1):
        print(f"\nArticle {i}:")
        print("Title:", article['title'])
        print("URL:", article['url'])
        print("Timestamp:", article['timestamp'])
        print("Author:", article['author'])
        print("Category:", article['category'])  
        print("Full Content:", article['content'][:1000], '...')  
        print('-' * 50)
