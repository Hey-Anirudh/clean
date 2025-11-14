import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden, MessageIdInvalid
import asyncio
import time

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PyrogramChannelCleaner:
    def __init__(self, api_id: int, api_hash: str, bot_token: str):
        self.client = Client(
            "channel_cleaner_bot",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token
        )
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command handlers"""
        
        @self.client.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            """Send a message when the command /start is issued."""
            await message.reply_text(
                "🤖 Channel Cleaner Bot (Pyrogram)\n\n"
                "Commands:\n"
                "/clean @channel_username - Delete all messages from a channel\n"
                "/clean @channel_username 100 - Delete last 100 messages\n"
                "/clean_status - Check cleanup status\n\n"
                "Note: The bot must be an admin in the channel with delete permissions."
            )
        
        @self.client.on_message(filters.command("clean"))
        async def clean_command(client, message: Message):
            """Delete messages from a channel"""
            try:
                if len(message.command) < 2:
                    await message.reply_text(
                        "Usage:\n"
                        "/clean @channel_username - Delete all messages\n"
                        "/clean @channel_username 100 - Delete last 100 messages\n"
                    )
                    return
                
                channel_username = message.command[1]
                limit = None
                
                if len(message.command) > 2:
                    try:
                        limit = int(message.command[2])
                    except ValueError:
                        await message.reply_text("❌ Invalid limit number!")
                        return
                
                # Remove @ if present
                if channel_username.startswith('@'):
                    channel_username = channel_username[1:]
                
                await self.clean_channel(client, message, channel_username, limit)
                
            except Exception as e:
                logger.error(f"Error in clean command: {e}")
                await message.reply_text(f"❌ Error: {str(e)}")
        
        @self.client.on_message(filters.command("clean_status"))
        async def status_command(client, message: Message):
            """Check cleanup status"""
            if hasattr(self, 'last_cleanup_status'):
                status = self.last_cleanup_status
                await message.reply_text(
                    f"📊 Last Cleanup Status:\n"
                    f"Channel: @{status['channel']}\n"
                    f"Deleted: {status['deleted']} messages\n"
                    f"Failed: {status['failed']} messages\n"
                    f"Duration: {status['duration']:.2f} seconds"
                )
            else:
                await message.reply_text("No cleanup operations recorded yet.")
    
    async def clean_channel(self, client, message: Message, channel_username: str, limit: int = None):
        """Main channel cleaning logic"""
        try:
            # Get channel info
            try:
                chat = await client.get_chat(channel_username)
            except Exception as e:
                await message.reply_text(f"❌ Cannot access channel @{channel_username}. Make sure:\n"
                                       "1. The channel exists\n"
                                       "2. Bot is added to the channel\n"
                                       "3. Bot has admin rights")
                return
            
            # Check if it's a channel
            if chat.type not in ["channel", "supergroup"]:
                await message.reply_text("❌ This is not a channel or supergroup!")
                return
            
            # Check admin permissions
            try:
                member = await chat.get_member(client.me.id)
                if not member.privileges:
                    await message.reply_text("❌ Bot is not an admin in this channel!")
                    return
                
                if not member.privileges.can_delete_messages:
                    await message.reply_text("❌ Bot doesn't have permission to delete messages!")
                    return
                    
            except Exception as e:
                await message.reply_text("❌ Cannot check bot permissions. Make sure bot is admin!")
                return
            
            await message.reply_text(f"🚀 Starting to clean messages from @{channel_username}...\n"
                                   f"Limit: {'All messages' if not limit else f'Last {limit} messages'}")
            
            # Initialize counters
            deleted_count = 0
            failed_count = 0
            start_time = time.time()
            
            # Use iter_history for more reliable message fetching
            async for msg in client.get_chat_history(chat.id, limit=limit):
                try:
                    await msg.delete()
                    deleted_count += 1
                    
                    # Progress updates
                    if deleted_count % 50 == 0:
                        await message.reply_text(f"✅ Progress: {deleted_count} messages deleted...")
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)
                    
                except FloodWait as e:
                    # Handle flood waits
                    wait_time = e.value
                    await message.reply_text(f"⏳ Rate limited. Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                except MessageDeleteForbidden:
                    logger.warning(f"Cannot delete message {msg.id} - no permission")
                    failed_count += 1
                    continue
                    
                except Exception as e:
                    logger.warning(f"Error deleting message {msg.id}: {e}")
                    failed_count += 1
                    continue
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Save status
            self.last_cleanup_status = {
                'channel': channel_username,
                'deleted': deleted_count,
                'failed': failed_count,
                'duration': duration
            }
            
            # Final report
            await message.reply_text(
                f"🎉 Cleanup completed!\n\n"
                f"📊 Results:\n"
                f"✅ Successfully deleted: {deleted_count} messages\n"
                f"❌ Failed to delete: {failed_count} messages\n"
                f"⏱️ Duration: {duration:.2f} seconds\n"
                f"📈 Speed: {deleted_count/duration:.2f} msg/sec"
            )
            
        except Exception as e:
            logger.error(f"Error in clean_channel: {e}")
            await message.reply_text(f"❌ Unexpected error: {str(e)}")
    
    async def run(self):
        """Run the client"""
        await self.client.start()
        print("Bot is running...")
        await self.client.idle()

# Alternative version with batch deletion for better performance
class AdvancedPyrogramCleaner(PyrogramChannelCleaner):
    async def clean_channel_batch(self, client, message: Message, channel_username: str, limit: int = None):
        """Advanced cleaning with batch operations"""
        try:
            chat = await client.get_chat(channel_username)
            
            if chat.type not in ["channel", "supergroup"]:
                await message.reply_text("❌ This is not a channel or supergroup!")
                return
            
            # Check permissions
            member = await chat.get_member(client.me.id)
            if not member.privileges or not member.privileges.can_delete_messages:
                await message.reply_text("❌ Bot needs admin rights with delete permission!")
                return
            
            await message.reply_text(f"🚀 Starting BATCH cleanup for @{channel_username}...")
            
            deleted_count = 0
            failed_count = 0
            message_ids = []
            start_time = time.time()
            batch_size = 100  # Telegram allows deleting up to 100 messages at once
            
            # Collect message IDs
            async for msg in client.get_chat_history(chat.id, limit=limit):
                message_ids.append(msg.id)
                
                # Process in batches
                if len(message_ids) >= batch_size:
                    success_count = await self.delete_batch(client, chat.id, message_ids)
                    deleted_count += success_count
                    failed_count += (len(message_ids) - success_count)
                    message_ids = []
                    
                    # Progress update
                    if deleted_count % 500 == 0:
                        await message.reply_text(f"✅ Progress: {deleted_count} messages deleted...")
            
            # Process remaining messages
            if message_ids:
                success_count = await self.delete_batch(client, chat.id, message_ids)
                deleted_count += success_count
                failed_count += (len(message_ids) - success_count)
            
            duration = time.time() - start_time
            
            await message.reply_text(
                f"🎉 Batch cleanup completed!\n\n"
                f"📊 Results:\n"
                f"✅ Deleted: {deleted_count} messages\n"
                f"❌ Failed: {failed_count} messages\n"
                f"⏱️ Duration: {duration:.2f} seconds"
            )
            
        except Exception as e:
            await message.reply_text(f"❌ Error in batch cleanup: {str(e)}")
    
    async def delete_batch(self, client, chat_id: int, message_ids: list) -> int:
        """Delete a batch of messages"""
        try:
            await client.delete_messages(chat_id, message_ids)
            return len(message_ids)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await self.delete_batch(client, chat_id, message_ids)
        except Exception as e:
            logger.warning(f"Batch deletion failed: {e}")
            # Try deleting individually
            return await self.delete_individual(client, chat_id, message_ids)
    
    async def delete_individual(self, client, chat_id: int, message_ids: list) -> int:
        """Delete messages individually when batch fails"""
        success_count = 0
        for msg_id in message_ids:
            try:
                await client.delete_messages(chat_id, msg_id)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Failed to delete message {msg_id}: {e}")
                continue
        return success_count

def main():
    """Main function to run the bot"""
    API_ID = 21370037
    API_HASH = "0b57036f40bb6da488d05b43e2d20dc1"
    BOT_TOKEN = "8309666031:AAGuAHKvoLY5Q43VOUPvqIbHxEBsUlc0_Ls"

    bot = PyrogramChannelCleaner(API_ID, API_HASH, BOT_TOKEN)
    bot.run()


if __name__ == "__main__":
    main()


if __name__ == '__main__':
    asyncio.run(main())
