#pylint: skip-file
# type: ignore
import concurrent.futures
import csv
import datetime
import glob
import math
import os
import pickle
from dataclasses import dataclass, asdict
from typing import Any, Optional


# ============================================================
# CONFIG
# ============================================================

INPUT_FILES_GLOB = "model/training/data/*.json"

OUTPUT_ALL_BARS_FILE = "model/positive_30pct_trend_start_days_all_bars.csv"
OUTPUT_TREND_STARTS_FILE = "model/positive_30pct_trend_start_candidates.csv"

MAX_WORKERS = 10

MARKET_OPEN = datetime.time(9, 30)
MARKET_CLOSE = datetime.time(16, 0)

# We only search positive cases.
ONLY_POSITIVE_CASES = False

# A selected trend-start bar must have at least this gain after it.
MIN_GAIN_AFTER_ENTRY_PCT = 0.1

# Search only earlier/midday bars. Change if needed.
MAX_ENTRY_TIME = datetime.time(12, 30)

# Future path quality.
# To avoid selecting bars that only eventually run after a huge failure,
# we require support low not to break before the 30% move.
SUPPORT_LOOKBACK_BARS = 30
SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT = 0.003

# Current buyer bar quality.
MIN_CLOSE_POSITION_IN_RANGE = 0.80
MAX_UPPER_WICK_PCT = 0.20
MIN_BODY_PCT = 0.45
MIN_VOLUME_VS_AVERAGE = 1.2

# Context thresholds for "trend is starting".
MIN_PREVIOUS_CONTEXT_BARS = 20


# ============================================================
# OUTPUT ROWS
# ============================================================

@dataclass
class TrendStartCandidateRow:
    symbol: str
    trade_date: str
    is_positive: bool

    trend_start_time: datetime.datetime
    minutes_from_open: float

    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_average: float

    vwap: float
    ema_9: float
    ema_20: float
    macd: float
    histogram: float
    signal_line: float

    candle_body_pct_of_range: float
    upper_wick_pct_of_range: float
    close_position_in_range: float

    close_to_vwap_pct: Optional[float]
    close_to_ema_9_pct: Optional[float]
    close_to_ema_20_pct: Optional[float]
    ema_9_to_ema_20_pct: Optional[float]

    volume_vs_previous_bar_ratio: Optional[float]
    volume_vs_average_ratio: Optional[float]

    pre_5_bar_gain_pct: Optional[float]
    pre_10_bar_gain_pct: Optional[float]
    pre_20_bar_gain_pct: Optional[float]

    pre_5_bar_avg_volume_ratio: Optional[float]
    pre_10_bar_avg_volume_ratio: Optional[float]
    pre_20_bar_avg_volume_ratio: Optional[float]

    pre_10_close_above_vwap_count: int
    pre_10_close_above_ema9_count: int
    pre_10_higher_or_flat_low_count: int

    recent_20_high: Optional[float]
    recent_20_low: Optional[float]
    close_above_recent_20_high_pct: Optional[float]
    pullback_from_recent_20_high_pct: Optional[float]
    minutes_since_recent_20_high: Optional[float]

    support_low_reference: Optional[float]
    support_low_reference_time: Optional[datetime.datetime]

    max_gain_after_entry_full_session_pct: Optional[float]
    max_gain_after_entry_full_session_high: Optional[float]
    max_gain_after_entry_full_session_high_time: Optional[datetime.datetime]
    minutes_until_max_gain_full_session: Optional[float]

    reached_30pct_before_support_low_break: bool
    minutes_until_30pct_gain: Optional[float]

    support_low_broke_before_30pct: bool
    support_low_break_time: Optional[datetime.datetime]
    support_low_break_price: Optional[float]

    max_drawdown_before_30pct_or_break_pct: Optional[float]

    trend_start_reason_tags: str
    selection_score: float


