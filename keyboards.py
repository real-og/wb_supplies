from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import buttons


menu = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text=buttons.generate, callback_data='generate')
button_2 = InlineKeyboardButton(text=buttons.generate_warehouse, callback_data='generate_warehouse')
button_3 = InlineKeyboardButton(text=buttons.settings, callback_data='settings')
menu.add(button_1)
menu.add(button_2)
menu.add(button_3)

settings = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text=buttons.max_goods, callback_data='max_goods')
button_2 = InlineKeyboardButton(text=buttons.days_to_plan, callback_data='days_to_plan')
button_3 = InlineKeyboardButton(text=buttons.mode, callback_data='mode')
button_4 = InlineKeyboardButton(text=buttons.autostock_excluded, callback_data='autostock_excluded')
button_5 = InlineKeyboardButton(text=buttons.choose_warehouse, callback_data='choose_warehouses')
button_6 = InlineKeyboardButton(text=buttons.menu, callback_data='menu')
settings.add(button_1)
settings.add(button_2)
settings.add(button_3)
settings.add(button_4)
settings.add(button_5)
settings.add(button_6)

autostock_mode = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text='Уведомления', callback_data='notif')
button_2 = InlineKeyboardButton(text="Автоматически", callback_data='on')
button_3 = InlineKeyboardButton(text="Выключен", callback_data='off')
autostock_mode.add(button_1)
autostock_mode.add(button_2)
autostock_mode.add(button_3)

back_to_menu = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text='В меню', callback_data='menu')
back_to_menu.add(button_1)


def warehouses_kb(warehouses, choosed):
    kb = InlineKeyboardMarkup()
    for wh in warehouses:
        name = wh['name']
        if str(wh['ID']) in choosed:
            name = '✅ ' + name
        kb.add(InlineKeyboardButton(text=name, callback_data=wh['ID']))
    return kb

def warehouses_with_menu_kb(warehouses, choosed):
    kb = InlineKeyboardMarkup()
    for wh in warehouses:
        name = wh['name']
        if str(wh['ID']) in choosed:
            name = '✅ ' + name
        kb.add(InlineKeyboardButton(text=name, callback_data=wh['ID']))
    kb.add(InlineKeyboardButton(text=buttons.menu, callback_data='menu'))
    return kb


back_to_menu = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text=buttons.menu, callback_data='menu')
back_to_menu.add(button_1)

def update_warehouses_keyboard(old_markup, choosed_warehouses):
    new_kb = InlineKeyboardMarkup(row_width=1)

    choosed_ids = set(str(x) for x in choosed_warehouses)

    for row in old_markup.inline_keyboard:
        new_row = []

        for button in row:
            warehouse_id = button.callback_data

            # menu не трогаем
            if warehouse_id == "menu":
                new_row.append(button)
                continue

            text = button.text.replace("✅ ", "")

            if str(warehouse_id) in choosed_ids:
                text = f"✅ {text}"

            new_row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=button.callback_data
                )
            )

        new_kb.row(*new_row)

    return new_kb


