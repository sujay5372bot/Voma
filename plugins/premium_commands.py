# plugins/premium_commands.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, PLANS
from utils.helpers import is_premium, get_role
import razorpay

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def setup_premium_commands(bot: Client):
    @bot.on_message(filters.private & filters.command("subscribe"))
    async def subscribe(_, m: Message):
        user_id = m.from_user.id
        if len(m.command) < 2 or m.command[1] not in PLANS:
            await m.reply(f"Usage: /subscribe {', '.join(PLANS.keys())}")
            return
        plan = m.command[1]
        plan_data = PLANS[plan]
        data = {
            "amount": plan_data['price'] * 100,
            "currency": "INR",
            "description": f"{plan} Premium Plan",
            "notes": {
                "user_id": str(user_id),
                "plan": plan,
                "days": str(plan_data['days'])
            }
        }
        payment_link = razorpay_client.payment_link.create(data)
        await m.reply(f"Pay here: {payment_link['short_url']}")

    @bot.on_message(filters.private & filters.command("premium_status"))
    async def premium_status(_, m: Message):
        user_id = m.from_user.id
        if is_premium(user_id):
            user = users.find_one({'user_id': user_id})
            await m.reply(f"Premium: {user['premium_plan']}, Expires: {user['premium_expiry']}")
        else:
            await m.reply("No active premium.")
