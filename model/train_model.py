import math
import json
from pathlib import Path
import os

import joblib
import numpy as np
import pandas as pd


from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


# ============================================================
# CONFIG
# ============================================================

POSITIVE_CSV = "model/positive_results.csv"
FALSE_POSITIVE_CSV = "model/false_positive_results.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.3

# Thresholds to inspect
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]

# Output files
TRAIN_SCORED_OUTPUT = "model/scored_training_dataset.csv"
POSITIVE_SCORED_OUTPUT = "model/positive_results_scored.csv"
FALSE_POSITIVE_SCORED_OUTPUT = "model/false_positive_results_scored.csv"
MODEL_INFO_OUTPUT = "model/model_info.json"

if os.path.exists(TRAIN_SCORED_OUTPUT):
    os.remove(TRAIN_SCORED_OUTPUT)

if os.path.exists(POSITIVE_SCORED_OUTPUT):
    os.remove(POSITIVE_SCORED_OUTPUT)

if os.path.exists(FALSE_POSITIVE_SCORED_OUTPUT):
    os.remove(FALSE_POSITIVE_SCORED_OUTPUT)

if os.path.exists(MODEL_INFO_OUTPUT):
    os.remove(MODEL_INFO_OUTPUT)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def stable_sigmoid(x):
    # Included in case you want to transform custom scores later.
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def find_shared_numeric_features(pos_df, neg_df):
    pos_num = set(pos_df.select_dtypes(include=[np.number, np.bool]).columns)
    neg_num = set(neg_df.select_dtypes(include=[np.number, np.bool]).columns)
    shared_columns = sorted((pos_num & neg_num) - {"label"})
    final_shares_columns = []
    for feature in shared_columns:
        if str(feature).startswith("feature_"):
            final_shares_columns.append(feature)

    return final_shares_columns

def evaluate_threshold(df, threshold):
    """
    Positive pass rate: positives classified as pass
    False-positive reject rate: negatives classified as reject
    """
    passed = df["probability"] >= threshold

    positives = df["label"] == 1
    negatives = df["label"] == 0

    pos_pass_rate = passed[positives].mean() if positives.any() else np.nan
    neg_reject_rate = (~passed[negatives]).mean() if negatives.any() else np.nan

    balanced = np.nanmean([pos_pass_rate, neg_reject_rate])

    return {
        "threshold": threshold,
        "positive_pass_rate": float(pos_pass_rate),
        "false_positive_reject_rate": float(neg_reject_rate),
        "balanced_score": float(balanced),
    }

def format_features_data(
    positive_data: pd.DataFrame,
    false_positive_data: pd.DataFrame,
):
    for features_data in [
        positive_data,
        false_positive_data,
    ]:
        features_data["feature_has_positive_more_than_negative_bars"] = features_data["feature_has_positive_more_than_negative_bars"] == 'True'
        features_data["feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open"] = features_data["feature_most_of_bars_with_volume_close_to_entry_point_than_to_market_open"] == 'True'

# ============================================================
# LOAD DATA
# ============================================================

pos_path = Path(POSITIVE_CSV)
neg_path = Path(FALSE_POSITIVE_CSV)

if not pos_path.exists():
    raise FileNotFoundError(f"Could not find {POSITIVE_CSV}")
if not neg_path.exists():
    raise FileNotFoundError(f"Could not find {FALSE_POSITIVE_CSV}")

positive_df = pd.read_csv(pos_path)
false_positive_df = pd.read_csv(neg_path)

positive_df["label"] = 1
false_positive_df["label"] = 0

# Keep original copies for later scoring
positive_raw = positive_df.copy()
false_positive_raw = false_positive_df.copy()

# ============================================================
# PREP FEATURES
# ============================================================

shared_features = find_shared_numeric_features(positive_df, false_positive_df)

if not shared_features:
    raise ValueError("No shared numeric features were found between the two CSV files.")

df = pd.concat([positive_df, false_positive_df], ignore_index=True).copy()

# Keep only shared numeric features + label
model_df = df[shared_features + ["label"]].copy()

# Impute missing values
X = model_df[shared_features].copy()
y = model_df["label"].copy()

imputer = SimpleImputer(strategy="median")
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=shared_features, index=X.index)

# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)

# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=7,
    min_samples_leaf=4,
    min_samples_split=8,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

# ============================================================
# EVALUATION ON TEST SET
# ============================================================

test_probs = model.predict_proba(X_test)[:, 1]
test_pred_default = (test_probs >= 0.5).astype(int)

print("\n================ TEST SET REPORT (threshold=0.50) ================\n")
print(classification_report(y_test, test_pred_default, digits=4))
print("Confusion matrix:")
print(confusion_matrix(y_test, test_pred_default))

# ============================================================
# SCORE FULL DATASET
# ============================================================

full_probs = model.predict_proba(X_imputed)[:, 1]

scored_df = df.copy()
scored_df["probability"] = full_probs
scored_df["score"] = (scored_df["probability"] * 100.0).round(2)

# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

