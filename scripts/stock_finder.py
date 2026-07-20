import csv
from typing import Generator, Any

import tqdm
import yfinance
import requests

FLOAT_THRESHOLD = 20000000

def get_stocks_list_from_nasdaq() -> Generator[Any, Any, Any]:
    nasdaq_stocks_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=false&limit=10000&download=true"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "he,en-US;q=0.9,en;q=0.8",
        "origin": "https://www.nasdaq.com",
        "priority": "u=1, i",
        "referer": "https://www.nasdaq.com/",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
    }

    stocks_list_response = requests.get(nasdaq_stocks_url, headers=headers, timeout=200)
    stocks_data = stocks_list_response.json()

    list_to_return: list[dict[str,any]] = []
    t = tqdm.tqdm(stocks_data['data']['rows'])
    for symbol in stocks_data['data']['rows']:
        list_to_return.append(
            {
                'symbol': symbol['symbol'],
                'market_cap': symbol['marketCap'],
                'price': symbol['lastsale']
            },
        )
        t.update(1)
        if len(list_to_return) == 1000:
            yield list_to_return
            list_to_return = []

    if list_to_return:
        yield list_to_return

def get_dynamic_symbols_data_from_period(
    period: str = "1mo",
) -> dict[str, list[str]]:
    symbol_to_date: dict[str,list[str]] = {}
    stock_bulks = get_stocks_list_from_nasdaq()
    for stock_bulk in stock_bulks:
        symbols_to_download: list[str] = []
        for stock in stock_bulk:
            is_valid_symbol = True
            for char in stock["symbol"]:
                if not char.isalpha():
                    is_valid_symbol = False
                    break

            if not is_valid_symbol:
                continue

            symbol = stock["symbol"].rstrip()
            price = float(stock["price"].replace('$', ''))

            if price > 1:
                symbols_to_download.append(symbol)

        historical_data = yfinance.download(
            symbols_to_download,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            prepost=True,
            threads=False,
            timeout=30,
        )

        positive_data = historical_data[historical_data["Close"] > historical_data["Open"]] # type: ignore
        positive_data = historical_data
        for symbol in symbols_to_download:
            low_to_high = {}
            filtered_data_by_price = positive_data.Low[symbol][
                (positive_data.Low[symbol] > 1) & (positive_data.Volume[symbol] > 10000000)
            ]

            for date, stock_low_price in filtered_data_by_price.items():
                if not low_to_high.get(symbol, None):
                    low_to_high[symbol] = {
                        date: {
                            "low": stock_low_price,
                        },
                    }
                else:
                    if not low_to_high[symbol].get(date, None):
                        low_to_high[symbol][date] = {
                            "low": stock_low_price
                        }
                    else:
                        low_to_high[symbol][date]["low"] = stock_low_price

            filtered_data_by_price = positive_data.High[symbol][positive_data.High[symbol] > 1]
            for date, stock_high_price in filtered_data_by_price.items():
                if not low_to_high.get(symbol, None):
                    low_to_high[symbol] = {
                        date: {
                            "high": stock_high_price,
                        },
                    }
                else:
                    if not low_to_high[symbol].get(date, None):
                        low_to_high[symbol][date] = {
                            "high": stock_high_price
                        }
                    else:
                        low_to_high[symbol][date]["high"] = stock_high_price

            for symbol, dates in low_to_high.items():
                for date, price in dates.items():
                    if not price.get("low", None):
                        continue
                    ratio = (price["high"] - price["low"])/price["low"]
                    if ratio < 0.5 or price["high"] < price["low"]:
                        continue

                    if symbol_to_date.get(symbol) is not None:
                        symbol_to_date[symbol].append(date.strftime("%m.%d.%yT%H:%M:%S"))
                    else:
                        symbol_to_date[symbol] = [
                            date.strftime("%m.%d.%yT%H:%M:%S"),
                        ]

    return symbol_to_date
