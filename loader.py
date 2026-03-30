from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
import logging
import config_io


logging.basicConfig(level=logging.WARNING,
                    #  filename='bot_log.txt'
                     )

BOT_TOKEN = config_io.get_value('BOT_TOKEN')
ACCOUNT_NAME = config_io.get_value('ACCOUNT_NAME')

if ACCOUNT_NAME == 'OOO':
    storage = RedisStorage2(db=1)
elif ACCOUNT_NAME == 'IP':
    storage = RedisStorage2(db=4)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)