import redis
import json
import time
import wb_api
import config_io
import utils
from datetime import datetime


ACCOUNT_NAME = config_io.get_value('ACCOUNT_NAME')
WB_TOKEN = config_io.get_value('WB_TOKEN')
DAYS_TO_COLLECT_STAT = 14
EXCEPTION_TIMEOUT = 60
CIRCLE_TIMEOUT = 60
STEP_TIMEOUT = 30

import logging

logging.basicConfig(
    filename="db_worker_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

if ACCOUNT_NAME == 'OOO':
    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True, db=1)
elif ACCOUNT_NAME == 'IP':
    redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True, db=4)


nmids_key = ACCOUNT_NAME + ":wb_nmids"
nmid_prefix = ACCOUNT_NAME + ":wb_nmid"

def get_json(key: str):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def set_json(key: str, value: dict | list):
    redis_client.set(key, json.dumps(value, ensure_ascii=False))



def _get_nmid_key(nmid: int) -> str:
    return f"{nmid_prefix}:{int(nmid)}"


def upsert_nmid_data(nmid: int, vendor: str, item: dict) -> None:
    """
    Добавляет или обновляет данные по конкретному nmID.
    """
    timestamp = int(time.time())
    human_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "nmID": int(nmid),
        "vendor": vendor,
        "timestamp": human_time,
        **item
    }

    redis_client.set(_get_nmid_key(nmid), json.dumps(payload, ensure_ascii=False))
    redis_client.sadd(nmids_key, int(nmid))


def get_all_nmid_data() -> list[dict]:
    """
    Возвращает все записи по всем nmID, ничего не меняя.
    """
    nmids = redis_client.smembers(nmids_key)
    if not nmids:
        return []

    keys = [_get_nmid_key(int(nmid)) for nmid in nmids]
    raw_items = redis_client.mget(keys)

    result = []
    for raw in raw_items:
        if not raw:
            continue

        try:
            result.append(json.loads(raw))
        except Exception:
            continue

    result.sort(key=lambda x: x.get("nmID", 0))
    return result


if __name__ == "__main__":
    while True:
        try:
            response = wb_api.get_my_cards(WB_TOKEN)
            cards = response.json().get("cards", [])
        except Exception:
            logging.exception("Ошибка получения карточек")
            time.sleep(EXCEPTION_TIMEOUT)
            continue

        for card in cards:
            try:
                nm_id = card.get("nmID")
                vendor = card.get("vendorCode")
                if not nm_id:
                    continue

                response_for_nm_id = wb_api.get_stocks_report_by_sizes(
                    WB_TOKEN,
                    int(nm_id),
                    utils.get_date_n_days_ago(DAYS_TO_COLLECT_STAT),
                    utils.get_today_date()
                )

                data = response_for_nm_id.json()
                upsert_nmid_data(int(nm_id), vendor, data)

                time.sleep(STEP_TIMEOUT)
            except Exception:
                logging.exception(f"Ошибка обработки nmID={card.get('nmID')}")
                time.sleep(EXCEPTION_TIMEOUT)
        
        time.sleep(CIRCLE_TIMEOUT)