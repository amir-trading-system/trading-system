
#pylint:disable=unspecified-encoding
def create_watchlist_for_tomorrow(
    potential_for_tomorrow_file_path,
):
    symbols_for_tomorrow: list[str] = []
    with open(potential_for_tomorrow_file_path, "r") as f:
        potential_for_tomorrow = f.readlines()
        for symbol_to_date in potential_for_tomorrow:
            symbol, _ = symbol_to_date.split("--")
            symbols_for_tomorrow.append(symbol)

    watchlist_symbols: list[str] = ["COLUMN,0\n"]
    for symbol in symbols_for_tomorrow:
        watchlist_symbols.append(f"DES,{symbol},STK,SMART/AMEX,,,,,\n")

    with open("/Users/ayaffe/Jts/watchlist.csv", "w") as f:
        f.writelines(watchlist_symbols)

if __name__ == '__main__':
    create_watchlist_for_tomorrow("./potential_symbols_for_tomorrow.txt")
