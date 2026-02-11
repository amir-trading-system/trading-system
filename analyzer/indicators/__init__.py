from . import indicator

from . import case_1

__indicators__ : list[type[indicator.Indicator]] = [
    case_1.Indicator,
]
