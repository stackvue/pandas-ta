# -*- coding: utf-8 -*-
from pandas import DataFrame

from pandas_ta.utils import get_offset, is_datetime_ordered, verify_series
from .hlc3 import hlc3


def vwap(high, low, close, volume, anchor=None, offset=None, grouper=None, **kwargs):
    """Indicator: Volume Weighted Average Price (VWAP)"""
    # Validate Arguments
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    volume = verify_series(volume)
    anchor = anchor.upper() if anchor and isinstance(anchor, str) and len(anchor) >= 1 else "D"
    grouper = verify_series(grouper)
    anchors = [volume.index.to_period(anchor)]
    if grouper is not None:
        anchors.append(grouper)
    offset = get_offset(offset)
    factor = float(kwargs.get("factor", 0))
    factor_range = float(kwargs.get("factor_range", 0))
    typical_price = hlc3(high=high, low=low, close=close)
    if not is_datetime_ordered(volume):
        print(f"[!] VWAP volume series is not datetime ordered. Results may not be as expected.")
    if not is_datetime_ordered(typical_price):
        print(f"[!] VWAP price series is not datetime ordered. Results may not be as expected.")
    multiplier = None
    if factor or factor_range:
        candles = volume.groupby(anchors).count().max()
        multiplier = volume.groupby(anchors).cumcount().groupby(anchors).transform(
            lambda x: (x + 1) ** (factor + factor_range * x / candles))
        volume = volume * multiplier

    # Calculate Result
    wp = typical_price * volume
    vwap = wp.groupby(anchors).cumsum()
    vwap /= volume.groupby(anchors).cumsum()

    _props = f"_{anchor}"
    df = DataFrame({
        f"VWAP{_props}": vwap,
        f"VWAPf{_props}": multiplier if multiplier is not None else 1,
        f"VWAPw{_props}": volume
    }, index=volume.index)

    df.name = f"VWAP_{_props}"
    df.category = "overlap"

    # Offset
    if offset != 0:
        df = df.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df.fillna(method=kwargs["fill_method"], inplace=True)
    return df


vwap.__doc__ = \
    """Volume Weighted Average Price (VWAP)
    
    The Volume Weighted Average Price that measures the average typical price
    by volume.  It is typically used with intraday charts to identify general
    direction.
    
    Sources:
        https://www.tradingview.com/wiki/Volume_Weighted_Average_Price_(VWAP)
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/volume-weighted-average-price-vwap/
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vwap_intraday
    
    Calculation:
        tp = typical_price = hlc3(high, low, close)
        tpv = tp * volume
        VWAP = tpv.cumsum() / volume.cumsum()
    
    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        anchor (str): How to anchor VWAP. Depending on the index values, it will
            implement various Timeseries Offset Aliases as listed here:
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
            Default: "D".
        offset (int): How many periods to offset the result. Default: 0
    
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.Series: New feature generated.
    """
