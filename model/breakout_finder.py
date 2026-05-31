#pylint: skip-file

import concurrent.futures
import datetime
import pickle
import glob
import csv
import math
import tqdm

from dataclasses import dataclass, asdict
from typing import Optional, Any

import common


POSITIVE_FILE_NAME = "model/training/positive_results.csv"
FALSE_POSITIVE_FILE_NAME = "model/training/false_positive_results.csv"
POTENTIAL_HARD_RULES_FILE_NAME = "model/training/hard_rules.json"


def load_pickle_data(
    file_path: str,
) -> Any:
    with open(file_path, "rb") as f:
        obj = pickle.load(f)

    return obj


def load_data_for_training_model() -> list[dict[str, Any]]:
    pickled_data: list[dict[str, Any]] = []
    files = glob.glob("model/training/data/*.json")
    futures = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=10,
    ) as executor:
        for file_path in files:
            f = executor.submit(
                load_pickle_data,
                file_path,
            )
            futures.append(f)

    for future in concurrent.futures.as_completed(futures):
        pickled_object = future.result()
        pickled_data.append(pickled_object)

    return pickled_data


@dataclass
class BreakoutResult:
    symbol: str
    trade_date: str
    bar_time: datetime.datetime
    is_positive: bool

    breakout_type: str
    reason: str

    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_average: float
    volume_ratio: float

    candle_body_pct_of_range: float
    upper_wick_pct_of_range: float
    lower_wick_pct_of_range: float
    close_position_in_range: float

    previous_highest_high_time: Optional[datetime.datetime]
    previous_highest_high: Optional[float]
    previous_highest_high_close: Optional[float]
    previous_highest_high_volume: Optional[float]
    previous_highest_high_volume_average: Optional[float]
    previous_highest_high_bar_wick_percentage: Optional[float]

    lowest_low_since_previous_high_time: Optional[datetime.datetime]
    lowest_low_since_previous_high: Optional[float]
    lowest_low_since_previous_high_close: Optional[float]
    lowest_low_since_previous_high_bar_lower_wick_percentage: Optional[float]

    previous_high_to_lowest_low_pullback_pct: Optional[float]
    breakout_close_above_previous_high_pct: Optional[float]
    minutes_since_previous_high: Optional[float]

    max_gain_after_breakout_pct: float
    max_gain_after_breakout_abs: float
    max_gain_after_breakout_high: Optional[float]
    max_gain_after_breakout_high_time: Optional[datetime.datetime]

    max_gain_after_breakout_next_30_minutes_pct: float
    max_gain_after_breakout_next_30_minutes_abs: float
    max_gain_after_breakout_next_30_minutes_high: Optional[float]
    max_gain_after_breakout_next_30_minutes_high_time: Optional[datetime.datetime]
    reached_10_percent_gain_within_30_minutes: bool
    minutes_until_10_percent_gain: Optional[float]

    went_below_lowest_low_before_10_percent_gain_30_minutes: bool
    lowest_low_break_before_10_percent_gain_30_minutes_time: Optional[datetime.datetime]
    lowest_low_break_before_10_percent_gain_30_minutes_price: Optional[float]

    vwap: Optional[float]
    ema_9: Optional[float]
    ema_20: Optional[float]
    macd: Optional[float]
    histogram: Optional[float]
    signal_line: Optional[float]


@dataclass
class FindBreakoutsResult:
    breakouts: list[BreakoutResult]
    is_positive: bool


def safe_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return default

        float_value = float(value)

        if math.isnan(float_value):
            return default

        return float_value

    except Exception:
        return default


def pct_change(
    from_value: float,
    to_value: float,
) -> float:
    if from_value == 0:
        return 0.0

    return (to_value - from_value) / from_value


def get_bar_range(
    bar_object: common.objects.BarData,
) -> float:
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)

    return max(0.000001, high - low)


