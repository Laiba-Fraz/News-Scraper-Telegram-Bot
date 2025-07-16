import os
import time
import io
import random

import json
import base64
import requests
import pyperclip
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from langdetect import detect
from deep_translator import GoogleTranslator

from PIL import Image
import win32clipboard
import win32con

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

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


    """Count emojis in text"""
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+", flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))

# Remove characters not supported by Chrome
def remove_non_bmp_chars(text):
    return ''.join(char for char in text if ord(char) <= 0xFFFF)


# # Rewrite content to be concise and safe for public channels using OpenAI GPT
# def rewrite_content_precisely(content, max_chars=300, base_url=None):
#     try:
#         filters = get_filters_for_url(base_url) if base_url else []
#         print(f"🛠️ Filters applied for URL '{base_url}': {filters}") 
#         banned_words_text = ""
#         if filters:
#             banned_words_text = f" Avoid using the following words: {', '.join(filters)}."

#             prompt = (
#                 f"You are a rebellious crypto content editor. Rewrite the article below into a bold, punchy, engaging summary "
#                 f"with a max length of {max_chars} characters — including line breaks and emojis. "
#                 f"Use informal English with light slang that resonates with crypto natives and digital anarchists. "
#                 f"The tone should be meme-aware, rebellious, and fit for crypto degens. "

#                 f"Structure your response into 2–3 ultra-short paragraphs. "
#                 # f"**Each paragraph must be under 100 characters.** "

#                 f"Wrap up with a spicy rhetorical question or provocative comment to spark discussion. "

#                 f"⚠️ CRITICAL CONSTRAINTS (do not violate these):\n"
#                 f"- Max **2 emojis TOTAL** in the entire output\n"
#                 f"- DO NOT use one emoji per paragraph — use 0, 1, or 2 total only\n"
#                 f"- DO NOT use face/emotion emojis\n"
#                 f"- DO NOT exceed {max_chars} characters total (including line breaks and emojis)\n"
#                 f"- DO NOT use bold, special symbols, or hashtags (unless absolutely essential)\n"

#                 f"{banned_words_text}\n\n"
#                 f"ONLY OUTPUT the rewritten summary. Do NOT include the original content.\n"
#                 f"DO NOT explain anything.\n\n"
#                 f"---\n"
#                 f"Original article:\n{content}"
#             )


            
#             # prompt = (
#             #     f"You are an expert crypto content editor. Rewrite the following article into a bold, punchy, and rebellious summary, "
#             #     f"strictly limited to {max_chars} characters total (including line breaks and emojis). "
#             #     f"Use clear English with mild slang for crypto natives and digital anarchists. "
#             #     f"Use short, meme-aware sentences across 2–3 **short** paragraphs — **each under 100 characters**. "
#             #     f"Wrap up with a spicy rhetorical question or sharp comment. "
#             #     f"Use **no more than 2 emojis total** (no faces). Use no bold, symbols, hashtags, or formatting. "
#             #     f"{banned_words_text}"
#             #     f"\n\n### IMPORTANT RULES ###\n"
#             #     f"- Stay under {max_chars} characters, including emojis and line breaks\n"
#             #     f"- Max 2 emojis TOTAL\n"
#             #     f"- Max 3 paragraphs\n"
#             #     f"- Each paragraph must be under 100 characters\n"
#             #     f"- No formatting, no hashtags (unless deeply relevant), no emotion-face emojis\n\n"
#             #     f"Output ONLY the rewritten summary. Do NOT repeat or reference the original.\n\n"
#             #     f"---\n"
#             #     f"Original content:\n{content}"
#             # )

#             # prompt = (
#             #     f"You'll get the full article content below. Your task is to rewrite it into a bold, punchy, and engaging summary, max {max_chars} characters. "
#             #     f"Use casual English with light slang that resonates with crypto natives and digital anarchists. "
#             #     f"Keep the tone rebellious, meme-aware, and fit for degens. "
#             #     f"Structure the output in 2 or max 3 short and punchy paragraphs. Not more than 100 characters in a para "
#             #     f"Wrap it up with a spicy comment or rhetorical question to spark discussion. "
#             #     f"Use maximum 2 relevant emojis in total (no emotion-face emojis). "
#             #     f"**Strictly stay within the limit of max 2 emojis in total**"
#             #     f"**DO NOT CROSS THE EMOJIS COUNT LIMIT and CHARACTER COUNT LIMIT**"
#             #     f"No bold text, special characters, or formatting. No hashtags unless truly meaningful. "
#             #     f"Strictly stay within the character limit—count all line breaks and emojis. "
#             #     f"{banned_words_text}\n\n"
#             #     f"Final output format:\n\n"
#             #     f"<rewritten summary>\n\n"
#             #     f"Original content:\n{content}"
#             # )



