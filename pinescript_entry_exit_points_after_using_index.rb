// This Pine Script® code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © amiryaffe

//@version=6
indicator(title="DayTrader: Momentum Confirmed", overlay = true)
import TradingView/ta/10

last_bars = 4
min_momentun_vol_avg = 5000
positive_sign = "✅"
negative_sign = "👮‍♂️"
buying_the_dip_sign = "📉🛒"

show_logs = input.bool(false, "Show Debug Logs")


////           Negative indications           ////

current_bar_is_negative(index) =>
    close[index] < open[index]

current_bar_volume_is_high_than_usual(index, volume_src) =>
    vol_avg = ta.sma(volume_src[index], 20)
    volume_higher = volume_src[index] > vol_avg * 2

    volume_higher and volume_src[index] > volume_src[index+1]

current_bar_deletes_most_of_value_before(last_bars, index, volume_src) =>
    last_highest = ta.highest(high[index], last_bars)
    last_lowest = ta.lowest(low[index], last_bars)
    volume_higher = current_bar_volume_is_high_than_usual(index, volume_src)
    current_bar_is_negative = current_bar_is_negative(index)

    length = last_highest - last_lowest
    current_bar_length = high[index] - low[index]

    current_bar_length / length > 0.5 and current_bar_is_negative and volume_higher

current_bar_is_weak(index, close_src, open_src, volume_src) =>
    nine_ema = ta.ema(close_src, 9)
    volume_higher = current_bar_volume_is_high_than_usual(index, volume_src)
    current_bar_is_negative = current_bar_is_negative(index)
    (close_src[index] < nine_ema or open_src[index] < nine_ema) and current_bar_is_negative and volume_higher

current_bar_makes_new_low(index, volume_src) =>
    volume_higher = current_bar_volume_is_high_than_usual(index, volume_src)
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
    current_bar_is_weak = current_bar_is_weak(index, close[index], open[index], volume[index])
    current_bar_makes_new_low = current_bar_makes_new_low(index, volume[index])
    current_bar_deletes_most_of_value_before = current_bar_deletes_most_of_value_before(last_bars, index, volume[index])
    current_bar_crosses_nine_ema = current_bar_crosses_nine_ema(index, close[index], open[index])
    current_bar_dropped_its_majority_value = current_bar_dropped_its_majority_value(index)

    current_bar_is_weak
      or current_bar_makes_new_low
      or current_bar_deletes_most_of_value_before
      or current_bar_crosses_nine_ema
      or current_bar_dropped_its_majority_value

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

current_ema_is_above_vwap(ema_9_src, vwap_src, open_src) =>
    rounded_vwap = (math.round(vwap_src * 100) / 100)
    rounded_9_ema = (math.round(ema_9_src * 100) / 100)
    rounded_open = (math.round(open_src * 100) / 100)

    rounded_9_ema >= rounded_vwap and rounded_open > rounded_vwap

last_bars_emas_higher(last_bars, ema_9_src, ema_20_src, vwap_src, index) =>
    last_bars_emas_higher = true
    for i = 0 to last_bars
        if not (math.max(ema_9_src[index + i], ema_20_src[index + i]) == ema_9_src[index + i])
            last_bars_emas_higher := false
            break

    rounded_vwap = (math.round(vwap_src * 100) / 100)
    rounded_9_ema = (math.round(ema_9_src * 100) / 100)

    last_bars_emas_higher

buyers_coming_in(last_bars, close_src, open_src, volume_src, index) =>
    vol_avg = ta.sma(volume_src[last_bars], 20)[index]
    sellers_are_still_in_the_game = false
    green_bars_volume = 0.0
    red_bars_volume = 0.0

    for i = 0 to last_bars
        bar_is_negative = close_src[index + i] < open_src[index + i]
        if bar_is_negative
            red_bars_volume += volume_src[i]
        else
            green_bars_volume += volume_src[i]
        if bar_is_negative and volume_src[i] > vol_avg
            sellers_are_still_in_the_game := true
            break

    negative_condition = sellers_are_still_in_the_game and (green_bars_volume / (green_bars_volume + red_bars_volume)) < 0.6

    not negative_condition

current_bar_has_new_high(high_src, index) =>
    high_src > ta.highest(high_src[1], 5)[index]

