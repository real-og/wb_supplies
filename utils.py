from datetime import datetime, timedelta



def get_today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def get_date_n_days_ago(days: int) -> str:
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%d")

