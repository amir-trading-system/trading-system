import csv
import tqdm
import yfinance

FLOAT_THRESHOLD = 20000000

def get_stocks_by_volume():
    t = tqdm.tqdm()
    with open("stocks.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        with open("stocks_by_volume.csv", "w") as csv_write_file:
            writer = csv.DictWriter(
                csv_write_file,
                fieldnames=["Symbol", "Float", "Date", "Volume"],
            )
            writer.writeheader()
            for row in reader:
                symbol = row["Symbol"]
                market_cap = int(float(row["Market Cap"]))
                price = float(row["Price"])

                if market_cap > 0 and price > 1:
                    stock_float = int(market_cap/price)
                    if stock_float > FLOAT_THRESHOLD:
                        continue

                    ticker = yfinance.Ticker(symbol)
                    if not ticker.info.get("floatShares", None):
                        float_shares = 0
                    else:
                        float_shares = ticker.info.get("floatShares", None)

                    historical_data = yfinance.download(
                        symbol,
                        period="1mo",
                        interval="1d",
                        auto_adjust=False,
                        progress=False,
                    )
                    filtered_data_by_volume = historical_data.Volume[symbol][historical_data.Volume[symbol] > 10000000]
                    if not filtered_data_by_volume.empty:
                        for date, volume in filtered_data_by_volume.items():
                            t.update(1)
                            writer.writerow(
                                {
                                    "Symbol": symbol,
                                    "Float": float_shares,
                                    "Date": date.date(),
                                    "Volume": volume,
                                }
                            )

def get_stocks_by_price_change():
    t = tqdm.tqdm()
    with open("stocks.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        with open("stocks_by_price_change.csv", "w") as csv_write_file:
            writer = csv.DictWriter(
                csv_write_file,
                fieldnames=["Symbol", "Date", "Open To High Ratio"],
            )
            writer.writeheader()
            for row in reader:
                open_to_high = {}
                symbol = row["Symbol"]
                market_cap = int(float(row["Market Cap"]))
                price = float(row["Price"])

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
                    )
                    filtered_data_by_price = historical_data.Open[symbol][historical_data.Open[symbol] > 1]

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
                            if ratio < 0.8:
                                continue
                            t.update(1)
                            writer.writerow(
                                {
                                    "Symbol": symbol,
                                    "Date": date.date(),
                                    "Open To High Ratio": ratio,
                                }
                            )

if __name__ == "__main__":
    get_stocks_by_price_change()