@dataclass
class BarExportRow:
    selected_case_id: str
    trend_start_time: datetime.datetime
    trend_start_close: float
    trend_start_reason_tags: str

    symbol: str
    trade_date: str
    is_positive: bool

    bar_time: datetime.datetime
    minutes_from_trend_start: Optional[float]
    minutes_from_open: float

    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_average: float
    volume_average_last_3: float
    volume_average_last_10: float

    vwap: float
    ema_9: float
    ema_20: float
    ema_12: float
    ema_26: float
    ema_200: float
    macd: float
    histogram: float
    signal_line: float

    bar_gain_from_trend_start_close_pct: Optional[float]
    close_to_vwap_pct: Optional[float]
    close_to_ema_9_pct: Optional[float]
    close_to_ema_20_pct: Optional[float]
    volume_vs_average_ratio: Optional[float]

    is_trend_start_bar: bool


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value):
            return default
        return value
    except Exception:
        return default


def ratio(value: Any, base: Any) -> Optional[float]:
    value = safe_float(value, None)
    base = safe_float(base, None)

    if value is None or base is None or base <= 0:
        return None

    return value / base


def pct_change(base: Any, value: Any) -> Optional[float]:
    base = safe_float(base, None)
    value = safe_float(value, None)

    if base is None or value is None or base <= 0:
        return None

    return (value - base) / base


def minutes_between(start: datetime.datetime, end: datetime.datetime) -> float:
    return (end - start).total_seconds() / 60.0


def minutes_from_open(bar_time: datetime.datetime) -> float:
    open_dt = datetime.datetime(
        year=bar_time.year,
        month=bar_time.month,
        day=bar_time.day,
        hour=9,
        minute=30,
    )
    return minutes_between(open_dt, bar_time)


def load_pickle_data(file_path: str) -> Any:
    with open(file_path, "rb") as file_obj:
        return pickle.load(file_obj)


def candle_stats(bar: Any) -> dict[str, float]:
    candle_range = bar.high - bar.low

    if candle_range <= 0:
        return {
            "body_pct": 0.0,
            "upper_wick_pct": 0.0,
            "close_position": 0.0,
        }

    body = abs(bar.close - bar.open_value)
    upper_wick = bar.high - max(bar.open_value, bar.close)

    return {
        "body_pct": body / candle_range,
        "upper_wick_pct": max(0.0, upper_wick / candle_range),
        "close_position": (bar.close - bar.low) / candle_range,
    }


def summarize_window(
    bars: list[Any],
    current_index: int,
    size: int,
) -> dict[str, Any]:
    window = bars[max(0, current_index - size):current_index]

    result = {
        "gain_pct": None,
        "avg_volume_ratio": None,
        "close_above_vwap_count": 0,
        "close_above_ema9_count": 0,
        "higher_or_flat_low_count": 0,
    }

    if len(window) < 2:
        return result

    result["gain_pct"] = pct_change(window[0].close, window[-1].close)

    volume_ratios = []

    for bar in window:
        vol_ratio = ratio(bar.volume, bar.volume_average)
        if vol_ratio is not None:
            volume_ratios.append(vol_ratio)

        if bar.close > bar.vwap:
            result["close_above_vwap_count"] += 1

        if bar.close > bar.ema_9:
            result["close_above_ema9_count"] += 1

    for idx in range(1, len(window)):
        previous_low = window[idx - 1].low
        current_low = window[idx].low

        if previous_low > 0 and current_low >= previous_low * 0.985:
            result["higher_or_flat_low_count"] += 1

    if volume_ratios:
        result["avg_volume_ratio"] = sum(volume_ratios) / len(volume_ratios)

    return result


