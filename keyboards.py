from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
import buttons


menu = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text=buttons.generate, callback_data='generate')
button_2 = InlineKeyboardButton(text=buttons.settings, callback_data='settings')
menu.add(button_1)
menu.add(button_2)

settings = InlineKeyboardMarkup()
button_1 = InlineKeyboardButton(text=buttons.max_goods, callback_data='max_goods')
button_2 = InlineKeyboardButton(text=buttons.days_to_plan, callback_data='days_to_plan')
button_3 = InlineKeyboardButton(text=buttons.mode, callback_data='mode')
button_4 = InlineKeyboardButton(text=buttons.autostock_excluded, callback_data='autostock_excluded')
button_5 = InlineKeyboardButton(text=buttons.menu, callback_data='menu')
settings.add(button_1)
settings.add(button_2)
settings.add(button_3)
settings.add(button_4)
settings.add(button_5)

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

