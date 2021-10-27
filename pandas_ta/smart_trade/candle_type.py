# -*- coding: utf-8 -*-
import pandas as pd

from pandas_ta.utils import verify_series


def candle_type(open_, close, offset=None, **kwargs):
    open_ = verify_series(open_)
    close = verify_series(close)

    df = pd.DataFrame({"open": open_, "close": close})
    df["green_candle"] = df.apply(lambda row_candle: 1 if (row_candle["open"] < row_candle["close"]) else 0, axis=1)
    df["red_candle"] = df.apply(lambda row_candle: 1 if (row_candle["open"] >= row_candle["close"]) else 0, axis=1)
    df["reverse_candle"] = abs(df["green_candle"] - df["green_candle"].shift(1))
    df["green_candles"] = df.groupby(pd.Grouper(freq='D'))['green_candle'].cumsum()
    df["red_candles"] = df.groupby(pd.Grouper(freq='D'))['red_candle'].cumsum()
    df["reverse_candles"] = df.groupby(pd.Grouper(freq='D'))['reverse_candle'].cumsum()

    df.drop("close", axis=1, inplace=True)
    df.drop("open", axis=1, inplace=True)

    df.name = "Candle_Type"
    df.category = "smart-trade"

    return df
