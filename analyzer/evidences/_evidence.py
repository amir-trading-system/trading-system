import common

class Evidence:
    name: str = ""
    must_to_be_true: bool = False
    is_base_evidence: bool = False

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        raise NotImplementedError()

    def get_resistance_levels(
        self,
        stock: common.objects.Stock,
        relevant_bars: list[common.objects.BarData],
        current_bar: common.objects.BarData,
    ) -> dict[float, int]:
        resistance_level_to_breaking_attempts: dict[float, int] = {}
        for bar_object in relevant_bars[:current_bar.index+40]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )

            high_pattern_one = (
                True
                and bar_object.high > bar_object.close
                and bar_object.high > bar_object.open_value
                and (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) >= 0.1
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and bar_object.high > bar_object.vwap
                and previous_bar is not None
                and previous_bar.high < bar_object.high
            )
            high_pattern_two = (
                True
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high > next_bar.high
                and bar_object.volume > bar_object.volume_average
            )

            if (
                True
                and (high_pattern_one or high_pattern_two)
            ):
                if not resistance_level_to_breaking_attempts.get(bar_object.high):
                    resistance_level_to_breaking_attempts[bar_object.high] = 1
                else:
                    resistance_level_to_breaking_attempts[bar_object.high] += 1

        resistance_levels = sorted(resistance_level_to_breaking_attempts.keys())
        for i, resistance_level in enumerate(resistance_levels):
            if i+1 > len(resistance_levels) - 1:
                continue

            if  resistance_level/resistance_levels[i+1] >= 0.95:
                attempts = resistance_level_to_breaking_attempts.pop(resistance_level)
                resistance_level_to_breaking_attempts[resistance_levels[i+1]] += attempts

        return resistance_level_to_breaking_attempts

    def crossed_resistance_level_strongly(
        self,
        resistance_levels: list[float],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        return any(
            resistance_level
            for resistance_level in resistance_levels
            if resistance_level < potential_confirmation_bar.close
            and resistance_level > potential_confirmation_bar.open_value
            and (potential_confirmation_bar.close - resistance_level)/(resistance_level - potential_confirmation_bar.open_value) >= 0.25
        ) and not any(
            resistance_level
            for resistance_level in resistance_levels
            if resistance_level > potential_confirmation_bar.high
            and potential_confirmation_bar.high/resistance_level >= 0.8
        )

    def confirm(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute: float,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        raise NotImplementedError()
