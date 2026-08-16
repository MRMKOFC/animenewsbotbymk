# Anime News Telegram Bot

A Python automation bot that fetches anime news from **Anime News Network (ANN)** and publishes formatted updates to a Telegram channel.

## Pipeline

```text
Anime News Network
        ↓
     Scraper
        ↓
 Parse / filter
        ↓
 Duplicate check
        ↓
 Format + escape HTML
        ↓
 Image validation / publishing
        ↓
 Telegram channel
```

## Features

- Fetches recent anime news from ANN
- Publishes images with formatted captions when available
- Falls back to text when image publishing fails
- Prevents duplicate posts using local JSON state
- Asia/Kolkata timezone-aware filtering
- HTML escaping for Telegram messages
- Retry handling for transient network failures
- Concurrent article-detail fetching
- Designed for scheduled/cron execution

## Requirements

- Python 3.9+
- Telegram Bot Token
- Telegram chat/channel ID
- Network access to Anime News Network and Telegram API

## Installation

```bash
git clone https://github.com/mohith-krishnaa/animenewsbotbymk.git
cd animenewsbotbymk
python -m venv .venv
```

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

The bot reads these environment variables directly:

```text
BOT_TOKEN=<telegram-bot-token>
CHAT_ID=<telegram-channel-or-chat-id>
```

These are the exact names used by `animebot.py`. fileciteturn72file0

**Never commit a real Telegram token to Git.**

For GitHub Actions, store the values as repository secrets and expose them to the workflow environment.

## Duplicate protection

Published titles are stored in `posted_titles.json`. A title already present in the state file is skipped on later scheduled runs.

The state is local runtime data. If the execution environment is ephemeral, duplicate history can be lost between runs unless the file is persisted.

## Image handling

The bot validates image URLs before attempting publication. If an image cannot be retrieved or processed, the text-only fallback can still publish the article. fileciteturn72file0

## Reliability

Network operations use a persistent HTTP session, timeouts and retry handling. Article-detail work can be performed concurrently to reduce overall scraping time.

## Scheduling

The bot is designed to run periodically through GitHub Actions or another cron scheduler rather than requiring a permanently running process.

## Limitations

- The bot depends on ANN's current website structure and availability.
- Scraping can require maintenance if ANN changes its HTML.
- Telegram imposes API and media limits.
- Local JSON state is not a database and is not designed for concurrent writers.
- Third-party image URLs can expire or reject requests.

## Legal / source notice

News content and images remain subject to the rights and terms of their respective publishers and owners. This project does not claim ownership of third-party content.

## License

See the repository license for the applicable terms.

## Author

**Mohith Krishnaa** — [@mohith-krishnaa](https://github.com/mohith-krishnaa)
