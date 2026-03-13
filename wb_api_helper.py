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