def get_candle_stats(
    bar_object: common.objects.BarData,
) -> dict[str, float]:
    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)
    close = safe_float(bar_object.close, 0.0)

    bar_range = max(0.000001, high - low)
    body = abs(close - open_value)
    upper_wick = high - max(open_value, close)
    lower_wick = min(open_value, close) - low

    return {
        "body_pct_of_range": body / bar_range,
        "upper_wick_pct_of_range": max(0.0, upper_wick / bar_range),
        "lower_wick_pct_of_range": max(0.0, lower_wick / bar_range),
        "close_position_in_range": (close - low) / bar_range,
    }


def get_volume_ratio(
    bar_object: common.objects.BarData,
) -> float:
    volume = safe_float(bar_object.volume, 0.0)
    volume_average = safe_float(bar_object.volume_average, 0.0)

    if volume_average <= 0:
        return 0.0

    return volume / volume_average


def calculate_max_gain_after_breakout(
    bar_index: int,
    bars: list[common.objects.BarData],
) -> dict[str, Optional[float] | Optional[datetime.datetime]]:
    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)
    future_bars = bars[bar_index + 1:]

    if breakout_close <= 0 or not future_bars:
        return {
            "max_gain_after_breakout_pct": 0.0,
            "max_gain_after_breakout_abs": 0.0,
            "max_gain_after_breakout_high": None,
            "max_gain_after_breakout_high_time": None,
        }

    highest_future_bar = max(
        future_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )

    highest_future_high = safe_float(highest_future_bar.high, 0.0)
    gain_abs = max(0.0, highest_future_high - breakout_close)
    gain_pct = (gain_abs / breakout_close) * 100.0

    return {
        "max_gain_after_breakout_pct": gain_pct,
        "max_gain_after_breakout_abs": gain_abs,
        "max_gain_after_breakout_high": highest_future_high,
        "max_gain_after_breakout_high_time": highest_future_bar.bar_time,
    }




def calculate_max_gain_after_breakout_next_30_minutes(
    bar_index: int,
    bars: list[common.objects.BarData],
) -> dict[str, Optional[float] | Optional[datetime.datetime] | bool]:
    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)

    if breakout_close <= 0:
        return {
            "max_gain_after_breakout_next_30_minutes_pct": 0.0,
            "max_gain_after_breakout_next_30_minutes_abs": 0.0,
            "max_gain_after_breakout_next_30_minutes_high": None,
            "max_gain_after_breakout_next_30_minutes_high_time": None,
            "reached_10_percent_gain_within_30_minutes": False,
            "minutes_until_10_percent_gain": None,
        }

    end_time = breakout_bar.bar_time + datetime.timedelta(minutes=30)

    future_bars_next_30_minutes = [
        bar_object
        for bar_object in bars[bar_index + 1:]
        if breakout_bar.bar_time < bar_object.bar_time <= end_time
    ]

    if not future_bars_next_30_minutes:
        return {
            "max_gain_after_breakout_next_30_minutes_pct": 0.0,
            "max_gain_after_breakout_next_30_minutes_abs": 0.0,
            "max_gain_after_breakout_next_30_minutes_high": None,
            "max_gain_after_breakout_next_30_minutes_high_time": None,
            "reached_10_percent_gain_within_30_minutes": False,
            "minutes_until_10_percent_gain": None,
        }

    highest_future_bar = max(
        future_bars_next_30_minutes,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )

    highest_future_high = safe_float(highest_future_bar.high, 0.0)
    gain_abs = max(0.0, highest_future_high - breakout_close)
    gain_pct = (gain_abs / breakout_close) * 100.0

    ten_percent_target_price = breakout_close * 1.10
    first_10_percent_gain_bar = None

    for future_bar in future_bars_next_30_minutes:
        if safe_float(future_bar.high, 0.0) >= ten_percent_target_price:
            first_10_percent_gain_bar = future_bar
            break

    minutes_until_10_percent_gain = None
    if first_10_percent_gain_bar is not None:
        minutes_until_10_percent_gain = (
            first_10_percent_gain_bar.bar_time - breakout_bar.bar_time
        ).total_seconds() / 60.0

    return {
        "max_gain_after_breakout_next_30_minutes_pct": gain_pct,
        "max_gain_after_breakout_next_30_minutes_abs": gain_abs,
        "max_gain_after_breakout_next_30_minutes_high": highest_future_high,
        "max_gain_after_breakout_next_30_minutes_high_time": highest_future_bar.bar_time,
        "reached_10_percent_gain_within_30_minutes": first_10_percent_gain_bar is not None,
        "minutes_until_10_percent_gain": minutes_until_10_percent_gain,
    }



