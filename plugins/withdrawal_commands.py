# plugins/withdrawal_commands.py
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
from config import MIN_WITHDRAW, ADMIN_IDS
from database import users, withdrawals
from utils.helpers import require_reseller, require_admin, get_role

def setup_withdrawal_commands(bot: Client):
    @bot.on_message(filters.private & filters.command("withdraw"))
    async def withdraw(_, m: Message):
        if not await require_reseller(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /withdraw AMOUNT UPI_ID")
            return
        try:
            amount = float(m.command[1])
            upi_id = m.command[2]
            user_id = m.from_user.id
            user = users.find_one({'user_id': user_id})
            if amount < MIN_WITHDRAW:
                await m.reply(f"Minimum withdrawal is {MIN_WITHDRAW}.")
                return
            if user['wallet_balance'] < amount:
                await m.reply("Insufficient balance.")
                return
            withdrawals.insert_one({
                'user_id': user_id,
                'amount': amount,
                'upi_id': upi_id,
                'status': 'pending',
                'request_date': datetime.utcnow()
            })
            await m.reply("Withdrawal requested. Await admin approval.")
        except ValueError:
            await m.reply("Invalid amount.")

    @bot.on_message(filters.private & filters.command("withdraw_requests"))
    async def withdraw_requests(_, m: Message):
        if not await require_admin(m):
            return
        pending = withdrawals.find({'status': 'pending'})
        response = "Pending withdrawals:\n"
        for req in pending:
            response += f"User: {req['user_id']}, Amount: {req['amount']}, UPI: {req['upi_id']}, Date: {req['request_date']}\n"
        await m.reply(response or "No pending requests.")

    @bot.on_message(filters.private & filters.command("approve_withdraw"))
    async def approve_withdraw(_, m: Message):
        if not await require_admin(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /approve_withdraw USER_ID AMOUNT")
            return
        try:
            user_id = int(m.command[1])
            amount = float(m.command[2])
            req = withdrawals.find_one({'user_id': user_id, 'amount': amount, 'status': 'pending'})
            if not req:
                await m.reply("No matching pending request.")
                return
            users.update_one({'user_id': user_id}, {'$inc': {'wallet_balance': -amount}})
            withdrawals.update_one({'_id': req['_id']}, {'$set': {'status': 'approved', 'action_date': datetime.utcnow()}})
            await m.reply("Withdrawal approved.")
        except ValueError:
            await m.reply("Invalid inputs.")

    @bot.on_message(filters.private & filters.command("reject_withdraw"))
    async def reject_withdraw(_, m: Message):
        if not await require_admin(m):
            return
        if len(m.command) < 3:
            await m.reply("Usage: /reject_withdraw USER_ID AMOUNT")
            return
        try:
            user_id = int(m.command[1])
            amount = float(m.command[2])
            req = withdrawals.find_one({'user_id': user_id, 'amount': amount, 'status': 'pending'})
            if not req:
                await m.reply("No matching pending request.")
                return
            withdrawals.update_one({'_id': req['_id']}, {'$set': {'status': 'rejected', 'action_date': datetime.utcnow()}})
            await m.reply("Withdrawal rejected.")
        except ValueError:
            await m.reply("Invalid inputs.")
