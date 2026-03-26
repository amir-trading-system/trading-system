import joblib
import pandas as pd
import numpy as np

import shap

import common


class Runner:
    def __init__(
        self,
        should_run_model: bool,
    ):
        self.should_run_model = should_run_model
        if should_run_model:
            self.model = joblib.load("model/trade_model.pkl")
            self.imputer = joblib.load("model/trade_imputer.pkl")

            bundle = joblib.load("model/trade_model_bundle.pkl")
            self.features = bundle["features"]
            self.threshold = bundle["threshold"]
            self.explainer = shap.TreeExplainer(self.model)

    def score_potential_confirmation_bar(
        self,
        bar_statistics: dict[str, float],
    ) -> common.objects.Score:
        if not self.should_run_model:
            return common.objects.Score(
                score=0.0,
                probability=0.0,
                threshold=0.0,
                should_take_trade=True,
                features_tree={},
            )

        features_data = {}
        for feature_name in self.features:
            features_data[feature_name] = bar_statistics.get(feature_name, np.nan)

        x_live = pd.DataFrame([features_data], columns=self.features)
        x_live = pd.DataFrame(self.imputer.transform(x_live), columns=self.features)

        probability = float(self.model.predict_proba(x_live)[0, 1])
        should_take_trade = probability >= self.threshold
        features_tree = {}

        if should_take_trade:
            shap_values = self.explainer.shap_values(x_live)
            values = shap_values[1][0]

            for feature, value in zip(x_live.columns, values):
              features_tree[feature] = value

        score = round(probability * 100, 2)

        return common.objects.Score(
            score=score,
            probability=probability,
            threshold=self.threshold,
            should_take_trade=should_take_trade,
            features_tree=features_tree,
        )