def calculate_lowest_low_break_before_10_percent_gain_next_30_minutes(
    bar_index: int,
    bars: list[common.objects.BarData],
    lowest_low_since_previous_high: Optional[float],
) -> dict[str, Optional[float] | Optional[datetime.datetime] | bool]:
    """
    Checks whether price goes below the setup's lowest low after the breakout,
    before reaching a 10% gain target, within the next 30 minutes.

    This is useful for identifying breakouts where the stock first invalidates
    the pullback/support low before making the desired move.
    """

    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)

    if breakout_close <= 0 or lowest_low_since_previous_high is None or lowest_low_since_previous_high <= 0:
        return {
            "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
            "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
            "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
        }

    ten_percent_target_price = breakout_close * 1.10
    end_time = breakout_bar.bar_time + datetime.timedelta(minutes=30)

    future_bars_next_30_minutes = [
        bar_object
        for bar_object in bars[bar_index + 1:]
        if breakout_bar.bar_time < bar_object.bar_time <= end_time
    ]

    for future_bar in future_bars_next_30_minutes:
        future_low = safe_float(future_bar.low, 0.0)
        future_high = safe_float(future_bar.high, 0.0)

        if future_low < lowest_low_since_previous_high:
            return {
                "went_below_lowest_low_before_10_percent_gain_30_minutes": True,
                "lowest_low_break_before_10_percent_gain_30_minutes_time": future_bar.bar_time,
                "lowest_low_break_before_10_percent_gain_30_minutes_price": future_low,
            }

        if future_high >= ten_percent_target_price:
            return {
                "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
                "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
                "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
            }

    return {
        "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
        "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
        "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
    }


def _is_valid_breakout(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> bool:
    previous_highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
        current_one_minute_bar=potential_confirmation_bar,
        only_before_current_bar=True,
    )
    if previous_highest_high_one_minute_bar is None:
        return False

    crossed_previous_highest_high = previous_highest_high_one_minute_bar.high < potential_confirmation_bar.close
    if not crossed_previous_highest_high:
        return False

    previous_highest_high_bar_is_recent = previous_highest_high_one_minute_bar.bar_time > potential_confirmation_bar.bar_time - datetime.timedelta(
        minutes=30,
    )
    if not previous_highest_high_bar_is_recent:
        return False

    lowest_low_bar_since_highest_high = one_minute_timeframe_stock.get_lowest_low_bar_between_bars(
        from_bar=previous_highest_high_one_minute_bar,
        to_bar=potential_confirmation_bar,
    )
    if lowest_low_bar_since_highest_high is None:
        return False

    lowest_low_became_support_or_previous_resistance = False
    for bar_object in one_minute_timeframe_stock.bars:
        if bar_object.bar_time >= previous_highest_high_one_minute_bar.bar_time:
            continue

        if bar_object.bar_time < lowest_low_bar_since_highest_high.bar_time - datetime.timedelta(
            minutes=30,
        ):
            continue

        highest_high_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=bar_object,
            only_before_current_bar=True,
        )

        if (
            True
            and highest_high_bar is not None
            and 0.97 <= highest_high_bar.high/lowest_low_bar_since_highest_high.low <= 1.03
            and highest_high_bar.close <= lowest_low_bar_since_highest_high.low
            and lowest_low_bar_since_highest_high.bar_lower_wick_percentage >= 0.2
            and highest_high_bar.bar_wick_percentage >= 0.1
            and highest_high_bar.above_volume_average
            and highest_high_bar.ema_9 > highest_high_bar.vwap
            and highest_high_bar.ema_9 > highest_high_bar.ema_20
            and highest_high_bar.high > highest_high_bar.ema_9
        ):
            lowest_low_became_support_or_previous_resistance = True
            break

    return lowest_low_became_support_or_previous_resistance


