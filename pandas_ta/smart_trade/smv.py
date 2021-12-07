# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def smv(close, length=None, offset=None, **kwargs):
    """Indicator: Simple Moving Volatility (SMV)"""
    # Validate Arguments
    close = verify_series(close)
    length = int(length) if length and length > 0 else 10
    min_periods = int(kwargs["min_periods"]) if "min_periods" in kwargs and kwargs["min_periods"] is not None else length
    offset = get_offset(offset)

    # Calculate Result
    close_before = close.shift(1)
    close_diff = (close - close_before)
    pos = close_diff.where(close_diff > 0).fillna(0).rolling(length, min_periods=min_periods).sum()
    neg = -1 * close_diff.where(close_diff < 0).fillna(0).rolling(length, min_periods=min_periods).sum()
    smv = pos / (pos + neg)

    # Offset
    if offset != 0:
        smv = smv.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        smv.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        smv.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    smv.name = f"SMV_{length}"
    smv.category = "smart-trade"

    df = DataFrame({
            f"SMV_{length}": smv,
        }, index=close.index)

    df.name = f"SMV{length}"
    df.category = "smart-trade"


    return df


smv.__doc__ = \
"""Simple Moving Volatility (SMV)

The Simple Moving Zone is the classic moving high low zone over n periods.

Sources:
    https://smart-trade.reluminos.com

Calculation:
    Default Inputs:
        length=10
    SMV = ROLLING(close, length)

Args:
    close (pd.Series): Series of 'close's
    length (int): It's period. Default: 10
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: SMV (highzone)
"""
