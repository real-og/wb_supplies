from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from states import State
import keyboards as kb
import wb_api
import texts
import datetime
from loader import dp, bot
import config_io
import utils
import sys


@dp.message_handler(lambda message: str(message.from_user.id) in config_io.get_value('ADMINS'), commands=['start'], state="*")
async def send_welcome(message: types.Message):
    await message.answer(message.text)
    print(message)