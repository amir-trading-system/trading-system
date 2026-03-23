import csv
import pandas

import math

#pylint:disable=unspecified-encoding

def passes_rules(row) -> bool:
    return (
        float(row["pullback_structure_score"]) > -0.2 and
        float(row["ema9_minus_ema20_at_entry"]) > 0 and
        float(row["volume_trend_strength"]) > -0.3 and
        float(row["movement_under_vwap_since_market_open"]) < float(row["movement_above_vwap_since_market_open"]) and
        float(row["negative_volume_since_open"]) < float(row["positive_volume_since_open"])
    )

def calculate_score_for_row(row) -> float:
    score = 0

    # --- Pullback quality ---
    score += 1.2 * float(row["pullback_duration"])
    score += 1.0 * float(row["pullback_depth"])
    score += 1.0 * float(row["pullback_structure_score"])

    # --- Volume confirmation ---
    score += 1.1 * float(row["volume_during_pullback"])
    score += 0.8 * float(row["volume_trend"])

    # --- Trend strength ---
    score += 1.2 * float(row["ema9_minus_ema20_at_entry"])
    score += 0.8 * float(row["movement_above_vwap_since_market_open"])

    # --- Entry quality ---
    score += 1.0 * float(row["entry_bar_body_pct"])

    # --- Distance context ---
    score += 0.7 * float(row["distance_from_high_of_day"])

    # --- Penalties (VERY important) ---
    score -= 1.5 * abs(min(0, float(row["pullback_structure_score"])))
    score -= 1.2 * abs(min(0, float(row["ema9_minus_ema20_at_entry"])))
    score -= 1.0 * float(row["negative_volume_since_open"])
    score -= 0.8 * float(row["movement_under_vwap_since_market_open"])

    return score

def probability(score):
    x = score / 5.0

    if x > 60:
        x = 60
    elif x < -60:
        x = -60

    return 1 / (1 + math.exp(-x))

def classify_trade(row):
    if not passes_rules(row):
        return "REJECT", 0.0, 0.0

    score = calculate_score_for_row(row)
    prob = probability(score)

    if prob > 0.7:
        return "STRONG", prob, score
    elif prob > 0.55:
        return "MEDIUM", prob, score
    else:
        return "WEAK", prob, score

def calculate_score():
    positive_data: list[dict[str, any]] = []
    false_positive_data: list[dict[str, any]] = []
    positive_file_path = "positive_results.csv"
    false_positive_file_path = "false_positive_results.csv"

    with open(positive_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row["symbol"] == "AVERAGE":
                continue
            positive_data.append(row)

    with open(false_positive_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row["symbol"] == "AVERAGE":
                continue
            false_positive_data.append(row)

    # positive_scores = []
    for p_d in positive_data:
        rank, prob, score = classify_trade(
            row=p_d,
        )
        # positive_scores.append(score)
        print(f"POSITIVE - symbol: {p_d["symbol"]}. rank: {rank}. score: {score}. prob: {prob}")

    # false_positive_scores = []
    for f_p_d in false_positive_data:
        rank, prob, score = classify_trade(
            row=f_p_d,
        )
        # false_positive_scores.append(score)
        print(f"NEGATIVE - symbol: {f_p_d["symbol"]}. rank: {rank}. score: {score}. prob: {prob}")

    # for p_d in positive_data:
    #     probability = evidence_object.compute_probability(
    #         symbol_statistics=p_d,
    #         older_positive_scores=positive_scores,
    #     )

    # for f_p_d in false_positive_data:
    #     probability = evidence_object.compute_probability(
    #         symbol_statistics=f_p_d,
    #         older_positive_scores=positive_scores,
    #     )

def format_data():
    for file_path in ["positive_results.csv", "false_positive_results.csv"]:
        df = pandas.read_csv(file_path)
        df_new = df.drop(
            columns=[
                "original_bar_time",
                "collection_status",
                "analysis_status",
                "actual_confirmation_bar_time",
                "evidence",
                "result",
            ],
            errors='ignore',
        )
        averages = df_new.mean(numeric_only=True)
        averages["symbol"] = "AVERGAE"
        df_new.loc["AVERAGE"] = averages
        df_new.to_csv(file_path, index=False)

if __name__ == '__main__':
    calculate_score()
