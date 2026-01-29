import csv
import datetime

import yfinance
import requests

FLOAT_THRESHOLD = 20000000

def get_stocks_list_from_nasdaq():
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

    return [
        {
            'Symbol': stock['symbol'],
            'Market Cap': stock['marketCap'],
            'Price': stock['lastsale']
        }
        for stock in stocks_data['data']['rows']
    ][:1000]

#pylint:disable=unspecified-encoding,too-many-locals
def get_stocks_by_price_change_and_volume() -> list[str]:
    relevant_stocks: list[str] = []
    all_stocks = get_stocks_list_from_nasdaq()
    for stock in all_stocks:
        if stock["Market Cap"] == '':
            continue
        is_valid_symbol = True
        for char in stock["Symbol"]:
            if not char.isalpha():
                is_valid_symbol = False
                break

        if not is_valid_symbol:
            continue

        low_to_high = {}
        symbol = stock["Symbol"].rstrip()
        market_cap = int(float(stock["Market Cap"]))
        price = float(stock["Price"].replace('$', ''))

        if market_cap > 0 and market_cap < 100000000 and price > 1:
            stock_float = int(market_cap/price)
            if stock_float > FLOAT_THRESHOLD:
                continue

            historical_data = yfinance.download(
                symbol,
                period="5d",
                interval="1d",
                auto_adjust=False,
                progress=False,
                prepost=False,
                threads=40,
                timeout=5,
            )
            filtered_data_by_price = historical_data.Low[symbol][
                (historical_data.Low[symbol] > 1)
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

            filtered_data_by_price = historical_data.High[symbol][historical_data.High[symbol] > 1]
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
                    if ratio < 0.8 or price["high"] < price["low"]:
                        continue

                    relevant_stocks.append(symbol)

    return relevant_stocks

def extract_symbols_names_from_csv():
    symbols_names = []
    with open("/Users/ayaffe/Downloads/full_year_trades_sumamry.csv", "r") as csv_file:
        reader = csv.DictReader(
            csv_file,
        )
        for row in reader:
            if "." not in row["Symbol"]:
                edited_datetime = datetime.datetime.strptime(row["DateTime"], "%Y%m%d;%H%M%S")
                if edited_datetime.hour < 9:
                    continue
                final_line = f"{row["Symbol"]}: {edited_datetime}"
                if final_line not in symbols_names:
                    symbols_names.append(f"{row["Symbol"]}: {edited_datetime}")

    with open("full_year_traded_symbols.txt", "w") as f:
        for symbol in symbols_names:
            f.write(f"{symbol}\n")


# if __name__ == "__main__":
#     get_stocks_by_price_change_and_volume()
