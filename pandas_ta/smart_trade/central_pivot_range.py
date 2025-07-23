# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def cpr(high, low, close, offset, frequency='D', **kwargs):
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    offset = get_offset(offset)

    df = DataFrame({"high": high, "low": low, "close": close})
    df.reset_index(inplace=True)
    df.set_index("candle_time", inplace=True, drop=False)

    cpr_df = df.resample(frequency, label='left', closed='left').agg(
        _high= ('high', 'max'),
        _low= ('low', 'min'),
        _close= ('close', 'last'),
        candle_time= ('candle_time', 'last'),
    )

    cpr_df.set_index("candle_time", inplace=True)
    cpr_df.dropna(inplace=True)

    # day_high = high.resample(frequency, label='left', closed='left').max()
    # day_low = low.resample(frequency, label='left', closed='left').min()
    # day_close = close.resample(frequency, label='left', closed='left').last()
    #
    # cpridx = close.to_frame().reset_index().set_index("candle_time", drop=False)["candle_time"].resample(frequency, label='left', closed='left').last()
    #
    # cpr_df =

    cpr_df["pivot"] = (cpr_df["_high"] + cpr_df["_low"] + cpr_df["_close"]) / 3
    cpr_df["cw"] = abs((cpr_df["_high"] + cpr_df["_low"]) / 2 - cpr_df["pivot"])

    df = df.merge(cpr_df, "left", left_index=True, right_index=True)
    df["pivot"] = df["pivot"].shift(1).ffill()
    df["cw"] = df["cw"].shift(1).ffill()

    result = DataFrame({"close": close})
    result["Pivot"] = df["pivot"]
    result["Bottom_CPR"] = df["pivot"] - df["cw"]
    result["Top_CPR"] = df["pivot"] + df["cw"]
    result["CW"] = df["cw"]
    result["S2"] = df["pivot"] - 2 * df["cw"]
    result["R2"] = df["pivot"] + 2 * df["cw"]
    result["S3"] = df["pivot"] - 3 * df["cw"]
    result["R3"] = df["pivot"] + 3 * df["cw"]
    result.drop("close", axis=1, inplace=True)

    df.name = "Central_Pivot_Range"
    df.category = "smart-trade"

    return result
