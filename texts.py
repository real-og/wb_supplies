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


