# -*- coding: utf-8 -*-
from pandas import DataFrame
import pandas as pd
from pandas_ta.utils import get_offset, verify_series


def candle_brick(close, volume, brick_size=1, offset=None, **kwargs):
    """Indicator: Archer On Balance Volume (AOBV)"""
    # Validate arguments
    close = verify_series(close)
    volume = verify_series(volume)
    offset = get_offset(offset)

    close_diff = close.diff()
    bricks = close_diff / close
    bricks_count = bricks.abs().floordiv(brick_size) * bricks / bricks.abs()
    bricks_count = bricks_count.fillna(0).astype(int)

    brick_number = bricks_count.groupby(pd.Grouper(freq='D')).cumsum()
    brick_id = bricks_count.abs().groupby(pd.Grouper(freq='D')).cumsum()
    brick_id.name = "brick_id"
    bricks_df = pd.concat([brick_id, volume], axis=1)
    brick_volume = bricks_df.groupby([pd.Grouper(freq='D'), "brick_id"])["volume"].cumsum()

    bricks_df['candle_time'] = bricks_df.index
    bricks_df["brick_start_time"] = bricks_df.groupby([pd.Grouper(freq='D'), 'brick_id'])['candle_time'].transform('min')
    brick_duration = bricks_df.apply(
        lambda row: (row["candle_time"] - row["brick_start_time"]).total_seconds() / 60
        if row["brick_start_time"] != pd.NaT else 0,
        axis=1)

    # Offset
    if offset != 0:
        brick_number = brick_number.shift(offset)
        brick_id = brick_id.shift(offset)
        brick_volume = brick_volume.shift(offset)
        brick_duration = brick_duration.shift(offset)

    # # Handle fills
    if "fillna" in kwargs:
        brick_number.fillna(kwargs["fillna"], inplace=True)
        brick_id.fillna(kwargs["fillna"], inplace=True)
        brick_volume.fillna(kwargs["fillna"], inplace=True)
        brick_duration.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        brick_number.fillna(method=kwargs["fill_method"], inplace=True)
        brick_id.fillna(method=kwargs["fill_method"], inplace=True)
        brick_volume.fillna(method=kwargs["fill_method"], inplace=True)
        brick_duration.fillna(method=kwargs["fill_method"], inplace=True)

    # Prepare DataFrame to return
    data = {
        f"CANDLEBRICK_brick_number_{brick_size}": brick_number,
        f"CANDLEBRICK_brick_id_{brick_size}": brick_id,
        f"CANDLEBRICK_brick_volume_{brick_size}": brick_volume,
        f"CANDLEBRICK_brick_duration_{brick_size}": brick_duration,
    }
    candlebrick = DataFrame(data)

    # Name and Categorize it
    candlebrick.name = f"CANDLEBRICK_{brick_size}"
    candlebrick.category = "smart_trade"

    return candlebrick
