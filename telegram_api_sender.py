import requests
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Telegram bot token and chat ID from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(title, url, timestamp, description):
    # Limit description length to avoid very long messages (optional)
    max_length = 700
    short_description = description if len(description) <= max_length else description[:max_length] + "..."

    message = f"<b>{title}</b>\n{url}\n🕒 {timestamp}\n\n{short_description}"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        print("📨 Message sent to Telegram.")
        return True
    else:
        print("❌ Telegram API failed:", response.text)
        return False
