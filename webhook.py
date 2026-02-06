# webhook.py
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from config import WEBHOOK_SECRET, PLANS
from database import db, users, transactions
from bot import bot  # Import bot to send notifications (run webhook separately)
from utils.helpers import send_notification

app = FastAPI()

@app.post("/razorpay_webhook")
async def razorpay_webhook(request: Request):
    signature = request.headers.get('x-razorpay-signature')
    body = await request.body()
    digest = hmac.new(WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if signature != digest:
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body)
    event = payload.get('event')

    if event == 'payment_link.paid':
        payment_link = payload['payload']['payment_link']['entity']
        notes = payment_link['notes']
        user_id = int(notes['user_id'])
        plan = notes['plan']
        days = int(notes['days'])
        reseller_id = int(notes['reseller_id']) if 'reseller_id' in notes else None

        # Activate premium
        expiry = datetime.utcnow() + timedelta(days=days)
        users.update_one(
            {'user_id': user_id},
            {'$set': {'premium_plan': plan, 'premium_expiry': expiry}},
            upsert=True
        )

        # Credit commission if reseller
        if reseller_id:
            amount = payload['payload']['payment']['entity']['amount'] / 100
            reseller = users.find_one({'user_id': reseller_id})
            if reseller:
                comm_percent = reseller.get('commission_percent', 30)
                commission = (comm_percent / 100) * amount
                users.update_one({'user_id': reseller_id}, {'$inc': {'wallet_balance': commission}})

        # Log transaction
        transactions.insert_one({
            'transaction_id': payload['payload']['payment']['entity']['id'],
            'user_id': user_id,
            'amount': payload['payload']['payment']['entity']['amount'] / 100,
            'plan': plan,
            'days': days,
            'reseller_id': reseller_id,
            'date': datetime.utcnow()
        })

        # Notify user
        await send_notification(bot, user_id, f"Your {plan} premium has been activated for {days} days!")

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
