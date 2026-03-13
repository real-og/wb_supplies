from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
import logging
import config_io


logging.basicConfig(level=logging.WARNING)

BOT_TOKEN = config_io.get_value('BOT_TOKEN')

storage = RedisStorage2(db=1)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)