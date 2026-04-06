import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("model/training/test_predictions.csv")

# Make sure you have these columns:
# - score OR probability
# - label (actual result: 1=positive, 0=negative)
# - prediction (model decision after threshold)

# If you only have probability, use that
score_col = "probability" if "probability" in df.columns else "score"

# Create classification types
prediction_col = "prediction"   # or "pass_recommended"

df["prediction"] = df[prediction_col].astype(int)

df["type"] = "TN"

df.loc[(df["label"] == 1) & (df["prediction"] == 1), "type"] = "TP"
df.loc[(df["label"] == 0) & (df["prediction"] == 1), "type"] = "FP"
df.loc[(df["label"] == 1) & (df["prediction"] == 0), "type"] = "FN"
df.loc[(df["label"] == 0) & (df["prediction"] == 0), "type"] = "TN"
# Split distributions
tp_scores = df[df["type"] == "TP"][score_col]
fp_scores = df[df["type"] == "FP"][score_col]
tn_scores = df[df["type"] == "TN"][score_col]
fn_scores = df[df["type"] == "FN"][score_col]

# Plot histogram
plt.figure(figsize=(10,6))

plt.hist(tp_scores, bins=20, alpha=0.6, label="TP (Good Trades)")
plt.hist(fp_scores, bins=20, alpha=0.6, label="FP (Bad Trades)")

plt.axvline(0.55, linestyle="--", label="Threshold 0.55")
plt.axvline(0.60, linestyle="--", label="Threshold 0.60")
plt.axvline(0.70, linestyle="--", label="Potential Safe Zone")

plt.legend()
plt.title("Score Distribution: TP vs FP")
plt.xlabel("Score / Probability")
plt.ylabel("Count")

plt.show()

# ---- STATISTICS ----
print("\n=== DISTRIBUTION STATS ===")

print("\nTP (Good Trades):")
print(tp_scores.describe())

print("\nFP (Bad Trades):")
print(fp_scores.describe())

print(df.groupby("type")["probability"].describe())

# ---- OVERLAP ANALYSIS ----
print("\n=== OVERLAP ANALYSIS ===")

# How many FP above thresholds
for t in [0.55, 0.60, 0.65, 0.70]:
    fp_above = (fp_scores >= t).sum()
    tp_above = (tp_scores >= t).sum()

    print(f"\nThreshold {t}:")
    print(f"TP above: {tp_above}")
    print(f"FP above: {fp_above}")

# for file_name in [
#     'model/training/positive_results_scored.csv',
#     'model/training/false_positive_results_scored.csv',
# ]:
#     df = pd.read_csv(file_name)
#     thresholds = compute_thresholds_from_positives(df)
#     df["passes_quality_filter"] = compute_quality_filter_df_v2(df, thresholds)

#     df.to_csv(file_name, index=False)
