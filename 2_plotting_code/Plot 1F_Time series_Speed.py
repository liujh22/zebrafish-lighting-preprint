#%%
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
import tables
from tqdm import tqdm
from datetime import date
from get_visualization_ready import set_font_type, load_data
from plt_tools import defaultPlotting

#%%

plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

# Set font type and default plotting style
set_font_type()
defaultPlotting()

DATA_FILENAME = "wt_2025_day_timeSeries.csv"

fig_dir = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")

all_around_peak_data = load_data(filename=DATA_FILENAME)

#%%
toplt = all_around_peak_data

all_features = ['propBoutAligned_speed']

mean_data = toplt.groupby(['cond1', 'ztime', 'time_ms'])[all_features].mean().reset_index()
std_data = toplt.groupby(['cond1', 'ztime', 'time_ms'])[all_features].std().reset_index()


#%%
########################################
# Speed timeseries dd_day vs. ld_day #
########################################

# Plot mean lines (second figure, grouped by cond1 for ztime='day')
plt.figure(figsize=(10, 6))

feature_toplt = 'propBoutAligned_speed'  # Feature to plot
# Filter for ztime=='day'
cond1_filtered_mean_data = mean_data[mean_data['ztime'] == 'day']
cond1_filtered_std_data = std_data[std_data['ztime'] == 'day']

p2 = sns.lineplot(
    data=cond1_filtered_mean_data, x='time_ms', y=feature_toplt,
    hue='cond1',  # use cond1 to distinguish groups
    markers=True,  # optional: add markers
    dashes=False   # optional: disable dashed lines
)

# For each cond1, compute mean and std
for cond in cond1_filtered_mean_data['cond1'].unique():
    # Get mean and std for this condition
    cond_mean = cond1_filtered_mean_data[cond1_filtered_mean_data['cond1'] == cond]
    cond_std = cond1_filtered_std_data[cond1_filtered_std_data['cond1'] == cond]

    # Add translucent band representing mean ± std
    plt.fill_between(
        cond_mean['time_ms'],
        cond_mean[feature_toplt] - cond_std[feature_toplt],
        cond_mean[feature_toplt] + cond_std[feature_toplt],
        alpha=0.2  # set transparency
    )

plt.axvline(x=0, linewidth=1, color=".5", zorder=0)  # Add vertical line
plt.title(f"Feature: {feature_toplt} (Grouped by cond1, ztime=day)")  # Add title
plt.xlim([-250, 200])  # Set X-axis limits
plt.grid(False)  # Disable grid background
plt.savefig(os.path.join(fig_dir, f"{plot_ID}_{feature_toplt}.pdf"), format='PDF')
plt.show()
#%%
