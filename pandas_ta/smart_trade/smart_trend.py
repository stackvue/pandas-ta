# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pandas_ta.utils import verify_series


def smart_trend(open_, close, length, **kwargs):
    open_ = verify_series(open_)
    close = verify_series(close)
    length = int(length) if length and length > 0 else 10

    df = pd.DataFrame({
        "st_open": open_,
        "st_close": close
    })

    candle_number = df.groupby(pd.Grouper(freq='D')).cumcount()
    df["batch"] = candle_number // length
    block = ((candle_number % length) == 0).shift(-1)
    grouped = df.groupby([pd.Grouper(freq='D'), pd.Grouper('batch')])
    df["st_open"] = grouped["st_open"].transform("first")
    df["st_close"] = grouped["st_close"].transform("last")

    df["st_open"] = df["st_open"].where(block).fillna(method='ffill')
    df["st_close"] = df["st_close"].where(block).fillna(method='ffill')

    df["st_trend"] = np.sign(df["st_close"] - df["st_open"])
    df["st_signal"] = np.sign(df["st_trend"] - df["st_trend"].shift())
    df["st_signal"].fillna(df["st_trend"], inplace=True)

    df.name = "Smart_Trend"
    df.category = "smart-trade"
    df.drop('batch', axis=1, inplace=True)
    return df


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