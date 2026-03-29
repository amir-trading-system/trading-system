import pandas as pd

for file_name in [
    'model/positive_results.csv',
    'model/false_positive_results.csv',
]:
    df = pd.read_csv(file_name)
    df["feature_entry_bar_close_strong"] = (df["entry_bar_close"] - df["entry_bar_open"])/(df["entry_bar_high"] - df["entry_bar_low"]) >= 0.8
    df.to_csv(file_name, index=False)