def recent_high_low_context(
    bars: list[Any],
    current_index: int,
    size: int,
    current_bar: Any,
) -> dict[str, Any]:
    window = bars[max(0, current_index - size):current_index]

    if not window:
        return {
            "recent_high": None,
            "recent_low": None,
            "close_above_recent_high_pct": None,
            "pullback_from_recent_high_pct": None,
            "minutes_since_recent_high": None,
        }

    high_bar = max(window, key=lambda bar: bar.high)
    low_bar = min(window, key=lambda bar: bar.low)

    close_above_high_pct = pct_change(high_bar.high, current_bar.close)

    pullback_pct = None
    if high_bar.high > 0:
        pullback_pct = (high_bar.high - current_bar.low) / high_bar.high

    return {
        "recent_high": high_bar.high,
        "recent_low": low_bar.low,
        "close_above_recent_high_pct": close_above_high_pct,
        "pullback_from_recent_high_pct": pullback_pct,
        "minutes_since_recent_high": minutes_between(high_bar.bar_time, current_bar.bar_time),
    }


def get_support_low_reference(
    bars: list[Any],
    current_index: int,
) -> tuple[Optional[float], Optional[datetime.datetime]]:
    window = bars[max(0, current_index - SUPPORT_LOOKBACK_BARS):current_index]

    if not window:
        return None, None

    support_bar = min(window, key=lambda bar: bar.low)

    return support_bar.low, support_bar.bar_time


# ============================================================
# TREND START + FUTURE PATH
# ============================================================

def bar_has_buyer_entry_quality(
    bars: list[Any],
    current_index: int,
) -> bool:
    if current_index <= 0:
        return False

    bar = bars[current_index]
    previous_bar = bars[current_index - 1]
    stats = candle_stats(bar)

    if bar.bar_time.time() > MAX_ENTRY_TIME:
        return False

    if bar.close <= bar.open_value:
        return False

    if stats["close_position"] < MIN_CLOSE_POSITION_IN_RANGE:
        return False

    if stats["upper_wick_pct"] > MAX_UPPER_WICK_PCT:
        return False

    if stats["body_pct"] < MIN_BODY_PCT:
        return False

    if bar.close <= bar.vwap:
        return False

    if bar.close <= bar.ema_9:
        return False

    if bar.close <= bar.ema_20:
        return False

    vol_avg_ratio = ratio(bar.volume, bar.volume_average)
    if vol_avg_ratio is None or vol_avg_ratio < MIN_VOLUME_VS_AVERAGE:
        return False

    # Need either volume expansion vs previous bar, or very good volume vs average.
    vol_prev_ratio = ratio(bar.volume, previous_bar.volume)
    if (
        (vol_prev_ratio is None or vol_prev_ratio < 1.4)
        and vol_avg_ratio < 2.0
    ):
        return False

    return True


def trend_context_tags(
    bars: list[Any],
    current_index: int,
) -> tuple[list[str], dict[str, Any]]:
    bar = bars[current_index]

    pre5 = summarize_window(bars, current_index, 5)
    pre10 = summarize_window(bars, current_index, 10)
    pre20 = summarize_window(bars, current_index, 20)
    rc20 = recent_high_low_context(bars, current_index, 20, bar)

    tags = []

    if pre5["avg_volume_ratio"] is not None and pre5["avg_volume_ratio"] <= 0.8:
        tags.append("volume_dryup_before_entry")

    if pre10["close_above_vwap_count"] >= 8:
        tags.append("base_above_vwap")

    if pre10["close_above_ema9_count"] >= 8:
        tags.append("base_above_ema9")

    if pre10["higher_or_flat_low_count"] >= 7:
        tags.append("higher_or_flat_lows")

    if pre20["gain_pct"] is not None and pre20["gain_pct"] >= 0.06:
        tags.append("pre20_rebuild")

    if rc20["close_above_recent_high_pct"] is not None and rc20["close_above_recent_high_pct"] >= 0.04:
        tags.append("breaks_20bar_high")

    if rc20["pullback_from_recent_high_pct"] is not None and rc20["pullback_from_recent_high_pct"] >= 0.05:
        tags.append("meaningful_recent_pullback")

    if rc20["minutes_since_recent_high"] is not None and rc20["minutes_since_recent_high"] >= 8:
        tags.append("mature_recent_resistance")

    if bar.ema_9 > bar.ema_20:
        tags.append("ema9_above_ema20")

    if bar.ema_9 > bar.vwap:
        tags.append("ema9_above_vwap")

    # Market/open tags.
    if datetime.time(9, 30) <= bar.bar_time.time() <= datetime.time(9, 35):
        tags.append("market_open")

    context = {
        "pre5": pre5,
        "pre10": pre10,
        "pre20": pre20,
        "rc20": rc20,
    }

    return tags, context


