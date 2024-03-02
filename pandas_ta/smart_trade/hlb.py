# -*- coding: utf-8 -*-
from pandas import DataFrame, Grouper

from pandas_ta.utils import get_offset, verify_series
import pandas as pd


def hlb(high, low, start_candle=0, end_candle=0, anchor=None, offset=None, **kwargs):
    """Indicator: HILO_BLOCK (HILO_BLOCK)"""
    # Validate Arguments
    high = verify_series(high)
    low = verify_series(low)
    offset = get_offset(offset)
    anchor = anchor.upper() if anchor and isinstance(anchor, str) and len(anchor) >= 1 else "D"

    # Prepare DataFrame to return
    df = DataFrame({"HLB_HIGH": high, "HLB_LOW": low})
    df.name = f"HILO_BLOCK"
    df.category = "smart-trade"

    grouped = df.groupby(df.index.tz_localize(None).to_period(anchor))
    block_size = kwargs.get("block_size", 0)
    if block_size:
        candle_number = (grouped.cumcount() / block_size).astype(int)
        grouped = df.groupby([df.index.tz_localize(None).to_period(anchor), candle_number])

    candle_number = grouped.cumcount() + 1

    block = candle_number >= start_candle
    if end_candle:
        if end_candle < start_candle:
            block = block | (candle_number <= end_candle)
        else:
            block = block & (candle_number <= end_candle)

    df["HLB_HIGH"].where(block, inplace=True)
    df["HLB_LOW"].where(block, inplace=True)

    df["HLB_HIGH"] = grouped["HLB_HIGH"].transform("cummax")
    df["HLB_LOW"] = grouped["HLB_LOW"].transform("cummin")

    df["HLB_HIGH"].fillna(inplace=True, method='ffill')
    df["HLB_LOW"].fillna(inplace=True, method='ffill')

    # Offset
    if offset != 0:
        df["HLB_HIGH"] = df["HLB_HIGH"].shift(offset)
        df["HLB_LOW"] = df["HLB_LOW"].shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df["HLB_HIGH"].fillna(kwargs["fillna"], inplace=True)
        df["HLB_LOW"].fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df["HLB_HIGH"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HLB_LOW"].fillna(method=kwargs["fill_method"], inplace=True)

    df["HLB_HIGH"].category = df["HLB_LOW"].category = "smart-trade"
    return df


hlb.__doc__ = \
"""HILO BLOCK (HILO_BLOCK)

HILO BLOCK (HILO_BLOCK).

Sources:
    https://smart-trade.reluminos.com

Calculation:
    HLB_HIGH = cumulative high for the given block
    HLB_LOW = cumulative low for the given block

Args:
    high (pd.Series): Series of 'high's
    low (pd.Series): Series of 'low's
    start_candle (float): First Candle Number of block to be created
    end_candle (float): Last Candle Number of block to be created
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: HLB_HIGH (line), HLB_LOW (line) columns.
"""
