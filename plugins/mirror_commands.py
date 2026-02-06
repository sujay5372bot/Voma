# plugins/mirror_commands.py
from pyrogram import Client, filters
from pyrogram.types import Message
from database import sources, mirror_settings
from utils.helpers import is_premium, require_premium, get_role

def setup_mirror_commands(bot: Client):
    @bot.on_message(filters.private & filters.command("mirror_on"))
    async def mirror_on(_, m: Message):
        if not await require_premium(m):
            return
        mirror_settings.update_one({'user_id': m.from_user.id}, {'$set': {'auto_mirror': True}}, upsert=True)
        await m.reply("Auto mirror enabled.")

    @bot.on_message(filters.private & filters.command("mirror_off"))
    async def mirror_off(_, m: Message):
        if not await require_premium(m):
            return
        mirror_settings.update_one({'user_id': m.from_user.id}, {'$set': {'auto_mirror': False}}, upsert=True)
        await m.reply("Auto mirror disabled.")

    @bot.on_message(filters.private & filters.command("mode"))
    async def set_mode(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 2 or m.command[1] not in ['smart', 'force']:
            await m.reply("Usage: /mode smart or /mode force")
            return
        mode = m.command[1]
        mirror_settings.update_one({'user_id': m.from_user.id}, {'$set': {'mirror_mode': mode}}, upsert=True)
        await m.reply(f"Mirror mode set to {mode}.")

    @bot.on_message(filters.private & filters.command("add_mirror"))
    async def add_mirror(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /add_mirror SOURCE_ID TARGET_ID")
            return
        try:
            source_id = int(m.command[1])
            target_id = int(m.command[2])
            user_id = m.from_user.id
            sources.update_one(
                {'user_id': user_id, 'source_id': source_id},
                {'$addToSet': {'targets': target_id}},
                upsert=True
            )
            await m.reply(f"Added mirror pair: {source_id} -> {target_id}. Add me to both channels (as member for source, admin for target).")
        except ValueError:
            await m.reply("Invalid IDs.")

    @bot.on_message(filters.private & filters.command("remove_mirror"))
    async def remove_mirror(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 2:
            await m.reply("Usage: /remove_mirror SOURCE_ID")
            return
        try:
            source_id = int(m.command[1])
            user_id = m.from_user.id
            sources.delete_one({'user_id': user_id, 'source_id': source_id})
            await m.reply(f"Removed source {source_id}.")
        except ValueError:
            await m.reply("Invalid ID.")

    @bot.on_message(filters.private & filters.command("mirror_list"))
    async def mirror_list(_, m: Message):
        if not await require_premium(m):
            return
        user_id = m.from_user.id
        user_sources = sources.find({'user_id': user_id})
        response = "Your mirror pairs:\n"
        for src in user_sources:
            response += f"Source: {src['source_id']}, Filters: {', '.join(src.get('filters', []))}, Targets: {', '.join(map(str, src.get('targets', [])))}\n"
        await m.reply(response or "No mirrors set.")

    @bot.on_message(filters.private & filters.command("set_source_filter"))
    async def set_source_filter(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /set_source_filter SOURCE_ID video image text pdf (space-separated)")
            return
        try:
            source_id = int(m.command[1])
            filters_list = m.command[2:]
            valid_filters = {'video', 'image', 'text', 'pdf'}
            filters_list = [f for f in filters_list if f in valid_filters]
            user_id = m.from_user.id
            sources.update_one(
                {'user_id': user_id, 'source_id': source_id},
                {'$set': {'filters': filters_list}},
                upsert=True
            )
            await m.reply(f"Filters set for {source_id}: {', '.join(filters_list)}")
        except ValueError:
            await m.reply("Invalid ID.")

    @bot.on_message(filters.private & filters.command("source_status"))
    async def source_status(_, m: Message):
        await mirror_list(_, m)  # Reuse list for status

    @bot.on_message(filters.private & filters.command("set_watermark"))
    async def set_watermark(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 2:
            await m.reply("Usage: /set_watermark TEXT")
            return
        text = ' '.join(m.command[1:])
        mirror_settings.update_one({'user_id': m.from_user.id}, {'$set': {'watermark': text}}, upsert=True)
        await m.reply("Watermark set.")

    @bot.on_message(filters.private & filters.command("set_delay"))
    async def set_delay(_, m: Message):
        if not await require_premium(m):
            return
        if len(m.command) < 2:
            await m.reply("Usage: /set_delay SECONDS")
            return
        try:
            seconds = int(m.command[1])
            if seconds < 0:
                raise ValueError
            mirror_settings.update_one({'user_id': m.from_user.id}, {'$set': {'delay': seconds}}, upsert=True)
            await m.reply(f"Delay set to {seconds} seconds.")
        except ValueError:
            await m.reply("Invalid seconds.")
