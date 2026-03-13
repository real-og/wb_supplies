import wb_api
import wb_api_helper
import config_io
import utils

WB_TOKEN = config_io.get_value('WB_TOKEN')
DAYS_TO_COLLECT_STAT = 14

if __name__ == "__main__":
    while True:
        wb_fbw_stocks = wb_api.get_stocks_report_by_products(
                    WB_TOKEN,
                    utils.get_date_n_days_ago(DAYS_TO_COLLECT_STAT),
                    utils.get_today_date()
                )
        wb_fbs_stocks = wb_api_helper.get_fbs_stocks(WB_TOKEN)
        my_cards = wb_api.get_my_cards(WB_TOKEN)
        for card in my_cards.json()['cards']:
            nm_id = card['nmID']
            chrt_id = card['sizes'][0]['chrtID']
            vendor = card['vendorCode']

            print(f"{nm_id} - {chrt_id} - {vendor}")
            for fbs_item in wb_fbs_stocks.json()['stocks']:
                if str(fbs_item['chrtId']) == str(chrt_id):
                    print(f"fbs amount {fbs_item['amount']}")
            
            for fbw_item in wb_fbw_stocks.json()['data']['items']:
                if str(fbw_item['nmID']) == str(nm_id):
                    print(f"fbw amount {fbw_item['metrics']['stockCount']}")
        break



        