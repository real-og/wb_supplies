import wb_api

def get_my_chrt_ids(auth):
    my_cards_response = wb_api.get_my_cards(auth)
    chrt_ids = {}
    for card in my_cards_response.json().get('cards'):
        sku = card['vendorCode']
        chrt_ids[sku] = card.get('sizes')[0].get('chrtID')

    return chrt_ids

def get_fbs_stocks(auth):
    fbs_warehouses = wb_api.get_my_fbs_warehouses(auth)
    warehouse_id = fbs_warehouses.json()[0]['id']
    chrt_ids = get_my_chrt_ids(auth)
    chrt_ids_list = []
    for key in chrt_ids:
        chrt_ids_list.append(chrt_ids[key])
    fbs_stocks = wb_api.get_my_fbs_stocks(auth, warehouse_id, chrt_ids_list)
    return fbs_stocks


from datetime import datetime, timedelta, timezone


def parse_wb_date(date_str):
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception:
        return None


def is_not_older_than_30_days(supply):
    supply_date = parse_wb_date(supply.get('supplyDate'))
    create_date = parse_wb_date(supply.get('createDate'))

    dt = supply_date or create_date
    if dt is None:
        return False

    now = datetime.now(timezone.utc)
    return dt >= now - timedelta(days=30)


def get_fbw_in_transit_by_warehouse_and_vendor_code(auth):
    result = {}

    # Только реальные не принятые поставки, без черновиков
    status_ids = [2, 3, 4, 6]

    supplies_response = wb_api.get_fbw_supplies(auth=auth, status_ids=status_ids, limit=20)
    supplies_response.raise_for_status()
    supplies = supplies_response.json()

    for supply in supplies:
        supply_id = supply.get('supplyID')

        if supply_id is None:
            continue

        if not is_not_older_than_30_days(supply):
            continue

        details_response = wb_api.get_fbw_supply_details(auth=auth, supply_id=supply_id)
        details_response.raise_for_status()
        details = details_response.json()

        warehouse_name = (
            details.get('warehouseName')
            or details.get('actualWarehouseName')
            or f"warehouse_{details.get('warehouseID') or details.get('actualWarehouseID') or 'unknown'}"
        )

        if warehouse_name not in result:
            result[warehouse_name] = {}

        goods_response = wb_api.get_fbw_supply_goods(auth=auth, supply_id=supply_id)
        goods_response.raise_for_status()
        goods = goods_response.json()

        for good in goods:
            vendor_code = good.get('vendorCode')
            if not vendor_code:
                continue

            quantity = int(good.get('quantity') or 0)
            accepted_quantity = int(good.get('acceptedQuantity') or 0)
            not_accepted = max(quantity - accepted_quantity, 0)

            if not_accepted <= 0:
                continue

            result[warehouse_name][vendor_code] = (
                result[warehouse_name].get(vendor_code, 0) + not_accepted
            )

    return result

def nm_id_to_barcode(auth):
    response = wb_api.get_my_cards(auth)
    result = {}
    for card in response.json()['cards']:
        nmId = card['nmID']
        barcode = card['sizes'][0]['skus'][0]
        result[nmId] = barcode
    return result