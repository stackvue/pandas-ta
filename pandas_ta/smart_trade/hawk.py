import numpy as np
from pandas import Series, DataFrame

from pandas_ta.utils import verify_series


def hawk(close, kappa, lookback, adx, adx_threshold):
    close = verify_series(close)
    adx = verify_series(adx)
    v_hawk = hawkes_process(close, kappa)
    signals = vol_signal(close, v_hawk, lookback)
    positions = get_position_series(signals, adx, adx_threshold)
    df = DataFrame({"signals": positions}, index=close.index)
    return df


def hawkes_process(data: Series, kappa: float) -> Series:
    """
    Compute a recursively decaying sum (a simple hawkes transform) using lfilter.
    (Our recurrence is: y[n] = exp(-kappa) * y[n-1] + data[n].)
    """
    assert kappa > 0.0, "kappa must be positive"
    alpha = np.exp(-kappa)
    arr = data.to_numpy()
    from scipy.signal import lfilter
    # lfilter implements the recursion efficiently. (Initial condition is arr[0].)
    y = lfilter([1], [1, -alpha], arr)
    # Multiply by kappa (as in the original function)
    return Series(y, index=data.index) * kappa


def vol_signal(close: Series, vol_hawk: Series, lookback: int) -> Series:
    """
    Generate a trading signal from a close price series and a hawkes-transformed volatility series.
    In this version the trade condition is inverted so that:
      - if the price change is > 0 then signal = -1 (i.e. take a short)
      - otherwise signal = +1 (i.e. take a long)
    (Signals are still 1, 0, or -1.)
    """
    signal = np.zeros(len(close))
    # Calculate rolling quantiles over the specified lookback period.
    q05 = vol_hawk.rolling(lookback).quantile(0.05)
    q95 = vol_hawk.rolling(lookback).quantile(0.95)

    last_below = -1
    curr_sig = 0

    # Loop over time (starting at 1 so that we have a valid i-1)
    for i in range(1, len(signal)):
        # When volatility is very low, “reset” the signal.
        if vol_hawk.iloc[i] < q05.iloc[i]:
            last_below = i
            curr_sig = 0

        # When volatility jumps above the high quantile (and just crossed above it)
        # and there was a recent low, generate an inverted signal.
        if (vol_hawk.iloc[i] > q95.iloc[i] and
                vol_hawk.iloc[i - 1] <= q95.iloc[i - 1] and
                last_below > 0):
            change = close.iloc[i] - close.iloc[last_below]
            # Invert the original condition: if change > 0, signal is now -1 (short)
            # and if change <= 0, signal is +1 (long)
            curr_sig = -1 if change > 0.0 else 1

        signal[i] = curr_sig

    return Series(signal, index=close.index)


def get_position_series(signal: Series, adx: Series, adx_threshold: float = 3.0) -> Series:
    """
    Returns a position series that updates only when ADX is above a threshold and the signal is extreme.
    (Positions are 1 for long, -1 for short, and 0 for flat.)
    """
    pos = 0
    pos_list = []
    for s, a in zip(signal, adx):
        if a > adx_threshold and s in [1, -1]:
            if s != pos:
                pos = s
        pos_list.append(pos)
    return Series(pos_list, index=signal.index)
