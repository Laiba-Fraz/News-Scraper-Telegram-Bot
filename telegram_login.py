from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
import os

def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--user-data-dir=C:/temp/selenium_profile")  # Use fresh path
    service = Service()
    return webdriver.Chrome(service=service, options=chrome_options)
    
def telegram_automation():
    url = "https://web.telegram.org/k/"  # Correct URL
    cookies_file = "telegram_cookies.json"
    driver = setup_driver()

    driver.maximize_window()  # Optional: opens full screen
    driver.get(url)
    time.sleep(5)

    if os.path.exists(cookies_file):
        load_cookies(driver, cookies_file)
        driver.refresh()
        time.sleep(5)
        if "login" not in driver.current_url:
            print("✅ Auto-login successful with cookies.")
        else:
            print("⚠️ Cookies invalid or expired. Please log in manually.")
    else:
        print("🔐 No cookie file found. Please log in manually.")
        print("⏳ Waiting 60 seconds for manual login...")
        time.sleep(60)
        save_cookies(driver, cookies_file)
        print("✅ Cookies saved for future auto-login.")

    input("🔚 Press Enter to quit...")
    driver.quit()

if __name__ == "__main__":
    telegram_automation()
