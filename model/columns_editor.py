import pandas as pd

for file_name in [
    'model/positive_results.csv',
    'model/false_positive_results.csv',
]:
    df = pd.read_csv(file_name)
    df = df.drop(
        columns=[
            "feature_last_10_bars_volume_positive_vs_negative_pct"
        ]
    )
    df.to_csv(file_name, index=False)
