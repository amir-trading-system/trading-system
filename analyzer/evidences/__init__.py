from . import _evidence
from . import current_day_continues_trend
from . import current_day_breaks_highest_high_since_fall
from . import current_day_continues_without_touching_previous
from . import current_day_breaks_last_post_and_pre_market_high
from . import current_day_crossed_resistance_and_daily_highest_high
from . import current_day_is_after_healthy_retracement
from . import current_day_comes_after_9_ema_retracement
from . import current_day_comes_after_strong_day


__evidences__: list[type[_evidence.Evidence]] = [
    current_day_continues_trend.Evidence,
    current_day_breaks_highest_high_since_fall.Evidence,
    current_day_continues_without_touching_previous.Evidence,
    current_day_breaks_last_post_and_pre_market_high.Evidence,
    current_day_crossed_resistance_and_daily_highest_high.Evidence,
    current_day_is_after_healthy_retracement.Evidence,
    current_day_comes_after_9_ema_retracement.Evidence,
    current_day_comes_after_strong_day.Evidence,
]
