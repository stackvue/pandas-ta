# -*- coding: utf-8 -*-

import pandas as pd
from pandas import DataFrame

from pandas_ta.utils import get_offset, verify_series


def prepare_boundary(close, mode, u_bound, l_bound):
    if mode == "abs":
        return u_bound, l_bound
    else:
        return close * u_bound / 100, close * l_bound / 100


def prepare(df, close, mode, u_bound, l_bound, upper_offset, lower_offset, upper_delta, lower_delta, l_offset,
            u_offset):
    if df.empty:
        return
    df["HLZ_HIGH"] = close + df["u_decay"].cumprod() * (upper_delta)
    df["HLZ_LOW"] = close - df["l_decay"].cumprod() * (lower_delta)
    broken = ((df["close"] > df["HLZ_HIGH"]).astype(int) + (df["close"] < df["HLZ_LOW"]).astype(
        int)).cumsum().shift().fillna(0)
    segment = df[broken == 0]
    value = 0
    if segment["close"].iloc[-1] > segment["HLZ_HIGH"].iloc[-1]:
        value = 1
    if segment["close"].iloc[-1] < segment["HLZ_LOW"].iloc[-1]:
        value = -1

    if value:
        broken_close = segment["close"].iloc[-1]
        upper_delta, lower_delta = prepare_boundary(broken_close, mode, u_bound, l_bound)
        if value == 1:
            upper_offset = 0
            lower_offset += l_offset
            lower_delta -= (lower_offset if mode == "abs" else broken_close * lower_offset / 100)
        if value == -1:
            lower_offset = 0
            upper_offset += u_offset
            upper_delta -= (upper_offset if mode == "abs" else broken_close * upper_offset / 100)
    else:
        broken_close = close
        upper_delta = segment["HLZ_HIGH"].iloc[-1] - broken_close
        lower_delta = broken_close - segment["HLZ_LOW"].iloc[-1]
    return segment, df[broken != 0], broken_close, upper_delta, lower_delta, upper_offset, lower_offset, value


