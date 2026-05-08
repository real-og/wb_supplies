from aiogram.dispatcher.filters.state import StatesGroup, State


class State(StatesGroup):
    menu = State()
    settings = State()
    max_goods = State()
    max_days = State()
    autostock_mode = State()
    autostock_excluded = State()
    choosing_warehouses = State()
    warehouse_to_report = State()
