# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def hilo_band(close, offset=None, **kwargs):
    """Indicator: HILO BAND (HILO_BAND)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)

    # Calculate Result

    close_before = close.shift(1)
    close_after = close.shift(-1)

    is_before_plateau = (close == close_before)
    close_before = close_before.mask(is_before_plateau)

    is_after_plateau = (close == close_after)
    close_after = close_after.mask(is_after_plateau)

    close_before.fillna(inplace=True, method='ffill')
    close_after.fillna(inplace=True, method='bfill')

    is_high = (close_before < close) & (close_after < close)
    is_low = (close_before > close) & (close_after > close)

    high_band = close.where(is_high).shift(1)
    low_band = close.where(is_low).shift(1)

    high_band.fillna(inplace=True, method='ffill')
    low_band.fillna(inplace=True, method='ffill')

    high_band = high_band.mask(is_before_plateau)
    low_band = low_band.mask(is_before_plateau)

    high_band.fillna(inplace=True, method='ffill')
    low_band.fillna(inplace=True, method='ffill')

    # Offset
    if offset != 0:
        high_band = high_band.shift(offset)
        low_band = low_band.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        high_band.fillna(kwargs["fillna"], inplace=True)
        low_band.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        high_band.fillna(method=kwargs["fill_method"], inplace=True)
        low_band.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    high_band.name = f"HILO_BAND_HIGH"
    low_band.name = f"HILO_BAND_LOW"
    high_band.category = low_band.category = "smart-trade"

    # Prepare DataFrame to return
    df = DataFrame({high_band.name: high_band, low_band.name: low_band})
    df.name = f"HILO_BAND"
    df.category = "smart-trade"

    return df


hilo_band.__doc__ = \
"""HILO BAND (HILO_BAND)

HILO BAND (HILO_BAND).

Sources:
    https://smart-trade.stackvue.com

Calculation:
    is_high = close[t] > close[t-1] and close[t] > close[t+1]            
    is_low = close[t] < close[t-1] and close[t] < close[t+1]            

Args:
    close (pd.Series): Series of 'close's
    offset (int): How many periods to offset the result. Default: 0

Kwargs:
    fillna (value, optional): pd.DataFrame.fillna(value)
    fill_method (value, optional): Type of fill method

Returns:
    pd.DataFrame: HILO_BAND_HIGH (line), HILO_BAND_LOW (line) columns.
"""