def hlz(close, u_bound, l_bound, mode=None, offset=None, anchor=None, new=True, **kwargs):
    """Indicator: HILO_ZONE (HILO_ZONE)"""
    # Validate Arguments
    close = verify_series(close)
    offset = get_offset(offset)
    anchor = anchor.upper() if anchor and isinstance(anchor, str) and len(anchor) >= 1 else "D"

    mode = mode or "abs"
    decay = kwargs.get("decay", 0)
    u_decay = kwargs.get("u_decay", decay) / 100
    l_decay = kwargs.get("l_decay", decay) / 100
    intraday = kwargs.get("intraday", False)

    u_offset = kwargs.get("u_offset", 0)
    l_offset = kwargs.get("l_offset", 0)

    # Prepare DataFrame to return
    df = DataFrame({"close": close, "HLZ_HIGH": close, "HLZ_LOW": close, })
    df.name = f"HILO_ZONE"
    df.category = "smart-trade"

    anchor_group = df.groupby(df.index.tz_localize(None).to_period(anchor))
    upper_delta, lower_delta = prepare_boundary(close.iloc[0], mode, u_bound, l_bound)
    seq = upper_offset = lower_offset = 0
    broken_close = prev_close = close.iloc[0]
    add_zone = not new
    anchor_segments = []
    # print(new, datetime.now())
    df["u_decay"] = 1 - u_decay
    df["l_decay"] = 1 - l_decay

    for anchor_name, anchor_close in anchor_group:
        # print(new, anchor_name, datetime.now())
        segments = []
        if intraday:
            # prev_date = close.first_valid_index().date()
            seq = upper_offset = lower_offset = 0
            upper_delta, lower_delta = prepare_boundary(anchor_close.iloc[0]["close"], mode, u_bound, l_bound)
            broken_close = prev_close = anchor_close.iloc[0]["close"]
        if new:
            remaining = anchor_close[::]
            while not remaining.empty:
                segment, remaining, broken_close, upper_delta, lower_delta, upper_offset, lower_offset, value = prepare(
                    remaining, broken_close, mode, u_bound, l_bound, upper_offset, lower_offset, upper_delta,
                    lower_delta, l_offset, u_offset)
                segments.append(segment)

            adf = pd.concat(segments)
            adf["HLZ_BREAK"] = (adf["close"] > adf["HLZ_HIGH"]).astype(int) + (adf["close"] < adf["HLZ_LOW"]).astype(
                int) * -1
            adf["HLZ_ZONE"] = adf["HLZ_BREAK"].where(adf["HLZ_BREAK"] != 0).fillna(method="ffill").fillna(0)
            adf["HLZ_SEQ"] = (adf["HLZ_ZONE"] != adf["HLZ_ZONE"].shift()).astype(int).cumsum()
            adf["HLZ_SEQ"] = adf["HLZ_BREAK"].groupby(adf["HLZ_SEQ"]).cumsum()
            anchor_segments.append(adf)

        else:
            for index, row in anchor_close.iterrows():
                # if index.date() != prev_date:
                #     if intraday:
                #         broken_close = row["close"]
                #     else:
                #         broken_close = prev_close
                #     upper_delta, lower_delta  = prepare_boundary(broken_close, mode, u_bound, l_bound)
                upper_delta *= (1 - u_decay)
                lower_delta *= (1 - l_decay)
                upper = df.loc[index, "HLZ_HIGH"] = (broken_close + upper_delta)
                lower = df.loc[index, "HLZ_LOW"] = broken_close - lower_delta
                if not lower < row["close"] < upper:
                    add_zone = False
                    value = 1 if row["close"] >= upper else -1
                    if seq * value >= 0:
                        seq += value
                    else:
                        seq = value
                    df.loc[index, "HLZ_BREAK"] = value
                    df.loc[index, "HLZ_ZONE"] = value
                    df.loc[index, "HLZ_SEQ"] = seq
                    upper_delta, lower_delta = prepare_boundary(row["close"], mode, u_bound, l_bound)
                    if value == 1:
                        upper_offset = 0
                        lower_offset += l_offset
                        lower_delta -= lower_offset if mode == "abs" else row["close"] * lower_offset / 100
                    else:
                        lower_offset = 0
                        upper_offset += u_offset
                        upper_delta -= upper_offset if mode == "abs" else row["close"] * upper_offset / 100
                    broken_close = row["close"]
                else:
                    df.loc[index, "HLZ_BREAK"] = 0
                # prev_date = index.date()
                # prev_close = row["close"]
        # print(new, anchor_name, datetime.now())

    if new:
        df = pd.concat(anchor_segments)

    # print(new, datetime.now())

    if add_zone:
        df["HLZ_ZONE"] = 0
        df["HLZ_SEQ"] = 0
    if intraday:
        df["HLZ_ZONE"] = df["HLZ_ZONE"].groupby(df["HLZ_ZONE"].index.tz_localize(None).to_period(anchor)).fillna(method='ffill')
        df["HLZ_SEQ"] = df["HLZ_SEQ"].groupby(df["HLZ_SEQ"].index.tz_localize(None).to_period(anchor)).fillna(method='ffill')
    else:
        df["HLZ_ZONE"].fillna(inplace=True, method='ffill')
        df["HLZ_SEQ"].fillna(inplace=True, method='ffill')
        df["HLZ_ZONE"] = df["HLZ_ZONE"].groupby(df["HLZ_ZONE"].index.tz_localize(None).to_period(anchor)).fillna(method='bfill')
        df["HLZ_SEQ"] = df["HLZ_SEQ"].groupby(df["HLZ_SEQ"].index.tz_localize(None).to_period(anchor)).fillna(method='bfill')
    df["HLZ_ZONE"].fillna(0, inplace=True)
    df["HLZ_SEQ"].fillna(0, inplace=True)

    # Offset
    if offset != 0:
        df["HLZ_HIGH"] = df["HLZ_HIGH"].shift(offset)
        df["HLZ_LOW"] = df["HLZ_LOW"].shift(offset)
        df["HLZ_BREAK"] = df["HLZ_BREAK"].shift(offset)
        df["HLZ_ZONE"] = df["HLZ_ZONE"].shift(offset)
        df["HLZ_SEQ"] = df["HLZ_SEQ"].shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df["HLZ_HIGH"].fillna(kwargs["fillna"], inplace=True)
        df["HLZ_LOW"].fillna(kwargs["fillna"], inplace=True)
        df["HLZ_BREAK"].fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        df["HLZ_HIGH"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HLZ_LOW"].fillna(method=kwargs["fill_method"], inplace=True)
        df["HLZ_BREAK"].fillna(method=kwargs["fill_method"], inplace=True)

    df["HLZ_HIGH"].category = df["HLZ_LOW"].category = df["HLZ_BREAK"].category = df["HLZ_ZONE"].category = df[
        "HLZ_SEQ"].category = "smart-trade"
    df.drop('close', axis=1, inplace=True)
    df.drop('u_decay', axis=1, inplace=True)
    df.drop('l_decay', axis=1, inplace=True)
    # print(new, datetime.now())
    return df


hlz.__doc__ = \
    """HILO ZONE (HILO_ZONE)
    
    HILO ZONE (HILO_ZONE).
    
    Sources:
        https://smart-trade.reluminos.com
    
    Calculation:
        zone_high[t] = close[t-1] + u_bound if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_high[t-1]
        zone_low[t] = close[t-1] - l_bound if not zone_high[t-1] > close[t-1] > zone_low[t-1] else zone_low[t-1]
    
    Args:
        close (pd.Series): Series of 'close's
        u_bound (float): Upper Bound of zone to be created
        l_bound (float): Lower Bound of zone to be created
        offset (int): How many periods to offset the result. Default: 0
        mode (abs/pct): bound type (Absolute or pct), default abs
    
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    
    Returns:
        pd.DataFrame: HLZ_HIGH (line), HLZ_LOW (line), HLZ_BREAK (line), HLZ_ZONE (line), HLZ_SEQ (line) columns.
    """
