def autostock_add_fbs(vendor, fbs_amount, fbw_amount):
    return f"""⚠️↗️ Нужно <b>добавить</b> на фбс <b>{vendor}</b>

Остаток на фбс: <b>{fbs_amount}</b>
Остаток на фбо: <b>{fbw_amount}</b>"""

def autostock_reset_fbs(vendor, fbs_amount, fbw_amount):
    return f"""⚠️↘️ Нужно <b>обнулить</b> фбс <b>{vendor}</b>

Остаток на фбс: <b>{fbs_amount}</b>
Остаток на фбо: <b>{fbw_amount}</b>"""



def autostock_added_fbs(vendor, fbs_amount, fbw_amount):
    return f"""☑️🤖↗️ <b>Добавлено</b> на фбс <b>{vendor}</b>

Остаток на фбс: <b>{fbs_amount}</b>
Остаток на фбо: <b>{fbw_amount}</b>"""

def autostock_reseted_fbs(vendor, fbs_amount, fbw_amount):
    return f"""☑️🤖↘️ <b>Обнулено</b> автоматически фбс <b>{vendor}</b>

Остаток на фбс: <b>{fbs_amount}</b>
Остаток на фбо: <b>{fbw_amount}</b>"""


def generate_menu_text(autostock_mode, max_goods_amount, days_to_plan):
    return f"""Меню
Планирование на дней вперед: <b>{days_to_plan}</b>
Максимальное количество товаров в поставке: <b>{max_goods_amount}</b>
Режим автостока: <b>{autostock_mode}</b>"""

generation_in_process = 'Планирование займет до минуты'
export_caption = 'Файл для вставки на wb'
report_caption = 'Отчет'

settings = 'Настройки'

def generate_excluded_text(excluded):
    if len(excluded) == 0:
        return 'Сейчас все товары отслеживаются автостоком'
    else:
        return f'Следующие товары не отслеживаются автостоком {excluded}'
    

choose_warehouse = 'Выбирайте склады для отобраения'
choose_warehouse_to_get_report = "Выберите склад на поставку"



