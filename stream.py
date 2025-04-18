
import asyncio
import logging
from typing import Dict, Optional, Any, Callable
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound

from queues import music_queue
from config import ACTIVE_CALLS, MESSAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream")

class MusicPlayer:
    def __init__(self, user_client: Client):
        self.user_client = user_client
        self.py_tgcalls = PyTgCalls(user_client)
        self.active_streams: Dict[int, Dict[str, Any]] = {}
        
        # Set up callback handlers
        self.py_tgcalls.on_stream_end(self._on_stream_end)
        self.py_tgcalls.on_group_call_ended(self._on_group_call_ended)
    
    async def start(self):
        """Start the PyTgCalls client."""
        await self.py_tgcalls.start()
        logger.info("PyTgCalls client started.")
    
    async def _on_stream_end(self, _, update: Update):
        """Handle stream end event."""
        chat_id = update.chat_id
        logger.info(f"Stream ended in chat {chat_id}")
        
        # Check if there are more songs in queue
        if music_queue.has_next(chat_id):
            await self.skip(chat_id)
        else:
            # No more songs, clean up
            await self.stop(chat_id)
    
    async def _on_group_call_ended(self, _, update: Update):
        """Handle group call ended event."""
        chat_id = update.chat_id
        logger.info(f"Group call ended in chat {chat_id}")
        
        # Clean up
        if chat_id in self.active_streams:
            del self.active_streams[chat_id]
        
        if chat_id in ACTIVE_CALLS:
            del ACTIVE_CALLS[chat_id]
    
    async def join_call(self, chat_id: int) -> bool:
        """Join a voice chat."""
        try:
            # Check if already in call
            if chat_id in self.active_streams:
                return True
            
            # Get group call instance
            await self.py_tgcalls.join_group_call(
                chat_id,
                InputAudioStream(
                    'input.raw',  # Placeholder, will be replaced when playing
                    HighQualityAudio(),
                ),
                stream_type=0  # Audio stream
            )
            
            # Update active calls
            ACTIVE_CALLS[chat_id] = {
                "joined_at": asyncio.get_event_loop().time(),
                "active": True
            }
            
            return True
        
        except (NoActiveGroupCall, GroupCallNotFound):
            logger.error(f"No active group call in chat {chat_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error joining voice chat in {chat_id}: {e}")
            return False
    
    async def leave_call(self, chat_id: int) -> bool:
        """Leave a voice chat."""
        try:
            if chat_id in self.active_streams:
                await self.py_tgcalls.leave_group_call(chat_id)
                
                # Clean up
                if chat_id in self.active_streams:
                    del self.active_streams[chat_id]
                
                if chat_id in ACTIVE_CALLS:
                    del ACTIVE_CALLS[chat_id]
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error leaving voice chat in {chat_id}: {e}")
            return False
    
    async def play(self, chat_id: int, audio_url: str, song_info: Dict[str, Any]) -> bool:
        """Play a song in a voice chat."""
        try:
            # Join call if not already in call
            if chat_id not in self.active_streams:
                success = await self.join_call(chat_id)
                if not success:
                    return False
            
            # Start streaming
            await self.py_tgcalls.change_stream(
                chat_id,
                InputAudioStream(
                    audio_url,
                    HighQualityAudio(),
                )
            )
            
            # Update active streams
            self.active_streams[chat_id] = {
                "started_at": asyncio.get_event_loop().time(),
                "song_info": song_info
            }
            
            return True
        
        except Exception as e:
            logger.error(f"Error playing song in {chat_id}: {e}")
            return False
    
    async def pause(self, chat_id: int) -> bool:
        """Pause playback."""
        try:
            if chat_id in self.active_streams:
                await self.py_tgcalls.pause_stream(chat_id)
                self.active_streams[chat_id]["paused"] = True
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error pausing playback in {chat_id}: {e}")
            return False
    
    async def resume(self, chat_id: int) -> bool:
        """Resume playback."""
        try:
            if chat_id in self.active_streams and self.active_streams[chat_id].get("paused", False):
                await self.py_tgcalls.resume_stream(chat_id)
                self.active_streams[chat_id]["paused"] = False
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error resuming playback in {chat_id}: {e}")
            return False
    
    async def stop(self, chat_id: int) -> bool:
        """Stop playback and leave voice chat."""
        try:
            if chat_id in self.active_streams:
                # Clear queue first
                music_queue.clear_queue(chat_id)
                
                # Leave call
                await self.leave_call(chat_id)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error stopping playback in {chat_id}: {e}")
            return False
    
    async def skip(self, chat_id: int) -> bool:
        """Skip current song and play next if available."""
        try:
            # Skip current song in queue
            next_song = music_queue.skip(chat_id)
            
            if next_song:
                # Play next song
                audio_url = next_song.get("audio_url")
                if audio_url:
                    return await self.play(chat_id, audio_url, next_song)
                return False
            else:
                # No more songs, stop playback
                await self.stop(chat_id)
                return True
        
        except Exception as e:
            logger.error(f"Error skipping song in {chat_id}: {e}")
            return False
    
    async def set_volume(self, chat_id: int, volume: int) -> bool:
        """Set volume (1-200)."""
        try:
            if chat_id in self.active_streams:
                # Ensure volume is in valid range
                volume = max(1, min(200, volume))
                
                await self.py_tgcalls.change_volume_call(chat_id, volume)
                self.active_streams[chat_id]["volume"] = volume
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error setting volume in {chat_id}: {e}")
            return False
    
    def is_playing(self, chat_id: int) -> bool:
        """Check if music is playing in the chat."""
        return chat_id in self.active_streams and not self.active_streams[chat_id].get("paused", False)
    
    def is_in_call(self, chat_id: int) -> bool:
        """Check if the bot is in a voice chat."""
        return chat_id in self.active_streams
    
    def get_active_streams(self) -> Dict[int, Dict[str, Any]]:
        """Get all active streams."""
        return self.active_streams.copy()
