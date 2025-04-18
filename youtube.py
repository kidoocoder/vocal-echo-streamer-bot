
import asyncio
import logging
from typing import Dict, Optional, List, Tuple
import yt_dlp
import re
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("youtube")

# YT-DLP options
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "usenetrc": True,
    "geo-bypass": True,
    "geo-bypass-country": "US",
    "extractor_args": {
        "youtube": {
            "skip": ["dash", "hls"],
            "player_skip": ["js", "configs", "webpage"],
        },
    },
}

# Create YT-DLP client
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Functions
def is_youtube_url(url: str) -> bool:
    """Check if the provided URL is a YouTube URL."""
    patterns = [
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$',
    ]
    return any(re.match(pattern, url) for pattern in patterns)

def extract_video_id(url: str) -> Optional[str]:
    """Extract the video ID from a YouTube URL."""
    if not is_youtube_url(url):
        return None
    
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'youtu.be':
        return parsed_url.path.lstrip('/')
    elif parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            query = parse_qs(parsed_url.query)
            return query.get('v', [None])[0]
        elif match := re.match(r'/embed/([^/]+)', parsed_url.path):
            return match.group(1)
        elif match := re.match(r'/v/([^/]+)', parsed_url.path):
            return match.group(1)
    
    return None

async def search_youtube(query: str, limit: int = 5) -> List[Dict]:
    """Search for videos on YouTube without using cookies."""
    try:
        # If query is a valid YouTube URL, extract info directly
        if is_youtube_url(query):
            info = await asyncio.to_thread(
                ytdl.extract_info, query, download=False
            )
            if info:
                return [info]
        
        # Otherwise, search for videos using the query
        else:
            search_query = f"ytsearch{limit}:{query}"
            info = await asyncio.to_thread(
                ytdl.extract_info, search_query, download=False
            )
            if info and 'entries' in info:
                return info['entries']
        
        return []
    
    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return []

async def get_audio_url(video_url: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Get audio URL and metadata for a YouTube video without using cookies."""
    try:
        # Extract info without downloading
        info = await asyncio.to_thread(
            ytdl.extract_info, video_url, download=False
        )
        
        if not info:
            return None, "Failed to extract video information"
        
        # Find the best audio format
        for format_id in info.get('formats', []):
            if format_id.get('acodec') != 'none' and format_id.get('vcodec') == 'none':
                audio_url = format_id['url']
                return info, audio_url
        
        # If no audio-only format was found, use the best format available
        if info.get('url'):
            return info, info['url']
        
        return None, "No suitable audio format found"
    
    except Exception as e:
        logger.error(f"Error getting audio URL: {e}")
        return None, f"Error: {str(e)}"

def format_duration(duration: Optional[int]) -> str:
    """Format duration in seconds to MM:SS format."""
    if duration is None:
        return "Unknown"
    
    minutes, seconds = divmod(int(duration), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
