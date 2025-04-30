// This Pine Script® code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © amiryaffe

//@version=6
indicator(title="Enter / Exit Position", overlay = true)
import TradingView/ta/10

last_bars = 4
positive_sign = "✅"
negative_sign = "👮‍♂️"

////           Negative indications           ////

current_bar_is_negative(index) =>
    close[index] < open[index]

current_bar_volume_is_high_than_usual(index) =>
    vol_avg = ta.sma(volume, 20)
    volume_higher = volume[index] > vol_avg * 2

    volume_higher and volume[index] > volume[index+1]

current_bar_deletes_most_of_value_before(last_bars, index) =>
    last_highest = ta.highest(high[index], last_bars)
    last_lowest = ta.lowest(low[index], last_bars)
    volume_higher = current_bar_volume_is_high_than_usual(index)
    current_bar_is_negative = current_bar_is_negative(index)

    length = last_highest - last_lowest
    current_bar_length = high[index] - low[index]

    current_bar_length / length > 0.5 and current_bar_is_negative and volume_higher

current_bar_is_weak(index, close_src, open_src) =>
    nine_ema = ta.ema(close_src, 9)
    volume_higher = current_bar_volume_is_high_than_usual(index)
    current_bar_is_negative = current_bar_is_negative(index)
    (close_src[index] < nine_ema or open_src[index] < nine_ema) and current_bar_is_negative and volume_higher

current_bar_makes_new_low(index) =>
    volume_higher = current_bar_volume_is_high_than_usual(index)
    current_bar_is_negative = current_bar_is_negative(index)
    low[index] < ta.lowest(low[index+1], 5) and current_bar_is_negative and volume_higher

current_bar_crosses_nine_ema(index, close_src, open_src) =>
    nine_ema = ta.ema(close_src, 9)
    twenty_ema = ta.ema(close_src, 20)

    vol_avg = ta.sma(volume, 20)
    volume_higher_than_avg = volume[index] > vol_avg

    open_src[index] > nine_ema and close_src[index] < nine_ema and volume_higher_than_avg

current_bar_dropped_its_majority_value(index) =>
    is_green_bar = close[index] > open[index]
    threshold = 0.2
    bar_is_weak = false

    if is_green_bar
        bar_is_weak := (close[index] - low[index]) / (high[index] - low[index]) < threshold
    else
        bar_is_weak := (open[index] - low[index]) / (high[index] - low[index]) < threshold

    bar_is_weak

run_negative_indicator(index) =>
    current_bar_is_weak(index, close[index], open[index])
      or current_bar_makes_new_low(index)
      or current_bar_deletes_most_of_value_before(last_bars, index)
      or current_bar_crosses_nine_ema(index, close[index], open[index])
      or current_bar_dropped_its_majority_value(index)

////           Positive indications           ////

current_bar_is_bullish(high_src, close_src, low_src) =>
    high_src - close_src < close_src - low_src

current_bar_volume_is_higher_than_last_ones(last_bars, close_src, open_src, volume_src, index) =>
    sum_of_buyers = 0.0
    sum_of_sellers = 0.0
    volume_is_higher_than_last_ones = true
    for i = 1 to last_bars
        if close_src[index + i] > open_src[index + i]
            sum_of_buyers += volume_src[index + i]
            continue
        else
            sum_of_sellers += volume_src[index + i]
            if volume_src[index + i] > volume_src
                volume_is_higher_than_last_ones := false

    volume_is_higher_than_last_ones or (sum_of_buyers > sum_of_sellers)

current_bar_is_above_vwap(vwap_src, close_src, high_src) =>
    close_src > vwap_src and high_src > vwap_src

last_bars_emas_higher(last_bars, ema_9_src, ema_20_src, ema_200_src, vwap_src, open_src, index) =>
    last_bars_emas_higher = true
    for i = 0 to last_bars
        if not (math.max(ema_9_src[index + i], ema_20_src[index + i], ema_200_src[index + i]) == ema_9_src[index + i])
            last_bars_emas_higher := false
            break

    rounded_vwap = (math.round(vwap_src * 100) / 100)
    rounded_9_ema = (math.round(ema_9_src * 100) / 100)
    rounded_open = (math.round(open_src * 100) / 100)

    last_bars_emas_higher and rounded_9_ema >= rounded_vwap and rounded_open > rounded_vwap