def build_breakout_result(
    data: dict[str, Any],
    bars: list[common.objects.BarData],
    bar_index: int,
    one_minute_timeframe_stock: common.objects.Stock,
) -> BreakoutResult:
    bar_object = bars[bar_index]

    specific_bar_time: datetime.datetime = data["day_timeframe_stock"].specific_bar_time
    is_positive: bool = data["day_timeframe_stock"].is_positive

    previous_highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
        current_one_minute_bar=bar_object,
        only_before_current_bar=True,
    )

    lowest_low_bar_since_highest_high = None
    if previous_highest_high_one_minute_bar is not None:
        lowest_low_bar_since_highest_high = one_minute_timeframe_stock.get_lowest_low_bar_between_bars(
            from_bar=previous_highest_high_one_minute_bar,
            to_bar=bar_object,
        )

    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)
    close = safe_float(bar_object.close, 0.0)
    volume = safe_float(bar_object.volume, 0.0)
    volume_average = safe_float(bar_object.volume_average, 0.0)
    volume_ratio = get_volume_ratio(bar_object)
    bar_time = bar_object.bar_time

    candle_stats = get_candle_stats(bar_object)

    max_gain_after_breakout_stats = calculate_max_gain_after_breakout(
        bar_index=bar_index,
        bars=bars,
    )

    max_gain_after_breakout_next_30_minutes_stats = calculate_max_gain_after_breakout_next_30_minutes(
        bar_index=bar_index,
        bars=bars,
    )

    previous_highest_high = (
        safe_float(previous_highest_high_one_minute_bar.high, 0.0)
        if previous_highest_high_one_minute_bar is not None
        else None
    )

    lowest_low_since_previous_high = (
        safe_float(lowest_low_bar_since_highest_high.low, 0.0)
        if lowest_low_bar_since_highest_high is not None
        else None
    )

    lowest_low_break_before_10_percent_gain_30_minutes_stats = calculate_lowest_low_break_before_10_percent_gain_next_30_minutes(
        bar_index=bar_index,
        bars=bars,
        lowest_low_since_previous_high=lowest_low_since_previous_high,
    )

    previous_high_to_lowest_low_pullback_pct = None
    if previous_highest_high is not None and lowest_low_since_previous_high is not None and previous_highest_high > 0:
        previous_high_to_lowest_low_pullback_pct = (
            (previous_highest_high - lowest_low_since_previous_high) / previous_highest_high
        )

    breakout_close_above_previous_high_pct = None
    if previous_highest_high is not None and previous_highest_high > 0:
        breakout_close_above_previous_high_pct = pct_change(previous_highest_high, close)

    minutes_since_previous_high = None
    if previous_highest_high_one_minute_bar is not None:
        minutes_since_previous_high = (
            (bar_object.bar_time - previous_highest_high_one_minute_bar.bar_time).total_seconds() / 60.0
        )

    return BreakoutResult(
        symbol=bar_object.symbol,
        trade_date=str(specific_bar_time.date()),
        bar_time=bar_time,
        is_positive=is_positive,

        breakout_type="clean_breakout",
        reason="previous_high_break_with_pullback_low_support_or_previous_resistance",

        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        volume_average=volume_average,
        volume_ratio=volume_ratio,

        candle_body_pct_of_range=candle_stats["body_pct_of_range"],
        upper_wick_pct_of_range=candle_stats["upper_wick_pct_of_range"],
        lower_wick_pct_of_range=candle_stats["lower_wick_pct_of_range"],
        close_position_in_range=candle_stats["close_position_in_range"],

        previous_highest_high_time=(
            previous_highest_high_one_minute_bar.bar_time
            if previous_highest_high_one_minute_bar is not None
            else None
        ),
        previous_highest_high=previous_highest_high,
        previous_highest_high_close=(
            safe_float(previous_highest_high_one_minute_bar.close, 0.0)
            if previous_highest_high_one_minute_bar is not None
            else None
        ),
        previous_highest_high_volume=(
            safe_float(previous_highest_high_one_minute_bar.volume, 0.0)
            if previous_highest_high_one_minute_bar is not None
            else None
        ),
        previous_highest_high_volume_average=(
            safe_float(previous_highest_high_one_minute_bar.volume_average, 0.0)
            if previous_highest_high_one_minute_bar is not None
            else None
        ),
        previous_highest_high_bar_wick_percentage=(
            safe_float(getattr(previous_highest_high_one_minute_bar, "bar_wick_percentage", None), 0.0)
            if previous_highest_high_one_minute_bar is not None
            else None
        ),

        lowest_low_since_previous_high_time=(
            lowest_low_bar_since_highest_high.bar_time
            if lowest_low_bar_since_highest_high is not None
            else None
        ),
        lowest_low_since_previous_high=lowest_low_since_previous_high,
        lowest_low_since_previous_high_close=(
            safe_float(lowest_low_bar_since_highest_high.close, 0.0)
            if lowest_low_bar_since_highest_high is not None
            else None
        ),
        lowest_low_since_previous_high_bar_lower_wick_percentage=(
            safe_float(getattr(lowest_low_bar_since_highest_high, "bar_lower_wick_percentage", None), 0.0)
            if lowest_low_bar_since_highest_high is not None
            else None
        ),

        previous_high_to_lowest_low_pullback_pct=previous_high_to_lowest_low_pullback_pct,
        breakout_close_above_previous_high_pct=breakout_close_above_previous_high_pct,
        minutes_since_previous_high=minutes_since_previous_high,

        max_gain_after_breakout_pct=max_gain_after_breakout_stats["max_gain_after_breakout_pct"],
        max_gain_after_breakout_abs=max_gain_after_breakout_stats["max_gain_after_breakout_abs"],
        max_gain_after_breakout_high=max_gain_after_breakout_stats["max_gain_after_breakout_high"],
        max_gain_after_breakout_high_time=max_gain_after_breakout_stats["max_gain_after_breakout_high_time"],

        max_gain_after_breakout_next_30_minutes_pct=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_pct"],
        max_gain_after_breakout_next_30_minutes_abs=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_abs"],
        max_gain_after_breakout_next_30_minutes_high=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_high"],
        max_gain_after_breakout_next_30_minutes_high_time=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_high_time"],
        reached_10_percent_gain_within_30_minutes=max_gain_after_breakout_next_30_minutes_stats["reached_10_percent_gain_within_30_minutes"],
        minutes_until_10_percent_gain=max_gain_after_breakout_next_30_minutes_stats["minutes_until_10_percent_gain"],

        went_below_lowest_low_before_10_percent_gain_30_minutes=lowest_low_break_before_10_percent_gain_30_minutes_stats["went_below_lowest_low_before_10_percent_gain_30_minutes"],
        lowest_low_break_before_10_percent_gain_30_minutes_time=lowest_low_break_before_10_percent_gain_30_minutes_stats["lowest_low_break_before_10_percent_gain_30_minutes_time"],
        lowest_low_break_before_10_percent_gain_30_minutes_price=lowest_low_break_before_10_percent_gain_30_minutes_stats["lowest_low_break_before_10_percent_gain_30_minutes_price"],

        vwap=safe_float(getattr(bar_object, "vwap", 0), 0),
        ema_9=safe_float(getattr(bar_object, "ema_9", 0), 0),
        ema_20=safe_float(getattr(bar_object, "ema_20", 0), 0),
        macd=safe_float(getattr(bar_object, "macd", 0), 0),
        histogram=safe_float(getattr(bar_object, "histogram", 0), 0),
        signal_line=safe_float(getattr(bar_object, "signal_line", 0), 0),
    )


