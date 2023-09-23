# -*- coding: utf-8 -*-
import pandas as pd
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def sp(close, high, low, length=None, offset=None, **kwargs):
    """Indicator: Smart Pivot(SP)"""
    # Validate Arguments
    close = verify_series(close)
    high = verify_series(high)
    low = verify_series(low)
    length = int(length) if length and length > 0 else 1
    min_periods = int(kwargs["min_periods"]) if "min_periods" in kwargs and kwargs["min_periods"] is not None else 2*length+1
    offset = get_offset(offset)
    group_by = kwargs.get("anchor")
    # Calculate Result
    if group_by:
        grouper = pd.Grouper(freq=group_by)
        p_mins = close.groupby(grouper).transform(lambda s: s.rolling(2*length+1, min_periods=min_periods, center=True).min())
        p_maxs = close.groupby(grouper).transform(lambda s: s.rolling(2*length+1, min_periods=min_periods, center=True).max())
        s_mins = low.groupby(grouper).transform(lambda s: s.rolling(2*length+1, min_periods=min_periods, center=True).min())
        s_maxs = high.groupby(grouper).transform(lambda s: s.rolling(2*length+1, min_periods=min_periods, center=True).max())
    else:
        p_mins = close.rolling(2*length+1, min_periods=min_periods, center=True).min()
        p_maxs = close.rolling(2*length+1, min_periods=min_periods, center=True).max()
        s_mins = low.rolling(2*length+1, min_periods=min_periods, center=True).min()
        s_maxs = high.rolling(2*length+1, min_periods=min_periods, center=True).max()
    l_pivot = (close == p_mins) & (low == s_mins)
    h_pivot = (close == p_maxs) & (high == s_maxs)
    sph = close.where(h_pivot).shift(length).fillna(method='ffill')
    spl = close.where(l_pivot).shift(length).fillna(method='ffill')
    spp = (-1*l_pivot.astype(int) + h_pivot.astype(int)).shift(length)


    # Offset
    if offset != 0:
        sph = sph.shift(offset)
        spl = spl.shift(offset)
        spp = spp.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        sph.fillna(kwargs["fillna"], inplace=True)
        spl.fillna(kwargs["fillna"], inplace=True)
        spp.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        sph.fillna(method=kwargs["fill_method"], inplace=True)
        spl.fillna(method=kwargs["fill_method"], inplace=True)
        spp.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    sph.name = f"SPH_{length}"
    sph.category = "smart-trade"
    spl.name = f"SPL_{length}"
    spl.category = "smart-trade"
    spp.name = f"SPP_{length}"
    spp.category = "smart-trade"

    df = DataFrame({
            f"SPH_{length}": sph,
            f"SPL_{length}": spl,
            f"SPP_{length}": spp,
        }, index=close.index)

    df.name = f"SP{length}"
    df.category = "smart-trade"


    return df


sp.__doc__ = \
"""Smart Pivot (SP)

The Smart Pivot is the Short term Pivots over n periods.

Sources:
    https://smart-trade.reluminos.com

Calculation:
    Default Inputs:
        length=10
    SMH = Short Term High Pivot
    SML = Short Term Low Pivot
    SMP = Pivot Direction

Args:
    close (pd.Series): Series of 'close's
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    length (int): It's period. Default: 10
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: SPH (highpivot), SPL (lowpivot), SPP (pivotdirection).
"""
