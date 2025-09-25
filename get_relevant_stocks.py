import csv
import tqdm
import yfinance

FLOAT_THRESHOLD = 20000000

def get_stocks_by_price_change_and_volume():
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
                        period="3mo",
                        interval="1d",
                        auto_adjust=False,
                        progress=False,
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
                            t.update(1)
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
