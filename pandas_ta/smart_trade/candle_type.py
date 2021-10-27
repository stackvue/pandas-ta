# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import verify_series


def candle_type(open_, close, offset=None, **kwargs):
    open_ = verify_series(open_)
    close = verify_series(close)
    base = kwargs.get("base", "")

    df = DataFrame({"open": open_, "close": close})
    df[base + "green_candle"] = df.apply(
        lambda row_candle: 1 if (row_candle["open"] < row_candle["close"]) else 0, axis=1)
    df[base + "red_candle"] = df.apply(
        lambda row_candle: 1 if (row_candle["open"] >= row_candle["close"]) else 0, axis=1)
    df[base + "reverse_candle"] = abs(df[base + "green_candle"] - df[base + "green_candle"].shift(1))
    df.drop("close", axis=1, inplace=True)
    df.drop("open", axis=1, inplace=True)

    df.name = "Candle_Type"
    df.category = "smart-trade"

    return df
