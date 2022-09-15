# -*- coding: utf-8 -*-
import pandas as pd

from pandas_ta.utils import verify_series


def caggr(column, agg_types, group_by=None, group_on=None, **kwargs):
    column = verify_series(column)
    df = pd.DataFrame({column.name: column})
    if group_by:
        grouper = pd.Grouper(freq=group_by)
    else:
        grouper = group_on

    result = df.groupby(grouper)[column.name].agg(agg_types)#.add_prefix(column.name + '_')
    result.name = "Candle_Aggregation"
    result.category = "smart-trade"
    return result
