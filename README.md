# Telegram News Bot Automation System

An intelligent automation system built to **collect, categorize, translate, and dispatch news content via a Telegram bot**. Designed for reliability and precision, the system ensures timely delivery of high-quality news posts to your Telegram channel based on your defined criteria — all managed through a lightweight dashboard.

## Features

- 🧠 **Automated News Collection** from pre-defined RSS feeds or source sites
- 🔍 **Keyword-based Filtering** to match only relevant content
- 📊 **Quota Management** using category-percentage logic
- 🌐 **Automatic Translation** of articles into the target language
- 🗕️ **Scheduled Delivery** – waits until 8 AM before dispatching posts
- 🔏 **Message Precision** – titles are cleaned, content trimmed, and media checked
- 🚀 **Telegram Integration** via bot token and channel config
- 📋 **Logging & History** – every post and status is stored for review
- 🛠️ **Admin Dashboard** for managing APIs, cookies, categories, keywords, and source sites

## How It Works (Telegram Bot Logic)

1. **News Aggregation**  
   The backend regularly fetches articles from registered RSS feeds or web scrapers, storing them locally with metadata.

2. **Filtering & Categorization**  
   Articles are compared against configured categories and keywords, assigning a category and checking quota limits.

3. **Translation**  
   Using external APIs, the content is translated into the target language as needed.

4. **Content Curation**  
   Messages are trimmed to fit Telegram formatting, removing clutter, ensuring readability, and validating media links.

5. **Smart Scheduling**  
   Posts are queued and **only dispatched after 8:00 AM** based on availability and priority.

6. **Telegram Dispatch**  
   The bot sends the curated post to the Telegram channel using the bot token and channel ID set in the backend.

7. **Post Tracking**  
   Every sent message is logged with time, category, and status (success/fail) for analytics and audit.

## 💻 Dashboard Overview (Client-Side UI)

The admin panel (frontend) allows users to:

- 🔑 Manage API tokens and endpoints
- 📂 Add or edit RSS feed source sites
- 📡 Configure Telegram channels
- 🍪 Manage browser session cookies for scraping
- 📟 Monitor posting history
- 🏷️ Create and control categories, keywords, and quotas

This is a helper UI for clients — the core functionality runs in the background regardless of dashboard use.

## 📦 Tech Stack

- **Backend:** Python (FastAPI)
- **Frontend:** FastAPI (for serving the frontend), HTML, JavaScript, Bootstrap 5
- **Bot Communication:** Telegram Bot API (using Python's `python-telegram-bot` library)
- **Translation & Scraping:** External APIs (Google Translate API for translation, custom scraping logic for RSS feeds and websites)
- **Database:** Supabase (for storing logs, post history, and other relevant data)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-user/telegram-news-bot.git
cd telegram-news-bot
````

### 2. Setup and Activate Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Run the Bot Scraper

```bash
python scraper.py
```

> This will start the news gathering, filtering, translating, and Telegram posting loop.

### 4. Start the Frontend Admin Panel

```bash
uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

> Open [http://localhost:8000](http://localhost:8000) in your browser to access the dashboard.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions to this project! If you would like to contribute, please follow these steps:

1. **Fork the repository**: Click the "Fork" button at the top-right of the repository to create a copy of the project in your own GitHub account.
2. **Clone the repository**: Clone your fork to your local machine:

   ```bash
   git clone https://github.com/your-username/your-forked-repo.git
   ```
3. **Create a new branch**: It's recommended to create a new branch for each feature or fix:

   ```bash
   git checkout -b feature-branch-name
   ```
4. **Make changes**: Implement your feature or fix.
5. **Commit your changes**: Commit your changes with a descriptive message:

   ```bash
   git commit -m "Add a detailed description of your change"
   ```
6. **Push changes**: Push your changes to your forked repository:

   ```bash
   git push origin feature-branch-name
   ```
7. **Create a Pull Request**: Once your changes are pushed, go to your repository on GitHub, and click on "New Pull Request" to submit your changes for review.

Please ensure that your code follows the existing style guide and passes any relevant tests. Contributions are greatly appreciated!



