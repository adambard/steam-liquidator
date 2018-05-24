import re
import logging
import pickle
import json
import requests

from .crypto import make_key, encrypt

URL_GET_RSA_KEY = 'https://store.steampowered.com/login/getrsakey/'
URL_LOGIN = 'https://store.steampowered.com/login/dologin/'
URL_STORE_TRANSFER = 'https://steamcommunity.com/login/transfer'
URL_CHECK_ELIGIBILITY = 'https://steamcommunity.com/market/eligibilitycheck/'
URL_INVENTORY_PAGE = 'https://steamcommunity.com/profiles/{steam_id}/inventory/'
URL_INVENTORY = 'https://steamcommunity.com/inventory/{steam_id}/{app_id}/{context_id}'
URL_PRICE_OVERVIEW = 'https://steamcommunity.com/market/priceoverview'
URL_UPDATE_SESSION_COOKIES = 'https://steamcommunity.com/actions/GetNotificationCounts'
URL_SELL_ITEM = 'https://steamcommunity.com/market/sellitem/'


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def get_rsa_key(jar, username):

    resp = requests.post(URL_GET_RSA_KEY, params={'username': username}, cookies=jar)
    assert resp.status_code == 200, "Invalid response code: {}".format(resp.status_code)
    data = resp.json()

    mod = int(data['publickey_mod'], 16)
    exp = int(data['publickey_exp'], 16)

    return {
        'key': make_key(mod, exp),
        'timestamp': data['timestamp']
    }


def login(jar, username, password):
    rsa = get_rsa_key(jar, username)

    params = {
        'captcha_text': '',
        'captchagid': -1,
        'emailauth': '',
        'emailsteamid': '',
        'loginfriendlyname': '',
        'captcha_text': '',
        'remember_login': False,
        'username': username,
        'rsatimestamp': rsa['timestamp'],
        'password': encrypt(rsa['key'], password)
    }

    resp = requests.post(URL_LOGIN, data=params, cookies=jar)
    assert resp.status_code == 200, "Login failed."

    data = resp.json()
    jar.update(resp.cookies)

    if data['success'] and 'transfer_parameters' in data:
        return data['transfer_parameters']

    elif data.get('emailauth_needed'):
        code = input("Enter the code you received in your email: ")
        params['emailauth'] = code
        params['emailsteamid'] = data['emailsteamid']

        resp = requests.post(URL_LOGIN, data=params, cookies=jar)
        assert resp.status_code == 200, "Login failed."

        data = resp.json()
        assert data['success'], "Login failed."

        jar.update(resp.cookies)
        return data['transfer_parameters']

    else:
        logger.info("Login failed.")
        logger.info(data)
        assert False, "Could not log in. Sorry."


def transfer_login(jar, auth_ctx):
    resp = requests.post(URL_STORE_TRANSFER, auth_ctx, cookies=jar)
    jar.update(resp.cookies)
    return jar


def check_eligibility(jar):
    resp = requests.get(URL_CHECK_ELIGIBILITY, cookies=jar, allow_redirects=False)
    jar.update(resp.cookies)

    return resp.status_code == 302

def update_session_cookie(jar):
    resp = requests.get(URL_UPDATE_SESSION_COOKIES, cookies=jar)
    jar.update(resp.cookies)
    return jar

def extract_inventories(jar, auth_ctx):
    resp = requests.get(URL_INVENTORY_PAGE.format(steam_id=auth_ctx['steamid']), cookies=jar)
    result = re.search(r"g_rgAppContextData = (.*);", resp.text)

    data = json.loads(result.group(1))
    return [(appid, contextid)
           for appid, v in data.items()
           for contextid in v.get('rgContexts', {}) ]


def list_inventory(jar, auth_ctx, appid, contextid):
    url = URL_INVENTORY.format(
        steam_id=auth_ctx['steamid'],
        app_id=appid,
        context_id=contextid
    )
    resp = requests.get(url, cookies=jar)
    assert resp.status_code == 200

    jar.update(resp.cookies)
    jar['strInventoryLastContext'] = '753_6'

    data = resp.json()
    items = zip(data['assets'], data['descriptions'])
    return [dict(item, **asset) for (asset, item) in items
            if item.get('marketable')]


def get_price(jar, auth_ctx, item_info):
    params = {
        'appid': item_info['appid'],
        'country': jar['steamCountry'].split('|')[0],
        'currency': item_info['currency'],
        'market_hash_name': item_info['market_hash_name']
    }

    resp = requests.get(URL_PRICE_OVERVIEW, params, cookies=jar)
    try:
        return int(float(resp.json()['lowest_price'][1:]) * 100)
    except:
        logger.warn("No price found for item %s", params['market_hash_name'])


def sell_item(jar, auth_ctx, item_info, price_cents):
    params = dict(
        amount=1,
        appid=item_info['appid'],
        assetid=item_info['assetid'],
        contextid=item_info['contextid'],
        sessionid=jar['sessionid'],
        price=price_cents
    )

    headers = {
        'Referer': URL_INVENTORY_PAGE.format(steam_id=auth_ctx['steamid']),
        'DNT': '1',
        #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0'
    }


    resp = requests.post(URL_SELL_ITEM, params, cookies=jar, headers=headers)

    assert resp.status_code == 200

    return resp.json()


def load_cached_obj(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def save_cached_obj(filename, jar):
    with open(filename, 'wb') as f:
        return pickle.dump(jar, f)


def liquidate(username, password):
    jar = requests.cookies.RequestsCookieJar()
    auth_ctx = login(jar, username, password)

    # init session
    resp = requests.get('https://steamcommunity.com/', cookies=jar)
    jar.update(resp.cookies)

    market_jar = transfer_login(jar, auth_ctx)
    check_eligibility(market_jar)

    market_jar['timezoneOffset'] = '-25200,0'


    inventories = extract_inventories(market_jar, auth_ctx)
    for appid, contextid in inventories:
        items = list_inventory(market_jar, auth_ctx, appid, contextid)

        logger.info("Processing %s items for appid=%s, contextid=%s", len(items), appid, contextid)

        for item in items:
            price = get_price(market_jar, auth_ctx, item) 
            if price:
                logger.info("Selling item %s for %s cents", item['market_hash_name'], price)
                sell_item(market_jar, auth_ctx, item, price)
