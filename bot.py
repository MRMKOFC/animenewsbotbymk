import requests
from bs4 import BeautifulSoup
import time
import re
import os

# Your Telegram Bot Token and Group Chat ID
bot_token = "BOT TOKEN "
chat_id = "GROUP ID "

# File to store all posted news titles
POSTED_TITLES_FILE = "posted_titles.txt"

# Function to escape special characters for MarkdownV2
def escape_markdown(text):
    """Escapes special characters in MarkdownV2 formatting"""
    return re.sub(r'([_*()~`>#\+\-=|{}.!])', r'\\\1', text)

# Function to load all posted titles from file
def load_posted_titles():
    if os.path.exists(POSTED_TITLES_FILE):
        with open(POSTED_TITLES_FILE, "r", encoding="utf-8") as file:
            return set(file.read().splitlines())  # Store as a set for quick lookups
    return set()

# Function to save new posted titles to file
def save_posted_title(title):
    with open(POSTED_TITLES_FILE, "a", encoding="utf-8") as file:
        file.write(title + "\n")

# Function to fetch the latest anime news
def fetch_anime_news():
    url = "https://www.animenewsnetwork.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.find_all('div', class_='herald box news t-news')

    news_list = []

    for article in articles:
        title_tag = article.find('h3')
        title = title_tag.get_text().strip() if title_tag else "No Title"

        image_tag = article.find('div', class_='thumbnail lazyload')
        image_url = image_tag['data-src'] if image_tag else None

        trailer_tag = article.find('a', {'class': 'trailer'})
        trailer_url = trailer_tag['href'] if trailer_tag and 'youtube.com' in trailer_tag['href'] else None  # Only YouTube links

        news_item = {
            'title': title,
            'image': f"https://www.animenewsnetwork.com{image_url}" if image_url else None,
            'trailer': trailer_url if trailer_url else None
        }
        news_list.append(news_item)

    return news_list

# Function to send a message with an image and/or trailer to Telegram group
def send_to_telegram(title, image_url=None, trailer_url=None):
    title = escape_markdown(title)

    caption = f"📰 {title}"
    if trailer_url:
        caption += f"\n📹 [Watch Trailer]({trailer_url})"
    caption += "\n\n```@TheAnimeTimes_acn```"

    params = {'chat_id': chat_id, 'parse_mode': 'MarkdownV2'}
    if image_url:
        send_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        params.update({'photo': image_url, 'caption': caption})
    else:
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params.update({'text': caption})

    response = requests.get(send_url, params=params)
    if response.status_code == 200:
        print(f"✅ Posted: {title}")
        save_posted_title(title)  # Save the title after a successful post
    else:
        print(f"❌ Error posting: {title} - Status: {response.status_code}")
        print(f"❌ Telegram API error: {response.json()}")

# Function to check for new news and post it
def check_and_post_news():
    news_list = fetch_anime_news()
    posted_titles = load_posted_titles()  # Load all previously posted titles

    new_posts = 0

    for news in news_list:
        if news['title'] in posted_titles:
            print(f"🔄 Skipping (Already Posted): {news['title']}")
            continue  # Skip already posted news

        send_to_telegram(news['title'], news['image'], news['trailer'])
        new_posts += 1
        time.sleep(2)  # Prevent spamming

    if new_posts == 0:
        print("🔄 No new news to post.")

# Function to run continuously and update news
def auto_update(interval=600):
    while True:
        print("🔄 Checking for new news updates...")
        check_and_post_news()
        time.sleep(interval)

# Start auto update
auto_update()