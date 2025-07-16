import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from db_handler import insert_article
from db_handler import get_filters_for_url, get_categories_and_keywords  # Assuming you have a function like this

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

def scrape_site2():
    base_url = "https://decrypt.co/news"
    
    response = requests.get(base_url)
    if response.status_code != 200:
        print("Failed to fetch page:", response.status_code)
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    article_details = []
    articles = soup.find_all("article")
    seen_urls = set()
    inserted_articles = []

    for article in articles:
        link_tag = article.find("a", class_="linkbox__overlay")
        if not link_tag or 'href' not in link_tag.attrs:
            continue

        href = link_tag['href']
        if '/price/' in href:
            continue
        
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Title
        title_tag = article.find("h3") or article.find("span", class_="font-medium")
        title = title_tag.get_text(strip=True) if title_tag else "No title available"

        # Timestamp
        timestamp = "No timestamp available"
        timestamp_tag = article.find("time")
        if timestamp_tag:
            timestamp_text = timestamp_tag.get_text(strip=True)
            if "min read" not in timestamp_text and "min" not in timestamp_text:
                timestamp = timestamp_text
        if timestamp == "No timestamp available":
            span_tag = article.find("span", class_="text-neutral-700")
            if span_tag:
                timestamp = span_tag.get_text(strip=True)

        # Description from full article
        description = "No description available"
        try:
            article_response = requests.get(full_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.text, "html.parser")
                content_tags = article_soup.find_all("p", class_="font-meta-serif-pro")
                full_paragraphs = [p.get_text(strip=True) for p in content_tags if p.get_text(strip=True)]
                if full_paragraphs:
                    description = "\n\n".join(full_paragraphs)
        except Exception as e:
            print(f"Error fetching article content: {e}")
        # # Description from full article
        # description = "No description available"
        # try:
        #     article_response = requests.get(full_url)
        #     if article_response.status_code == 200:
        #         article_soup = BeautifulSoup(article_response.text, "html.parser")
        #         desc_tag = article_soup.find("p", class_="font-meta-serif-pro")
        #         if desc_tag:
        #             description = desc_tag.get_text(strip=True)
        # except Exception as e:
        #     print(f"Error fetching article content: {e}")

        # Debug print
        print(f"Title: {title}")
        print(f"URL: {full_url}")
        print(f"Timestamp: {timestamp}")
        print(f"Description: {description[:700]}...")
        print('-' * 50)

        # Get the category for the article based on keywords
        category = categorize_article(title, description)  # Categorize based on title and description
        print(f"Category assigned: {category}")  # Debug print to verify category assignment

        article_data = {
            'title': title,
            'timestamp': timestamp,
            'url': full_url,
            'content': description,  # ✅ use 'content' as the correct key
            'category': category  # Add category here
        }

        inserted = insert_article(article_data)
        if inserted:
            inserted_articles.append({
                'id': inserted["id"],
                'title': title,
                'url': full_url,
                'timestamp': timestamp,
                'content': description,
                'category': category,  # Include category in the inserted article data
                'base_url': "https://decrypt.co/news"
            })
            break

    return inserted_articles


if __name__ == "__main__":
    articles = scrape_site2()
    print(f"\n✅ Total articles inserted: {len(articles)}\n")
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Timestamp: {article['timestamp']}")
        print(f"URL: {article['url']}")
        print(f"Description: {article['content'][:800]}...")
        print(f"Category: {article['category']}")
        print("=" * 50)
