# -*- coding: utf-8 -*-
from pandas import DataFrame
from pandas_ta.utils import get_offset, verify_series


def cpr(high, low, close, offset, **kwargs):
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    offset = get_offset(offset)

    day_high = high.resample(f'D', label='left', closed='left').max().dropna().shift(1)
    day_low = low.resample(f'D', label='left', closed='left').min().dropna().shift(1)
    day_close = close.resample(f'D', label='left', closed='left').last().dropna().shift(1)

    pivot = (day_high + day_low + day_close) / 3
    bottom_cpr = (day_high + day_low) / 2
    top_cpr = 2 * pivot - bottom_cpr

    cpr_df = DataFrame({"pivot": pivot, "bottom_cpr": bottom_cpr, "top_cpr": top_cpr})

    cpr_dict = {}
    for day, row in cpr_df.iterrows():
        cpr_list = sorted([row["pivot"], row["bottom_cpr"], row["top_cpr"]])
        cpr_dict[day.date()] = {"pivot": cpr_list[1],
                                "bottom_cpr": cpr_list[0],
                                "top_cpr": cpr_list[2]}

    df = DataFrame({"close": close})
    df["Pivot"] = df.apply(lambda row: cpr_dict[row.name.date()]["pivot"], axis=1)
    df["Bottom_CPR"] = df.apply(lambda row: cpr_dict[row.name.date()]["bottom_cpr"], axis=1)
    df["Top_CPR"] = df.apply(lambda row: cpr_dict[row.name.date()]["top_cpr"], axis=1)
    df["CW"] = (df["Top_CPR"] - df["Bottom_CPR"]) / 2
    df["S2"] = df["Pivot"] - 2 * df["CW"]
    df["R2"] = df["Pivot"] + 2 * df["CW"]
    df["S3"] = df["Pivot"] - 3 * df["CW"]
    df["R3"] = df["Pivot"] + 3 * df["CW"]
    df.drop("close", axis=1, inplace=True)

    df.name = "Central_Pivot_Range"
    df.category = "smart-trade"

    return df