def looks_like_trend_start(
    bars: list[Any],
    current_index: int,
) -> tuple[bool, list[str], dict[str, Any]]:
    if not bar_has_buyer_entry_quality(bars, current_index):
        return False, [], {}

    tags, context = trend_context_tags(bars, current_index)

    # Keep broad enough, because we want to discover patterns later.
    has_base_or_reclaim_context = (
        "base_above_vwap" in tags
        or "higher_or_flat_lows" in tags
        or "pre20_rebuild" in tags
        or "breaks_20bar_high" in tags
        or "volume_dryup_before_entry" in tags
        or "market_open" in tags
    )

    if not has_base_or_reclaim_context:
        return False, tags, context

    return True, tags, context


def future_reaches_30pct_before_support_break(
    bars: list[Any],
    current_index: int,
    support_low: Optional[float],
) -> dict[str, Any]:
    entry_bar = bars[current_index]
    entry_close = entry_bar.close

    invalidation_price = None
    if support_low is not None and support_low > 0:
        invalidation_price = support_low * (1 - SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT)

    max_gain_pct = None
    max_gain_high = None
    max_gain_time = None

    reached_30 = False
    minutes_until_30 = None

    support_broke_before_30 = False
    support_break_time = None
    support_break_price = None

    max_drawdown_before_30_or_break_pct = 0.0

    for future_bar in bars[current_index + 1:]:
        if future_bar.bar_time.time() > MARKET_CLOSE:
            break

        gain_pct = (future_bar.high - entry_close) / entry_close

        if max_gain_pct is None or gain_pct > max_gain_pct:
            max_gain_pct = gain_pct
            max_gain_high = future_bar.high
            max_gain_time = future_bar.bar_time

        drawdown_pct = max(0.0, (entry_close - future_bar.low) / entry_close)
        max_drawdown_before_30_or_break_pct = max(
            max_drawdown_before_30_or_break_pct,
            drawdown_pct,
        )

        if not reached_30 and future_bar.high >= entry_close * (1 + MIN_GAIN_AFTER_ENTRY_PCT):
            reached_30 = True
            minutes_until_30 = minutes_between(entry_bar.bar_time, future_bar.bar_time)

        if invalidation_price is not None and future_bar.low < invalidation_price:
            if not reached_30:
                support_broke_before_30 = True
                support_break_time = future_bar.bar_time
                support_break_price = future_bar.low
            break

    minutes_to_max = None
    if max_gain_time is not None:
        minutes_to_max = minutes_between(entry_bar.bar_time, max_gain_time)

    return {
        "max_gain_pct": max_gain_pct,
        "max_gain_high": max_gain_high,
        "max_gain_time": max_gain_time,
        "minutes_to_max": minutes_to_max,
        "reached_30": reached_30,
        "minutes_until_30": minutes_until_30,
        "support_broke_before_30": support_broke_before_30,
        "support_break_time": support_break_time,
        "support_break_price": support_break_price,
        "max_drawdown_before_30_or_break_pct": max_drawdown_before_30_or_break_pct,
    }