buyers_coming_in(last_bars, close_src, open_src, volume_src, index) =>
    red_bars_volume = 0.0
    green_bars_volume = 0.0

    for i = 0 to last_bars
        bar_is_negative = close_src[index + i] < open_src[index + i]
        if bar_is_negative
            red_bars_volume += volume_src[index + i]
        else
            green_bars_volume += volume_src[index + i]

    green_bars_volume / red_bars_volume > 0.75

current_bar_has_new_high(high_src, index) =>
    high_src > ta.highest(high_src[1], 5)[index]

inside_momentum(last_bars, close_src, open_src, volume_src, index) =>
    under_avg_vol_bars_counter = 0
    above_avg_vol_bars_counter = 0
    vol_avg = ta.sma(volume_src[last_bars], 20)[index]
    current_bar_volume_is_higher_than_last_ones = current_bar_volume_is_higher_than_last_ones(last_bars, close_src, open_src, volume_src, index)

    for i = 0 to last_bars
        if close_src < open_src
            under_avg_vol_bars_counter += 1
        else if current_bar_volume_is_higher_than_last_ones
            above_avg_vol_bars_counter += 1

    above_avg_vol_bars_counter > under_avg_vol_bars_counter and volume_src > vol_avg

current_bar_must_be_positive_and_volatile(last_bars, low_src, high_src, volume_src, close_src, open_src, index) =>
    current_bar_volume_is_higher_than_last_ones = current_bar_volume_is_higher_than_last_ones(last_bars, close_src, open_src, volume_src, index)
    rounded_low = math.round(low_src * 100) / 100
    rounded_high = math.round(high_src * 100) / 100
    vol_avg = ta.sma(volume_src, 20)[index]
    close_src > open_src and volume_src > vol_avg and current_bar_volume_is_higher_than_last_ones

current_bar_closes_where_buyers_still_in(close_src, low_src, high_src) =>
    close_src - low_src > high_src - close_src

current_bar_has_at_least_one_weak_bar_before(last_bars, close_src, open_src, high_src, low_src, index) =>
    has_weak_bar_before = false

    for i = 1 to last_bars
        if close_src[index+i] < open_src[index+i] or ((high_src[index+i] - close_src[index+i]) >= close_src[index+i] - low_src[index+i])
            has_weak_bar_before := true
            break
    has_weak_bar_before

current_bar_is_above_support_line(last_bars, low_src, index) =>
    current_bar_above_support_line = true
    for i = 1 to last_bars
        if low_src < low_src[index + i] - 2
            current_bar_above_support_line := false
            break
    current_bar_above_support_line

current_bar_close_to_nine_ema_by_avg(last_bars, close_src, low_src, ema_9, ema_20, index) =>
    current_bar_close_to_nine_ema_by_avg = false
    sum_ema_distances = 0.0

    for i = last_bars to 1
        sum_ema_distances += low_src[index + i] - ema_9[index + i]

    last_bars_ema_avg = sum_ema_distances / last_bars

    (low_src - ema_9 < last_bars_ema_avg or ema_9 - close_src < last_bars_ema_avg) or (low_src > ema_20 and low_src < ema_9)

current_bar_bigger_than_last_red_candle_body(last_bars, close_src, open_src, index) =>
    current_bar_bigger = true
    for i = 1 to last_bars
        if close_src[index + i] > open_src[index + i]
            continue
        else if open_src[index + i] - close_src[index + i] > close_src - open_src
            current_bar_bigger := false
            break

    current_bar_bigger

current_bar_macd_is_positive(close_src, index) =>
    [macdLine, signalLine, histogram] = ta.macd(close_src, 12, 26, 9)

    macd_current_is_positive = macdLine[index] > 0 and macdLine[index] > signalLine[index] and histogram[index] > 0
    if not macd_current_is_positive
        false

    macd_crossed_recently = false

    macd_crossed_down = ta.crossunder(macdLine,signalLine)
    macd_crossed_up = ta.crossover(macdLine,signalLine)
    var bool had_cross_under = false
    var bool pattern_detected = false

    if macd_crossed_down
        had_cross_under := true
        pattern_detected := false

    if macd_crossed_up and had_cross_under
        pattern_detected := true
        had_cross_under := false

    macd_is_still_strong_after_going_down = macdLine[index] > 0 and histogram[index] > 0.01 and pattern_detected

    for i = 1 to 5
        if macd_current_is_positive and histogram[index+i] <= 0.01 and macd_is_still_strong_after_going_down
            macd_crossed_recently := true

    macd_current_is_positive and macd_crossed_recently

