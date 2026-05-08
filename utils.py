from datetime import datetime, timedelta
import config_io

def get_today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def get_date_n_days_ago(days: int) -> str:
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%d")

def get_report_filename():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_report_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}.xlsx'

def get_export_filename():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_WBexport_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}.xlsx'

def get_report_filename_warehouse():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_WAREHOUSE_report_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}.xlsx'

def get_export_filename_warehouse():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_WB_WAREHOUSE_export_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}.xlsx'

def get_report_filename_ex():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_report_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}_extended.xlsx'

def get_export_filename_ex():
    NAME = config_io.get_value('ACCOUNT_NAME')
    return f'{NAME}_WBexport_{datetime.now().strftime("%Y.%m.%d__%Hh%Mmin")}_extended.xlsx'

from pathlib import Path

def delete_file_by_name(filename: str, folder: str = "content") -> bool:
    path = Path(folder) / filename

    if not path.exists() or not path.is_file():
        return False

    path.unlink()
    return True

