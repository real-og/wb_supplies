import requests
import copy
import json
import time
import requests

# Получаю до 100 карточек на аккаунте
def get_my_cards(auth):
    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    headers = {'Authorization': auth}
    base_body = {
    "settings": {
        "sort": {
            "ascending": True
            },
        "cursor": {
            "limit": 100
            },
        "filter": {
            "withPhoto": -1
            }
        }
    }

    body = copy.deepcopy(base_body)
    all_cards = []
    first_response = None
    last_response_json = None
    limit = body["settings"]["cursor"]["limit"]

    while True:
        response = requests.post(url, headers=headers, json=body)

        # если какая-то страница вернула ошибку — возвращаем как есть
        if not response.ok:
            return response

        response_json = response.json()

        if first_response is None:
            first_response = response

        cards = response_json.get("cards", [])
        all_cards.extend(cards)
        last_response_json = response_json

        cursor = response_json.get("cursor", {}) or {}
        page_total = cursor.get("total", len(cards))

        # по документации: если total < limit, значит это последняя страница
        if page_total < limit:
            break

        updated_at = cursor.get("updatedAt")
        nm_id = cursor.get("nmID")

        # если курсора нет, дальше пагинировать нельзя
        if not updated_at or nm_id is None:
            break

        body["settings"]["cursor"] = {
            "limit": limit,
            "updatedAt": updated_at,
            "nmID": nm_id
        }

        time.sleep(0.65)

    # оставляем тот же формат response, но подменяем body на объединенный JSON
    merged_json = dict(last_response_json or {})
    merged_json["cards"] = all_cards

    first_response._content = json.dumps(
        merged_json,
        ensure_ascii=False
    ).encode("utf-8")
    first_response.encoding = "utf-8"

    return first_response
    


def get_my_fbs_warehouses(auth):
    # 300 per 1 min
    url = 'https://marketplace-api.wildberries.ru/api/v3/warehouses'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response


def get_my_fbs_stocks(auth, warehouse_id, chrt_ids):
    # 300 per 1 min
    url = f'https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}'
    headers = {'Authorization': auth}
    body = {'chrtIds':chrt_ids}
    response = requests.post(url, headers=headers, json=body)
    return response


# получить остатки по всем складам (для автостока особенно)
def get_stocks_report_by_products(auth, period_start, period_end):
    # 3 per 1 min
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/products/products'
    headers = {'Authorization': auth}
    body = {
        "currentPeriod": {
            "start": period_start,
            "end": period_end
        },
        "stockType": "wb",
        "skipDeletedNm": True,
        "orderBy": {
            "field": "avgOrders",
            "mode": "asc"
        },
        "availabilityFilters": [
            "deficient",
            "balanced",
            'actual',
            'nonActual',
            'nonLiquid',
            'invalidData',
        ],
        "limit": 1000,
        "offset": 0
    }
    response = requests.post(url, headers=headers, json=body)
    print(response.text)
    return response


#получить инфу как в кабинете в аналитеке по складам по одному товару раз в 20 сек
def get_stocks_report_by_sizes(auth, nm_id, period_start, period_end):
    # 3 per 1 min
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/products/sizes'
    headers = {'Authorization': auth}
    body = {
        "nmID": nm_id,
        "currentPeriod": {
            "start": period_start,
            "end": period_end
        },
        "stockType": "wb",
        "orderBy": {
            "field": "avgOrders",
            "mode": "asc"
        },
        "includeOffice": True
    }
    response = requests.post(url, headers=headers, json=body)
    return response




# получить текущие остатки товаров на складах вб в моменте отчетом
def create_stat_report_wb_offices(auth):
    # 1 per 1 min
    url = 'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains'
    headers = {'Authorization': auth}
    params = {'groupBySa': True}
    response = requests.get(url, headers=headers, params=params)
    return response

def check_status_stat_report_wb_offices(auth, task_id):
    # 12 per 1 min
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/status'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response

def get_stat_report_wb_offices(auth, task_id):
    # 1 per 1 min
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/download'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response


def get_fbw_supplies(auth, status_ids=None, limit=1000, offset=0):
    # 30 per 1 min
    url = 'https://supplies-api.wildberries.ru/api/v1/supplies'
    headers = {'Authorization': auth}
    params = {
        'limit': limit,
        'offset': offset
    }
    body = {}

    if status_ids is not None:
        body['statusIDs'] = status_ids

    response = requests.post(url, headers=headers, params=params, json=body)
    return response


# Получить товары одной FBW-поставки
def get_fbw_supply_goods(auth, supply_id, is_preorder=False, limit=1000, offset=0):
    # 30 per 1 min
    url = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_id}/goods'
    headers = {'Authorization': auth}
    params = {
        'limit': limit,
        'offset': offset
    }

    if is_preorder:
        params['isPreorderID'] = 'true'

    response = requests.get(url, headers=headers, params=params)
    return response

def get_fbw_supply_details(auth, supply_id):
    # 30 per 1 min
    url = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_id}'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response


def add_product_to_fbs_warehouse(auth, warehouse_id, chrt_id, amount):
    # 300 per 1 min
    url = f'https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}'
    headers = {'Authorization': auth}
    body = {
        'stocks': [
            {
                'chrtId': chrt_id,
                'amount': amount
            }
        ]
    }
    response = requests.put(url, headers=headers, json=body)
    return response


# удалить товар со склада FBS
def delete_product_from_fbs_warehouse(auth, warehouse_id, chrt_id):
    # 10 per 1 min
    url = f'https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}'
    headers = {'Authorization': auth}
    body = {
        'chrtIds': [chrt_id]
    }
    response = requests.delete(url, headers=headers, json=body)
    return response


def get_fbw_warehouses(auth):
    # 6 per 1 min
    url = f'https://supplies-api.wildberries.ru/api/v1/warehouses'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response
