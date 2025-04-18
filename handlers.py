
import time
import asyncio
import logging
from typing import Dict, Optional, List
from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.errors import (
    ChannelPrivate, 
    ChatAdminRequired, 
    UserNotParticipant,
    PeerIdInvalid
)

import youtube
from queues import music_queue
from config import MESSAGES, DURATION_LIMIT, DEFAULT_VOLUME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handlers")

# Store references to clients
bot_client: Optional[Client] = None
user_client: Optional[Client] = None
music_player = None

# Helper functions
async def is_admin(chat_id: int, user_id: int) -> bool:
    """Check if a user is an admin in the chat."""
    try:
        member = await bot_client.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

async def is_user_in_call(chat_id: int, user_id: int) -> bool:
    """Check if a user is in the voice chat."""
    try:
        # This is a simplification as PyTgCalls doesn't provide an easy way to check
        # In a real implementation, you'd need a more sophisticated approach
        return True
    except Exception:
        return False

def get_readable_time(seconds: int) -> str:
    """Convert seconds to readable time format."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{days}d")
    if hours > 0:
        time_parts.append(f"{hours}h")
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if seconds > 0 or not time_parts:
        time_parts.append(f"{seconds}s")
    
    return " ".join(time_parts)

# Handler setup function
def setup_handlers(bot: Client, user: Client, player):
    """Set up command handlers."""
    global bot_client, user_client, music_player
    bot_client = bot
    user_client = user
    music_player = player
    
    # Start and help commands
    @bot.on_message(filters.command("start"))
    async def start_command(client: Client, message: Message):
        """Handle /start command."""
        await message.reply_text(MESSAGES["start"])
    
    @bot.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        """Handle /help command."""
        await message.reply_text(MESSAGES["help"])
    
    @bot.on_message(filters.command("ping"))
    async def ping_command(client: Client, message: Message):
        """Handle /ping command."""
        start_time = time.time()
        m = await message.reply_text("Pinging...")
        end_time = time.time()
        
        # Calculate ping time in milliseconds
        ping_time = round((end_time - start_time) * 1000, 2)
        
        await m.edit_text(
            MESSAGES["ping"].format(time_taken=ping_time)
        )
    
    # Play commands
    @bot.on_message(filters.command(["play", "p"]))
    async def play_command(client: Client, message: Message):
        """Handle /play command."""
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if query was provided
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text(
                "Please provide a song name or YouTube link after the command!"
            )
            return
        
        # Get query from message
        if message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text
        else:
            query = " ".join(message.command[1:])
        
        # Send processing message
        processing_msg = await message.reply_text(MESSAGES["processing"])
        
        try:
            # Search for song
            await processing_msg.edit_text(MESSAGES["extracting_info"])
            search_results = await youtube.search_youtube(query, limit=1)
            
            if not search_results:
                await processing_msg.edit_text(
                    MESSAGES["no_results"].format(query=query)
                )
                return
            
            # Get first result
            song_info = search_results[0]
            
            # Check duration limit
            duration = song_info.get("duration", 0)
            if duration > DURATION_LIMIT * 60:
                await processing_msg.edit_text(
                    f"❌ **Songs longer than {DURATION_LIMIT} minutes are not allowed!**\n"
                    f"**Requested song duration:** {youtube.format_duration(duration)}"
                )
                return
            
            # Get audio URL
            video_url = song_info.get("webpage_url", "") or f"https://www.youtube.com/watch?v={song_info.get('id', '')}"
            await processing_msg.edit_text(MESSAGES["downloading"])
            info, audio_url = await youtube.get_audio_url(video_url)
            
            if not audio_url:
                await processing_msg.edit_text(
                    f"❌ **Failed to extract audio URL!**\n{info}"
                )
                return
            
            # Format song info
            title = song_info.get("title", "Unknown Title")
            duration_str = youtube.format_duration(duration)
            thumbnail = song_info.get("thumbnail", "")
            
            # Enhanced song info
            formatted_song = {
                "title": title,
                "duration": duration,
                "duration_str": duration_str,
                "thumbnail": thumbnail,
                "webpage_url": video_url,
                "audio_url": audio_url,
                "requested_by": user_id
            }
            
            # Add to queue
            current_queue = music_queue.get_queue(chat_id)
            position = 0
            
            # Check if queue is empty and bot is not currently playing
            if not current_queue or not music_player.is_playing(chat_id):
                # Add to queue
                position = music_queue.add_to_queue(chat_id, formatted_song, user_id)
                
                # Play immediately since queue was empty or not playing
                success = await music_player.play(chat_id, audio_url, formatted_song)
                
                if success:
                    # Create inline keyboard
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                            InlineKeyboardButton("⏹ Stop", callback_data="stop"),
                            InlineKeyboardButton("⏭ Skip", callback_data="skip")
                        ],
                        [InlineKeyboardButton("🎵 YouTube", url=video_url)]
                    ])
                    
                    # Send now playing message
                    await processing_msg.edit_text(
                        MESSAGES["playing"].format(
                            title=title,
                            duration=duration_str,
                            requester=f"[{message.from_user.first_name}](tg://user?id={user_id})"
                        ),
                        reply_markup=keyboard,
                        disable_web_page_preview=False
                    )
                else:
                    await processing_msg.edit_text(
                        "❌ **Failed to join voice chat!**\n"
                        "Make sure a voice chat is active in this group."
                    )
                    music_queue.clear_queue(chat_id)
            else:
                # Add to queue since we're already playing something
                position = music_queue.add_to_queue(chat_id, formatted_song, user_id)
                
                if position == -1:
                    await processing_msg.edit_text(
                        f"❌ **Queue limit reached!** ({music_queue.max_size} songs)"
                    )
                else:
                    # Create inline keyboard
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎵 YouTube", url=video_url)]
                    ])
                    
                    # Send queued message
                    await processing_msg.edit_text(
                        MESSAGES["queued"].format(
                            title=title,
                            duration=duration_str,
                            requester=f"[{message.from_user.first_name}](tg://user?id={user_id})",
                            position=position + 1
                        ),
                        reply_markup=keyboard,
                        disable_web_page_preview=False
                    )
        
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await processing_msg.edit_text(
                MESSAGES["error"].format(error=str(e))
            )
    
    @bot.on_message(filters.command("search"))
    async def search_command(client: Client, message: Message):
        """Handle /search command."""
        # Check if query was provided
        if len(message.command) < 2:
            await message.reply_text(
                "Please provide a search query after the command!"
            )
            return
        
        # Get query from message
        query = " ".join(message.command[1:])
        
        # Send processing message
        processing_msg = await message.reply_text(MESSAGES["processing"])
        
        try:
            # Search for songs
            search_results = await youtube.search_youtube(query, limit=5)
            
            if not search_results:
                await processing_msg.edit_text(
                    MESSAGES["no_results"].format(query=query)
                )
                return
            
            # Format results
            text = f"🔍 **Search results for:** {query}\n\n"
            buttons = []
            
            for i, result in enumerate(search_results, start=1):
                title = result.get("title", "Unknown Title")
                duration = result.get("duration", 0)
                duration_str = youtube.format_duration(duration)
                video_id = result.get("id", "")
                
                text += f"**{i}.** {title}\n⏱ {duration_str}\n\n"
                buttons.append([
                    InlineKeyboardButton(
                        f"{i}. {title[:30]}...",
                        callback_data=f"play_{video_id}"
                    )
                ])
            
            # Send results
            await processing_msg.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
        
        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await processing_msg.edit_text(
                MESSAGES["error"].format(error=str(e))
            )
    
    # Queue commands
    @bot.on_message(filters.command("queue"))
    async def queue_command(client: Client, message: Message):
        """Handle /queue command."""
        chat_id = message.chat.id
        
        # Get queue for this chat
        queue = music_queue.get_queue(chat_id)
        
        if not queue:
            await message.reply_text(MESSAGES["no_songs_in_queue"])
            return
        
        # Format queue message
        queue_text = "🎵 **Current Queue:**\n\n"
        
        for i, song in enumerate(queue):
            title = song.get("title", "Unknown Title")
            duration = song.get("duration_str", "Unknown Duration")
            requested_by = song.get("requested_by", 0)
            
            status = "🎵 Playing" if i == 0 else f"#{i+1} In Queue"
            queue_text += f"**{status}:** {title}\n⏱ {duration} • Requested by: <a href='tg://user?id={requested_by}'>User</a>\n\n"
            
            # Limit message length
            if len(queue_text) > 3900:
                queue_text += f"\n... and {len(queue) - i - 1} more songs"
                break
        
        # Add queue stats
        stats = music_queue.get_queue_stats(chat_id)
        total_duration = get_readable_time(stats["total_duration"])
        queue_text += f"\n**Queue Stats:**\n" \
                     f"• Total songs: {stats['size']}/{stats['max_size']}\n" \
                     f"• Total duration: {total_duration}"
        
        # Create controls keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                InlineKeyboardButton("⏹ Stop", callback_data="stop"),
                InlineKeyboardButton("⏭ Skip", callback_data="skip")
            ],
            [
                InlineKeyboardButton("🗑 Clear Queue", callback_data="clear_queue")
            ]
        ])
        
        # Send queue message
        await message.reply_text(
            queue_text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
            parse_mode="html"
        )
    
    @bot.on_message(filters.command("skip"))
    async def skip_command(client: Client, message: Message):
        """Handle /skip command."""
        chat_id = message.chat.id
        
        # Check if bot is in call
        if not music_player.is_in_call(chat_id):
            await message.reply_text(MESSAGES["not_in_call"])
            return
        
        # Skip current song
        success = await music_player.skip(chat_id)
        
        if success:
            await message.reply_text(MESSAGES["song_skipped"])
        else:
            await message.reply_text("❌ **Failed to skip song!**")
    
    @bot.on_message(filters.command("clear"))
    async def clear_command(client: Client, message: Message):
        """Handle /clear command."""
        chat_id = message.chat.id
        
        # Clear queue
        success = music_queue.clear_queue(chat_id)
        
        if success:
            # Also stop current playback
            await music_player.stop(chat_id)
            await message.reply_text(MESSAGES["queue_cleared"])
        else:
            await message.reply_text(MESSAGES["no_songs_in_queue"])
    
    # Control commands
    @bot.on_message(filters.command("pause"))
    async def pause_command(client: Client, message: Message):
        """Handle /pause command."""
        chat_id = message.chat.id
        
        # Check if bot is in call
        if not music_player.is_in_call(chat_id):
            await message.reply_text(MESSAGES["not_in_call"])
            return
        
        # Pause playback
        success = await music_player.pause(chat_id)
        
        if success:
            await message.reply_text(MESSAGES["playback_paused"])
        else:
            await message.reply_text("❌ **Nothing is playing to pause!**")
    
    @bot.on_message(filters.command("resume"))
    async def resume_command(client: Client, message: Message):
        """Handle /resume command."""
        chat_id = message.chat.id
        
        # Check if bot is in call
        if not music_player.is_in_call(chat_id):
            await message.reply_text(MESSAGES["not_in_call"])
            return
        
        # Resume playback
        success = await music_player.resume(chat_id)
        
        if success:
            await message.reply_text(MESSAGES["playback_resumed"])
        else:
            await message.reply_text("❌ **Nothing is paused to resume!**")
    
    @bot.on_message(filters.command("stop"))
    async def stop_command(client: Client, message: Message):
        """Handle /stop command."""
        chat_id = message.chat.id
        
        # Check if bot is in call
        if not music_player.is_in_call(chat_id):
            await message.reply_text(MESSAGES["not_in_call"])
            return
        
        # Stop playback
        success = await music_player.stop(chat_id)
        
        if success:
            await message.reply_text(MESSAGES["playback_stopped"])
        else:
            await message.reply_text("❌ **Nothing is playing to stop!**")
    
    @bot.on_message(filters.command("volume"))
    async def volume_command(client: Client, message: Message):
        """Handle /volume command."""
        chat_id = message.chat.id
        
        # Check if bot is in call
        if not music_player.is_in_call(chat_id):
            await message.reply_text(MESSAGES["not_in_call"])
            return
        
        # Check if volume level was provided
        if len(message.command) != 2:
            await message.reply_text(
                "Please provide a volume level between 1 and 200!"
            )
            return
        
        # Get volume level
        try:
            volume = int(message.command[1])
            if volume < 1 or volume > 200:
                raise ValueError("Volume must be between 1 and 200!")
        except ValueError as e:
            await message.reply_text(f"❌ **Invalid volume level:** {str(e)}")
            return
        
        # Set volume
        success = await music_player.set_volume(chat_id, volume)
        
        if success:
            await message.reply_text(
                MESSAGES["volume_set"].format(volume=volume)
            )
        else:
            await message.reply_text("❌ **Failed to set volume!**")
    
    # Callback handlers
    @bot.on_callback_query()
    async def callback_handler(client: Client, query: CallbackQuery):
        """Handle callback queries from inline keyboards."""
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        data = query.data
        
        # Handle different callback data
        if data == "pause":
            success = await music_player.pause(chat_id)
            if success:
                await query.answer("Playback paused!")
            else:
                await query.answer("Nothing is playing!", show_alert=True)
        
        elif data == "resume":
            success = await music_player.resume(chat_id)
            if success:
                await query.answer("Playback resumed!")
            else:
                await query.answer("Nothing is paused!", show_alert=True)
        
        elif data == "stop":
            success = await music_player.stop(chat_id)
            if success:
                await query.answer("Playback stopped!")
            else:
                await query.answer("Nothing is playing!", show_alert=True)
        
        elif data == "skip":
            success = await music_player.skip(chat_id)
            if success:
                await query.answer("Song skipped!")
            else:
                await query.answer("Failed to skip song!", show_alert=True)
        
        elif data == "clear_queue":
            success = music_queue.clear_queue(chat_id)
            if success:
                await music_player.stop(chat_id)
                await query.answer("Queue cleared!")
            else:
                await query.answer("Queue is already empty!", show_alert=True)
        
        elif data.startswith("play_"):
            # Extract video ID
            video_id = data.split("_")[1]
            
            # Get video URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Reply to the original search message
            await query.message.reply_text(f"/play {video_url}")
            
            # Answer callback query
            await query.answer("Processing your request...")
        
        else:
            await query.answer("Unknown command!")
