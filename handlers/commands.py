from aiogram import types
from states import State
import keyboards as kb
import texts
from loader import dp
import config_io
import config_io
from aiogram import types
from aiogram.types import InputFile


@dp.message_handler(lambda message: str(message.from_user.id) in config_io.get_value('ADMINS'), commands=['start'], state="*")
async def send_welcome(message: types.Message):
    autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
    max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
    days_to_plan = config_io.get_value('DAYS_TO_PLAN')
    await message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
    await State.menu.set()


@dp.message_handler(lambda message: str(message.from_user.id) in config_io.get_value('ADMINS'), commands=['menu'], state="*")
async def send_welcome(message: types.Message):
    autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
    max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
    days_to_plan = config_io.get_value('DAYS_TO_PLAN')
    await message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)


@dp.message_handler(lambda message: str(message.from_user.id) in config_io.get_value('ADMINS'), commands=['logs'], state="*")
async def send_welcome(message: types.Message):
    file = InputFile('bot_log.txt')
    await message.answer_document(file)
    file = InputFile('db_worker_log.txt')
    await message.answer_document(file)
    file = InputFile('autostock_log.txt')
    await message.answer_document(file)
