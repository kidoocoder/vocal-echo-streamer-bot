
import os
from typing import Dict

# Bot configuration
API_ID = 12345  # Your API ID from my.telegram.org
API_HASH = "your_api_hash_here"  # Your API hash from my.telegram.org
BOT_TOKEN = "your_bot_token_here"  # Your bot token from @BotFather
SESSION_STRING = "your_session_string_here"  # Your string session for user account

# Music configuration
MAX_PLAYLIST_SIZE = 50
DURATION_LIMIT = 180  # in minutes
DEFAULT_VOLUME = 100

# Messages
MESSAGES = {
    "start": "👋 Hi! I'm a Music Bot powered by Pyrogram and Py-TgCalls.\n\nUse /help to see available commands.",
    "help": """🎵 **Available Commands**:

**Music Commands**
• /play [song name/link] - Play song from YouTube
• /search [query] - Search for a song on YouTube

**Queue Commands**
• /queue - Show current queue
• /skip - Skip current song
• /clear - Clear the queue

**Player Controls**
• /pause - Pause playback
• /resume - Resume playback
• /stop - Stop playback
• /volume [1-200] - Adjust volume

**Other Commands**
• /ping - Check bot response time
• /help - Show this message
""",
    "not_in_call": "❌ **I'm not in a voice chat!**",
    "already_in_call": "✅ **Already in voice chat!**",
    "joined_voice_chat": "✅ **Joined voice chat!**",
    "left_voice_chat": "✅ **Left voice chat!**",
    "no_voice_chat": "❌ **No active voice chat found!**",
    "not_in_same_voice_chat": "❌ **You need to be in the same voice chat!**",
    "playing": "🎵 **Playing:** {title}\n⏱ **Duration:** {duration}\n🔗 **Requested by:** {requester}",
    "queued": "🎵 **Queued:** {title}\n⏱ **Duration:** {duration}\n🔗 **Requested by:** {requester}\n🔢 **Position:** #{position}",
    "no_results": "❌ **No results found for:** {query}",
    "no_songs_in_queue": "❌ **No songs in queue!**",
    "queue_cleared": "🗑 **Queue cleared!**",
    "song_skipped": "⏭ **Song skipped!**",
    "playback_paused": "⏸ **Playback paused!**",
    "playback_resumed": "▶️ **Playback resumed!**",
    "playback_stopped": "⏹ **Playback stopped!**",
    "volume_set": "🔊 **Volume set to:** {volume}%",
    "processing": "⏳ **Processing...**",
    "extracting_info": "📥 **Extracting information...**",
    "downloading": "📥 **Downloading audio...**",
    "error": "❌ **Error:** {error}",
    "ping": "🏓 **Pong!** `{time_taken}ms`",
}

# Active voice chats (chat_id: call_info)
ACTIVE_CALLS: Dict[int, Dict] = {}