inside_momentum(last_bars, close_src, open_src, volume_src, index) =>
    under_avg_vol_bars_counter = 0
    above_avg_vol_bars_counter = 0
    vol_avg = ta.sma(volume_src[last_bars], 20)[index]
    current_bar_volume_is_higher_than_last_ones = current_bar_volume_is_higher_than_last_ones(last_bars, close_src, open_src, volume_src, index)

    for i = 0 to last_bars
        if vol_avg[i] < min_momentun_vol_avg
            under_avg_vol_bars_counter += 1
        else if close_src < open_src
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
    macd_current_is_positive = macdLine[index] > 0 and macdLine[index] > signalLine[index] and histogram[index] > 0.005

    macd_crossed_recently = false

    macd_crossed_down = ta.crossunder(macdLine[index],signalLine[index])
    macd_crossed_up = ta.crossover(macdLine[index],signalLine[index])
    var bool had_cross_under = false
    var bool pattern_detected = false

    if macd_crossed_down
        had_cross_under := true
        pattern_detected := false

    if macd_crossed_up and had_cross_under
        pattern_detected := true
        had_cross_under := false

    macd_is_still_strong_after_going_down = macd_current_is_positive and pattern_detected

    macd_crossed_last_bars = 10
    for i = 1 to macd_crossed_last_bars
        bar_before_is_weak_but_above_zero_line = histogram[index+i] <= 0.02 and macdLine[index+i] >= 0 and macdLine[index+i] - signalLine[index+i] < 0.02
        current_bar_is_strong = macdLine[index] > 0 and histogram[index] > 0.01
        if bar_before_is_weak_but_above_zero_line and current_bar_is_strong
            macd_crossed_recently := true
            break

    pre_market_start_time = timestamp("America/New_York", year, month, dayofmonth, 4, 1)
    relevant_market_start_time = timestamp("America/New_York", year, month, dayofmonth, 6, 1)
    highest_macdLine = ta.highestSince(relevant_market_start_time > time, macdLine[index])
    lowest_macdLine = ta.lowestSince(macdLine == highest_macdLine, macdLine[index])
    pre_market_highest_macdLine = ta.highestSince(pre_market_start_time > time, macdLine[index])
    macd_fixed_less_than_50_percent = lowest_macdLine/highest_macdLine >= 0.5
    macdLine_keep_up_growing = macd_fixed_less_than_50_percent and pre_market_highest_macdLine <= highest_macdLine

    macd_current_is_positive and macd_crossed_recently and macd_is_still_strong_after_going_down and macdLine_keep_up_growing

most_of_the_value_did_not_came_in_one_bar(index, high_src, low_src) =>
    relevant_market_start_time = timestamp("America/New_York", year, month, dayofmonth, 6, 1)
    highest_price = ta.highestSince(relevant_market_start_time > time, high_src)
    lowest_price = ta.lowestSince(relevant_market_start_time > time, low_src)
    highest_range = ta.highestSince(relevant_market_start_time > time, high_src - low_src)
    most_of_the_value_did_not_came_in_one_bar = highest_range / (highest_price - lowest_price) <= 0.6

    most_of_the_value_did_not_came_in_one_bar

current_bar_gets_50_percent_above_9_ema(close_src, low_src, ema_9) =>
    close_src - ema_9 > ema_9 - low_src

last_bars_volume_is_higher(index, last_bars, volume_src) =>
    vol_avg = ta.sma(volume_src, 20)[index]
    volume_average = 0.0
    for i = 0 to 5
        volume_average += vol_avg[i]

    minimum_volume_per_bar_in_momentum = 1000
    volume_is_higher = true

    for i = 1 to 5
        if volume[index+i] < minimum_volume_per_bar_in_momentum
            volume_is_higher := false
            break

    minimum_average_volume_per_bar = 0
    if timeframe.period == "1"
        minimum_average_volume_per_bar := 5000
    else
        minimum_average_volume_per_bar := 10000

    volume_is_higher and (volume_average / 5) > minimum_average_volume_per_bar

no_bearish_bar_detected_in_the_last_bars(last_bars) =>
    at_least_one_bar_is_weak = false
    for i = 1 to last_bars
        at_least_one_bar_is_weak := run_negative_indicator(i)
        if at_least_one_bar_is_weak
            break

    not at_least_one_bar_is_weak

last_biggest_volume_bar_was_green(volume_src, close_src, open_src, high_src, low_src, last_bars) =>
    highest_bar_volume = ta.highest(volume_src[1], last_bars)
    highest_volume_bar_is_green = false

    for i = 1 to last_bars
        if volume_src[i] == highest_bar_volume and close_src[i] > open_src[i] and ((high_src[i] - close_src[i]) / (high_src[i] - low_src[i]) < 0.6)
            highest_volume_bar_is_green := true
            break

    highest_volume_bar_is_green

