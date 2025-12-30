import asyncio
from telegram import Bot

TELEGRAM_BOT_TOKEN = '8571936110:AAERqN-YhP_SZyj8_STi5nSwhqguwrUhcZc'
CHAT_ID = "-5177099672"

#Define bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)

async def run_bot(messages, chat_id):
    text = '\n'.join(messages)
    await send_message(text, chat_id)

#Test messages
messages = [
    'whats up my friend!'
]

if messages:
    asyncio.run(run_bot(messages, CHAT_ID))
