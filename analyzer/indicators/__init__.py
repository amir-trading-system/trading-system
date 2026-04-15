from . import indicator

from . import case_1
from . import case_2
from . import case_3
from . import case_4
from . import case_5
from . import case_6
from . import case_7
from . import case_8
from . import case_9
from . import case_10

__indicators__ : list[type[indicator.Indicator]] = [
    case_1.Indicator,
    case_2.Indicator,
    case_3.Indicator,
    case_4.Indicator,
    case_5.Indicator,
    case_6.Indicator,
    case_7.Indicator,
    case_8.Indicator,
    case_9.Indicator,
    case_10.Indicator,
]
