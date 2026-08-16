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
 Image publishing
        ↓
 Telegram channel
```

## Features

- Fetches recent anime news from ANN
- Publishes images with formatted captions when available
- Falls back to text when image publishing fails
- Prevents duplicate posts using local JSON state
- Timezone-aware filtering with `Asia/Kolkata` as the documented default
- HTML escaping for Telegram messages
- Retry handling for transient network failures
- Designed for scheduled/cron execution

## Requirements

- Python 3.9+
- Telegram Bot Token
- Telegram channel/group chat ID
- Network access to the configured news source and Telegram API

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

Provide the Telegram credentials expected by the application through environment variables or the configuration mechanism used by the current source code.

**Never commit a real bot token to Git.**

Typical deployment configuration should include:

```text
BOT_TOKEN=<telegram-bot-token>
CHANNEL_ID=<telegram-channel-or-chat-id>
```

Check the source for the exact variable names before deployment.

## Duplicate protection

The bot keeps local state so an article already published by a previous scheduled run can be skipped. This makes repeated cron/GitHub Actions executions safer than publishing every fetched article blindly.

Because the state is local, deployments that destroy or reset the filesystem can lose the duplicate history.

## Reliability

Network and Telegram operations use retry/fallback handling. Image delivery can fall back to a text-only post when the image cannot be published.

A production deployment should additionally monitor failed scheduled runs and persist state on durable storage if the runtime is ephemeral.

## Scheduling

The bot is intended to be run periodically rather than kept alive unnecessarily. GitHub Actions or another cron scheduler can invoke the scraper at the desired interval.

## Limitations

- The bot depends on the upstream news site's availability and markup.
- Scraping can break when the source changes its HTML structure.
- Telegram limits message/media size and request frequency.
- Local JSON state is not a database and is not designed for concurrent writers.

## Legal / source notice

News content and images remain subject to the rights and terms of their respective publishers and owners. This project is an automation/learning project and does not claim ownership of third-party content.

## License

See the repository license for the applicable terms.

## Author

**Mohith Krishnaa** — [@mohith-krishnaa](https://github.com/mohith-krishnaa)
