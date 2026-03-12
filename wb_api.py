import requests

# Получаю до 100 карточек на аккаунте
def get_my_cards(auth):
    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    headers = {'Authorization': auth}
    body = {
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
    response = requests.post(url, headers=headers, json=body)
    return response


def get_my_fbs_warehouses(auth):
    url = 'https://marketplace-api.wildberries.ru/api/v3/warehouses'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response


def get_my_fbs_stocks(auth, warehouse_id, chrt_ids):
    url = f'https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}'
    headers = {'Authorization': auth}
    body = {'chrtIds':chrt_ids}
    response = requests.post(url, headers=headers, json=body)
    return response


def get_stocks_report_by_products(auth, period_start, period_end):
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
    return response


#получить инфу как в кабинете в аналитеке по складам по одному товару раз в 20 сек
def get_stocks_report_by_sizes(auth, nm_id, period_start, period_end):
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


# def get_stocks_report_by_offices(auth, period_start, period_end):
#     url = 'https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/offices'
#     headers = {'Authorization': auth}
#     body = {
#         "currentPeriod": {
#             "start": period_start,
#             "end": period_end
#         },
#         "stockType": "wb",
#         "skipDeletedNm": True,
#     }
#     response = requests.post(url, headers=headers, json=body)
#     return response


# def get_stat_wb_offices(auth, period_start):
#     url = 'https://statistics-api.wildberries.ru/api/v1/supplier/stocks'
#     headers = {'Authorization': auth}
#     params = {'dateFrom': period_start}
#     response = requests.get(url, headers=headers, params=params)
#     return response





# получить текущие остатки товаров на складах вб в моменте отчетом
def create_stat_report_wb_offices(auth):
    url = 'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains'
    headers = {'Authorization': auth}
    params = {'groupBySa': True}
    response = requests.get(url, headers=headers, params=params)
    return response

def check_status_stat_report_wb_offices(auth, task_id):
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/status'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response

def get_stat_report_wb_offices(auth, task_id):
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/tasks/{task_id}/download'
    headers = {'Authorization': auth}
    response = requests.get(url, headers=headers)
    return response

