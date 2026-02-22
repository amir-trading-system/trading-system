import common

class Evidence:
    name: str = ""
    must_to_be_true: bool = False
    is_base_evidence: bool = False
    relevant_bars: list[common.objects.BarData] = []

    def is_potential_starting_bar(
        self,
        stock: common.objects.Stock,
        bar_object: common.objects.BarData,
    ) -> bool:
        base_condition = True
        previous_bar = stock.previous_bar(
            bar_object=bar_object,
        )
        if previous_bar is not None:
            base_condition = (
                True
                and base_condition
                and previous_bar is not None
                and bar_object.high > previous_bar.high
            )

        first_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.close > bar_object.ema_9
            and bar_object.close > bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
            and bar_object.volume > 500000
            and bar_object.high > bar_object.vwap
            and bar_object.ema_9/bar_object.low >= 0.9
        )
        second_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.high > bar_object.vwap
            and bar_object.close > bar_object.ema_9
            and bar_object.histogram > 0
            and bar_object.volume/bar_object.volume_average > 7
            and max(
                stock.bars[bar_object.index:],
                key=lambda bar_obj: bar_obj.volume
            ) == bar_object
        )

        return first_option or second_option

    def get_starting_bar(
        self,
        stock: common.objects.Stock,
    ) -> common.objects.MilestoneBar | None:
        for bar_object in self.relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            potential_starting_bar = (
                True
                and self.is_potential_starting_bar(
                    stock=stock,
                    bar_object=bar_object
                )
                and (
                    not self.is_potential_starting_bar(
                        stock=stock,
                        bar_object=previous_bar,
                    ) if previous_bar is not None else True
                )
            )
            if potential_starting_bar:
                if len(self.relevant_bars[:10]) > 0:
                    potential_starting_bar = max(
                        [
                            bar_obj.high
                            for bar_obj in self.relevant_bars[:10]
                        ]
                    ) == bar_object.high

                return common.objects.MilestoneBar(
                    index=bar_object.index,
                    bar_object=bar_object,
                    bar_type=common.objects.MilestoneType.STARTING_BAR,
                    bar_time=bar_object.bar_time,
                    timeframe=bar_object.timeframe,
                )

    def get_top_bar(
        self,
        starting_bar: common.objects.BarData,
        current_bar: common.objects.BarData,
    ) -> common.objects.MilestoneBar | None:
        top_bar_options = [
            bar_object
            for bar_object in self.relevant_bars[:starting_bar.index]
            if (
                True
                and bar_object.index > current_bar.index
                and bar_object.high > starting_bar.high
                and len(self.relevant_bars[1:starting_bar.index]) > 0
                and bar_object.high == max(
                    [
                        bar_obj.high
                        for bar_obj in self.relevant_bars[:starting_bar.index]
                        if bar_obj.index > current_bar.index
                    ]
                )
            )
        ]
        if len(top_bar_options) > 0:
            top_bar = top_bar_options[0]
            return common.objects.MilestoneBar(
                index=top_bar.index,
                bar_object=top_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=top_bar.bar_time,
                timeframe=top_bar.timeframe,
            )

    def stock_is_valid_for_evidence(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
    ) -> bool:
        self.relevant_bars = stock.bars[1:]
        if len(self.relevant_bars) == 0:
            return False

        stock.resistance_levels = self.get_resistance_levels(
            stock=stock,
            relevant_bars=self.relevant_bars,
            current_bar=current_bar,
        )

        return True

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
    ) -> list[common.objects.BarData]:
        resistance_levels: list[common.objects.BarData] = []
        for bar_object in relevant_bars[:current_bar.index+40]:
            if (
                bar_object.vwap is None
                or bar_object.ema_9 is None
                or bar_object.ema_20 is None
            ):
                continue

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
            )

            if (
                True
                and (high_pattern_one or high_pattern_two)
            ):
                resistance_level = [
                    r_l
                    for r_l in resistance_levels
                    if bar_object.high == r_l.high
                ]
                if not resistance_level:
                    resistance_levels.append(bar_object)

        resistance_levels = sorted(
            resistance_levels,
            key=lambda r_l: r_l.high,
        )
        temp_resistance_levels = [temp_r_l for temp_r_l in resistance_levels]
        for i, resistance_level in enumerate(temp_resistance_levels):
            if i+1 > len(resistance_levels) - 1:
                continue

            if resistance_level.high/resistance_levels[i+1].high >= 0.95:
                resistance_levels = [
                    r_l
                    for r_l in resistance_levels
                    if r_l.bar_time != resistance_level.bar_time
                ]

        return resistance_levels

    def crossed_resistance_level_strongly(
        self,
        resistance_levels: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        return any(
            resistance_level
            for resistance_level in resistance_levels
            if potential_confirmation_bar.low < resistance_level.high < potential_confirmation_bar.close
            and abs(resistance_level.high - potential_confirmation_bar.open_value) > 0
            and (potential_confirmation_bar.close - resistance_level.high)/abs(resistance_level.high - potential_confirmation_bar.open_value) >= 0.25
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.volume > 10000
            and not resistance_level.has_strong_rejection()
        ) and not any(
            resistance_level
            for resistance_level in resistance_levels
            if resistance_level.high > potential_confirmation_bar.high
        and potential_confirmation_bar.high/resistance_level.high >= 0.8
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
