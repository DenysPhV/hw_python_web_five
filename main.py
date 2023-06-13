import argparse
import asyncio
import logging
import platform
from datetime import date

import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol, WebSocketProtocolError
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description="exchange currency")

LIMIT_DAYS = 10
PB_CURRENCY = ['AUD', 'AZN', 'BYN', 'CAD', 'CHF', 'CNY', 'CZK', 'DKK', 'EUR', 'GBP', 'GEL', 'HUF', 'ILS', 'JPY',
               'KZT', 'MDL', 'NOK', 'PLN', 'SEK', 'SGD', 'TMT', 'TRY', 'UAH', 'USD', 'UZS', 'XAU']

parser.add_argument('-d', '--days', required=True)
parser.add_argument('-c', '--curr', default="EUR,USD")


def check_args(necessary_days: int, currency: list) -> list:
    if necessary_days > LIMIT_DAYS:
        necessary_days = LIMIT_DAYS

    for pies in currency:
        if not pies in PB_CURRENCY:
            currency.remove(pies)

    if not len(currency):
        currency.append('USD')

    return [necessary_days, currency]


def valid_param(args) -> list:
    return check_args(int(args.get('days')), args.get('curr').split(','))


def prepare_url(days: int) -> list:
    result = []
    base_url = 'https://api.privatbank.ua/p24api/exchange_rates?date='

    for i in range(date.toordinal(date.today()), date.toordinal(date.today())-days, -1):
        result.append(base_url+date.fromordinal(i-1).strftime('%d.%m.%Y'))
    return result


def format_result(curr_list: list, raw: dict) -> dict:
    result = dict()
    result[raw.get('date')] = dict()
    f_date = result[raw.get('date')]
    for c in curr_list:
        list_rate = raw.get("exchangeRate")
        for i in list_rate:
            if c == i.get("currency"):
                f_sale = i.get("saleRate")
                f_purchase = i.get("purchaseRate")
                f_date[c] = {"sale": f_sale, "purchase": f_purchase}
                break
    return result


async def request(args: list) -> list:
    result = []
    async with aiohttp.ClientSession() as session:
        for url in prepare_url(args[0]):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        result.append(format_result(args[1], res_json))

                    logging.error(f"Error status {response.status} for {url}")

            except aiohttp.ClientConnectionError as err:
                logging.error(f"Connection error {url}: {err}")

        return result


def get_curr_rate_list(params):
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(request(params))


if __name__ == '__main__':
    params = valid_param(vars(parser.parse_args()))
    result = get_curr_rate_list(params)
    print(result)

