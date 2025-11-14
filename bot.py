import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChannelCleanerBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("clean", self.clean_channel))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            "🤖 Channel Cleaner Bot\n\n"
            "Commands:\n"
            "/clean @channel_username - Delete all messages from a channel\n"
            "Note: The bot must be an admin in the channel with delete permissions."
        )
    
    async def clean_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete all messages from a channel"""
        if not context.args:
            await update.message.reply_text("Please provide a channel username. Usage: /clean @channel_username")
            return
        
        channel_username = context.args[0]
        
        # Remove @ if present
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
        
        try:
            # Get channel info
            chat = await context.bot.get_chat(f"@{channel_username}")
            chat_id = chat.id
            
            # Check if bot is admin
            bot_member = await chat.get_member(context.bot.id)
            if not bot_member.status in ['administrator', 'creator']:
                await update.message.reply_text("❌ Bot must be an admin in the channel with delete permissions!")
                return
            
            if not bot_member.can_delete_messages and bot_member.status != 'creator':
                await update.message.reply_text("❌ Bot doesn't have permission to delete messages!")
                return
            
            await update.message.reply_text(f"🚀 Starting to clean messages from @{channel_username}...")
            
            # Get message history and delete messages
            deleted_count = 0
            message_id = 1
            
            while True:
                try:
                    # Try to delete message
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
                    
                    # Show progress every 10 messages
                    if deleted_count % 10 == 0:
                        await update.message.reply_text(f"✅ Deleted {deleted_count} messages so far...")
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    # Stop when we reach the end or encounter other errors
                    if "message to delete not found" in str(e).lower():
                        break
                    elif "too many requests" in str(e).lower():
                        await asyncio.sleep(1)  # Wait longer if rate limited
                        continue
                    else:
                        # For other errors, log and continue
                        logger.warning(f"Error deleting message {message_id}: {e}")
                
                message_id += 1
            
            await update.message.reply_text(f"🎉 Cleanup completed! Deleted {deleted_count} messages from @{channel_username}")
            
        except Exception as e:
            logger.error(f"Error cleaning channel: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    def run(self):
        """Run the bot"""
        self.application.run_polling()

# Alternative version with more advanced features
class AdvancedChannelCleanerBot(ChannelCleanerBot):
    async def clean_channel_advanced(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced channel cleaning with more options"""
        if not context.args:
            await update.message.reply_text(
                "Usage:\n"
                "/clean @channel_username - Delete all messages\n"
                "/clean @channel_username 100 - Delete last 100 messages\n"
            )
            return
        
        channel_username = context.args[0]
        limit = None
        
        if len(context.args) > 1:
            try:
                limit = int(context.args[1])
            except ValueError:
                await update.message.reply_text("Invalid limit number!")
                return
        
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
        
        try:
            chat = await context.bot.get_chat(f"@{channel_username}")
            chat_id = chat.id
            
            # Check admin permissions
            bot_member = await chat.get_member(context.bot.id)
            if not bot_member.status in ['administrator', 'creator']:
                await update.message.reply_text("❌ Bot must be an admin!")
                return
            
            if not bot_member.can_delete_messages and bot_member.status != 'creator':
                await update.message.reply_text("❌ Bot needs delete permissions!")
                return
            
            await update.message.reply_text(f"🚀 Cleaning @{channel_username}...")
            
            deleted_count = 0
            message_id = 1
            max_messages = limit if limit else float('inf')
            
            while deleted_count < max_messages:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
                    
                    if deleted_count % 20 == 0:
                        await update.message.reply_text(f"✅ Progress: {deleted_count} messages deleted")
                    
                    await asyncio.sleep(0.2)  # Increased delay for safety
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "message to delete not found" in error_msg:
                        break
                    elif "too many requests" in error_msg:
                        await update.message.reply_text("⏳ Rate limited, waiting 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        # Skip to next message for other errors
                        logger.warning(f"Skipping message {message_id}: {e}")
                
                message_id += 1
            
            await update.message.reply_text(f"🎉 Completed! Deleted {deleted_count} messages")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Main function to run the bot"""
    # Replace with your bot token
    BOT_TOKEN = "8309666031:AAGuAHKvoLY5Q43VOUPvqIbHxEBsUlc0_Ls"
    
    # Create and run bot
    bot = ChannelCleanerBot(BOT_TOKEN)
    
    print("Bot is running...")
    bot.run()

if __name__ == '__main__':
    main()
