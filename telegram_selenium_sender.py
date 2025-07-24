import os
import io
import time
import random
import json
import base64
import requests
import pyperclip
import win32clipboard
import win32con

from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from langdetect import detect
from deep_translator import GoogleTranslator
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from openai import OpenAI
from db_handler import supabase

import API.crud as crud
from db_handler import get_filters_for_url


# Load environment variables
load_dotenv()
print("Loaded key:", os.getenv("OPENAI_API_KEY"))

# Initialize OpenAI client using env variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load cookies from file
def load_cookies(driver, path="telegram_cookies.json"):
    if os.path.exists(path):
        with open(path, "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)

#clear images folder
def cleanup_old_images(folder_path="images", max_age_seconds=86400):  # 86400 sec = 24 hours
    now = time.time()
    deleted_files = 0

    if not os.path.exists(folder_path):
        print(f"📁 Folder not found: {folder_path}")
        return

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    deleted_files += 1
                    print(f"🧹 Deleted old image: {filename}")
                except Exception as e:
                    print(f"❌ Could not delete {filename}: {e}")
    
    print(f"✅ Cleanup complete. Deleted {deleted_files} old file(s).")

# Setup Chrome browser with options
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-data-dir=C:/temp/selenium_profile")
    chrome_options.add_argument("--start-maximized")  # <-- ADD THIS LINE for full size window
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Fetch active channels from database
def get_active_channels():
    try:
        result = supabase.table("channels").select("channel_url").eq("is_active", True).execute()
        if result.data:
            # Extract just the URLs from the result
            channel_urls = [channel["channel_url"] for channel in result.data if channel["channel_url"]]
            print(f"📡 Fetched {len(channel_urls)} active channels from database")
            return channel_urls
        else:
            print("⚠️ No active channels found in database")
            return []
    except Exception as e:
        print(f"❌ Error fetching channels from database: {e}")
        return []

# Remove characters not supported by Chrome
def remove_non_bmp_chars(text):
    return ''.join(char for char in text if ord(char) <= 0xFFFF)

# Rehrase the article content according to requirements
def rewrite_content_precisely(content, max_chars=300, base_url=None, retry_count=0):
    try:
        filters = get_filters_for_url(base_url) if base_url else []
        print(f"🛠️ Filters applied for URL '{base_url}': {filters}") 
        banned_words_text = ""
        if filters:
            banned_words_text = f" Avoid using the following words: {', '.join(filters)}."

            prompt = (
                f"🚨 CRITICAL EMOJI RULE - VIOLATING THIS WILL INVALIDATE YOUR RESPONSE:\n"
                f"USE EXACTLY 0, 1, OR 2 EMOJIS TOTAL (NOT PER PARAGRAPH - TOTAL)\n"
                f"DO NOT exceed {max_chars} characters total (including line breaks and emojis)\n"
                f"Before submitting your response, COUNT THE EMOJIS. If more than 2, REMOVE EXCESS.\n\n"
                
                f"Use informal English with light slang that resonates with crypto natives and digital anarchists. "
                f"The tone should be meme-aware, rebellious, and fit for crypto degens. "
                f"Structure your response into 2–3 ultra-short paragraphs. Each para should be within 100 characters"
                f"Wrap up with a spicy rhetorical question or provocative comment to spark discussion. "
                f"- NO bold text, hashtags, or formatting\n"
                f"- NO face emojis (😂🤣😭😱😍)\n\n"
                
                f"EXAMPLES OF ACCEPTABLE RESPONSES:\n"
                f"✅ Example 1: 'Fed keeps printing while Bitcoin stays strong. DeFi protocols gaining traction. Ready for the next pump? 🚀💎'\n"
                f"✅ Example 2: 'Whales accumulating during this dip. Smart money moving in. Time to follow the giants? 📈'\n"
                f"✅ Example 3: 'Another exchange hack, another reminder. Not your keys, not your crypto.'\n\n"
                
                f"UNACCEPTABLE (TOO MANY EMOJIS):\n"
                f"❌ 'Bitcoin pumping hard! 🚀💎🔥⚡ Moon mission activated! 🌙💰📈'\n\n"
                
                f"FINAL CHECK: Before responding, count your emojis. Maximum 2 allowed. Also strictl stay within character limit\n"
                f"{banned_words_text}\n\n"
                f"Original article:\n{content}"
            )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a concise editorial assistant that rewrites news clearly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        rewritten = response.choices[0].message.content.strip()
        

        return rewritten

    except Exception as e:
        print(f"❌ Error rewriting with GPT: {e}")
        return content[:max_chars]

#Translate msg into desired language
def translate_with_gpt(text, target_lang_code, base_url=None):
    # return text[:300]
    try:
        # Fetch banned words (if any)
        filters = get_filters_for_url(base_url) if base_url else []
        print(f"🛠️ Filters applied for URL '{base_url}': {filters}")
        banned_words_text = ""
        if filters:
            banned_words_text = f" Avoid using the following words in the translation: {', '.join(filters)}."

        # 💬 Style instructions by language
        if target_lang_code == "ru":
            style_instructions = (
                "Translate this text into casual Russian with light slang (e.g. 'инфосфера', 'реврайт', 'алгоритм', 'контроль нарратива'). "
                "Make sure it's not Latin-style Russian. "
                "Tone should be bold, rebellious, meme-aware, and appealing to digital anarchists and crypto degens, designed for a Telegram channel with a crypto-native audience. "
                "Keep it simple — no complex or formal words. No need to chnage foramtting and stick  to the original wordcount."
                "Also no need to remove or add emojis or edit any other thing"
                "No need ot anything by your own. Just simply translate it"
            )
        else:
            style_instructions = (
                f"Translate this text into natural, fluent {target_lang_code} with a confident, bold tone. "
                "Keep the meaning accurate. Avoid formal or stiff phrasing. Keep it simple — no complex words."
                "Make sure not to add any other language words and stick to the original wordcount."
                "Also no need to remove emojis or edit any other thing"
                "No need ot anything by your own"
            )

        # 🧠 Compose the full GPT prompt
        prompt = (
            f"{style_instructions}"
            f"{banned_words_text}\n\n"
            f"Original text:\n{text}"
        )

        # 🧠 Call OpenAI GPT
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a precise and fluent translator for Telegram news posts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        translated_text = response.choices[0].message.content.strip()
        return translated_text

    except Exception as e:
        print(f"❌ GPT translation failed: {e}")
        return text  # Fallback

#Image generation function
def generate_image_from_message(translated_title, rephrased_content, original_title, original_content):
    try:
        prompt = (
            f"Create an editorial illustration that represents the following news headline and summary. "
            f"Avoid logos or text. Make it visually clear, clean, and professional.\n\n"
            f"Title: {translated_title}\nContent: {rephrased_content}"
        )

        try:
            # Primary image generation attempt
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

        except Exception as e:
            print(f"⚠️ Initial image generation failed: {e}")
            print("🔁 Retrying with fallback prompt...")

            # Retry with generic fallback prompt
            fallback_prompt = (
                "Create an editorial illustration that indicates the news content is restricted or unavailable. "
                "Use abstract or symbolic imagery to convey a placeholder or blocked content."
            )

            response = client.images.generate(
                model="dall-e-3",
                prompt=fallback_prompt,
                n=1,
                size="1024x1024"
            )

        # Handle the image saving
        image_url = response.data[0].url
        if not image_url:
            print("❌ No image URL returned.")
            return ""

        image_data = requests.get(image_url).content
        filename = f"generated_image_{int(time.time())}.png"
        filepath = os.path.join(os.getcwd(),"images", filename)

        with open(filepath, 'wb') as f:
            f.write(image_data)

        print(f"🖼️ Image saved to: {filepath}")
        return filepath

    except Exception as final_err:
        print(f"❌ Image generation completely failed: {final_err}")
        return ""

# Copy image to clipboard (Windows)
def copy_image_to_clipboard_windows(image_path):
    try:
        image = Image.open(image_path)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        print("📋 Copied image to clipboard.")
    except Exception as e:
        print(f"❌ Failed to copy image to clipboard: {e}")

# Before pasting msg make sure to clear the input field
def clear_message_input_field(driver):
    try:
        print("[🔍] Locating message editor input field...")
        message_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "editable-message-text"))
        )
        print("[✅] Message editor found. Pressing Ctrl + A to select all text...")
        
        message_input.click()
        message_input.send_keys(Keys.CONTROL, 'a')
        print("[⌫] Pressing Backspace to clear selected text...")
        
        message_input.send_keys(Keys.BACKSPACE)
        print("[✅] Input field cleared successfully.\n")
    except Exception as e:
        print(f"[❌] Failed to clear input field: {e}\n")

