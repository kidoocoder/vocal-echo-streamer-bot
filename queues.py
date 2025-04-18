
from typing import Dict, List, Optional, Any
import time
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("queues")

class MusicQueue:
    def __init__(self, max_size: int = 50):
        self.queues: Dict[int, List[Dict[str, Any]]] = {}
        self.max_size = max_size
    
    def get_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        """Get the queue for a chat."""
        if chat_id not in self.queues:
            self.queues[chat_id] = []
        return self.queues[chat_id]
    
    def add_to_queue(
        self, 
        chat_id: int, 
        song_info: Dict[str, Any], 
        requested_by: int
    ) -> int:
        """Add a song to the queue and return its position."""
        if chat_id not in self.queues:
            self.queues[chat_id] = []
        
        # Check if queue is full
        queue = self.queues[chat_id]
        if len(queue) >= self.max_size:
            return -1
        
        # Add song to queue with metadata
        queue_item = {
            **song_info,
            "requested_by": requested_by,
            "queued_at": time.time()
        }
        queue.append(queue_item)
        
        # Return position in queue (0-indexed)
        return len(queue) - 1
    
    def get_current(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get the current song playing in a chat."""
        queue = self.get_queue(chat_id)
        return queue[0] if queue else None
    
    def skip(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Skip the current song and return the next song."""
        queue = self.get_queue(chat_id)
        if not queue:
            return None
        
        # Remove the current song
        queue.pop(0)
        
        # Return the new current song or None if queue is empty
        return queue[0] if queue else None
    
    def clear_queue(self, chat_id: int) -> bool:
        """Clear the queue for a chat."""
        if chat_id in self.queues:
            self.queues[chat_id] = []
            return True
        return False
    
    def is_empty(self, chat_id: int) -> bool:
        """Check if the queue is empty."""
        return not bool(self.get_queue(chat_id))
    
    def has_next(self, chat_id: int) -> bool:
        """Check if there's a next song in the queue."""
        queue = self.get_queue(chat_id)
        return len(queue) > 1
    
    def remove_from_queue(self, chat_id: int, position: int) -> bool:
        """Remove a song from the queue by position."""
        queue = self.get_queue(chat_id)
        if position < 0 or position >= len(queue):
            return False
        
        queue.pop(position)
        return True
    
    def move_in_queue(self, chat_id: int, old_pos: int, new_pos: int) -> bool:
        """Move a song in the queue from old position to new position."""
        queue = self.get_queue(chat_id)
        if old_pos < 0 or old_pos >= len(queue) or new_pos < 0 or new_pos >= len(queue):
            return False
        
        item = queue.pop(old_pos)
        queue.insert(new_pos, item)
        return True
    
    def get_queue_stats(self, chat_id: int) -> Dict[str, Any]:
        """Get statistics about the queue."""
        queue = self.get_queue(chat_id)
        total_duration = sum(item.get('duration', 0) for item in queue)
        
        return {
            "size": len(queue),
            "total_duration": total_duration,
            "max_size": self.max_size,
            "remaining": self.max_size - len(queue)
        }

# Create global music queue instance
music_queue = MusicQueue()
