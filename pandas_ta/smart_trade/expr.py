# -*- coding: utf-8 -*-
import math

from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series

ALLOWED_NAMES = {
    k: v for k, v in math.__dict__.items() if not k.startswith("__")
}


def process(row, expression):
    try:
        return eval(expression, {"a": row["a"], "b": row["b"]}, ALLOWED_NAMES)
    except Exception as e:
        return None


def expr(series_a, series_b, expression=None, offset=None, **kwargs):
    """Indicator: Expr (expr)"""
    # Validate Arguments
    if not expression:
        return

    series_a = verify_series(series_a)
    series_b = verify_series(series_b)

    offset = get_offset(offset)

    df = DataFrame({"a": series_a, "b": series_b})

    result = df.apply(lambda row: process(row, expression), axis=1)
    # Offset
    if offset != 0:
        result = result.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        result.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        result.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    result.name = f"EXPR_{expression}"
    result.category = "smart-trade"

    # Prepare DataFrame to return
    df = DataFrame({result.name: result})
    df.name = f"EXPR"
    df.category = "smart-trade"

    return df


expr.__doc__ = \
    """Expr (expr)
    
    Expression (EXPR).
    
    Sources:
        https://smart-trade.reluminos.com
    
    Calculation:
        result = eval(expr)         
    
    Args:
        a (pd.Series): Series of 'close's
        b (pd.Series): Series of 'base's
        expr: Expression to evaluate or None
        offset (int): How many periods to offset the result. Default: 0
    
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.DataFrame: expr (line) columns.
    """
