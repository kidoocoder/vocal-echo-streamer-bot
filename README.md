# Telegram Music Bot

A high-quality Telegram music bot using Pyrogram and Py-TgCalls that plays songs in voice chats based on user requests. The bot uses YouTube as the primary music source and extracts audio using yt-dlp without requiring YouTube cookies.

## Deployment

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/kidoocoder/vocal-echo-streamer-bot)

## Features

- Play songs from YouTube via search queries or direct links
- Queue management (add, skip, clear)
- Basic controls (pause, resume, stop)
- Song information display (title, duration, thumbnail)
- Volume control
- Session management for user authentication

## Requirements

- Python 3.8 or higher
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Pyrogram user session string (for joining voice chats)
- API ID and API Hash from [my.telegram.org](https://my.telegram.org)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/telegram-music-bot.git
   cd telegram-music-bot
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - Open `config.py` and edit the following variables:
     - `API_ID`: Your API ID from my.telegram.org
     - `API_HASH`: Your API hash from my.telegram.org
     - `BOT_TOKEN`: Your bot token from @BotFather
     - `SESSION_STRING`: Your Pyrogram user session string

4. Run the bot:
   ```
   python main.py
   ```

## Getting a Session String

You need a Pyrogram session string for the user account that will join voice chats. To get one:

1. Install Pyrogram:
   ```
   pip install pyrogram TgCrypto
   ```

2. Run this script:
   ```python
   from pyrogram import Client

   API_ID = your_api_id
   API_HASH = "your_api_hash"

   with Client("my_account", API_ID, API_HASH) as app:
       print(app.export_session_string())
   ```

3. Follow the prompts and copy the session string to your `config.py` file.

## Commands

- `/play [song name/link]` - Play song from YouTube
- `/search [query]` - Search for a song on YouTube
- `/queue` - Show current queue
- `/skip` - Skip current song
- `/clear` - Clear the queue
- `/pause` - Pause playback
- `/resume` - Resume playback
- `/stop` - Stop playback
- `/volume [1-200]` - Adjust volume
- `/ping` - Check bot response time
- `/help` - Show help message

## Notes

- The bot requires both a bot account and a user account to function properly.
- The bot account handles commands, while the user account joins voice chats.
- YouTube cookies are not required, as the bot uses yt-dlp to extract audio.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Heroku Deployment

To deploy this bot on Heroku, you'll need to set the following environment variables:

- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `BOT_TOKEN`: Your Telegram Bot Token
- `SESSION_STRING`: Your Pyrogram User Session String

You can obtain these by following the instructions in the "Requirements" and "Getting a Session String" sections above.
