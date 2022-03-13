from math import floor
from typing import Union


def decimal(s: str) -> float:
    """
    Convert a numeric string with spaces and possibly comma instead of the decimal into float
    """
    s = s.replace(' ', '')
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        raise ValueError(f'Error converting "{s}" to float')


def quantity(s: str) -> Union[float, int]:
    """
    Convert a numeric string into integer (if whole number) or float
    """
    f = decimal(s)
    if floor(f) == f:
        return int(f)

    return f
