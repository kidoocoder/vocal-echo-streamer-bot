
import os
import asyncio
import logging
from pyrogram import Client
from pyrogram.errors import AuthKeyUnregistered, AuthKeyInvalid

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING
from stream import MusicPlayer
import handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

async def main():
    """Main entry point for the bot."""
    # Initialize clients
    logger.info("Initializing clients...")
    
    # Bot client
    bot = Client(
        "music_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    # User client (for voice chat joining)
    user = Client(
        "music_user",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    # Initialize PyTgCalls
    logger.info("Initializing PyTgCalls...")
    music_player = MusicPlayer(user)
    
    # Set up command handlers
    logger.info("Setting up command handlers...")
    handlers.setup_handlers(bot, user, music_player)
    
    # Start clients
    try:
        logger.info("Starting bot client...")
        await bot.start()
        
        logger.info("Starting user client...")
        await user.start()
        
        logger.info("Starting PyTgCalls client...")
        await music_player.start()
        
        logger.info("Bot started successfully!")
        me_bot = await bot.get_me()
        me_user = await user.get_me()
        logger.info(f"Bot username: @{me_bot.username}")
        logger.info(f"User account: {me_user.first_name} (@{me_user.username})")
        
        # Keep the program running
        await asyncio.Event().wait()
    
    except (AuthKeyUnregistered, AuthKeyInvalid):
        logger.error("Session string is invalid or expired! Please generate a new one.")
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    
    finally:
        # Stop clients
        logger.info("Stopping clients...")
        await bot.stop()
        await user.stop()
        logger.info("Clients stopped.")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
