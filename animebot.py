import requests
from bs4 import BeautifulSoup
import time
import re
import os
import json
import logging
import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("anime_news_bot.log"), logging.StreamHandler()],
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Fetch from environment variables
CHAT_ID = os.getenv("CHAT_ID")  # Fetch from environment variables
POSTED_TITLES_FILE = "posted_titles.json"
BASE_URL = "https://www.animenewsnetwork.com"
DEBUG_MODE = False  # Set True to test without date filter

if not BOT_TOKEN or not CHAT_ID:
    logging.error("BOT_TOKEN or CHAT_ID is missing. Check environment variables.")
    exit(1)

# Time Zone Handling
utc_tz = pytz.utc
local_tz = pytz.timezone("Asia/Kolkata")  # Change if needed
today_local = datetime.now(local_tz).date()

session = requests.Session()

def escape_html(text):
    """Escapes special characters for Telegram HTML formatting."""
    if not text or not isinstance(text, str):
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def load_posted_titles():
    """Loads posted titles from file."""
    try:
        if os.path.exists(POSTED_TITLES_FILE):
            with open(POSTED_TITLES_FILE, "r", encoding="utf-8") as file:
                return set(json.load(file))
        return set()
    except json.JSONDecodeError:
        logging.error("Error decoding posted_titles.json. Resetting file.")
        return set()

def save_posted_title(title):
    """Saves a title to prevent duplicate posting."""
    try:
        titles = load_posted_titles()
        titles.add(title)
        with open(POSTED_TITLES_FILE, "w", encoding="utf-8") as file:
            json.dump(list(titles), file)
    except Exception as e:
        logging.error(f"Error saving posted title: {e}")

def validate_image_url(image_url):
    """Validates if the image URL is accessible by fetching a small portion of the image."""
    if not image_url:
        return False
    try:
        # Fetch only the first 1KB to verify the image
        headers = {"Range": "bytes=0-1023"}
        response = session.get(image_url, headers=headers, timeout=5, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            logging.warning(f"URL {image_url} is not an image: {content_type}")
            return False
        return True
    except requests.RequestException as e:
        logging.warning(f"Invalid or inaccessible image URL {image_url}: {e}")
        return False

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_anime_news():
    """Fetches latest anime news from ANN."""
    try:
        response = session.get(BASE_URL, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        all_articles = soup.find_all("div", class_="herald box news t-news")
        logging.info(f"Total articles found: {len(all_articles)}")

        for article in all_articles:
            title_tag = article.find("h3")
            date_tag = article.find("time")
            
            if not title_tag or not date_tag:
                continue

            title = title_tag.get_text(strip=True)
            date_str = date_tag["datetime"]  
            try:
                news_date = datetime.fromisoformat(date_str).astimezone(local_tz).date()
            except ValueError as e:
                logging.error(f"Error parsing date {date_str}: {e}")
                continue

            if DEBUG_MODE or news_date == today_local:
                link = title_tag.find("a")
                article_url = f"{BASE_URL}{link['href']}" if link else None
                news_list.append({"title": title, "article_url": article_url, "article": article})
                logging.info(f"✅ Found today's news: {title}")
            else:
                logging.info(f"⏩ Skipping (not today's news): {title} - Date: {news_date}")

        logging.info(f"Filtered today's articles: {len(news_list)}")
        return news_list

    except requests.RequestException as e:
        logging.error(f"Fetch error: {e}")
        return []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_article_details(article_url, article):
    """Fetches article image and summary."""
    image_url = None
    summary = "No summary available."

    thumbnail = article.find("div", class_="thumbnail lazyload")
    if thumbnail and thumbnail.get("data-src"):
        img_url = thumbnail["data-src"]
        image_url = f"{BASE_URL}{img_url}" if not img_url.startswith("http") else img_url
        logging.info(f"🔹 Extracted Image URL: {image_url}")

    if article_url:
        try:
            article_response = session.get(article_url, timeout=5)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, "html.parser")
            content_div = article_soup.find("div", class_="meat") or article_soup.find("div", class_="content")
            if content_div:
                first_paragraph = content_div.find("p")
                if first_paragraph:
                    summary = first_paragraph.get_text(strip=True)[:300] + "..." if len(first_paragraph.text) > 300 else first_paragraph.text
        except requests.RequestException as e:
            logging.error(f"Error fetching article content: {e}")

    return {"image": image_url, "summary": summary}

def fetch_selected_articles(news_list):
    """Fetches article details concurrently."""
    posted_titles = load_posted_titles()
    articles_to_fetch = [news for news in news_list if news["title"] not in posted_titles]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_article_details, news["article_url"], news["article"]): news for news in articles_to_fetch}
        
        for future in futures:
            try:
                result = future.result(timeout=10)
                news = futures[future]
                news["image"] = result["image"]
                news["summary"] = result["summary"]
            except Exception as e:
                logging.error(f"Error processing article: {e}")
                news = futures[future]
                news["image"] = None
                news["summary"] = "Failed to fetch summary."

def send_to_telegram(title, image_url, summary):
    """Posts news to Telegram with HTML formatting."""
    safe_title = escape_html(title)
    safe_summary = escape_html(summary) if summary else "No summary available"

    # Format the caption with a bold title, a line, summary, and the required ending
    caption = (
        f"<b>{safe_title}</b> ⚡\n"
        f"﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n"
        f"{safe_summary}\n"
        f"﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋\n"
        f"🍁| @TheAnimeTimes_acn"
    )

    # Ensure caption length is within Telegram's 1024-character limit for sendPhoto
    if len(caption) > 1024:
        safe_summary = safe_summary[:1024 - len(safe_title) - 50] + "..."
        caption = (
            f"<b>{safe_title}</b> ⚡\n"
            f"﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n"
            f"{safe_summary}\n"
            f"﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋﹋\n"
            f"🍁| @TheAnimeTimes_acn"
        )

    logging.info(f"Sending to Telegram - Title: {title}")
    logging.info(f"Image URL: {image_url}")
    logging.info(f"Caption: {caption}")

    # First, try sending with a photo if the image URL is valid
    if image_url and validate_image_url(image_url):
        try:
            response = session.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": CHAT_ID,
                    "photo": image_url,
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            response.raise_for_status()
            logging.info(f"✅ Posted with photo: {title}")
            save_posted_title(title)
            return
        except requests.RequestException as e:
            logging.error(f"Failed to send photo for {title}: {e}")
            # Fall through to sendMessage

    # Fallback to sending a text message if photo fails or no valid image
    try:
        response = session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": caption,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        response.raise_for_status()
        logging.info(f"✅ Posted as text: {title}")
        save_posted_title(title)
    except requests.RequestException as e:
        logging.error(f"Failed to send message for {title}: {e}")
        # Do not retry; just log and move on

def run_once():
    logging.info("Fetching latest anime news...")
    logging.info(f"Today's date (local): {today_local}")
    news_list = fetch_anime_news()
    if not news_list:
        logging.info("No new articles to post.")
        return

    fetch_selected_articles(news_list)
    
    for news in news_list:
        if news["title"] not in load_posted_titles():
            send_to_telegram(news["title"], news["image"], news["summary"])
            time.sleep(2)  # Delay to avoid hitting Telegram rate limits

if __name__ == "__main__":
    run_once()
