import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden
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

        @self.client.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await message.reply_text(
                "🤖 **Channel Cleaner Bot**\n\n"
                "**Commands:**\n"
                "`/clean <chat_id>` – Delete ALL messages\n"
                "`/clean <chat_id> <limit>` – Delete last N messages\n\n"
                "Example:\n"
                "`/clean -1001234567890`\n"
                "`/clean -1001234567890 300`\n"
            )

        @self.client.on_message(filters.command("clean"))
        async def clean_command(client, message: Message):

            if len(message.command) < 2:
                await message.reply_text(
                    "Usage:\n"
                    "`/clean <chat_id>`\n"
                    "`/clean <chat_id> <limit>`"
                )
                return

            try:
                chat_id = int(message.command[1])
            except:
                await message.reply_text("❌ Invalid chat ID!")
                return

            limit = None
            if len(message.command) > 2:
                try:
                    limit = int(message.command[2])
                except:
                    await message.reply_text("❌ Invalid limit!")
                    return

            await self.clean_channel(client, message, chat_id, limit)

    async def clean_channel(self, client, message: Message, chat_id: int, limit: int):

        try:
            chat = await client.get_chat(chat_id)
        except Exception as e:
            await message.reply_text(
                f"❌ Cannot access chat `{chat_id}`.\n"
                "Make sure:\n"
                "1. Chat exists\n"
                "2. Bot is admin\n"
                "3. Bot has delete rights"
            )
            return

        # check permission
        try:
            member = await chat.get_member(client.me.id)
            if not member.privileges or not member.privileges.can_delete_messages:
                await message.reply_text("❌ Bot does not have permission to delete messages!")
                return
        except:
            await message.reply_text("❌ Cannot check permissions.")
            return

        await message.reply_text(
            f"🧹 **Cleaning chat:** `{chat_id}`\n"
            f"Limit: {limit if limit else 'ALL messages'}"
        )

        deleted = 0
        failed = 0
        start = time.time()

        async for msg in client.get_chat_history(chat_id, limit=limit):
            try:
                await msg.delete()
                deleted += 1

                if deleted % 50 == 0:
                    await message.reply_text(f"✔ Deleted {deleted} messages...")

                await asyncio.sleep(0.15)

            except FloodWait as e:
                await message.reply_text(f"⏳ FloodWait {e.value} sec")
                await asyncio.sleep(e.value)
            except MessageDeleteForbidden:
                failed += 1
            except Exception:
                failed += 1

        duration = time.time() - start

        await message.reply_text(
            f"🎉 **Cleanup Done!**\n\n"
            f"🧹 Deleted: `{deleted}`\n"
            f"⚠ Failed: `{failed}`\n"
            f"⏳ Duration: `{duration:.2f} sec`"
        )

    async def run(self):
        await self.client.start()
        print("Bot is running...")
        await asyncio.Event().wait()  # Keep bot running


async def main():
    API_ID = 21370037
    API_HASH = "0b57036f40bb6da488d05b43e2d20dc1"
    BOT_TOKEN = "8309666031:AAGuAHKvoLY5Q43VOUPvqIbHxEBsUlc0_Ls"

    bot = PyrogramChannelCleaner(API_ID, API_HASH, BOT_TOKEN)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
