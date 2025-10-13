import csv
import tqdm
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

    stocks_list_response = requests.get(nasdaq_stocks_url, headers=headers)
    stocks_data = stocks_list_response.json()

    return [
        {
            'Symbol': stock['symbol'],
            'Market Cap': stock['marketCap'],
            'Price': stock['lastsale']
        }
        for stock in stocks_data['data']['rows']
    ]

def get_stocks_by_price_change_and_volume():
    all_stocks = get_stocks_list_from_nasdaq()
    t = tqdm.tqdm(all_stocks)
    with open("stocks_by_price_change.csv", "w") as csv_write_file:
        writer = csv.DictWriter(
            csv_write_file,
            fieldnames=["Symbol", "Date", "Open To High Ratio"],
        )
        writer.writeheader()
        for stock in all_stocks:
            t.update(1)
            if stock["Market Cap"] == '':
                continue
            is_valid_symbol = True
            for char in stock["Symbol"]:
                if not char.isalpha():
                    is_valid_symbol = False
                    break

            if not is_valid_symbol:
                continue

            open_to_high = {}
            symbol = stock["Symbol"].rstrip()
            market_cap = int(float(stock["Market Cap"]))
            price = float(stock["Price"].replace('$', ''))

            if market_cap > 0 and price > 1:
                stock_float = int(market_cap/price)
                if stock_float > FLOAT_THRESHOLD:
                    continue

                historical_data = yfinance.download(
                    symbol,
                    period="1mo",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=40,
                )
                filtered_data_by_price = historical_data.Open[symbol][
                    (historical_data.Open[symbol] > 1) &
                    (historical_data.Volume[symbol] > 15000000)
                ]

                for date, stock_open_price in filtered_data_by_price.items():
                    if not open_to_high.get(symbol, None):
                        open_to_high[symbol] = {
                            date: {
                                "open": stock_open_price,
                            },
                        }
                    else:
                        if not open_to_high[symbol].get(date, None):
                            open_to_high[symbol][date] = {
                                "open": stock_open_price
                            }
                        else:
                            open_to_high[symbol][date]["open"] = stock_open_price

                filtered_data_by_price = historical_data.High[symbol][historical_data.High[symbol] > 1]
                for date, stock_high_price in filtered_data_by_price.items():
                    if not open_to_high.get(symbol, None):
                        open_to_high[symbol] = {
                            date: {
                                "high": stock_high_price,
                            },
                        }
                    else:
                        if not open_to_high[symbol].get(date, None):
                            open_to_high[symbol][date] = {
                                "high": stock_high_price
                            }
                        else:
                            open_to_high[symbol][date]["high"] = stock_high_price

                for symbol, dates in open_to_high.items():
                    for date, price in dates.items():
                        if not price.get("open", None):
                            continue
                        ratio = (price["high"] - price["open"])/price["open"]
                        if ratio < 0.4:
                            continue
                        writer.writerow(
                            {
                                "Symbol": symbol,
                                "Date": date.date(),
                                "Open To High Ratio": ratio,
                            }
                        )
                        csv_write_file.flush()

if __name__ == "__main__":
    get_stocks_by_price_change_and_volume()
