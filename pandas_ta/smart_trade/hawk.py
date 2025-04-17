import numpy as np
from pandas import Series, DataFrame

from pandas_ta.utils import verify_series


def hawk(high, low, close,  kappa, lookback, adx_threshold, adx_window):
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    adx_indicator = ADXIndicator(high=high, low=low, close=close, window=adx_window, fillna=True)
    adx = adx_indicator.adx()
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


class IndicatorMixin:
    """Util mixin indicator class"""

    _fillna = False

    def _check_fillna(self, series: Series, value: int = 0) -> Series:
        """Check if fillna flag is True.

        Args:
            series(pandas.Series): calculated indicator series.
            value(int): value to fill gaps; if -1 fill values using 'backfill' mode.

        Returns:
            pandas.Series: New feature generated.
        """
        if self._fillna:
            series_output = series.copy(deep=False)
            series_output = series_output.replace([np.inf, -np.inf], np.nan)
            if isinstance(value, int) and value == -1:
                series = series_output.ffill().bfill()
            else:
                series = series_output.ffill().fillna(value)
        return series

    @staticmethod
    def _true_range(
        high: Series, low: Series, prev_close: Series
    ) -> Series:
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = DataFrame(data={"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
        return true_range


class ADXIndicator(IndicatorMixin):
    """Average Directional Movement Index (ADX)

    The Plus Directional Indicator (+DI) and Minus Directional Indicator (-DI)
    are derived from smoothed averages of these differences, and measure trend
    direction over time. These two indicators are often referred to
    collectively as the Directional Movement Indicator (DMI).

    The Average Directional Index (ADX) is in turn derived from the smoothed
    averages of the difference between +DI and -DI, and measures the strength
    of the trend (regardless of direction) over time.

    Using these three indicators together, chartists can determine both the
    direction and strength of the trend.

    http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:average_directional_index_adx

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        window(int): n period.
        fillna(bool): if True, fill nan values.
    """

    def __init__(
        self,
        high: Series,
        low: Series,
        close: Series,
        window: int = 14,
        fillna: bool = False,
    ):
        self._high = high
        self._low = low
        self._close = close
        self._window = window
        self._fillna = fillna
        self._run()

    def _run(self):
        if self._window == 0:
            raise ValueError("window may not be 0")

        close_shift = self._close.shift(1)

        pdm = _get_min_max(self._high, close_shift, "max")
        pdn = _get_min_max(self._low, close_shift, "min")

        diff_directional_movement = pdm - pdn

        self._trs_initial = np.zeros(self._window - 1)
        self._trs = np.zeros(len(self._close) - (self._window - 1))
        self._trs[0] = diff_directional_movement.dropna().iloc[0 : self._window].sum()
        diff_directional_movement = diff_directional_movement.reset_index(drop=True)

        for i in range(1, len(self._trs) - 1):
            self._trs[i] = (
                self._trs[i - 1]
                - (self._trs[i - 1] / float(self._window))
                + diff_directional_movement[self._window + i]
            )

        diff_up = self._high - self._high.shift(1)
        diff_down = self._low.shift(1) - self._low

        pos = abs(((diff_up > diff_down) & (diff_up > 0)) * diff_up)
        neg = abs(((diff_down > diff_up) & (diff_down > 0)) * diff_down)

        self._dip = np.zeros(len(self._close) - (self._window - 1))
        self._dip[0] = pos.dropna().iloc[0 : self._window].sum()

        pos = pos.reset_index(drop=True)

        for i in range(1, len(self._dip) - 1):
            self._dip[i] = (
                self._dip[i - 1]
                - (self._dip[i - 1] / float(self._window))
                + pos[self._window + i]
            )

        self._din = np.zeros(len(self._close) - (self._window - 1))
        self._din[0] = neg.dropna().iloc[0 : self._window].sum()

        neg = neg.reset_index(drop=True)

        for i in range(1, len(self._din) - 1):
            self._din[i] = (
                self._din[i - 1]
                - (self._din[i - 1] / float(self._window))
                + neg[self._window + i]
            )

    def adx(self) -> Series:
        """Average Directional Index (ADX)

        Returns:
            pandas.Series: New feature generated.tr
        """
        dip = np.zeros(len(self._trs))

        for idx, value in enumerate(self._trs):
            if value != 0:
                dip[idx] = 100 * (self._dip[idx] / value)

            else:
                dip[idx] = 0

        din = np.zeros(len(self._trs))

        for idx, value in enumerate(self._trs):
            if value != 0:
                din[idx] = 100 * (self._din[idx] / value)

            else:
                din[idx] = 0

        directional_index = np.zeros(len(self._trs))

        for idx in range(len(self._trs)):
            if dip[idx] + din[idx] != 0:
                directional_index[idx] = 100 * np.abs(
                    (dip[idx] - din[idx]) / (dip[idx] + din[idx])
                )

            else:
                directional_index[idx] = 0

        adx_series = np.zeros(len(self._trs))
        adx_series[self._window] = directional_index[0 : self._window].mean()

        for i in range(self._window + 1, len(adx_series)):
            adx_series[i] = (
                (adx_series[i - 1] * (self._window - 1)) + directional_index[i - 1]
            ) / float(self._window)

        adx_series = np.concatenate((self._trs_initial, adx_series), axis=0)
        adx_series = Series(data=adx_series, index=self._close.index)
        adx_series = self._check_fillna(adx_series, value=20)

        return Series(adx_series, name="adx")

    def adx_pos(self) -> Series:
        """Plus Directional Indicator (+DI)

        Returns:
            pandas.Series: New feature generated.
        """
        dip = np.zeros(len(self._close))

        for i in range(1, len(self._trs) - 1):
            if self._trs[i] != 0:
                dip[i + self._window] = 100 * (self._dip[i] / self._trs[i])

            else:
                dip[i + self._window] = 0

        adx_pos_series = self._check_fillna(
            Series(dip, index=self._close.index), value=20
        )

        return Series(adx_pos_series, name="adx_pos")

    def adx_neg(self) -> Series:
        """Minus Directional Indicator (-DI)

        Returns:
            pandas.Series: New feature generated.
        """
        din = np.zeros(len(self._close))

        for i in range(1, len(self._trs) - 1):
            if self._trs[i] != 0:
                din[i + self._window] = 100 * (self._din[i] / self._trs[i])

            else:
                din[i + self._window] = 0

        adx_neg_series = self._check_fillna(
            Series(din, index=self._close.index), value=20
        )

        return Series(adx_neg_series, name="adx_neg")

def _get_min_max(series1: Series, series2: Series, function: str = "min"):
    """Find min or max value between two lists for each index"""
    series1 = np.array(series1)
    series2 = np.array(series2)
    if function == "min":
        output = np.amin([series1, series2], axis=0)
    elif function == "max":
        output = np.amax([series1, series2], axis=0)
    else:
        raise ValueError('"f" variable value should be "min" or "max"')

    return Series(output)
