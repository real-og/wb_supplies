from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from states import State
import keyboards as kb
import texts
from loader import dp, bot
import config_io
import config_io
from aiogram import types
import wb_api


@dp.callback_query_handler(state=State.settings)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'menu':
        autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
        max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
        days_to_plan = config_io.get_value('DAYS_TO_PLAN')
        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()

    elif callback.data == 'max_goods':
        await callback.message.answer("Введите максимальное число товаров в поставке")
        await State.max_goods.set()

    elif callback.data == 'days_to_plan':
        await callback.message.answer("Введите на сколько дней вперед планируется поставка")
        await State.max_days.set()
    
    elif callback.data == 'mode':
        await callback.message.answer("Выберите режим работы автостока", reply_markup=kb.autostock_mode)
        await State.autostock_mode.set()

    elif callback.data == 'autostock_excluded':
        await callback.message.answer("Введите артикул товара, который добавить/удалить из отслеживания сервисом автостока. Если артикула не было в списке - он добавится. Если артикул был в списке - он удалится")
        excluded = config_io.get_value('AUTOSTOCK_EXCLUDE')
        await callback.message.answer(texts.generate_excluded_text(excluded), reply_markup=kb.back_to_menu)
        await State.autostock_excluded.set()
    
    elif callback.data == 'choose_warehouses':
        warehouses_wb = wb_api.get_fbw_warehouses(config_io.get_value('WB_TOKEN')).json()
        choosed_warehouses = config_io.get_value('CHOOSED_WAREHOUSES')

        warehouses_parts = []

        for i in range(0, len(warehouses_wb), 50):
            warehouses_parts.append(warehouses_wb[i:i + 50])

        for part in warehouses_parts:
            await callback.message.answer(texts.choose_warehouse, reply_markup=kb.warehouses_kb(part, choosed_warehouses))

        await callback.message.answer('Когда завершите, возвращайтесь в меню', reply_markup=kb.back_to_menu)
        await State.choosing_warehouses.set()
        
    await bot.answer_callback_query(callback.id)




@dp.message_handler(state=State.max_goods)
async def send_welcome(message: types.Message):
    if message.text.isdecimal():
        config_io.update_key('MAX_FBW_GOODS_AMOUNT', int(message.text))
        await message.answer("Значение установлено")
        await message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()
    else:
        await message.answer("Введите число")

@dp.message_handler(state=State.max_days)
async def send_welcome(message: types.Message):
    if message.text.isdecimal():
        config_io.update_key('DAYS_TO_PLAN', int(message.text))
        await message.answer("Значение установлено")
        await message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()
    else:
        await message.answer("Введите число")


@dp.callback_query_handler(state=State.autostock_mode)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'on':
        config_io.update_key('AUTOSTOCK_MODE', 'ON')
        await callback.message.answer("Значение установлено")
        await callback.message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()
    elif callback.data == 'off':
        config_io.update_key('AUTOSTOCK_MODE', 'OFF')
        await callback.message.answer("Значение установлено")
        await callback.message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()
    elif callback.data == 'notif':
        config_io.update_key('AUTOSTOCK_MODE', 'NOTIFICATION')
        await callback.message.answer("Значение установлено")
        await callback.message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(state=State.autostock_excluded)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'menu':
        autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
        max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
        days_to_plan = config_io.get_value('DAYS_TO_PLAN')
        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()
    await bot.answer_callback_query(callback.id)


@dp.message_handler(state=State.autostock_excluded)
async def send_welcome(message: types.Message):
    excluded = config_io.get_value('AUTOSTOCK_EXCLUDE')
    if message.text in excluded:
        excluded.remove(message.text)
        config_io.update_key('AUTOSTOCK_EXCLUDE', excluded)
        await message.answer('Удалено', reply_markup=kb.back_to_menu)
    else:
        excluded.append(message.text)
        config_io.update_key('AUTOSTOCK_EXCLUDE', excluded)
        await message.answer('Добавлено', reply_markup=kb.back_to_menu)


@dp.callback_query_handler(state=State.choosing_warehouses)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    choosed_warehouses = config_io.get_value('CHOOSED_WAREHOUSES')
    if callback.data == 'menu':
        autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
        max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
        days_to_plan = config_io.get_value('DAYS_TO_PLAN')
        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()
    else:
        choosed_warehouses = config_io.get_value('CHOOSED_WAREHOUSES')
        warehouse_id = callback.data
        if warehouse_id in choosed_warehouses:
            choosed_warehouses.remove(warehouse_id)
        else:
            choosed_warehouses.append(str(warehouse_id))
        config_io.update_key('CHOOSED_WAREHOUSES', choosed_warehouses)
        new_markup = kb.update_warehouses_keyboard(
            callback.message.reply_markup,
            choosed_warehouses
        ) 
        await callback.message.edit_reply_markup(reply_markup=new_markup)

    await bot.answer_callback_query(callback.id)





    