#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a concise editorial assistant that rewrites news clearly."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )

#         rewritten = response.choices[0].message.content.strip()
#         import re

#         # # Remove leading/trailing * around the title
#         # lines = rewritten.splitlines()
#         # for i, line in enumerate(lines):
#         #     if "Title:" in line:
#         #         lines[i] = line.replace("*", " ")
#         #         # break
#         # rewritten = "\n".join(lines)

#         rewritten = re.sub(r"(Title:\s+)\*+(.+?)\*+\s*", r"\1\2", rewritten)


#         # Optional: Trim to 250 chars if needed
#         # return rewritten[:max_chars]
#         return rewritten

#     except Exception as e:
#         print(f"❌ Error rewriting with GPT: {e}")
#         return content[:max_chars]
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
        # prompt = (
        #     f"You are a rebellious crypto content editor. Rewrite the article below into a bold, punchy, engaging summary "
        #     f"with a max length of {max_chars} characters — including line breaks and emojis. "
        #     f"Use informal English with light slang that resonates with crypto natives and digital anarchists. "
        #     f"The tone should be meme-aware, rebellious, and fit for crypto degens. "

        #     f"Structure your response into 2–3 ultra-short paragraphs. "

        #     f"Wrap up with a spicy rhetorical question or provocative comment to spark discussion. "

        #     f"⚠️ CRITICAL CONSTRAINTS (do not violate these):\n"
        #     f"- Max **2 emojis TOTAL** in the entire output\n"
        #     f"- DO NOT use one emoji per paragraph — use 0, 1, or 2 total only\n"
        #     f"- DO NOT use face/emotion emojis\n"
        #     f"- DO NOT exceed {max_chars} characters total (including line breaks and emojis)\n"
        #     f"- DO NOT use bold, special symbols, or hashtags (unless absolutely essential)\n"

        #     f"{banned_words_text}\n\n"
        #     f"ONLY OUTPUT the rewritten summary. Do NOT include the original content.\n"
        #     f"DO NOT explain anything.\n\n"
        #     f"---\n"
        #     f"Original article:\n{content}"
        # )

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
                "Also no need to remove emojis or edit any other thing"
                "No need ot anything by your own"
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
    # return "C:/Users/HP/Documents/new_scrapper_sat/Images/generated_image_1750054934.png"

# ✅ Helper function (outside main function)
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


