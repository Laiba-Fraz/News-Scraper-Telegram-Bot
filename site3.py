import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from db_handler import insert_article, get_categories_and_keywords  # Import dynamic category fetching

def categorize_article(title, content):
    # Get categories and keywords dynamically from the database
    categories = get_categories_and_keywords()

    # Convert title and content to lowercase for case-insensitive matching
    title = title.lower()
    content = content.lower()

    print(f"Categorizing article: {title}")  # Debug print

    # Check each category's keywords in the title/content
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title or keyword in content:
                print(f"Match found for category: {category}")  # Debug print
                return category

    print("No match found, categorized as Uncategorized")  # Debug print
    return "Uncategorized"  # If no match, categorize as "Uncategorized"

def scrape_site3():
    base_url = "https://blockworks.co/news"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": base_url,
        "Connection": "keep-alive",
    }

    print("Scraping Site 3...")
    print("⏳ Sending GET request to main news page...")
    response = requests.get(base_url, headers=headers)
    print(f"➡️ Response status code: {response.status_code}")

    if response.status_code != 200:
        print("Failed to fetch page:", response.status_code)
        return []

    print(f"📝 Length of fetched HTML: {len(response.text)} characters")

    soup = BeautifulSoup(response.text, "html.parser")
    article_links = soup.find_all("a", class_="font-headline")
    print(f"🔎 Number of article links found: {len(article_links)}")

    seen_urls = set()
    inserted_articles = []

    for link in article_links:
        href = link.get("href")
        if not href or not href.startswith("/news/"):
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        title = link.get_text(strip=True) or "No title available"

        article_div = link.find_parent("div", class_="flex")

        timestamp = "No timestamp available"
        content = "No content available"

        if article_div:
            time_tag = article_div.find_next("time")
            if time_tag and time_tag.has_attr("datetime"):
                timestamp = time_tag.get_text(strip=True)

        # Fetch full article page to get full content
        print(f"📄 Fetching article page: {full_url}")
        article_resp = requests.get(full_url, headers=headers)
        if article_resp.status_code == 200:
            article_soup = BeautifulSoup(article_resp.text, "html.parser")
            content_div = article_soup.find("div", class_="p-2 basis-4/4 xl:basis-3/4")
            if content_div:
                paragraphs = content_div.find_all("p")
                content = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        print(f"Title: {title}")
        print(f"URL: {full_url}")
        print(f"Timestamp: {timestamp}")
        print(f"Content snippet: {content[:200]}...")  
        print("-" * 50)

        # Get the category for the article based on keywords
        category = categorize_article(title, content)  
        print(f"Category assigned: {category}") 

        article_data = {
            'title': title,
            'timestamp': timestamp,
            'url': full_url,
            'content': content,
            'category': category 
        }

        inserted = insert_article(article_data)
        if inserted:
            inserted_articles.append({
                'id': inserted["id"],
                'title': title,
                'url': full_url,
                'timestamp': timestamp,
                'content': content,
                'category': category, 
                "base_url": "https://blockworks.co/news"
            })
            # break

    return inserted_articles

if __name__ == "__main__":
    print("Starting site3 scraping...")
    articles = scrape_site3()
    print(f"Articles scraped: {len(articles)}")