def candidate_score(
    bar: Any,
    tags: list[str],
    future_path: dict[str, Any],
) -> float:
    stats = candle_stats(bar)

    score = 0.0
    score += (future_path.get("max_gain_pct") or 0.0) * 100.0
    score -= (future_path.get("max_drawdown_before_30_or_break_pct") or 0.0) * 120.0
    score += stats["close_position"] * 10.0
    score -= stats["upper_wick_pct"] * 10.0

    # Prefer earlier bars if both eventually get same move.
    score -= max(0.0, minutes_from_open(bar.bar_time)) * 0.03

    # Prefer useful setup tags.
    score += len(tags) * 1.5

    return score


# ============================================================
# EXPORT BUILDING
# ============================================================

def build_trend_start_candidate_row(
    data: dict[str, Any],
    bars: list[Any],
    current_index: int,
    tags: list[str],
    context: dict[str, Any],
    support_low: Optional[float],
    support_low_time: Optional[datetime.datetime],
    future_path: dict[str, Any],
) -> TrendStartCandidateRow:
    bar = bars[current_index]
    previous_bar = bars[current_index - 1]
    stats = candle_stats(bar)

    day_stock = data.get("day_timeframe_stock")
    is_positive = bool(getattr(day_stock, "is_positive", False))

    trade_date = str(bar.bar_time.date())
    if getattr(day_stock, "specific_bar_time", None) is not None:
        trade_date = str(day_stock.specific_bar_time.date())

    pre5 = context["pre5"]
    pre10 = context["pre10"]
    pre20 = context["pre20"]
    rc20 = context["rc20"]

    return TrendStartCandidateRow(
        symbol=bar.symbol,
        trade_date=trade_date,
        is_positive=is_positive,

        trend_start_time=bar.bar_time,
        minutes_from_open=minutes_from_open(bar.bar_time),

        open=bar.open_value,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        volume_average=bar.volume_average,

        vwap=bar.vwap,
        ema_9=bar.ema_9,
        ema_20=bar.ema_20,
        macd=bar.macd,
        histogram=bar.histogram,
        signal_line=bar.signal_line,

        candle_body_pct_of_range=stats["body_pct"],
        upper_wick_pct_of_range=stats["upper_wick_pct"],
        close_position_in_range=stats["close_position"],

        close_to_vwap_pct=pct_change(bar.vwap, bar.close),
        close_to_ema_9_pct=pct_change(bar.ema_9, bar.close),
        close_to_ema_20_pct=pct_change(bar.ema_20, bar.close),
        ema_9_to_ema_20_pct=pct_change(bar.ema_20, bar.ema_9),

        volume_vs_previous_bar_ratio=ratio(bar.volume, previous_bar.volume),
        volume_vs_average_ratio=ratio(bar.volume, bar.volume_average),

        pre_5_bar_gain_pct=pre5["gain_pct"],
        pre_10_bar_gain_pct=pre10["gain_pct"],
        pre_20_bar_gain_pct=pre20["gain_pct"],

        pre_5_bar_avg_volume_ratio=pre5["avg_volume_ratio"],
        pre_10_bar_avg_volume_ratio=pre10["avg_volume_ratio"],
        pre_20_bar_avg_volume_ratio=pre20["avg_volume_ratio"],

        pre_10_close_above_vwap_count=pre10["close_above_vwap_count"],
        pre_10_close_above_ema9_count=pre10["close_above_ema9_count"],
        pre_10_higher_or_flat_low_count=pre10["higher_or_flat_low_count"],

        recent_20_high=rc20["recent_high"],
        recent_20_low=rc20["recent_low"],
        close_above_recent_20_high_pct=rc20["close_above_recent_high_pct"],
        pullback_from_recent_20_high_pct=rc20["pullback_from_recent_high_pct"],
        minutes_since_recent_20_high=rc20["minutes_since_recent_high"],

        support_low_reference=support_low,
        support_low_reference_time=support_low_time,

        max_gain_after_entry_full_session_pct=future_path["max_gain_pct"],
        max_gain_after_entry_full_session_high=future_path["max_gain_high"],
        max_gain_after_entry_full_session_high_time=future_path["max_gain_time"],
        minutes_until_max_gain_full_session=future_path["minutes_to_max"],

        reached_30pct_before_support_low_break=future_path["reached_30"],
        minutes_until_30pct_gain=future_path["minutes_until_30"],

        support_low_broke_before_30pct=future_path["support_broke_before_30"],
        support_low_break_time=future_path["support_break_time"],
        support_low_break_price=future_path["support_break_price"],

        max_drawdown_before_30pct_or_break_pct=future_path["max_drawdown_before_30_or_break_pct"],

        trend_start_reason_tags="|".join(tags),
        selection_score=candidate_score(bar, tags, future_path),
    )


