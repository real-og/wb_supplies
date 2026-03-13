import asyncio
from aiogram import Bot
import config_io


bot = Bot(config_io.get_value('BOT_TOKEN'), parse_mode='HTML')

# sending message form the script not telegram bot instance
async def async_send_message(text, keyboard=None):
    try:
        mes = await bot.send_message(config_io.get_value('GROUP_ID'), text, reply_markup=keyboard)
        s = await bot.get_session()
        await s.close()
        return mes.message_id
    except Exception as e:
        print(e)

def send_text_message(text, keyboard=None):
    message_id = asyncio.run(async_send_message(text, keyboard))
    return message_id


# editing keyboard form the script not telegram bot instance
async def async_edit_kb(message_id, keyboard=None):
    try:
        mes = await bot.edit_message_reply_markup(config_io.get_value('GROUP_ID'), message_id, reply_markup=keyboard)
        s = await bot.get_session()
        await s.close()
        return message_id
    except Exception as e:
        print(e)

def edit_kb(message_id, keyboard):
    asyncio.run(async_edit_kb(message_id, keyboard))
    return message_id