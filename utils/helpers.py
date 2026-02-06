# utils/helpers.py
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
from database import users

async def is_premium(user_id: int) -> bool:
    user = users.find_one({'user_id': user_id})
    if not user or not user.get('premium_plan'):
        return False
    if user['premium_expiry'] < datetime.utcnow():
        users.update_one({'user_id': user_id}, {'$set': {'premium_plan': None, 'premium_expiry': None}})
        return False
    return True

async def require_premium(m: Message) -> bool:
    if not await is_premium(m.from_user.id):
        await m.reply("This command requires premium subscription. Use /subscribe to get one.")
        return False
    return True

def get_role(user_id: int) -> str:
    user = users.find_one({'user_id': user_id})
    return user.get('role', 'user') if user else 'user'

async def require_reseller(m: Message) -> bool:
    if get_role(m.from_user.id) != 'reseller':
        await m.reply("This command is for resellers only.")
        return False
    return True

async def require_admin(m: Message) -> bool:
    if get_role(m.from_user.id) != 'admin':
        await m.reply("This command is for admins only.")
        return False
    return True

async def send_notification(bot: Client, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass  # User blocked bot or error
