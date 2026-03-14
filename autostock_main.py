import wb_api
import wb_api_helper
import config_io
import utils
import time
import texts
import bot_outer_interface
import db_worker


WB_TOKEN = config_io.get_value('WB_TOKEN')

DAYS_TO_COLLECT_STAT = 14

MODE_OFF_TIMEOUT = 15
CIRCLE_TIMEOUT = 200

LAST_NOTIFICATIONS_REDIS_KEY = "AUTOSTOCK_LAST_NOTIFICATIONS"
BLACKLIST_REDIS_KEY = "AUTOSTOCK_BLACKLIST"


def is_less_hour_last_notification_redis(vendor):
    notifs = db_worker.get_json(LAST_NOTIFICATIONS_REDIS_KEY)
    if notifs is None:
        db_worker.set_json(LAST_NOTIFICATIONS_REDIS_KEY, {})
        return False
    last_notif = notifs.get(vendor, 11)
    hour_ago = time.time() - 3600
    if last_notif >= hour_ago:
        return True
    else:
        return False

def renew_last_notification_redis(vendor):
    notifs = db_worker.get_json(LAST_NOTIFICATIONS_REDIS_KEY)
    notifs[vendor] = time.time()
    db_worker.set_json(LAST_NOTIFICATIONS_REDIS_KEY, notifs)


def check_redis_blacklist(vendor):
    blacklist = db_worker.get_json(BLACKLIST_REDIS_KEY)
    if blacklist:
        for item in blacklist.get('data', []):
            if item == vendor:
                return True
    return False

def add_redis_blacklist(vendor):
    blacklist = db_worker.get_json(BLACKLIST_REDIS_KEY)
    if blacklist:
        for item in blacklist.get('data', []):
            if item == vendor:
                return
        blacklist['data'].append(vendor)
    else:
        blacklist = {'data': [vendor]}
    db_worker.set_json(BLACKLIST_REDIS_KEY)

def remove_redis_blacklist(vendor):
    blacklist = db_worker.get_json(BLACKLIST_REDIS_KEY)
    if blacklist:
        if blacklist['data'].count(vendor) > 0:
            blacklist['data'].remove(vendor)
        


if __name__ == "__main__":
    while True:

        mode = config_io.get_value('AUTOSTOCK_MODE')
        if mode == "OFF":
            time.sleep(MODE_OFF_TIMEOUT)
            continue

        FBW_MIN = config_io.get_value('FBW_MINIMUM_AUTOSTOCK')
        time.sleep(2)
        wb_fbw_stocks = wb_api.get_stocks_report_by_products(
                    WB_TOKEN,
                    utils.get_date_n_days_ago(DAYS_TO_COLLECT_STAT),
                    utils.get_today_date()
                )
        wb_fbs_stocks = wb_api_helper.get_fbs_stocks(WB_TOKEN)
        time.sleep(2)
        my_cards = wb_api.get_my_cards(WB_TOKEN)

        for card in my_cards.json()['cards']:
            nm_id = card['nmID']
            chrt_id = card['sizes'][0]['chrtID']
            vendor = card['vendorCode']
             
            if check_redis_blacklist(vendor):
                continue

            fbs_item_to_find = None
            for fbs_item in wb_fbs_stocks.json()['stocks']:
                if str(fbs_item['chrtId']) == str(chrt_id):
                    fbs_item_to_find = fbs_item
            if fbs_item_to_find:
                fbs_amount = int(fbs_item_to_find['amount'])
            else:
                fbs_amount = 0
            
            fbw_item_to_find = None
            for fbw_item in wb_fbw_stocks.json()['data']['items']:
                if str(fbw_item['nmID']) == str(nm_id):
                    fbw_item_to_find = fbw_item
            if fbw_item_to_find:
                fbw_amount = fbw_item_to_find['metrics']['stockCount']
            else:
                fbw_amount = 0

            if mode == "NOTIFICATION":
                if (int(fbw_amount) <= 3) and (int(fbs_amount) <= 3) and (not is_less_hour_last_notification_redis(vendor)):
                    text = texts.autostock_add_fbs(vendor, fbs_amount, fbw_amount) 
                elif (int(fbw_amount) > 3) and (int(fbs_amount) > 0) and (not is_less_hour_last_notification_redis(vendor)):
                    text = texts.autostock_reset_fbs(vendor, fbs_amount, fbw_amount)
                else:
                    continue
                renew_last_notification_redis(vendor)
                bot_outer_interface.send_text_message(text)

                
            elif mode =="ON":
                if (int(fbw_amount) <= 3) and (int(fbs_amount) <= 3):
                    text = texts.autostock_added_fbs(vendor, fbs_amount, fbw_amount) 
                elif (int(fbw_amount) > 3) and (int(fbs_amount) > 0):
                    text = texts.autostock_reseted_fbs(vendor, fbs_amount, fbw_amount)
                else:
                    continue
                bot_outer_interface.send_text_message(text)
        time.sleep(CIRCLE_TIMEOUT)






        