///////// buying the dip indicators /////////
last_bars_crossed_9_ema_but_didnt_closed_under_it(index, close_src, low_src, high_src, last_bars, ema_9, ema_20) =>
    some_last_bars_closed_under_9_ema = false

    for i = 1 to last_bars
        closed_under_9_ema = close_src[index+i] < ema_9[index+i]
        closed_under_20_ema = close_src[index+i] < ema_20[index+i]
        if closed_under_9_ema and closed_under_20_ema
            some_last_bars_closed_under_9_ema := true
            break

    rounded_9_ema = (math.round(ema_9 * 100) / 100)
    rounded_low = (math.round(low_src * 100) / 100)
    rounded_close = (math.round(close_src * 100) / 100)

    low_is_stronger_than_9_ema_but_close = rounded_low[index] <= rounded_9_ema[index]
    low_is_stronger_than_9_ema_but_close and rounded_close[index] > rounded_9_ema[index] and not some_last_bars_closed_under_9_ema

current_bar_close_is_not_highest(index, high_src, close_src) =>
    last_highest_high = ta.highest(high_src[index+1], 10)
    close_src[index] <= last_highest_high

///////// run indicators /////////

run_positive_indicator(i) =>
    vwap_index = ta.vwap(hlc3)[i]
    ema_9_index = ta.ema(close, 9)[i]
    ema_20_index = ta.ema(close, 20)[i]

    open_index = open[i]
    close_index = close[i]
    high_index = high[i]
    low_index = low[i]
    volume_index = volume[i]

    current_bar_is_above_vwap = current_bar_is_above_vwap(vwap_index, close_index, high_index)
    last_bars_emas_higher = last_bars_emas_higher(last_bars, ema_9_index, ema_20_index, vwap_index, i)
    current_ema_is_above_vwap = current_ema_is_above_vwap(ema_9_index, vwap_index, open_index)
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
    last_bars_volume_is_higher = last_bars_volume_is_higher(i, last_bars, volume_index)
    no_bearish_bar_detected_in_the_last_bars = no_bearish_bar_detected_in_the_last_bars(last_bars)
    last_biggest_volume_bar_was_green = last_biggest_volume_bar_was_green(volume_index, close_index, open_index, high_index, low_index, 5)
    most_of_the_value_did_not_came_in_one_bar = most_of_the_value_did_not_came_in_one_bar(i, high_index, low_index)

    current_bar_is_above_vwap
      and last_bars_emas_higher
      and current_ema_is_above_vwap
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
      and last_biggest_volume_bar_was_green
      and most_of_the_value_did_not_came_in_one_bar

run_buying_the_dip_indication(i) =>
    vwap_index = ta.vwap(hlc3)[i]
    ema_9_index = ta.ema(close, 9)[i]
    ema_20_index = ta.ema(close, 20)[i]

    open_index = open[i]
    close_index = close[i]
    high_index = high[i]
    low_index = low[i]
    volume_index = volume[i]

    last_bars_crossed_9_ema_but_didnt_closed_under_it = last_bars_crossed_9_ema_but_didnt_closed_under_it(i, close_index, low_index, high_index, 2, ema_9_index, ema_20_index)
    current_bar_close_is_not_highest = current_bar_close_is_not_highest(i, high_index, close_index)
    current_bar_is_above_vwap = current_bar_is_above_vwap(vwap_index, close_index, high_index)
    last_bars_emas_higher = last_bars_emas_higher(last_bars, ema_9_index, ema_20_index, vwap_index, i)
    current_bar_has_new_high = current_bar_has_new_high(high_index, i)
    current_bar_has_at_least_one_weak_bar_before = current_bar_has_at_least_one_weak_bar_before(last_bars, close_index, open_index, high_index, low_index, i)
    current_bar_must_be_positive_and_volatile = current_bar_must_be_positive_and_volatile(last_bars, low_index, high_index, volume_index, close_index, open_index, i)
    current_bar_volume_is_high_than_usual = current_bar_volume_is_high_than_usual(i, volume_index)

    last_bars_crossed_9_ema_but_didnt_closed_under_it
      and current_bar_close_is_not_highest
      and current_bar_is_above_vwap
      and last_bars_emas_higher
      and current_bar_has_new_high
      and current_bar_has_at_least_one_weak_bar_before
      and current_bar_must_be_positive_and_volatile
      and current_bar_volume_is_high_than_usual

positive_indication = run_positive_indicator(0)
negative_inidcation = run_negative_indicator(0)

is_long_term_minute_chart = timeframe.period == "15" or timeframe.period == "5"
buying_the_dip_indication = run_buying_the_dip_indication(0) and is_long_term_minute_chart

plotshape(positive_indication, title="Positive indication", color=color.green, display = display.pane, style = shape.arrowup, size = size.small, location = location.belowbar, text = positive_sign)
plotshape(negative_inidcation, title="Negative indication", color=color.red, display = display.pane, style = shape.arrowdown, size = size.small, location = location.abovebar, text = negative_sign)
plotshape(buying_the_dip_indication, title="Buying The Dip indication", color=color.green, display = display.pane, style = shape.arrowup, size = size.small, location = location.belowbar, text = buying_the_dip_sign)
