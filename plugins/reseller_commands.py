# plugins/reseller_commands.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, PLANS
from utils.helpers import require_reseller
import razorpay

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def setup_reseller_commands(bot: Client):
    @bot.on_message(filters.private & filters.command("generate_link"))
    async def generate_link(_, m: Message):
        if not await require_reseller(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /generate_link PLAN USER_ID")
            return
        plan = m.command[1]
        if plan not in PLANS:
            await m.reply(f"Invalid plan. Available: {', '.join(PLANS.keys())}")
            return
        try:
            target_user_id = int(m.command[2])
        except ValueError:
            await m.reply("Invalid user ID.")
            return
        reseller_id = m.from_user.id
        plan_data = PLANS[plan]
        data = {
            "amount": plan_data['price'] * 100,
            "currency": "INR",
            "description": f"{plan} Premium Plan via Reseller",
            "notes": {
                "user_id": str(target_user_id),
                "plan": plan,
                "days": str(plan_data['days']),
                "reseller_id": str(reseller_id)
            }
        }
        payment_link = razorpay_client.payment_link.create(data)
        await m.reply(f"Unique payment link for user {target_user_id}: {payment_link['short_url']}. Share this with them.")
