import yaml
import os
import datetime

def _has_numbers(
        string: str,
    ) -> bool:
    return any(
        a.isdigit()
        for a
        in string
    )

def load_summary_file(
        summary_file_path: str,
    ) -> any:
    with open(summary_file_path, "r") as f:
        summary_str = f.read()

    summary_yaml = yaml.safe_load(summary_str)
    return summary_yaml

def load_summaries(
        dir_summaries: str,
    ):
    summaries_files = os.listdir(
        path=dir_summaries,
    )
    current_month = datetime.datetime.now().month

    relevant_files = [
        file_path
        for file_path
        in summaries_files
        if _has_numbers(
            string=file_path,
        )
        and f" {current_month}-" in file_path
    ]
    summaries = [load_summary_file(f"{dir_summaries}/{f}") for f in relevant_files]

    return summaries

def get_monthly_profit(
        summaries: list[any],
    ) -> int:
    current_month = datetime.datetime.now().month

    total_profit = 0
    for summary in summaries:
        if "+" in summary["Profit"]:
            profit = summary["Profit"].replace("+", "").replace("$", "")
            total_profit += int(profit)
        else:
            profit = summary["Profit"].replace("-", "").replace("$", "")
            total_profit -= int(profit)

    return total_profit

if __name__ == '__main__':
    summaries = load_summaries("./Day trade summaries")
    monthly_profit = get_monthly_profit(summaries=summaries)
    print(monthly_profit)
