import joblib
import pandas as pd
import numpy as np

import common


class Runner:
    def __init__(
        self,
        should_run_model: bool,
    ):
        self.should_run_model = should_run_model
        if should_run_model:
            self.model = joblib.load("model/prod/stable/trade_model.pkl")
            self.imputer = joblib.load("model/prod/stable/trade_imputer.pkl")

            bundle = joblib.load("model/prod/stable/trade_model_bundle.pkl")
            self.features = bundle["features"]
            self.threshold = bundle["threshold"]

    def score_potential_confirmation_bar(
        self,
        potential_confirmation_bar: common.objects.BarData,
    ) -> common.objects.Score:
        if not self.should_run_model:
            return common.objects.Score(
                score=0.0,
                probability=0.0,
                threshold=0.0,
                should_take_trade=True,
            )

        features_data = {}
        for feature_name in self.features:
            features_data[feature_name] = potential_confirmation_bar.price_movement_statistics.get(feature_name, np.nan)

        x_live = pd.DataFrame([features_data], columns=self.features)
        x_live = x_live.reindex(columns=self.features, fill_value=0)
        x_live = pd.DataFrame(self.imputer.transform(x_live), columns=self.features)

        probability = float(self.model.predict_proba(x_live)[0, 1])
        should_take_trade = probability >= 0.50

        score = round(probability * 100, 2)

        return common.objects.Score(
            score=score,
            probability=probability,
            threshold=self.threshold,
            should_take_trade=should_take_trade,
        )
