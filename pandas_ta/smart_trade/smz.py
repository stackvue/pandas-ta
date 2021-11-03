# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def smz(high, low, length=None, offset=None, **kwargs):
    """Indicator: Simple Moving Zone (SMZ)"""
    # Validate Arguments
    high = verify_series(high)
    low = verify_series(low)
    length = int(length) if length and length > 0 else 10
    min_periods = int(kwargs["min_periods"]) if "min_periods" in kwargs and kwargs["min_periods"] is not None else length
    offset = get_offset(offset)

    # Calculate Result
    smh = high.rolling(length, min_periods=min_periods).max()
    sml = low.rolling(length, min_periods=min_periods).min()

    # Offset
    if offset != 0:
        smh = smh.shift(offset)
        sml = sml.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        smh.fillna(kwargs["fillna"], inplace=True)
        sml.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        smh.fillna(method=kwargs["fill_method"], inplace=True)
        sml.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    smh.name = f"SMH_{length}"
    smh.category = "smart-trade"
    sml.name = f"SML_{length}"
    sml.category = "smart-trade"

    df = DataFrame({
            f"SMH_{length}": smh,
            f"SML_{length}": sml,
        }, index=high.index)

    df.name = f"SMZ{length}"
    df.category = "smart-trade"


    return df


smz.__doc__ = \
"""Simple Moving Zone (SMA)

The Simple Moving Zone is the classic moving high low zone over n periods.

Sources:
    https://smart-trade.reluminos.com

Calculation:
    Default Inputs:
        length=10
    SMH = MAX(close, length)
    SML = MIN(close, length)

Args:
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    length (int): It's period. Default: 10
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: SMH (highzone), SML (lowzone).
"""
