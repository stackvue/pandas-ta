# -*- coding: utf-8 -*-
from pandas import DataFrame, Grouper

from pandas_ta.utils import get_offset, verify_series


def prepare_boundary(close, mode, u_bound, l_bound):
    if mode == "abs":
        return u_bound, l_bound
    else:
        return close * u_bound / 100 , close * l_bound / 100

def hlz(close, u_bound, l_bound, mode=None, offset=None, **kwargs):
    """Indicator: HILO_ZONE (HILO_ZONE)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)

    mode = mode or "abs"
    decay = kwargs.get("decay", 0)
    u_decay = kwargs.get("u_decay", decay) / 100
    l_decay = kwargs.get("l_decay", decay) / 100
    intraday = kwargs.get("intraday", False)


    # Prepare DataFrame to return
    df = DataFrame({"close": close})
    df.name = f"HILO_ZONE"
    df.category = "smart-trade"

    prev_date = close.first_valid_index().date()
    upper_delta, lower_delta = prepare_boundary(close.iloc[0], mode, u_bound, l_bound)
    broken_close = prev_close = close.iloc[0]
    add_zone = True
    for index, row in df.iterrows():
        if index.date() != prev_date:
            if intraday:
                broken_close = row["close"]
            else:
                broken_close = prev_close
            upper_delta, lower_delta  = prepare_boundary(broken_close, mode, u_bound, l_bound)
        upper_delta *= (1-u_decay)
        lower_delta *= (1-l_decay)
        upper = df.loc[index, "HLZ_HIGH"] = broken_close + upper_delta
        lower = df.loc[index, "HLZ_LOW"] = broken_close - lower_delta
        if not lower < row["close"] < upper:
            add_zone = False
            value = 1 if row["close"] >= upper else -1
            df.loc[index, "HLZ_BREAK"] = value
            df.loc[index, "HLZ_ZONE"] = value
            upper_delta, lower_delta = prepare_boundary(row["close"], mode, u_bound, l_bound)
            broken_close = row["close"]
        else:
            df.loc[index, "HLZ_BREAK"] = 0
        prev_date = index.date()
        prev_close = row["close"]

    if add_zone:
        df["HLZ_ZONE"] = 0
    if intraday:
        df["HLZ_ZONE"] = df["HLZ_ZONE"].groupby(Grouper(freq='D')).fillna(method='ffill')
    else:
        df["HLZ_ZONE"].fillna(inplace=True, method='ffill')
        df["HLZ_ZONE"] = df["HLZ_ZONE"].groupby(Grouper(freq='D')).fillna(method='bfill')
    df["HLZ_ZONE"].fillna(0, inplace=True)

    # Offset
    if offset != 0:
        df["HLZ_HIGH"] = df["HLZ_HIGH"].shift(offset)
        df["HLZ_LOW"] = df["HLZ_LOW"].shift(offset)
        df["HLZ_BREAK"] = df["HLZ_BREAK"].shift(offset)
        df["HLZ_ZONE"] = df["HLZ_ZONE"].shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df["HLZ_HIGH"].fillna(kwargs["fillna"], inplace=True)
        df["HLZ_LOW"].fillna(kwargs["fillna"], inplace=True)
        df["HLZ_BREAK"].fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df["HLZ_HIGH"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HLZ_LOW"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HLZ_BREAK"].fillna(method=kwargs["fill_method"], inplace=True)

    df["HLZ_HIGH"].category = df["HLZ_LOW"].category = df["HLZ_BREAK"].category = df["HLZ_ZONE"].category = "smart-trade"
    df.drop('close', axis=1, inplace=True)
    return df


hlz.__doc__ = \
"""HILO ZONE (HILO_ZONE)

HILO ZONE (HILO_ZONE).

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
    pd.DataFrame: HLZ_HIGH (line), HLZ_LOW (line), HLZ_BREAK (line), HLZ_ZONE (line) columns.
"""