def build_bar_export_rows(
    data: dict[str, Any],
    bars: list[Any],
    selected_candidate: TrendStartCandidateRow,
) -> list[BarExportRow]:
    day_stock = data.get("day_timeframe_stock")
    is_positive = bool(getattr(day_stock, "is_positive", False))

    trade_date = selected_candidate.trade_date

    selected_case_id = (
        f"{selected_candidate.symbol}-"
        f"{selected_candidate.trade_date}-"
        f"{selected_candidate.trend_start_time}"
    )

    rows: list[BarExportRow] = []

    for bar in bars:
        if bar.bar_time.date().isoformat() != trade_date:
            # Usually not needed, because bars are already filtered by day.
            pass

        minutes_from_trend = minutes_between(
            selected_candidate.trend_start_time,
            bar.bar_time,
        )

        row = BarExportRow(
            selected_case_id=selected_case_id,
            trend_start_time=selected_candidate.trend_start_time,
            trend_start_close=selected_candidate.close,
            trend_start_reason_tags=selected_candidate.trend_start_reason_tags,

            symbol=bar.symbol,
            trade_date=trade_date,
            is_positive=is_positive,

            bar_time=bar.bar_time,
            minutes_from_trend_start=minutes_from_trend,
            minutes_from_open=minutes_from_open(bar.bar_time),

            open=bar.open_value,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            volume_average=bar.volume_average,
            volume_average_last_3=getattr(bar, "volume_average_last_3", 0.0),
            volume_average_last_10=getattr(bar, "volume_average_last_10", 0.0),

            vwap=bar.vwap,
            ema_9=bar.ema_9,
            ema_20=bar.ema_20,
            ema_12=getattr(bar, "ema_12", 0.0),
            ema_26=getattr(bar, "ema_26", 0.0),
            ema_200=getattr(bar, "ema_200", 0.0),
            macd=bar.macd,
            histogram=bar.histogram,
            signal_line=bar.signal_line,

            bar_gain_from_trend_start_close_pct=pct_change(selected_candidate.close, bar.close),
            close_to_vwap_pct=pct_change(bar.vwap, bar.close),
            close_to_ema_9_pct=pct_change(bar.ema_9, bar.close),
            close_to_ema_20_pct=pct_change(bar.ema_20, bar.close),
            volume_vs_average_ratio=ratio(bar.volume, bar.volume_average),

            is_trend_start_bar=bar.bar_time == selected_candidate.trend_start_time,
        )

        rows.append(row)

    return rows


# ============================================================
# PER FILE
# ============================================================