def find_breakouts_for_trade(
    data: dict[str, Any],
    one_minute_bars: list[common.objects.BarData],
    one_minute_timeframe_stock: common.objects.Stock,
) -> list[BreakoutResult]:
    """
    Finds only clean breakouts by the new logic.

    No resistance zones.
    No fake-breakout classification.
    Only rows where _is_valid_breakout(...) returns True are written.
    """

    results: list[BreakoutResult] = []

    bars = sorted(
        one_minute_bars,
        key=lambda bar: bar.bar_time,
    )

    if len(bars) < 15:
        return results

    for i in range(10, len(bars)):
        current_bar = bars[i]

        market_open_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=9,
            minute=30,
        )

        market_close_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=16,
        )

        if current_bar.bar_time <= market_open_time or current_bar.bar_time >= market_close_time:
            continue

        if not _is_valid_breakout(
            potential_confirmation_bar=current_bar,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
        ):
            continue

        results.append(
            build_breakout_result(
                data=data,
                bars=bars,
                bar_index=i,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
            )
        )

    return results


def write_breakout_results_to_csv(
    results: list[BreakoutResult],
    output_file_path: str,
    desc: str,
) -> None:
    fieldnames = list(BreakoutResult.__dataclass_fields__.keys())

    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in tqdm.tqdm(results, desc=desc):
            writer.writerow(asdict(result))

    print(f"Wrote {len(results)} breakout rows to: {output_file_path}")

