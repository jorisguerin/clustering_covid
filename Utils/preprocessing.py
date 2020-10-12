import math
import numpy as np
import pandas as pd
from datetime import datetime
import time

def geometric_simple_moving_average(df, len=7):
    return df.apply(np.log).rolling(len).mean().apply(np.exp)

def arithmetic_simple_moving_average(df, len=7):
    return df.rolling(len).mean()

def fix_zeros(df_column):
    ind = np.where(df_column[1:] == 0.0)[0] + 1  # Ignore first value (<NA>).
    for i in ind[ind < df_column.size - 1]:
        df_column.iloc[i] = df_column.iloc[i+1] = 0.5 * df_column.iloc[i+1]

    return df_column

def prepare_data(df):
    df_cum_cases = df.select_dtypes(include='Int64').astype('float')
    df_new_cases = df_cum_cases.diff()  # 1st row is <NA>.

    ''' If using geometric moving average, required to run
    "fix_zeros" several times to avoid running log on a zero'''
    # df_new_cases = df_new_cases.apply(fix_zeros)

    df_cum_cases         = df_new_cases.cumsum()
    df_new_cases.columns = [column.replace('Cum', 'New') for column in df_new_cases.columns]
    df_all = df_cum_cases.join(df_new_cases)

    # df_movAvg = geometric_simple_moving_average(df_all, len=7)
    df_movAvg = arithmetic_simple_moving_average(df_all, len=7)

    return df_cum_cases, df_new_cases, df_all, df_movAvg

def get_conditional_date(ind, df):
    if len(ind) == 0:
        ind        = np.nan
        date       = np.nan
        days_since = np.nan
    else:
        ind        = ind[0]
        date       = df.iloc[ind]['date']
        days_since = (datetime.now() - date).days

    return ind, date, days_since

def get_features(df):
    # Check that 4 weeks of data are available (including the 7 days moving average)
    if df.size < 29+7:
        return { }
    # Remove last row if it seems broken (confirmed cases dropped by >80%).
    if df.iloc[-1]['CumConfirmed'] < 0.20 * df.iloc[-2]['CumConfirmed']:
        df = df[:-1]
    last = df.iloc[-1]
    df_cum_cases, df_new_cases, df_all, df_movAvg = prepare_data(df)
    # Index of outbreak date (cases > 100/20M).
    ind_outbreak, date_outbreak, days_since_outbreak = get_conditional_date(np.where(df_cum_cases.CumConfirmed / df.Population > 5 / 1E6)[0], df)

    # Index of 10x outbreak date (cases > 1000/20M).
    ind_10X, date_10X, _ = get_conditional_date(np.where(df_cum_cases.CumConfirmed / df.Population > 50 / 1E6)[0], df)

    # Index of Peak week.
    ind_peak  = np.argmax(df_movAvg.NewDeaths)
    date_peak = df.iloc[ind_peak]['date']

    # Early Motality.
    if (df_movAvg.shape[0] > ind_outbreak + 17):
        earlyMortality = df_movAvg.NewDeaths.iloc[ind_outbreak + 17] / df_movAvg.NewConfirmed.iloc[ind_outbreak + 3]
    else:
        earlyMortality = np.nan

    # Early Acceleration
    if (df_movAvg.shape[0] <= ind_outbreak + 17) or math.isnan(ind_outbreak):
        earlyAcceleration = np.nan
    elif (df_movAvg.NewConfirmed.iloc[ind_outbreak + 3] == 0.0) or \
         (df_movAvg.NewConfirmed.iloc[ind_outbreak + 10] == 0.0):
         earlyAcceleration = np.nan
    else:
        deltaW0W1 = df_movAvg.NewConfirmed.iloc[ind_outbreak + 10] / df_movAvg.NewConfirmed.iloc[ind_outbreak + 3]
        deltaW1W2 = df_movAvg.NewConfirmed.iloc[ind_outbreak + 17] / df_movAvg.NewConfirmed.iloc[ind_outbreak + 10]
        earlyAcceleration = deltaW1W2 / deltaW0W1

    return {
        'Population':last.Population,
        'OutbreakDate':date_outbreak,
        'DaysSinceOutbreak':days_since_outbreak,
        'DaysTo10X':ind_10X - ind_outbreak,
        'CasesPerMillion':last.CumConfirmed / last.Population * 1E6,
        'DeathsPerMillion':last.CumDeaths / last.Population * 1E6,
        'EarlyMortality':earlyMortality,
        'EarlyAccel':earlyAcceleration,
    }

def get_clustering_data(data):
    features = data.groupby(['Country', 'State']).apply(get_features)
    features = pd.DataFrame(list(features), index=features.index)
    features['Region'] = features.index.get_level_values('Country')
    is_region = (features.index.get_level_values('State') != '<all>')

    features.loc[is_region, 'Region'] = features.index.get_level_values('Country')[is_region] + ':' + \
        features.index.get_level_values('State')[is_region]

    return features

def get_features_with_correct_val(features, names=['DaysTo10X', 'EarlyMortality', 'EarlyAccel']):
    d = features[names + ['Region']].set_index('Region')
    d = d.dropna()

    return d