def process_training_file(file_path: str) -> tuple[list[TrendStartCandidateRow], list[BarExportRow]]:
    data = load_pickle_data(file_path)

    day_stock = data.get("day_timeframe_stock")
    stock = data.get("one_minute_timeframe_stock")

    if stock is None or not hasattr(stock, "bars"):
        return [], []

    is_positive = bool(getattr(day_stock, "is_positive", False))

    if ONLY_POSITIVE_CASES and not is_positive:
        return [], []

    bars = sorted(stock.bars, key=lambda bar: bar.bar_time)

    if getattr(day_stock, "specific_bar_time", None) is not None:
        trade_date = day_stock.specific_bar_time.date()
        bars = [bar for bar in bars if bar.bar_time.date() == trade_date]

    # Keep full regular session bars for export and future path.
    bars = [
        bar
        for bar in bars
        if MARKET_OPEN <= bar.bar_time.time() <= MARKET_CLOSE
    ]

    if len(bars) < MIN_PREVIOUS_CONTEXT_BARS + 10:
        return [], []

    candidate_rows: list[TrendStartCandidateRow] = []

    for current_index in range(MIN_PREVIOUS_CONTEXT_BARS, len(bars)):
        current_bar = bars[current_index]

        looks_good, tags, context = looks_like_trend_start(
            bars=bars,
            current_index=current_index,
        )

        if not looks_good:
            continue

        support_low, support_low_time = get_support_low_reference(
            bars=bars,
            current_index=current_index,
        )

        future_path = future_reaches_30pct_before_support_break(
            bars=bars,
            current_index=current_index,
            support_low=support_low,
        )

        if not future_path["reached_30"]:
            continue

        if future_path["support_broke_before_30"]:
            continue

        row = build_trend_start_candidate_row(
            data=data,
            bars=bars,
            current_index=current_index,
            tags=tags,
            context=context,
            support_low=support_low,
            support_low_time=support_low_time,
            future_path=future_path,
        )

        candidate_rows.append(row)

    if not candidate_rows:
        return [], []

    # Pick the earliest high-quality candidate per symbol/day.
    # This keeps the exported bars compact.
    candidate_rows = sorted(
        candidate_rows,
        key=lambda row: (
            row.trend_start_time,
            -row.selection_score,
        ),
    )

    selected_candidate = candidate_rows[0]

    bar_rows = build_bar_export_rows(
        data=data,
        bars=bars,
        selected_candidate=selected_candidate,
    )

    # Return all candidate rows for diagnostic CSV, but only full bars for selected earliest case.
    return candidate_rows, bar_rows


# ============================================================
# CSV WRITING
# ============================================================

def write_dataclass_rows(
    rows: list[Any],
    output_path: str,
    dataclass_type: Any,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = list(dataclass_type.__dataclass_fields__.keys())

    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))

    print(f"Wrote {len(rows)} rows to {output_path}")


def main() -> None:
    files = glob.glob(INPUT_FILES_GLOB)

    print(f"Found {len(files)} files")

    all_candidate_rows: list[TrendStartCandidateRow] = []
    all_bar_rows: list[BarExportRow] = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {
            executor.submit(process_training_file, file_path): file_path
            for file_path in files
        }

        completed = 0

        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            completed += 1

            try:
                candidate_rows, bar_rows = future.result()
                all_candidate_rows.extend(candidate_rows)
                all_bar_rows.extend(bar_rows)
            except Exception as exc:
                print(f"Failed processing {file_path}: {exc}")

            if completed % 10 == 0:
                print(
                    f"Completed {completed}/{len(files)} files. "
                    f"Candidates: {len(all_candidate_rows)}. "
                    f"Export bars: {len(all_bar_rows)}"
                )

    write_dataclass_rows(
        rows=all_candidate_rows,
        output_path=OUTPUT_TREND_STARTS_FILE,
        dataclass_type=TrendStartCandidateRow,
    )

    write_dataclass_rows(
        rows=all_bar_rows,
        output_path=OUTPUT_ALL_BARS_FILE,
        dataclass_type=BarExportRow,
    )

    print("")
    print("Done.")
    print(f"Trend-start candidates: {len(all_candidate_rows)}")
    print(f"Exported one-minute bars: {len(all_bar_rows)}")
    print("")
    print("Upload this file:")
    print(OUTPUT_ALL_BARS_FILE)
    print("")
    print("Optional diagnostic file:")
    print(OUTPUT_TREND_STARTS_FILE)


if __name__ == "__main__":
    main()
