# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pandas_ta.utils import verify_series


def smart_trend(open_, close, length, **kwargs):
    open_ = verify_series(open_)
    close = verify_series(close)
    length = int(length) if length and length > 0 else 10

    df = pd.DataFrame({
        "st_open": open_
    })

    df["batch"] = df.groupby(pd.Grouper(freq='D')).cumcount() // length
    grouped = df.groupby([pd.Grouper(freq='D'), pd.Grouper('batch')])
    result = grouped.transform("first")

    result["st_close"] = close
    result["st_trend"] = np.sign(result["st_close"] - result["st_open"])
    result["st_signal"] = np.sign(result["st_trend"] - result["st_trend"].shift())
    result.loc[result.first_valid_index(), "st_signal"] = result.iloc[0]["st_trend"]

    result.name = "Smart_Trend"
    result.category = "smart-trade"
    return result


smart_trend.__doc__ = \
"""SMART TREND (SMART_TREND)

SMART TREND (SMART_TREND).
Sources:
    https://smart-trade.stackvue.com

Calculation:
    st_open = open.groupby(day).window(length).first
    st_close = close.groupby(day).window(length).first
    st_trend = st[close] - st[open]
    st_signal = st_trend - st_trend.shift(1)         

Args:
    open (pd.Series): Series of 'open's
    close (pd.Series): Series of 'close's
    length (int) : length of window. Default: 10

Returns:
    pd.DataFrame: st_open (line), st_close (line), st_trend (trend), st_signal (direction), columns.
"""