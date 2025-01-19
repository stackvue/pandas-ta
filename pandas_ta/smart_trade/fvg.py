# -*- coding: utf-8 -*-
from math import copysign

from pandas import DataFrame

from pandas_ta.trend import increasing, decreasing
from pandas_ta.utils import get_offset, verify_series


def fvg(open_, high, low, close, peak, mode, offset=None, **kwargs):
    """Indicator: FVG"""
    # Validate Arguments
    opens = verify_series(open_).shift()
    closes = verify_series(close).shift()
    high = verify_series(high)
    low = verify_series(low)
    peak = verify_series(peak)
    seq = (close - open_).apply(lambda x: copysign(1, x)).rolling(3).sum()


    offset = get_offset(offset)
    mode = int(mode)
    if mode > 0:
        highs = high.shift(2)
        active = ((closes > low) & (low > highs) & (highs > opens) & (seq == 3) & increasing(high, length=3, strict=True, asint=False))
        h = low.where(active)
        l = highs.where(active)
        p = peak.groupby(active.astype(int).cumsum()).cummax()
    elif mode < 0:
        lows = low.shift(2)
        active = ((closes < high) & (high < lows) & (lows < opens) & (seq == -3) & decreasing(low, length=3, strict=True, asint=False))
        h = lows.where(active)
        l = high.where(active)
        p = peak.groupby(active.astype(int).cumsum()).cummin()

    h.fillna(method="ffill", inplace=True)
    l.fillna(method="ffill", inplace=True)
    p.fillna(method="ffill", inplace=True)

    # Offset
    if offset != 0:
        h = h.shift(offset)
        l = l.shift(offset)
        p = p.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        h.fillna(kwargs["fillna"], inplace=True)
        l.fillna(kwargs["fillna"], inplace=True)
        p.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        h.fillna(method=kwargs["fill_method"], inplace=True)
        l.fillna(method=kwargs["fill_method"], inplace=True)
        p.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    h.name = f"FVGH_{mode}"
    h.category = "smart-trade"
    l.name = f"FVGL_{mode}"
    l.category = "smart-trade"
    p.name = f"PVGP_{mode}"
    p.category = "smart-trade"

    df = DataFrame({
        f"FVGH_{mode}": h,
        f"FVGL_{mode}": l,
        f"FVGP_{mode}": p,
    }, index=close.index)

    df.name = f"FVG_{mode}"
    df.category = "smart-trade"

    return df


fvg.__doc__ = \
    """Fair Value Gaps (FVG)
    
    The Fair Value Gaps defines the gaps in the supply and demand.
    
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
        open_ (pd.Series): Series of 'open's
        close (pd.Series): Series of 'close's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        peak (pd.Series): Series of 'peak's
        mode (int): Direction (1:Buy, -1:Sell, 0: Both)
        offset (int): How many periods to offset the result. Default: 0
        
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.DataFrame: FH (high), FL (low), FP (peak).
    """
