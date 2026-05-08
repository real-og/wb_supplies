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
import json
import excel_warehouse



@dp.callback_query_handler(state=State.warehouse_to_report)
async def send_series(callback: types.CallbackQuery, state: FSMContext):
    autostock_mode = config_io.get_value('AUTOSTOCK_MODE')
    max_goods_amount = config_io.get_value('MAX_FBW_GOODS_AMOUNT')
    days_to_plan = config_io.get_value('DAYS_TO_PLAN')
    if callback.data == 'menu':
        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()
    else:
        warehouse_id = callback.data
        await callback.message.answer(texts.generation_in_process)
        WB_TOKEN = config_io.get_value('WB_TOKEN')
        goods_data = db_worker.get_all_nmid_data()
        in_transit_by_warehouse_vendor=wb_api_helper.get_fbw_in_transit_by_warehouse_and_vendor_code(WB_TOKEN)
        
        result_warehouse = planning_supply.calc_supply_for_warehouse(goods_data, int(warehouse_id), days_to_plan, in_transit_by_warehouse_vendor, 14, False, False)

        # print(result_warehouse)
        # with open('test.json', 'w') as f:
        #     f.write(json.dumps(result_warehouse))


        name_export = utils.get_export_filename_warehouse()
        name_report = utils.get_report_filename_warehouse()

        bar_tonmid = wb_api_helper.nm_id_to_barcode(WB_TOKEN)

        excel_warehouse.export_supply_plan_to_excel_warehouse(result_warehouse, name_report, days_to_plan)
        excel_warehouse.export_supply_barcodes_to_excel_warehouse(result_warehouse, name_export, barcode_by_nmid=bar_tonmid)


        file_report = InputFile(name_report)
        await callback.message.answer_document(file_report, caption=texts.report_caption)
        file_export = InputFile(name_export)
        await callback.message.answer_document(file_export, caption=texts.export_caption)

        await callback.message.answer(texts.generate_menu_text(autostock_mode, max_goods_amount, days_to_plan), reply_markup=kb.menu)
        await State.menu.set()

        utils.delete_file_by_name(name_export, folder='')
        utils.delete_file_by_name(name_report, folder='')

