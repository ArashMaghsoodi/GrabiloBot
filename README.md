# GrabiloBot

Open-source Telegram media downloader bot for YouTube, Instagram, and TikTok.

```
                    GRABILOBOT
                        │
             ┌──────────┴──────────┐
             │                     │
          PRIVATE                INLINE
             │                     │
       Download Center          Quick Share
             │                     │
      Maximum control          Minimum friction
             │                     │
       Full metadata          Minimal metadata
       Many options           Quality + size
       Advanced settings      One-tap selection
             │                     │
             └──────────┬──────────┘
                        │
                 Shared backend
```

---

## 🚀 Two Distinct Experiences

GrabiloBot is split into two specialized workflows:

### 1. Private Chat: Download Center (Maximum Control)
When chatting directly with `@GrabiloBot`:
- Send any YouTube, TikTok, or Instagram link.
- View detailed metadata (title, author, duration, clean formatted sizes).
- Select desired video resolution (2160p, 1440p, 1080p, 720p, 480p, etc.) or audio-only extraction.
- Automatic verification of file sizes against Telegram upload limits.

### 2. Inline Mode: Quick Share (Maximum Speed)
When chatting with friends or in groups:
- Type `@GrabiloBot <URL>` in any input field.
- Instantly preview quality choices with estimated file sizes.
- Tap a quality to share it directly into the active conversation.
- No intrusive menus or configuration popups.

---

## 🛠 Features & Architecture

- **Unified Shared Backend:** Core extraction, format normalization, download queuing, and caching are shared between Private and Inline handlers.
- **Normalized Media & Format Model:** Abstracts away raw stream IDs into clean human-friendly resolutions (`1080p`, `720p`, `Audio (320kbps)`).
- **Two-Layer Caching:**
  - **Metadata Cache:** Prevents duplicate network requests for recent links.
  - **Telegram Media Cache:** Reuses Telegram `file_id` for instant delivery on repeated requests.
- **Worker Queue & Concurrency Limits:** Protects against CPU exhaustion with configurable concurrent workers.
- **Rate Limiting & Abuse Protection:** Per-user request quotas and automated download timeouts.
- **Automatic Disk Cleanup:** Cleans workspace temporary files on boot and immediately after media uploads.

---

## 📦 Supported Platforms

- **YouTube:** Videos, Shorts, standard public URLs (`youtube.com`, `youtu.be`).
- **TikTok:** Public video links (`tiktok.com`, `vm.tiktok.com`, `vt.tiktok.com`).
- **Instagram:** Reels, Posts, IGTV (`instagram.com/reel/`, `/p/`, `/tv/`).

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your variables:

```env
BOT_TOKEN=123456789:ABCDefghIJKlmNoPQRsTUVwxyZ
BOT_USERNAME=GrabiloBot
MAX_CONCURRENT_DOWNLOADS=2
DOWNLOAD_TIMEOUT=600
MAX_DURATION=7200
USER_RATE_LIMIT=5
CACHE_TTL=86400
```

`MAX_FILE_SIZE` defaults to 50 MB with Telegram's hosted API and 2000 MB when a Local Bot API server is configured. Set it explicitly to override the limit.

### Enabling Inline Mode in BotFather
1. Message `@BotFather` on Telegram.
2. Send `/setinline`.
3. Choose your bot and provide a placeholder text (e.g., `Search or paste media link...`).

---

## Native Linux Deployment (without Docker)

The bot can use Telegram's Local Bot API server for local-mode features, including uploads up to 2000 MB. Docker is not required: install the server natively, then run the bot as a normal Python process or service.

### Build and install Telegram's Local Bot API server

1. Get an API ID and hash from [my.telegram.org](https://my.telegram.org).
2. Follow Telegram's [official build instructions generator](https://tdlib.github.io/telegram-bot-api/build.html), selecting the option to install to `/usr/local`. The official [Telegram Bot API repository](https://github.com/tdlib/telegram-bot-api) documents the source build and dependencies.
3. Create a dedicated service account and data directory:

```bash
sudo useradd --system --home-dir /var/lib/telegram-bot-api --create-home --shell /usr/sbin/nologin telegram-bot-api
sudo install -d -o telegram-bot-api -g telegram-bot-api -m 0750 /var/lib/telegram-bot-api
```

4. Create `/etc/telegram-bot-api.env` with the API credentials (do not commit or share this file):

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

Restrict access to the credentials file:

```bash
sudo chown root:telegram-bot-api /etc/telegram-bot-api.env
sudo chmod 0640 /etc/telegram-bot-api.env
```

5. Install and start the included systemd unit:

```bash
sudo install -m 0644 deploy/telegram-bot-api.service /etc/systemd/system/telegram-bot-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot-api
```

The service listens only on `127.0.0.1:8081`; it does not expose the HTTP API publicly. Check it with `systemctl status telegram-bot-api` and `journalctl -u telegram-bot-api`.

### Point the bot to the local server

In the bot's `.env`, set:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_API_URL=http://127.0.0.1:8081
```

Remove any existing `MAX_FILE_SIZE=52428800` setting or change it to `2097152000` to allow the Local Bot API's 2000 MB upload limit. Restart the bot after updating the environment. The bot retries startup indefinitely if Telegram is temporarily unreachable.

When migrating a bot from Telegram's hosted API to a local server, Telegram's [migration instructions](https://github.com/tdlib/telegram-bot-api#moving-a-bot-to-a-local-server) require calling `logOut` on the hosted API before switching the bot to the local endpoint. Follow those instructions before starting the bot against the local server.

## Optional Docker Deployment

Docker Compose remains available as an alternative way to run both the bot and the Local Bot API server:

```bash
docker compose up -d --build
```

---

## 💻 Local Development

1. Ensure `python 3.11+` and `ffmpeg` are installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run unit tests:
   ```bash
   python -m unittest discover tests
   ```
4. Start the bot:
   ```bash
   python app/bot.py
   ```

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
See the [NOTICE](NOTICE) file for attribution information.
