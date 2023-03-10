# -*- coding: utf-8 -*-
import math

from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def nr(close, src_start, src_end, dst_start, dst_end, exp=1, offset=None, **kwargs):
    """Indicator: Expr (expr)"""

    src_slope = src_end - src_start

    n_x = math.pow(dst_start, 1 / exp)
    n_y = math.pow(dst_end, 1 / exp)
    dest_slope = n_y - n_x
    absolute = kwargs.get("absolute", True)
    extrapolate = kwargs.get("extrapolate", True)
    close = verify_series(close)
    if absolute:
        close = close.abs()
    offset = get_offset(offset)

    def convert(row):
        if not extrapolate:
            if row <= src_start:
                return dst_start
            if row >= src_end:
                return dst_end
        return (((row - src_start) * dest_slope / src_slope) + n_x) ** exp

    result = close.apply(lambda row: convert(row))
    # Offset
    if offset != 0:
        result = result.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        result.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        result.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    result.name = f"NR"
    result.category = "smart-trade"

    # Prepare DataFrame to return
    df = DataFrame({result.name: result})
    df.name = f"NR"
    df.category = "smart-trade"

    return df


nr.__doc__ = \
    """Normalize Range (nr)
    
    Normalize Range (NR).
    
    Sources:
        https://smart-trade.reluminos.com
    
    Calculation:
        result = nr(expr)         
    
    Args:
        close (pd.Series): Series of 'close's
        src_start (float): Source Range Start Value
        src_end (float): Source Range End Value
        dst_start (float): Destination Range Start Value
        dst_end (float): Destination Range End Value
        exp (float): Exponent: Default: 1
        absolute (bool): True
        extrapolate (bool): False
        offset (int): How many periods to offset the result. Default: 0
    
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.DataFrame: nr (line) columns.
    """
