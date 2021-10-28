# -*- coding: utf-8 -*-
import pandas as pd

from pandas_ta.utils import verify_series


def cattr(open_, high, low, close, offset=None, **kwargs):
    open_ = verify_series(open_)
    close = verify_series(close)
    high = verify_series(high)
    low = verify_series(low)

    df = pd.DataFrame({"open": open_, "close": close, "high": high, "low": low})
    df["green_candle"] = df.apply(lambda row_candle: 1 if (row_candle["open"] < row_candle["close"]) else 0, axis=1)
    df["red_candle"] = df.apply(lambda row_candle: 1 if (row_candle["open"] >= row_candle["close"]) else 0, axis=1)
    df["reverse_candle"] = abs(df["green_candle"] - df["green_candle"].shift(1))

    candle_head_percent = df.apply(
        lambda row: (row['high'] - row['close']) / row['open'] * 100 if row['close'] > row['open'] else
        (row['high'] - row['open']) / row['open'] * 100, axis=1)

    candle_body_percent = df.apply(
        lambda row: (row['high'] - row['close']) / row['open'] * 100 if row['close'] > row['open'] else
        (row['high'] - row['open']) / row['open'] * 100, axis=1)

    candle_tail_percent = df.apply(
        lambda row: (row['high'] - row['close']) / row['open'] * 100 if row['close'] > row['open'] else
        (row['high'] - row['open']) / row['open'] * 100, axis=1)

    df["candle_head_percent"] = candle_head_percent
    df["candle_body_percent"] = candle_body_percent
    df["candle_tail_percent"] = candle_tail_percent

    df.drop("close", axis=1, inplace=True)
    df.drop("open", axis=1, inplace=True)
    df.drop("high", axis=1, inplace=True)
    df.drop("low", axis=1, inplace=True)

    df.name = "Candle_Type"
    df.category = "smart-trade"

    return df