# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from pandas_ta.overlap import sma
from pandas_ta.utils import verify_series, get_offset
from pandas_ta.volatility import atr


def half_trend(close, high, low, length=None, atr_length=None, deviation=None, offset=None, **kwargs):
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    length = int(length) if length and length > 0 else 2
    atr_length = int(
        atr_length) if atr_length is not None and atr_length > 0 else 100
    deviation = float(deviation) if deviation else 2
    offset = get_offset(offset)

    # Calculate Result

    trend = 0
    next_trend = 0

    up = 0.0
    down = 0.0

    df = pd.DataFrame({
        "close": close,
        "high": high,
        "low": low,
        "dev": (atr(high=high, low=low, close=close, length=atr_length) / 2) * deviation,
        "highPrice": high.rolling(length).max(),
        "lowPrice": low.rolling(length).min(),
        "highma": sma(high, length),
        "lowma": sma(low, length),
        "up": np.NaN,
        "down": np.NaN,
        "trend": np.NaN,
        "nextTrend": np.NaN
    })

    df["drop"] = df["close"] < df["low"].shift()
    df["rise"] = df["close"] > df["high"].shift()

    i = 0
    prev_index = None
    for index, row in df.iterrows():
        if i < atr_length:
            maxLowPrice = row["low"]
            minHighPrice = row["high"]
            i += 1
            continue
        if next_trend == 1:
            maxLowPrice = max(row["lowPrice"], maxLowPrice)

            if row["highma"] < maxLowPrice and row["drop"]:
                trend = 1
                next_trend = 0
                minHighPrice = row["highPrice"]
        else:
            minHighPrice = min(row["highPrice"], minHighPrice)

            if row["lowma"] > minHighPrice and row["rise"]:
                trend = 0
                next_trend = 1
                maxLowPrice = row["lowPrice"]

        if trend == 0:
            if prev_index and df["trend"].loc[prev_index] != 0:
                df.loc[index, "up"] = up = df["down"].loc[prev_index] or down
            else:
                df.loc[index, "up"] = up = max(maxLowPrice, df["up"].loc[prev_index]) if prev_index and df["up"].loc[
                    prev_index] else maxLowPrice
            df.loc[index, "atrHigh"] = up + row["dev"]
            df.loc[index, "atrLow"] = up - row["dev"]
        else:
            if prev_index and df["trend"].loc[prev_index] != 1:
                df.loc[index, "down"] = down = df["up"].loc[prev_index] or up
            else:
                df.loc[index, "down"] = down = min(minHighPrice, df["down"].loc[prev_index]) if prev_index and \
                                                                                              df["down"].loc[
                                                                                                  prev_index] else minHighPrice
            df.loc[index, "atrHigh"] = down + row["dev"]
            df.loc[index, "atrLow"] = down - row["dev"]

        df.loc[index, "trend"] = trend
        df.loc[index, "nextTrend"] = next_trend
        prev_index = index

    result = pd.DataFrame({
        "ht_high": df["atrHigh"],
        "ht_low": df["atrLow"],
        "ht_trend": df["up"],
        "ht_signal": df["trend"]
    })
    result["ht_trend"].fillna(df["down"], inplace=True)
    result.name = "Smart_Trend"
    result.category = "smart-trade"
    return result


half_trend.__doc__ = \
    """HALF TREND (HALF_TREND)
    
    HALF TREND (HALF_TREND).
    Sources:
        https://smart-trade.stackvue.com
    
    Args:
        close (pd.Series): Series of 'close's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        length (int) : length of window(amplitude). Default: 2
        atr_length (int) : length of atr window. Default: 100
        deviation (float) : channel deviation. Default: 2
    
    Returns:
        pd.DataFrame: ht_high (line), ht_low (line), ht_trend (trend), ht_signal (direction), columns.
    """
