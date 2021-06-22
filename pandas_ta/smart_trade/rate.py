# -*- coding: utf-8 -*-
from pandas import DataFrame, Timedelta

from pandas_ta.utils import get_offset, verify_series


def rate(close, base, length=None, unit=None, offset=None, accumulate=False, **kwargs):
    """Indicator: Rate (Rate)"""
    # Validate Arguments
    close = verify_series(close)
    base = verify_series(base)

    length = int(length) if length and length > 0 else 0
    offset = get_offset(offset)
    factor = 1
    if unit in ["days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"]:
        time_config = {
            unit: 1
        }
        factor = Timedelta(**time_config)

    # Calculate Result
    if accumulate:
        close = close.cumsum()

    close_before = close.shift(length)
    base_before = base.shift(length or 1)

    close_diff = (close - close_before) if length else close
    base_diff = (base - base_before) / factor

    rate = close_diff / base_diff

    # Offset
    if offset != 0:
        rate = rate.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        rate.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        rate.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    rate.name = f"RATE_{length}"
    rate.category = "smart-trade"

    # Prepare DataFrame to return
    df = DataFrame({rate.name: rate})
    df.name = f"RATE"
    df.category = "smart-trade"

    return df


rate.__doc__ = \
"""Rate (rate)

Rate Of Change (RATE).

Sources:
    https://smart-trade.reluminos.com

Calculation:
    rate = ((close - close_before(length)) if length else close) / ((base - base_before(length)) / factor)         

Args:
    close (pd.Series): Series of 'close's
    base (pd.Series): Series of 'base's
    unit: ["days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"] or None
    length (int): It's period. Default: 0
    accumulate (bool): False
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: rate (line) columns.
"""