print("\n================ THRESHOLD ANALYSIS (MODEL ONLY) ================\n")
model_results = []
for th in THRESHOLDS:
    r = evaluate_threshold(scored_df, th)
    model_results.append(r)
    print(
        f"threshold={r['threshold']:.2f} | "
        f"positive_pass_rate={r['positive_pass_rate']:.4f} | "
        f"false_positive_reject_rate={r['false_positive_reject_rate']:.4f} | "
        f"balanced={r['balanced_score']:.4f}"
    )

best_model = max(model_results, key=lambda x: x["balanced_score"])

print("\n================ BEST THRESHOLDS ================\n")
print("Best model threshold:", best_model)

# ============================================================
# FEATURE IMPORTANCE
# ============================================================

feature_importance = (
    pd.Series(model.feature_importances_, index=shared_features)
    .sort_values(ascending=False)
)

print("\n================ TOP 25 FEATURE IMPORTANCE ================\n")
print(feature_importance.head(25))

# ============================================================
# SCORE INDIVIDUAL ORIGINAL FILES
# ============================================================

def score_dataframe(raw_df, label_value=None):
    missing_features = [c for c in shared_features if c not in raw_df.columns]

    temp = raw_df.copy()

    # Ensure all model features exist
    for col in missing_features:
        temp[col] = np.nan

    temp_x = temp[shared_features].copy()
    temp_x_imputed = pd.DataFrame(
        imputer.transform(temp_x),
        columns=shared_features,
        index=temp.index,
    )

    temp["probability"] = model.predict_proba(temp_x_imputed)[:, 1]
    temp["score"] = (temp["probability"] * 100.0).round(2)

    if label_value is not None:
        temp["label"] = label_value

    # Recommended pass flag using best hybrid threshold
    chosen_threshold = best_model["threshold"]
    temp["pass_recommended"] = temp["probability"] >= chosen_threshold

    return temp


positive_scored = score_dataframe(positive_raw, label_value=1)
false_positive_scored = score_dataframe(false_positive_raw, label_value=0)

# ============================================================
# SAVE OUTPUTS
# ============================================================

scored_df.to_csv(TRAIN_SCORED_OUTPUT, index=False)
positive_scored.to_csv(POSITIVE_SCORED_OUTPUT, index=False)
false_positive_scored.to_csv(FALSE_POSITIVE_SCORED_OUTPUT, index=False)

model_info = {
    "shared_features": shared_features,
    "best_model_only_threshold": best_model,
    "best_hybrid_threshold": best_model,
    "top_25_feature_importance": feature_importance.head(25).to_dict(),
    "test_size": TEST_SIZE,
    "random_state": RANDOM_STATE,
}

with open(MODEL_INFO_OUTPUT, "w") as f:
    json.dump(model_info, f, indent=2)

print("\n================ FILES SAVED ================\n")
print(TRAIN_SCORED_OUTPUT)
print(POSITIVE_SCORED_OUTPUT)
print(FALSE_POSITIVE_SCORED_OUTPUT)
print(MODEL_INFO_OUTPUT)

# ============================================================
# LIVE-USE FUNCTIONS
# ============================================================

CHOSEN_THRESHOLD = best_model["threshold"]

def probability_from_row(row: pd.Series) -> float:
    """
    Returns probability from 0.0 to 1.0 using the trained model.
    row must contain the feature columns used by the model.
    Missing values are allowed.
    """
    row_dict = {}
    for col in shared_features:
        if col in row.index:
            row_dict[col] = row[col]
        else:
            row_dict[col] = np.nan

    row_df = pd.DataFrame([row_dict], columns=shared_features)
    row_df_imputed = pd.DataFrame(
        imputer.transform(row_df),
        columns=shared_features,
    )

    prob = float(model.predict_proba(row_df_imputed)[0, 1])
    return prob


def score_from_row(row: pd.Series) -> float:
    """
    Returns score from 0 to 100.
    """
    prob = probability_from_row(row)
    return round(prob * 100.0, 2)


def classify_row(row: pd.Series):
    """
    Hybrid decision:
    - must exceed chosen threshold
    """
    prob = probability_from_row(row)
    score = round(prob * 100.0, 2)

    passed = prob >= CHOSEN_THRESHOLD

    if not passed:
        grade = "REJECT"
    elif prob >= 0.85:
        grade = "A+"
    elif prob >= 0.75:
        grade = "A"
    elif prob >= 0.65:
        grade = "B"
    else:
        grade = "C"

    return {
        "probability": round(prob, 6),
        "score": score,
        "threshold": CHOSEN_THRESHOLD,
        "pass_recommended": passed,
        "grade": grade,
    }


# ============================================================
# EXAMPLE
# ============================================================

print("\n================ SAMPLE LIVE OUTPUT ================\n")
sample_row = positive_scored.iloc[0]

classified_row = classify_row(sample_row)
print(classified_row)



joblib.dump(model, "model/trade_model.pkl")
joblib.dump(imputer, "model/trade_imputer.pkl")

model_bundle = {
    "features": shared_features,
    "threshold": classified_row["probability"],
}

joblib.dump(model_bundle, "model/trade_model_bundle.pkl")
