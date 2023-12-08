# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.trend import increasing, decreasing
from pandas_ta.utils import get_offset, verify_series


def fractal(close, high, low, highs, lows, head=2, tail=2, strict=True, offset=None, **kwargs):
    """Indicator: FRACTAL"""
    # Validate Arguments
    close = verify_series(close)
    high = verify_series(high)
    low = verify_series(low)

    offset = get_offset(offset)

    highs = verify_series(highs)
    lows = verify_series(lows)

    higherclose = increasing(close, length=tail, strict=strict, offset=head-1, asint=False) & decreasing(close, length=head, strict=strict, asint=False)
    higherhigh = increasing(high, length=tail, strict=strict, offset=head-1, asint=False) & decreasing(high, length=head, strict=strict, asint=False)
    lowerclose = decreasing(close, length=tail, strict=strict, offset=head-1, asint=False) & increasing(close, length=head, strict=strict, asint=False)
    lowerlow = decreasing(low, length=tail, strict=strict, offset=head-1, asint=False) & increasing(close, length=head, strict=strict, asint=False)

    sth = higherclose & higherhigh
    stl = lowerclose & lowerlow

    h = highs.shift(head-1).where(sth).fillna(method="ffill")
    l = lows.shift(head-1).where(stl).fillna(method="ffill")
    z = sth.astype(int) + (-1*(stl.astype(int)))

    # Offset
    if offset != 0:
        h = h.shift(offset)
        l = l.shift(offset)
        z = z.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        h.fillna(kwargs["fillna"], inplace=True)
        l.fillna(kwargs["fillna"], inplace=True)
        z.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        h.fillna(method=kwargs["fill_method"], inplace=True)
        l.fillna(method=kwargs["fill_method"], inplace=True)
        z.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    h.name = f"FRACTALH_{head}_{tail}"
    h.category = "smart-trade"
    l.name = f"FRACTALL_{head}_{tail}"
    l.category = "smart-trade"
    z.name = f"FRACTALZ_{head}_{tail}"
    z.category = "smart-trade"

    df = DataFrame({
        f"FRACTALH_{head}_{tail}": h,
        f"FRACTALL_{head}_{tail}": l,
        f"FRACTALZ_{head}_{tail}": z,
    }, index=close.index)

    df.name = f"FRACTAL_{head}_{tail}"
    df.category = "smart-trade"

    return df


fractal.__doc__ = \
    """Fractals (SP)
    
    The Fractals is the Short term Pivots over {head} and {tail} periods.
    
    Sources:
        https://smart-trade.reluminos.com
    
    Calculation:
        Default Inputs:
            head=2
            tail=2
            strict=True
        FRACTALH = Fractal High Pivot
        FRACTALL = Fractal Low Pivot
        FRACTALZ = Pivot Direction
    
    Args:
        close (pd.Series): Series of 'close's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        highs (pd.Series): Series of 'high's for band
        lows (pd.Series): Series of 'low's for band
        head (int): It's look ahead. Default: 2
        tail (int): It's look before. Default: 2
        strict(bool): If True, checks if the series is continuously increasing/decreasing over the period. Default: True
        offset (int): How many periods to offset the result. Default: 0
        
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.DataFrame: FH (highpivot), FL (lowpivot), FZ (pivotdirection).
    """
