from . import indicator

from . import case_1
from . import case_2
from . import case_3

__indicators__ : list[type[indicator.Indicator]] = [
    case_1.Indicator,
    case_2.Indicator,
    case_3.Indicator,
]
