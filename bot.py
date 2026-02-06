# bot.py
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatWriteForbidden, ChannelInvalid
from config import API_ID, API_HASH, BOT_TOKEN, USER_SESSION_STRING, PLANS, ADMIN_IDS
from database import db, users, mirror_settings, sources, transactions, withdrawals
from utils.helpers import is_premium, get_role, send_notification
from utils.filters import match_media_filter
from plugins.mirror_commands import setup_mirror_commands
from plugins.premium_commands import setup_premium_commands
from plugins.reseller_commands import setup_reseller_commands
from plugins.withdrawal_commands import setup_withdrawal_commands

user_client = Client(
    "mirror_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USER_SESSION_STRING
)

bot = Client(
    "mirror_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Mirror handler
@user_client.on_message(filters.channel)
async def mirror_handler(client: Client, message: Message):
    source_id = message.chat.id
    source_docs = sources.find({'source_id': source_id})
    for source_doc in source_docs:
        user_id = source_doc['user_id']
        if not is_premium(user_id):
            continue
        settings = mirror_settings.find_one({'user_id': user_id})
        if not settings or not settings['auto_mirror']:
            continue
        if not match_media_filter(message, source_doc['filters']):
            continue
        mode = settings['mirror_mode']
        watermark = settings.get('watermark', '')
        delay = settings.get('delay', 5)
        targets = source_doc['targets']
        for target_id in targets:
            try:
                caption_or_text = (message.caption or message.text or '') + ('\n' + watermark if watermark else '')
                if mode == 'force' or message.chat.has_protected_content:
                    # Reupload mode
                    if message.photo:
                        file = await message.download(in_memory=True)
                        await client.send_photo(target_id, file, caption=caption_or_text)
                    elif message.video:
                        file = await message.download(in_memory=True)
                        await client.send_video(target_id, file, caption=caption_or_text)
                    elif message.document and message.document.mime_type == 'application/pdf':
                        file = await message.download(in_memory=True)
                        await client.send_document(target_id, file, caption=caption_or_text)
                    elif message.text:
                        await client.send_message(target_id, caption_or_text)
                else:
                    # Smart mode: forward
                    await client.copy_message(target_id, source_id, message.id)
                await asyncio.sleep(delay)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except (ChatWriteForbidden, ChannelInvalid):
                # Log error, notify user
                await send_notification(bot, user_id, f"Failed to post to {target_id}. Ensure I'm admin there.")
            except Exception as e:
                # Log error
                print(f"Mirror error: {e}")

async def is_user_active(user_id: int) -> bool:
    if not is_premium(user_id):
        return False
    settings = mirror_settings.find_one({'user_id': user_id})
    return settings and settings['auto_mirror']

async def main():
    await user_client.start()
    user_me = await user_client.get_me()
    print(f"Userbot started as @{user_me.username}")
    await bot.start()
    bot_me = await bot.get_me()
    print(f"Bot started as @{bot_me.username}")

    # Join all active sources (if public)
    active_sources = set()
    for source in sources.find():
        if await is_user_active(source['user_id']):
            active_sources.add(source['source_id'])
    for s_id in active_sources:
        try:
            await user_client.join_chat(s_id)
        except Exception:
            pass  # Private or already joined

    # Setup command handlers on bot
    setup_mirror_commands(bot)
    setup_premium_commands(bot)
    setup_reseller_commands(bot)
    setup_withdrawal_commands(bot)

    await asyncio.sleep(1)  # Ensure handlers are registered
    await user_client.idle()  # Use idle to keep running

if __name__ == "__main__":
    asyncio.run(main())