def find_breakouts(data: dict[str, Any], index: int, total_length: int) -> FindBreakoutsResult:
    specific_bar_time: datetime.datetime = data["day_timeframe_stock"].specific_bar_time
    is_positive: bool = data["day_timeframe_stock"].is_positive

    one_minute_bars: list[common.objects.BarData] = [
        bar_object
        for bar_object in data["one_minute_timeframe_stock"].bars
        if bar_object.bar_time.date() == specific_bar_time.date()
    ]

    trade_breakouts = find_breakouts_for_trade(
        data=data,
        one_minute_bars=one_minute_bars,
        one_minute_timeframe_stock=data["one_minute_timeframe_stock"],
    )

    print(f"finished gathering breakouts for: {data['day_timeframe_stock'].symbol_name}. {index}/{total_length}. completed: {(index / total_length) * 100:.2f}%")

    return FindBreakoutsResult(
        breakouts=trade_breakouts,
        is_positive=is_positive,
    )


if __name__ == '__main__':
    training_model_data_list = load_data_for_training_model()

    positive_breakout_results: list[BreakoutResult] = []
    false_positive_breakout_results: list[BreakoutResult] = []

    futures = []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=20,
    ) as executor:
        for i, data in enumerate(training_model_data_list):
            f = executor.submit(
                find_breakouts,
                data,
                i,
                len(training_model_data_list),
            )
            futures.append(f)

    for future in concurrent.futures.as_completed(futures):
        find_breakouts_result: FindBreakoutsResult = future.result()
        if find_breakouts_result.is_positive:
            positive_breakout_results.extend(find_breakouts_result.breakouts)
        else:
            false_positive_breakout_results.extend(find_breakouts_result.breakouts)

    write_breakout_results_to_csv(
        results=positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_positive.csv",
        desc="write_positive_breakout_results_to_csv",
    )

    write_breakout_results_to_csv(
        results=false_positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_false_positive.csv",
        desc="write_false_positive_breakout_results_to_csv",
    )

    print("")
    print("Done.")
    print(f"Positive breakout rows: {len(positive_breakout_results)}")
    print(f"False-positive breakout rows: {len(false_positive_breakout_results)}")
