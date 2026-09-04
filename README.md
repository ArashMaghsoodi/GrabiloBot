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
MAX_FILE_SIZE=52428800
MAX_DURATION=7200
USER_RATE_LIMIT=5
CACHE_TTL=86400
```

### Enabling Inline Mode in BotFather
1. Message `@BotFather` on Telegram.
2. Send `/setinline`.
3. Choose your bot and provide a placeholder text (e.g., `Search or paste media link...`).

---

## 🐳 Docker Deployment

Run with Docker Compose:

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