current_bar_gets_50_percent_above_9_ema(close_src, low_src, ema_9) =>
    close_src - ema_9 > ema_9 - low_src

last_bars_volume_is_higher(index, last_bars) =>
    minimum_volume_per_bar_in_momentum = 1000
    volume_is_higher = true

    for i = 1 to 5
        if volume[index+i] < minimum_volume_per_bar_in_momentum
            volume_is_higher := false
            break

    volume_is_higher

no_bearish_bar_detected_in_the_last_bars(last_bars) =>
    // need to run on the last bars and check for no bearish bar.
    at_leaast_one_bar_is_weak = false
    for i = 1 to last_bars
        at_leaast_one_bar_is_weak := run_negative_indicator(i)
        if at_leaast_one_bar_is_weak
            break

    not at_leaast_one_bar_is_weak

///////// run indicators /////////

run_positive_indicator(i) =>
    vwap_index = ta.vwap(hlc3)[i]
    ema_9_index = ta.ema(close, 9)[i]
    ema_20_index = ta.ema(close, 20)[i]
    ema_200_index = ta.ema(close, 200)[i]

    open_index = open[i]
    close_index = close[i]
    high_index = high[i]
    low_index = low[i]
    volume_index = volume[i]

    current_bar_is_above_vwap = current_bar_is_above_vwap(vwap_index, close_index, high_index)
    last_bars_emas_higher = last_bars_emas_higher(last_bars, ema_9_index, ema_20_index, ema_200_index, vwap_index, open_index, i)
    current_bar_has_new_high = current_bar_has_new_high(high_index, i)
    buyers_coming_in = buyers_coming_in(last_bars, close_index, open_index, volume_index, i)
    inside_momentum = inside_momentum(last_bars, close_index, open_index, volume_index, i)
    current_bar_has_at_least_one_weak_bar_before = current_bar_has_at_least_one_weak_bar_before(last_bars, close_index, open_index, high_index, low_index, i)
    current_bar_must_be_positive_and_volatile = current_bar_must_be_positive_and_volatile(last_bars, low_index, high_index, volume_index, close_index, open_index, i)
    current_bar_is_above_support_line = current_bar_is_above_support_line(3, low_index, i)
    current_bar_close_to_nine_ema_by_avg = current_bar_close_to_nine_ema_by_avg(last_bars, close_index, low_index, ema_9_index, ema_20_index, i)
    current_bar_bigger_than_last_red_candle_body = current_bar_bigger_than_last_red_candle_body(last_bars, close_index, open_index, i)
    current_bar_macd_is_positive = current_bar_macd_is_positive(close_index, i)
    current_bar_gets_50_percent_above_9_ema = current_bar_gets_50_percent_above_9_ema(close_index, low_index, ema_9_index)
    current_bar_closes_where_buyers_still_in = current_bar_closes_where_buyers_still_in(close_index, low_index, high_index)
    current_bar_is_bullish = current_bar_is_bullish(high_index, close_index, low_index)
    last_bars_volume_is_higher = last_bars_volume_is_higher(i, last_bars)
    no_bearish_bar_detected_in_the_last_bars = no_bearish_bar_detected_in_the_last_bars(last_bars)

    current_bar_is_above_vwap
      and last_bars_emas_higher
      and current_bar_has_new_high
      and buyers_coming_in
      and inside_momentum
      and current_bar_has_at_least_one_weak_bar_before
      and current_bar_must_be_positive_and_volatile
      and current_bar_is_above_support_line
      and current_bar_close_to_nine_ema_by_avg
      and current_bar_bigger_than_last_red_candle_body
      and current_bar_macd_is_positive
      and current_bar_gets_50_percent_above_9_ema
      and current_bar_closes_where_buyers_still_in
      and current_bar_is_bullish
      and last_bars_volume_is_higher
      and no_bearish_bar_detected_in_the_last_bars

positive_indication = run_positive_indicator(0)
negative_inidcation = run_negative_indicator(0)

plotshape(positive_indication, title="Positive indication", color=color.green, display = display.all, style = shape.arrowup, size = size.small, location = location.belowbar, text = positive_sign)
plotshape(negative_inidcation, title="Negative indication", color=color.red, display = display.all, style = shape.arrowdown, size = size.small, location = location.abovebar, text = negative_sign)
