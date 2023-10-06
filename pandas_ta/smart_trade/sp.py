# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def sp(close, high, low, length=None, offset=None, **kwargs):
    """Indicator: Smart Pivot(SP)"""
    # Validate Arguments
    close = verify_series(close)
    high = verify_series(high)
    low = verify_series(low)
    length = int(length) if length and length > 0 else 1
    min_periods = int(kwargs["min_periods"]) if "min_periods" in kwargs and kwargs[
        "min_periods"] is not None else 2 * length + 1
    offset = get_offset(offset)
    ask = kwargs.get("ask", 0) or length
    # Calculate Result

    df = DataFrame({"close": close, "high": high, "low": low, })
    df["low_after"] = df["low_before"] = df["high_after"] = df["high_before"] = 0
    for i in range(1, length + 1):
        minus_i = -1 * i
        df["high_before"] += ((df["close"] > df["close"].shift(i)) & (df["high"] > df["high"].shift(i))).astype(int)
        df["high_after"] += (
                (df["close"] > df["close"].shift(minus_i)) & (df["high"] > df["high"].shift(minus_i))).astype(int)
        df["low_before"] += ((df["close"] < df["close"].shift(i)) & (df["low"] < df["low"].shift(i))).astype(int)
        df["low_after"] += ((df["close"] < df["close"].shift(minus_i)) & (df["low"] < df["low"].shift(minus_i))).astype(
            int)

    df["h_pivot"] = (df["high_before"] >= ask) & (df["high_after"] >= ask)
    df["l_pivot"] = (df["low_before"] >= ask) & (df["low_after"] >= ask)
    df["sph"] = df["close"].where(df["h_pivot"]).fillna(method='ffill').shift(length)
    df["spl"] = df["close"].where(df["l_pivot"]).fillna(method='ffill').shift(length)
    df["lpb"] = df["close"] < df["spl"]
    df["hpb"] = df["close"] > df["sph"]

    df["lpb"] = df["lpb"] & (~df["lpb"]).shift(1)
    df["hpb"] = df["hpb"] & (~df["hpb"]).shift(1)

    df["lprs"] = (df["lpb"].astype(int) * -1).cumsum()  # .where(df["lpb"])
    df["hprs"] = (df["hpb"].astype(int)).cumsum()  # .where(df["hpb"])

    df["lpr"] = df.groupby("hprs")["lprs"].transform("cummin").where(df["lpb"])
    df["hpr"] = df.groupby("lprs")["hprs"].transform("cummin").where(df["hpb"])

    df["z"] = df["lpr"].fillna(df["hpr"]).fillna(method="ffill")

    grouped = df.groupby("z")
    sph = grouped["sph"].transform("cummax").where(df["z"] < 0).fillna(df["sph"])
    spl = grouped["spl"].transform("cummin").where(df["z"] > 0).fillna(df["spl"])

    spp = df["z"].apply(lambda row: (row / abs(row)) if row else 0)
    spd = (df["lpb"].astype(int) * -1) + (df["hpb"].astype(int))

    # Offset
    if offset != 0:
        sph = sph.shift(offset)
        spl = spl.shift(offset)
        spp = spp.shift(offset)
        spd = spd.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        sph.fillna(kwargs["fillna"], inplace=True)
        spl.fillna(kwargs["fillna"], inplace=True)
        spp.fillna(kwargs["fillna"], inplace=True)
        spd.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        sph.fillna(method=kwargs["fill_method"], inplace=True)
        spl.fillna(method=kwargs["fill_method"], inplace=True)
        spp.fillna(method=kwargs["fill_method"], inplace=True)
        spd.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    sph.name = f"SPH_{length}"
    sph.category = "smart-trade"
    spl.name = f"SPL_{length}"
    spl.category = "smart-trade"
    spp.name = f"SPP_{length}"
    spp.category = "smart-trade"
    spd.name = f"SPD_{length}"
    spd.category = "smart-trade"

    df = DataFrame({
        f"SPH_{length}": sph,
        f"SPL_{length}": spl,
        f"SPP_{length}": spp,
        f"SPD_{length}": spd,
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
        pd.DataFrame: SPH (highpivot), SPL (lowpivot), SPP (pivotdirection), SPD, (pivotbraks).
    """
