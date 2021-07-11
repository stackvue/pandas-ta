# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def option_chain(close, step, step_count, offset=None, **kwargs):
    """Indicator: Option Chain (OPTION_CHAIN)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)

    step = step if step and step > 0 else 0
    step_count = step_count if 0 < step_count <= 10 else 0

    # Calculate Result

    at_the_money = close.apply(lambda row: step * round(row/step))
    if offset != 0:
        at_the_money = at_the_money.shift(offset)
    if "fillna" in kwargs:
        at_the_money.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        at_the_money.fillna(method=kwargs["fill_method"], inplace=True)
    # Name & Category
    at_the_money.name = f"OC_AT_THE_MONEY"
    at_the_money.category = "smart-trade"
    # Prepare DataFrame to return
    df = DataFrame({at_the_money.name: at_the_money})
    df.name = f"OPTION_CHAIN"
    df.category = "smart-trade"
    i = 0
    while i < step_count:
        i += 1
        above = at_the_money + step * i
        below = at_the_money - step * i

        # Offset
        if offset != 0:
            above = above.shift(offset)
            below = below.shift(offset)


        # Handle fills
        if "fillna" in kwargs:
            at_the_money.fillna(kwargs["fillna"], inplace=True)
            above.fillna(kwargs["fillna"], inplace=True)
            below.fillna(kwargs["fillna"], inplace=True)
        if "fill_method" in kwargs:
            at_the_money.fillna(method=kwargs["fill_method"], inplace=True)
            above.fillna(method=kwargs["fill_method"], inplace=True)
            below.fillna(method=kwargs["fill_method"], inplace=True)

        above.name = f"OC_PLUS_{i}"
        below.name = f"OC_MINUS_{i}"
        above.category = below.category = "smart-trade"
        df[above.name] = above
        df[below.name] = below

    return df


option_chain.__doc__ = \
"""HILO BAND (HILO_BAND)

HILO BAND (HILO_BAND).

Sources:
    https://smart-trade.stackvue.com

Calculation:
    at_the_money = step * round(close/step)            
    plus_i = at_the_money + step * i
    minus_i = at_the_money - step * i            

Args:
    close (pd.Series): Series of 'close's
    step (float): Size of Step
    step_count(int): How many steps are to be calculated (MAX: 10)
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: OC_AT_THE_MONEY (line), OC_PLUS_{i} (line), OC_MINUS_{i} (line) columns.
"""