# Main function to send a message with translated text and image
def send_telegram_message_selenium(message, article_id, base_url=None):
    cleanup_old_images()
    driver = setup_driver()
    driver.get("https://web.telegram.org/k/")
    time.sleep(5)

    # Fetch article URL and description from Supabase
    article_data = supabase.table("articles").select("url, title, description").eq("id", article_id).execute()
    if not article_data.data:
        print("❌ No article found for ID:", article_id)
        return
    

    article_url = article_data.data[0]["url"]
    original_title = article_data.data[0]["title"]
    content_part = article_data.data[0]["description"]

    # Clean "Title:" line if present in content
    lines = content_part.splitlines()
    content_part = "\n".join(
        [line for line in lines if not line.strip().lower().startswith("Title:")]
    ).strip()

    # Rewrite content using filters and character limit
    cleaned_content = rewrite_content_precisely(content_part, base_url=base_url)
    print("🧹 Rewritten content:\n", cleaned_content)

    # Generate image
    image_path = generate_image_from_message(
        original_title,  # untranslated title is fine for image
        cleaned_content,
        original_title=original_title,
        original_content=content_part
    )
    print(f"🖼️ Image saved to: {image_path}")

    CHANNEL_URLS = get_active_channels()

    # Safety check - if no channels found, exit gracefully
    if not CHANNEL_URLS:
        print("❌ No active channels found. Exiting...")
        driver.quit()
        return

    # CHANNEL_URLS = [
    #     "https://web.telegram.org/a/#8042578096",
    #     "https://web.telegram.org/a/#-1002520978666",
    #     "https://web.telegram.org/a/#-1002667563445",
    #     # "https://web.telegram.org/a/#6730214198"
    # ]

    for channel_url in CHANNEL_URLS:
        try:
            driver.get("https://web.telegram.org/k/")
            time.sleep(3)

            load_cookies(driver)
            driver.refresh()
            time.sleep(5)

            driver.get(channel_url)
            time.sleep(5)
            print(f"📨 Opened channel: {channel_url}")

            header = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='MiddleColumn']/div[4]/div[2]/div[1]/div/div/div/div[2]/div"))
            )

            try:
                channel_name = header.text
                print(f"🔍 Detected Channel Name: {channel_name}")
            except Exception as e:
                print(f"❌ Error extracting channel name: {str(e)}")
                channel_name = "Unknown"

            # First try to get lang_code from DB
            lang_code = None
            try:
                result = supabase.table("channels").select("language").eq("channel_url", channel_url).execute()
                if result.data and result.data[0].get("language"):
                    lang_code = result.data[0]["language"]
                    print(f"🌐 Language from DB: {lang_code}")
            except Exception as e:
                print(f"⚠️ Could not fetch language from DB: {e}")

            # If not in DB, fall back to detecting from channel name
            if not lang_code:
                try:
                    lang_code = detect(channel_name)
                    print(f"🌐 Language detected from channel name: {lang_code}")
                except Exception as e:
                    print(f"❌ Failed to detect language: {e}")
                    lang_code = 'en'

            print(f"🌐 Detected language code: {lang_code}")

            # Translate parts

            translated_title = translate_with_gpt(original_title, lang_code, base_url=base_url)
            translated_content = translate_with_gpt(cleaned_content, lang_code, base_url=base_url)


            image_copied = False
            if image_path and os.path.exists(image_path):
                print("📁 Valid image path found. Copying to clipboard...")
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

            try:
                print("⌨️ Waiting for caption input modal to appear...")
                caption_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "editable-message-text-modal"))
                )
                caption_box.click()
                time.sleep(1)

    
                caption_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "editable-message-text-modal"))
                )
                caption_box.click()
                time.sleep(1)
                print("Caption box focused.")

                # STEP 2: Paste the TITLE (after image is pasted)

                actions.send_keys('**').perform()
                pyperclip.copy(translated_title)
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                actions.send_keys('**').perform()
                time.sleep(1)
                print("Title pasted.")


                # STEP 3: Insert a new lines safely using SHIFT + ENTER (prevents sending the message)
                for _ in range(2):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    time.sleep(0.3)

                # STEP 4: Paste translated content 
                pyperclip.copy(translated_content)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                print("✅ Translated content pasted safely ")

                # STEP 5: Add a line
                for _ in range(2):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    time.sleep(0.3)

                # STEP 6: Paste (verified source)
                actions.send_keys('(verified source)').perform()

                # STEP 7: Select the text i.e (verified source) (Shift + Arrow Left)
                
                for _ in range(17):
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).perform()
                    time.sleep(0.02)
                print("✅  selected.")

                # STEP 8: Click the "Add Link" button
                print("Clicking Add Link button...")
                hyperlink_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Add Link" or @title="Add Link"]'))
                )
                hyperlink_button.click()
                print("✅ Add Link button clicked.")
                time.sleep(1)

                # STEP 9: Wait for URL input and paste the URL
                link_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Enter URL..."]'))
                )
                link_input.click()
                print("✅  URL input box focused.")

                pyperclip.copy(article_url)
                link_input.send_keys(Keys.CONTROL, 'v')
                print("⌨️ CTRL+V sent to paste URL.")
                time.sleep(1)


                # STEP 10: Confirm hyperlink using the check icon
                check_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//i[contains(@class, "icon-check")]/parent::button'))
                )
                check_button.click()
                print("✅  Link confirmed via check icon.")
                time.sleep(1.5)

                # ✅ STEP 11: Refocus the caption box after link is confirmed
                caption_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "editable-message-text-modal"))
                )
                caption_box.click()
     
                time.sleep(1.5)  # Wait for modal and button to fully update

                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "wDqWK9MD")]//button[contains(@class, "primary") and text()="Send"]'))
                )
                send_button.click()
                time.sleep(2)
                print("✅ Image and caption sent.")

                # ✅ Log this send in posting_history
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

            except Exception as e:
                print(f"❌ Failed to send image and caption: {e}")

            print(f"📬 Message fully sent to {channel_url} in language '{lang_code}'")
            delay = random.uniform(30, 150)  # 30 sec to 2.5 minutes
            print(f"⏳ Waiting {delay:.2f} seconds before sending to the next channel...")
            time.sleep(delay)

        except Exception as e:
            print(f"❌ Error sending message to {channel_url}: {e}")

    # input("Press Enter to close the browser...")
    driver.quit()

