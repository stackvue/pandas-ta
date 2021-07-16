# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def hilo_zone(close, size, offset=None, **kwargs):
    """Indicator: HILO_ZONE (HILO_ZONE)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)

    # Prepare DataFrame to return
    df = DataFrame({"close": close})
    df.name = f"HILO_ZONE"
    df.category = "smart-trade"

    prev_date = close.first_valid_index().date()
    upper, lower = close.iloc[0] + size, close.iloc[0] - size
    prev_close = close.iloc[0]

    for index, row in df.iterrows():
        if index.date() != prev_date:
            upper, lower = prev_close + size, prev_close - size
        prev_close = row["close"]
        prev_date = index.date()
        df.loc[index, "HILO_ZONE_HIGH"] = upper
        df.loc[index, "HILO_ZONE_LOW"] = lower
        if not lower < row["close"] < upper:
            df.loc[index, "HILO_ZONE_BREAK"] = 1 if row["close"] >= upper else -1
            upper, lower = row["close"] + size, row["close"] - size
        else:
            df.loc[index, "HILO_ZONE_BREAK"] = 0

    # Offset
    if offset != 0:
        df["HILO_ZONE_HIGH"] = df["HILO_ZONE_HIGH"].shift(offset)
        df["HILO_ZONE_LOW"] = df["HILO_ZONE_LOW"].shift(offset)
        df["HILO_ZONE_BREAK"] = df["HILO_ZONE_BREAK"].shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df["HILO_ZONE_HIGH"].fillna(kwargs["fillna"], inplace=True)
        df["HILO_ZONE_LOW"].fillna(kwargs["fillna"], inplace=True)
        df["HILO_ZONE_BREAK"].fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df["HILO_ZONE_HIGH"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HILO_ZONE_LOW"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HILO_ZONE_BREAK"].fillna(method=kwargs["fill_method"], inplace=True)

    df["HILO_ZONE_HIGH"].category = df["HILO_ZONE_LOW"].category = df["HILO_ZONE_BREAK"].category = "smart-trade"
    df.drop('close', axis=1, inplace=True)
    return df


hilo_zone.__doc__ = \
"""HILO ZONE (HILO_ZONE)

HILO ZONE (HILO_ZONE).

Sources:
    https://smart-trade.reluminos.com

Calculation:
    zone_high[t] = close[t-1] + size if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_high[t-1]          
    zone_low[t] = close[t-1] - size if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_low[t-1]

Args:
    close (pd.Series): Series of 'close's
    size (float): Size of zone to be created
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: HILO_ZONE_HIGH (line), HILO_ZONE_LOW (line), HILO_ZONE_BREAK (line) columns.
"""
