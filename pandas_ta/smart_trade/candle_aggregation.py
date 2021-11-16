# -*- coding: utf-8 -*-
import pandas as pd

from pandas_ta.utils import verify_series


def caggr(column, agg_type, group_by=None, group_on=None, **kwargs):
    column = verify_series(column)
    df = pd.DataFrame({column.name: column})
    if group_by:
        grouper = pd.Grouper(freq=group_by)
    else:
        grouper = group_on
    df[column.name + '_' + agg_type] = getattr(df.groupby(grouper)[column.name], agg_type)()

    df.drop(column.name, axis=1, inplace=True)
    df.name = "Candle_Aggregation"
    df.category = "smart-trade"
    return df
