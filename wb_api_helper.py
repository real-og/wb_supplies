import wb_api

def get_my_chrt_ids(auth):
    my_cards_response = wb_api.get_my_cards(auth)
    chrt_ids = {}
    for card in my_cards_response.json().get('cards'):
        sku = card['vendorCode']
        chrt_ids[sku] = card.get('sizes')[0].get('chrtID')

    return chrt_ids