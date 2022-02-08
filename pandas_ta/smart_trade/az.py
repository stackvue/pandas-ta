# -*- coding: utf-8 -*-
from pandas import DataFrame, Grouper

from pandas_ta.utils import get_offset, verify_series


def prepare_boundary(close, mode, u_bound, l_bound):
    if mode == "abs":
        return u_bound, l_bound
    else:
        return close * u_bound / 100 , close * l_bound / 100


def az(close, u_bound, l_bound, mode=None, offset=None, **kwargs):
    """Indicator: ANGULAR_ZONE (ANGULAR_ZONE)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)

    mode = mode or "abs"
    delta = kwargs.get("delta", 0)
    u_delta = kwargs.get("u_delta", delta)
    l_delta = kwargs.get("l_delta", delta)

    # Prepare DataFrame to return
    df = DataFrame({"close": close})
    df.name = f"ANGULAR_ZONE"
    df.category = "smart-trade"

    prev_date = None
    upper_delta, lower_delta = prepare_boundary(close.iloc[0], mode, u_bound, l_bound)
    broken_close = prev_close = close.iloc[0]
    value = 0
    for index, row in df.iterrows():
        if index.date() != prev_date:
            upper_delta, lower_delta = prepare_boundary(row["close"], mode, u_bound, l_bound)
            broken_close = row["close"]
            value = 0
            df.loc[index, "AZ_HIGH"] = broken_close + upper_delta
            df.loc[index, "AZ_LOW"] = broken_close - lower_delta
            df.loc[index, "AZ_BREAK"] = value
            df.loc[index, "AZ_ZONE"] = value
        elif value == 0 and row["close"] != prev_close:
            value = 1 if row["close"] > prev_close else -1
            broken_close = row["close"]
            df.loc[index, "AZ_HIGH"] = broken_close + upper_delta
            df.loc[index, "AZ_LOW"] = broken_close - lower_delta
            df.loc[index, "AZ_BREAK"] = value
            df.loc[index, "AZ_ZONE"] = value
            upper_delta, lower_delta = prepare_boundary(row["close"], mode, u_bound, l_bound)
        else:
            if mode == "abs":
                upper_delta += u_delta * value
                lower_delta -= l_delta * value
            else:
                upper_delta *= ((1+u_delta/100) ** float(value))
                lower_delta *= ((1-l_delta/100) ** float(value))
            upper = df.loc[index, "AZ_HIGH"] = broken_close + upper_delta
            lower = df.loc[index, "AZ_LOW"] = broken_close - lower_delta
            if not lower < row["close"] < upper:
                add_zone = False
                value = 1 if row["close"] >= upper else -1
                df.loc[index, "AZ_BREAK"] = value
                df.loc[index, "AZ_ZONE"] = value
                upper_delta, lower_delta = prepare_boundary(row["close"], mode, u_bound, l_bound)
                broken_close = row["close"]
            else:
                df.loc[index, "AZ_BREAK"] = 0
        prev_close = row["close"]
        prev_date = index.date()


    df["AZ_ZONE"].fillna(inplace=True, method='ffill')
    df["AZ_ZONE"] = df["AZ_ZONE"].groupby(Grouper(freq='D')).fillna(method='bfill')
    df["AZ_ZONE"].fillna(0, inplace=True)

    # Offset
    if offset != 0:
        df["AZ_HIGH"] = df["AZ_HIGH"].shift(offset)
        df["AZ_LOW"] = df["AZ_LOW"].shift(offset)
        df["AZ_BREAK"] = df["AZ_BREAK"].shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df["AZ_HIGH"].fillna(kwargs["fillna"], inplace=True)
        df["AZ_LOW"].fillna(kwargs["fillna"], inplace=True)
        df["AZ_BREAK"].fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df["AZ_HIGH"].fillna(method=kwargs["fill_method"], inplace=True)
        df["AZ_LOW"].fillna(method=kwargs["fill_method"], inplace=True)
        df["AZ_BREAK"].fillna(method=kwargs["fill_method"], inplace=True)

    df["AZ_HIGH"].category = df["AZ_LOW"].category = df["AZ_BREAK"].category = "smart-trade"
    df.drop('close', axis=1, inplace=True)
    return df


az.__doc__ = \
"""ANGULAR ZONE (ANGULAR_ZONE)

ANGULAR ZONE (ANGULAR_ZONE).

Sources:
    https://smart-trade.reluminos.com

Calculation:
    zone_high[t] = close[t-1] + u_bound if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_high[t-1]
    zone_low[t] = close[t-1] - l_bound if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_low[t-1]

Args:
    close (pd.Series): Series of 'close's
    u_bound (float): Upper Bound of zone to be created
    l_bound (float): Lower Bound of zone to be created
    offset (int): How many periods to offset the result. Default: 0
    mode (abs/pct): bound type (Absolute or pct), default abs

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: AZ_HIGH (line), AZ_LOW (line), AZ_BREAK (line), AZ_ZONE (line) columns.
"""
