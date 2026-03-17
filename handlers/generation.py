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
import config_io
import planning_supply
import db_worker
import wb_api_helper
import wb_supply_excel_export
import wb_supply_barcode_export
from aiogram import types
from aiogram.types import InputFile


@dp.message_handler(lambda message: str(message.from_user.id) in config_io.get_value('ADMINS'), commands=['generate'], state="*")
async def send_welcome(message: types.Message):
    await message.answer(texts.generation_in_process)
    WB_TOKEN = config_io.get_value('WB_TOKEN')
    autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
    max_goods_amount = int(config_io.get_value('MAX_FBW_GOODS_AMOUNT'))
    days_to_plan = int(config_io.get_value('DAYS_TO_PLAN'))
    goods_data = db_worker.get_all_nmid_data()
    in_transit_by_warehouse_vendor=wb_api_helper.get_fbw_in_transit_by_warehouse_and_vendor_code(WB_TOKEN)
    result = planning_supply.plan_supply_from_wb_items(goods_data, max_goods_amount, days_to_plan, in_transit_by_warehouse_vendor=in_transit_by_warehouse_vendor)
    name_export = utils.get_export_filename()
    name_report = utils.get_report_filename()
    wb_supply_excel_export.export_supply_plan_to_excel(result, name_report, days_to_plan, max_goods_amount)
    wb_supply_barcode_export.export_supply_barcodes_to_excel(result, name_export, barcode_by_nmid=wb_api_helper.nm_id_to_barcode(WB_TOKEN))
    file_report = InputFile(name_report)
    await message.answer_document(file_report, caption=texts.report_caption)
    file_export = InputFile(name_export)
    await message.answer_document(file_export, caption=texts.export_caption)
    await message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
    await State.menu.set()
    utils.delete_file_by_name(name_export, folder='')
    utils.delete_file_by_name(name_report, folder='')


@dp.callback_query_handler(state=State.menu)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'generate':
        await callback.message.answer(texts.generation_in_process)
        WB_TOKEN = config_io.get_value('WB_TOKEN')
        autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
        max_goods_amount = int(config_io.get_value('MAX_FBW_GOODS_AMOUNT'))
        days_to_plan = int(config_io.get_value('DAYS_TO_PLAN'))
        goods_data = db_worker.get_all_nmid_data()
        in_transit_by_warehouse_vendor=wb_api_helper.get_fbw_in_transit_by_warehouse_and_vendor_code(WB_TOKEN)
        result = planning_supply.plan_supply_from_wb_items(goods_data, max_goods_amount, days_to_plan, in_transit_by_warehouse_vendor=in_transit_by_warehouse_vendor)
        name_export = utils.get_export_filename()
        name_report = utils.get_report_filename()
        wb_supply_excel_export.export_supply_plan_to_excel(result, name_report, days_to_plan, max_goods_amount)
        wb_supply_barcode_export.export_supply_barcodes_to_excel(result, name_export, barcode_by_nmid=wb_api_helper.nm_id_to_barcode(WB_TOKEN))
        file_report = InputFile(name_report)
        await callback.message.answer_document(file_report, caption=texts.report_caption)
        file_export = InputFile(name_export)
        await callback.message.answer_document(file_export, caption=texts.export_caption)
        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()
        utils.delete_file_by_name(name_export, folder='')
        utils.delete_file_by_name(name_report, folder='')
    elif callback.data == 'settings':
        await callback.message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()

    await bot.answer_callback_query(callback.id)
    