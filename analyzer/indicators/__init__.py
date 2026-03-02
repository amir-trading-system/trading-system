from . import indicator

from . import case_1
from . import case_2
from . import case_3
from . import case_4
from . import case_5
from . import case_6

__indicators__ : list[type[indicator.Indicator]] = [
    case_1.Indicator,
    case_2.Indicator,
    case_3.Indicator,
    case_4.Indicator,
    case_5.Indicator,
    # case_6.Indicator,
]
