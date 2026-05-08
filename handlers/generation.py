from aiogram import types
from aiogram.dispatcher import FSMContext
from states import State
import keyboards as kb
import texts
from loader import dp, bot
import config_io
import utils
import planning_supply
import db_worker
import wb_api_helper
import wb_supply_excel_export
import wb_supply_barcode_export
from aiogram import types
from aiogram.types import InputFile
import wb_export_bar_extended
import wb_export_report_extended
import coof_calc
from datetime import date
import wb_api



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

    name_export_extended = utils.get_export_filename_ex() 
    name_report_extended = utils.get_report_filename_ex() 
    coof = coof_calc.calculate_sales_ratio_from_json_by_calendar_days('report_coof.json', int(days_to_plan), date.today().strftime("%Y-%m-%d"))['ratio_future_to_past']
    bar_tonmid = wb_api_helper.nm_id_to_barcode(WB_TOKEN)
    wb_supply_excel_export.export_supply_plan_to_excel(result, name_report, days_to_plan, max_goods_amount)
    wb_supply_barcode_export.export_supply_barcodes_to_excel(result, name_export, barcode_by_nmid=bar_tonmid)

    wb_export_report_extended.export_supply_plan_to_excel(result, name_report_extended, days_to_plan, max_goods_amount, coof)
    wb_export_bar_extended.export_supply_barcodes_to_excel(result, name_export_extended, barcode_by_nmid=bar_tonmid, coefficient=coof)
    file_report = InputFile(name_report)
    await message.answer_document(file_report, caption=texts.report_caption)
    file_export = InputFile(name_export)
    await message.answer_document(file_export, caption=texts.export_caption)
    await message.answer('---------')
    file_report = InputFile(name_report_extended)
    await message.answer_document(file_report, caption='Отчет с учетом статистики')
    file_export = InputFile(name_export_extended)
    await message.answer_document(file_export, caption='Для вб с учетом статистики')

    await message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
    await State.menu.set()
    utils.delete_file_by_name(name_export, folder='')
    utils.delete_file_by_name(name_report, folder='')
    utils.delete_file_by_name(name_export_extended, folder='')
    utils.delete_file_by_name(name_report_extended, folder='')


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

        name_export_extended = utils.get_export_filename_ex() 
        name_report_extended = utils.get_report_filename_ex() 
        
        coof = coof_calc.calculate_sales_ratio_from_json_by_calendar_days('report_coof.json', int(days_to_plan), date.today().strftime("%Y-%m-%d"))['ratio_future_to_past']

        bar_tonmid = wb_api_helper.nm_id_to_barcode(WB_TOKEN)

        wb_supply_excel_export.export_supply_plan_to_excel(result, name_report, days_to_plan, max_goods_amount)
        wb_supply_barcode_export.export_supply_barcodes_to_excel(result, name_export, barcode_by_nmid=bar_tonmid)

        wb_export_report_extended.export_supply_plan_to_excel(result, name_report_extended, days_to_plan, max_goods_amount, coof)
        wb_export_bar_extended.export_supply_barcodes_to_excel(result, name_export_extended, barcode_by_nmid=bar_tonmid, coefficient=coof)

        file_report = InputFile(name_report)
        await callback.message.answer_document(file_report, caption=texts.report_caption)
        file_export = InputFile(name_export)
        await callback.message.answer_document(file_export, caption=texts.export_caption)

        await callback.message.answer('---------')

        file_report = InputFile(name_report_extended)
        await callback.message.answer_document(file_report, caption='Отчет с учетом статистики')
        file_export = InputFile(name_export_extended)
        await callback.message.answer_document(file_export, caption='Для вб с учетом статистики')

        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()
        utils.delete_file_by_name(name_export, folder='')
        utils.delete_file_by_name(name_report, folder='')
        utils.delete_file_by_name(name_export_extended, folder='')
        utils.delete_file_by_name(name_report_extended, folder='')
    elif callback.data == 'settings':
        await callback.message.answer(texts.settings, reply_markup=kb.settings)
        await State.settings.set()

    elif callback.data == 'generate_warehouse':
        warehouses_wb = wb_api.get_fbw_warehouses(config_io.get_value('WB_TOKEN')).json()
        choosed_warehouses = config_io.get_value('CHOOSED_WAREHOUSES')

        warehouses_to_draw = []
        for wh in warehouses_wb:
            if str(wh['ID']) in choosed_warehouses:
                warehouses_to_draw.append(wh)
        
        await callback.message.answer(texts.choose_warehouse_to_get_report, reply_markup=kb.warehouses_with_menu_kb(warehouses_to_draw, []))
        await State.warehouse_to_report.set()

    await bot.answer_callback_query(callback.id)
    