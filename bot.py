import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden, MessageIdInvalid
import asyncio
import time

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
        @self.client.on_message(filters.command("start"))
        async def start_command(client, message: Message):
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
                
                if channel_username.startswith('@'):
                    channel_username = channel_username[1:]
                
                await self.clean_channel(client, message, channel_username, limit)
                
            except Exception as e:
                logger.error(f"Error in clean command: {e}")
                await message.reply_text(f"❌ Error: {str(e)}")
        
        @self.client.on_message(filters.command("clean_status"))
        async def status_command(client, message: Message):
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
        try:
            try:
                chat = await client.get_chat(channel_username)
            except Exception:
                await message.reply_text(
                    f"❌ Cannot access channel @{channel_username}. Make sure:\n"
                    "1. The channel exists\n"
                    "2. Bot is added to the channel\n"
                    "3. Bot has admin rights"
                )
                return
            
            if chat.type not in ["channel", "supergroup"]:
                await message.reply_text("❌ This is not a channel or supergroup!")
                return

            try:
                member = await chat.get_member(client.me.id)
                if not member.privileges or not member.privileges.can_delete_messages:
                    await message.reply_text("❌ Bot doesn't have delete message permission!")
                    return
            except:
                await message.reply_text("❌ Cannot check bot permissions. Make sure bot is admin!")
                return
            
            await message.reply_text(
                f"🚀 Starting to clean messages from @{channel_username}...\n"
                f"Limit: {'All messages' if not limit else f'Last {limit} messages'}"
            )
            
            deleted_count = 0
            failed_count = 0
            start_time = time.time()
            
            async for msg in client.get_chat_history(chat.id, limit=limit):
                try:
                    await msg.delete()
                    deleted_count += 1
                    
                    if deleted_count % 50 == 0:
                        await message.reply_text(f"✅ Progress: {deleted_count} messages deleted...")
                    
                    await asyncio.sleep(0.2)
                    
                except FloodWait as e:
                    await message.reply_text(f"⏳ FloodWait: Waiting {e.value} sec...")
                    await asyncio.sleep(e.value)
                
                except MessageDeleteForbidden:
                    failed_count += 1
                
                except Exception:
                    failed_count += 1
            
            duration = time.time() - start_time
            
            self.last_cleanup_status = {
                'channel': channel_username,
                'deleted': deleted_count,
                'failed': failed_count,
                'duration': duration
            }
            
            await message.reply_text(
                f"🎉 Cleanup completed!\n\n"
                f"📊 Results:\n"
                f"✅ Deleted: {deleted_count}\n"
                f"❌ Failed: {failed_count}\n"
                f"⏱️ Duration: {duration:.2f} sec\n"
                f"📈 Speed: {deleted_count/duration:.2f} msg/sec"
            )
            
        except Exception as e:
            logger.error(f"Error in clean_channel: {e}")
            await message.reply_text(f"❌ Unexpected error: {str(e)}")
    
    async def run(self):
        await self.client.start()
        print("Bot is running...")

        # Pyrogram has NO idle() → use wait()
        try:
            await asyncio.Event().wait()
        except:
            await self.client.stop()

async def main():
    API_ID = 21370037
    API_HASH = "0b57036f40bb6da488d05b43e2d20dc1"
    BOT_TOKEN = "8309666031:AAGuAHKvoLY5Q43VOUPvqIbHxEBsUlc0_Ls"

    bot = PyrogramChannelCleaner(API_ID, API_HASH, BOT_TOKEN)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
