#%%
import os
import numpy as np
import pandas as pd
from datetime import timedelta
import matplotlib as mpl
from scipy import (signal)
import seaborn as sns
import matplotlib.pyplot as plt
# from plotnine import (
#     ggplot, aes, geom_line, geom_ribbon,
#     scale_y_continuous, scale_x_continuous,
#     labs, theme_minimal, facet_grid,
#     theme, element_line, element_blank
# )
from get_visualization_ready import set_font_type, load_data


# ------------------------------
# Configuration
# ------------------------------

set_font_type()

# Working directory and I/O paths
output_folder = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(output_folder, exist_ok=True)
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

#%%
# ------------------------------
# Load and prepare data
# ------------------------------
DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"

df = load_data(DATA_FILENAME)

# Cast these columns to categorical (factor in R)
for col in ['cond1', 'ztime', 'cond0', 'expNum']:
    df[col] = df[col].astype('category')

# Drop duplicate columns if any
df = df.loc[:, ~df.columns.duplicated()]

# ------------------------------
# Analysis parameters
# ------------------------------
# List numeric parameters to process

# ------------------------------
# Loop over parameters
# ------------------------------
for param in ['pre_IBI_time', 'WHM', 'rot_total']:
    temp = df.copy()
    temp['bout_time'] = pd.to_datetime(temp['bout_time'])

    # Compute experiment start at 10:00 on first day of each expNum
    min_bout = temp.groupby('expNum')['bout_time'].transform('min')
    exp_start = min_bout.dt.normalize() + pd.Timedelta(hours=10)
    third_day_10am = exp_start + pd.Timedelta(days=2)

    # Keep only bouts between day 1 10:00 and day 3 10:00
    mask = (temp['bout_time'] >= exp_start) & (temp['bout_time'] < third_day_10am)
    temp = temp.loc[mask].copy()

    # Compute time offset in hours and bin into 2-hour intervals
    temp['time_offset_hours'] = (
        temp['bout_time'] - exp_start
    ).dt.total_seconds() / 3600
    temp['hour_interval_shifted'] = np.floor(temp['time_offset_hours'] / 2) * 2
    temp['hour_interval_shifted_single_short_bin'] = np.floor(temp['time_offset_hours'] / 0.5) * 0.5


    #%

    # 1) Median within each experiment × time bin × cond1
    medians = (
        temp
        .groupby(['expNum', 'hour_interval_shifted', 'cond1'])[param]
        .median()
        .reset_index(name='median_value')
    )

    # 2) Z-transform the medians within each expNum × cond1 group
    medians['median_z'] = (
        medians
        .groupby(['expNum', 'cond1'])['median_value']
        .transform(lambda x: (x - x.mean()) / x.std(ddof=0))
    )

    # 1) Median within each experiment × time bin × cond1
    medians_smallBins = (
        temp
        .groupby(['expNum', 'hour_interval_shifted_single_short_bin', 'cond1'])[param]
        .median()
        .reset_index(name='median_value')
    )

    # 2) Z-transform the medians within each expNum × cond1 group
    medians_smallBins['median_z'] = (
        medians_smallBins
        .groupby(['expNum', 'cond1'])['median_value']
        .transform(lambda x: (x - x.mean()) / x.std(ddof=0))
    )

    # %
    medians_smallBins['val_fixna'] = medians_smallBins.median_value.interpolate()

    tidied_corr = []
    medians_smallBins = medians_smallBins.loc[medians_smallBins['hour_interval_shifted_single_short_bin']> medians_smallBins['hour_interval_shifted_single_short_bin'].min()]
    grouped = medians_smallBins.groupby(['cond1', 'expNum'], observed=False)

    for (cond1, expNum), group in grouped:
        g = group['val_fixna'].values

        # Subtract mean to center the signal
        g = g - g.mean()

        # Compute raw autocorrelation
        corr = signal.correlate(g, g, mode='full', method='auto')
        lags = signal.correlation_lags(len(g), len(g), mode='full')

        # Normalize by the 0-lag (central) value
        center_index = len(g) - 1
        norm_corr = corr / corr[center_index] if corr[center_index] != 0 else corr

        # Append to list
        for lag, value in zip(lags, norm_corr):
            tidied_corr.append({
                'cond1': cond1,
                'expNum': expNum,
                'lag': lag,
                param: value
            })

    tidied_corr = pd.DataFrame.from_records(tidied_corr)
    # # %%
    # g = sns.relplot(
    #     data=tidied_corr,
    #     x='lag',
    #     y='value',
    #     col='cond1',
    #     hue='expNum',
    #     kind='line',
    #     facet_kws={'sharey': False, 'sharex': True},
    #     height=3,
    #     aspect=1.5,
    #     errorbar='sd',
    # )
    tidied_corr['lag_hour'] = tidied_corr['lag'] * 0.5

    p = sns.relplot(
        data=tidied_corr.query("lag >=0"),
        x='lag_hour',
        y=param,
        hue='cond1',
        kind='line',
        facet_kws={'sharey': False, 'sharex': True},
        height=3,
        aspect=1,
        errorbar='sd',
    )
    plt.savefig(os.path.join(output_folder, f'{plot_ID}_{param}_autocorrelation.pdf'), bbox_inches='tight')
    # plt.show()
    # %

    # # Assume tidied_corr is your DataFrame with normalized autocorrelation
    # periods = []
    # tidied_corr['lag_hour'] = tidied_corr['lag'] * 0.5
    # for (cond1,expNum), group in tidied_corr.groupby(['cond1','expNum'], observed=False):
    #     lags = group['lag_hour'].unique()
    #     lags.sort()
        
    #     # Pivot to get mean value across expNum for each lag
    #     mean_corr = group.set_index(lags)[param].values
    #     mean_corr_smooth = signal.savgol_filter(mean_corr, window_length=11, polyorder=3)

    #     # Find peaks (excluding the central peak at lag=0)
    #     peaks, _ = signal.find_peaks(mean_corr_smooth, height=0, prominence=0.1, distance=4)
        
    #     # Filter out lag = 0
    #     nonzero_peaks = [lags[p] for p in peaks if lags[p] != 0]

    #     if nonzero_peaks:
    #         estimated_period = abs(nonzero_peaks[0])
    #     else:
    #         estimated_period = None
            
    #     periods.append({
    #         'cond1': cond1,
    #         'period': estimated_period,
    #         'expNum': expNum,
    #     })

    # periods_df = pd.DataFrame(periods)
    # print(periods_df)

    # sns.catplot(
    #     kind='point',
    #     data=periods_df,
    #     x='cond1',
    #     y='period',
    #     # hue='expNum',
    #     height=3,
    #     aspect=1,
    #     errorbar='sd',
    # )
    # plt.savefig(os.path.join(output_folder, f'{param}_period.pdf'), bbox_inches='tight')

    
    # Assume tidied_corr is your DataFrame with normalized autocorrelation
    periods = []
    for cond1, group in tidied_corr.groupby('cond1', observed=False):
        lags = group['lag_hour'].unique()
        lags.sort()
        
        # Pivot to get mean value across expNum for each lag
        mean_corr = group.groupby('lag')[param].mean().reset_index().set_index(lags)[param].values
        mean_corr_smooth = signal.savgol_filter(mean_corr, window_length=11, polyorder=3)
        # Find peaks (excluding the central peak at lag=0)
        peaks, _ = signal.find_peaks(mean_corr_smooth, height=0, prominence=0.1, distance=2)
        
        # Filter out lag = 0
        nonzero_peaks = [lags[p] for p in peaks if lags[p] != 0]

        if nonzero_peaks:
            estimated_period = abs(nonzero_peaks[0])
        else:
            estimated_period = None

        periods.append({
            'cond1': cond1,
            'period': estimated_period,
            # 'expNum': expNum,
        })

    periods_df = pd.DataFrame(periods)
    print(periods_df)

    # sns.catplot(
    #     kind='point',
    #     data=periods_df,
    #     x='cond1',
    #     y='period',
    #     # hue='expNum',
    #     height=3,
    #     aspect=1,
    #     errorbar='sd',
    # )
# %%

# %%