# Check if the msg is sent or not
def check_message_sent(driver, timeout=10):
    try:
        # Wait until either modal appears or input box becomes empty
        WebDriverWait(driver, timeout).until(lambda d: (
            is_input_empty(d) or is_error_modal_present(d)
        ))

        if is_error_modal_present(driver):
            print("❌ Message failed: 'Message too long' error shown.")
            return False
        elif is_input_empty(driver):
            print("✅ Message sent successfully.")
            return True
        else:
            print("❌ Unknown state after waiting.")
            return False

    except TimeoutException:
        print("❌ Timeout: Message probably failed (input not cleared and no error dialog).")
        return False

# Check if input box is empty
def is_input_empty(driver):
    try:
        input_box = driver.find_element(By.ID, "editable-message-text")
        return input_box.text.strip() == ""
    except NoSuchElementException:
        return True  # If input box vanishes, treat as empty (can happen)

# Check if error modal is present 
def is_error_modal_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-dialog"))
        )
        modal = driver.find_element(By.CLASS_NAME, "modal-dialog")
        title = modal.find_element(By.CLASS_NAME, "modal-title")
        return "Something went wrong" in title.text
    except:
        return False

# Post articles randomly to Telegram channels
def send_telegram_message_selenium(message, article_id, base_url=None):
    message_sent_successfully = False  # 🔹 Track if any message sent
    cleanup_old_images()
    driver = setup_driver()
    driver.get("https://web.telegram.org/k/")
    time.sleep(5)

    # Fetch article data
    article_data = supabase.table("articles").select("url, title, description").eq("id", article_id).execute()
    if not article_data.data:
        print("❌ No article found for ID:", article_id)
        return

    article_url = article_data.data[0]["url"]
    original_title = article_data.data[0]["title"]
    content_part = article_data.data[0]["description"]

    # Skip articles if description is empty
    if not content_part or content_part.lower() == "content not found" or len(content_part.split()) < 5:
        print(f"⚠️ Skipping article '{original_title}' due to insufficient content.")
        return  

    # Clean up title in description
    lines = content_part.splitlines()
    content_part = "\n".join([line for line in lines if not line.strip().lower().startswith("title:")]).strip()

    # Rewrite content for formatting
    cleaned_content = rewrite_content_precisely(content_part, base_url=base_url)
    print("🧹 Rewritten content:\n", cleaned_content)

    # Generate image
    image_path = generate_image_from_message(
        original_title, cleaned_content, original_title=original_title, original_content=content_part
    )
    print(f"🖼️ Image saved to: {image_path}")

    CHANNEL_URLS = get_active_channels()
    if not CHANNEL_URLS:
        print("❌ No active channels found. Exiting...")
        driver.quit()
        return

    for channel_url in CHANNEL_URLS:
        try:
            # Open Telegram and channel
            driver.get("https://web.telegram.org/k/")
            time.sleep(3)
            load_cookies(driver)
            driver.refresh()
            time.sleep(5)
            driver.get(channel_url)
            time.sleep(5)
            print(f"📨 Opened channel: {channel_url}")

            # Get channel name
            header = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='MiddleColumn']/div[4]/div[2]/div[1]/div/div/div/div[2]/div"))
            )
            try:
                channel_name = header.text
                print(f"🔍 Detected Channel Name: {channel_name}")
            except Exception as e:
                print(f"❌ Error extracting channel name: {str(e)}")
                channel_name = "Unknown"

            # Detect or fetch language
            lang_code = None
            try:
                result = supabase.table("channels").select("language").eq("channel_url", channel_url).execute()
                if result.data and result.data[0].get("language"):
                    lang_code = result.data[0]["language"]
                    print(f"🌐 Language from DB: {lang_code}")
            except Exception as e:
                print(f"⚠️ Could not fetch language from DB: {e}")

            if not lang_code:
                try:
                    lang_code = detect(channel_name)
                    print(f"🌐 Language detected from channel name: {lang_code}")
                except Exception as e:
                    print(f"❌ Failed to detect language: {e}")
                    lang_code = 'en'

            # Translate title and content
            translated_title = translate_with_gpt(original_title, lang_code, base_url=base_url)
            translated_content = translate_with_gpt(cleaned_content, lang_code, base_url=base_url)

            # Copy image to clipboard
            image_copied = False
            if image_path and os.path.exists(image_path):
                try:
                    copy_image_to_clipboard_windows(image_path)
                    image_copied = True
                    print("✅ Image copied to clipboard.")
                except Exception as e:
                    print(f"❌ Failed to copy image to clipboard: {e}")
            else:
                print("❌ Image path invalid or file does not exist.")

            if not image_copied:
                print("⛔ Aborting message send because image was not copied to clipboard.")
                continue

            clear_message_input_field(driver)


            # Paste image
            try:
                input_box = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
                )
                input_box.click()
                print("🖱️ Input box focused. Pasting image...")
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                time.sleep(5)
                print("✅ Image pasted successfully into Telegram.")
            except Exception as e:
                print(f"❌ Failed to paste image: {e}")
                continue

            # Type caption (title + content + hyperlink)
            try:
                print("⌨️ Waiting for caption input modal to appear...")
                caption_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "editable-message-text-modal"))
                )
                caption_box.click()
                time.sleep(1)

                actions.send_keys('**').perform()
                pyperclip.copy(translated_title)
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                actions.send_keys('**').perform()
                print("📝 Title pasted.")

                for _ in range(2):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    time.sleep(0.3)

                pyperclip.copy(translated_content)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                print("📄 Translated content pasted.")

                for _ in range(2):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    time.sleep(0.3)

                actions.send_keys('(verified source)').perform()
                for _ in range(17):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).perform()
                    time.sleep(0.02)

                # Add hyperlink
                hyperlink_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Add Link" or @title="Add Link"]'))
                )
                hyperlink_button.click()

                link_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Enter URL..."]'))
                )
                link_input.click()
                pyperclip.copy(article_url)
                link_input.send_keys(Keys.CONTROL, 'v')

                check_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//i[contains(@class, "icon-check")]/parent::button'))
                )
                check_button.click()

                caption_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "editable-message-text-modal"))
                )
                caption_box.click()
                time.sleep(1.5)

                # Click send
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "wDqWK9MD")]//button[contains(@class, "primary") and text()="Send"]'))
                )
                send_button.click()
                print("📨 Send button clicked. Waiting for message confirmation...")

                # Verify whether the message was actually sent
                if check_message_sent(driver):
                    print("✅ Message sent successfully.")
                    message_sent_successfully = True  # ✅ Set the success flag

                    # Log posting
                    try:
                        result = supabase.table("channels").select("id").eq("channel_url", channel_url).execute()
                        if result.data:
                            channel_id = result.data[0]["id"]
                            crud.log_posting(article_id, [channel_id])
                            print(f"📝 Logged posting: article {article_id} → channel {channel_id}")
                        else:
                            print(f"⚠️ No channel found for URL: {channel_url}")
                    except Exception as log_error:
                        print(f"❌ Failed to log posting history: {log_error}")
                else:
                    print("❌ Message not sent — input not cleared or error modal detected.")
                    continue

            except Exception as e:
                print(f"❌ Failed to send image and caption: {e}")
                continue

            print(f"📬 Message fully sent to {channel_url} in language '{lang_code}'")
            delay = random.uniform(30, 150)
            print(f"⏳ Waiting {delay:.2f} seconds before sending to the next channel...")
            time.sleep(delay)

        except Exception as e:
            print(f"❌ Error sending message to {channel_url}: {e}")

    driver.quit()
    return message_sent_successfully  # Return success to caller
