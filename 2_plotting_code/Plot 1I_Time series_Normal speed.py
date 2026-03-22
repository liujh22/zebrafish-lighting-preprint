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
# Set default background color to white
plt.style.use('default')

DATA_FILENAME = "wt_2025_day_timeSeries.csv"

OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")

all_around_peak_data = load_data(filename=DATA_FILENAME)

all_around_peak_data = all_around_peak_data.assign(
    normal_speed=all_around_peak_data['propBoutAligned_speed'] /
                 all_around_peak_data.groupby(['bout_number','cond1', 'ztime'])['peak_speed'].transform('mean')
)

#%%
toplt = all_around_peak_data
fig_dir = "../Plots_folder"

all_features = ['normal_speed']

mean_data = toplt.groupby(['cond1', 'ztime', 'time_ms'])[all_features].mean().reset_index()
std_data = toplt.groupby(['cond1', 'ztime', 'time_ms'])[all_features].std().reset_index()


#%%
###################################
##### Plotting Starts Here ######
###################################

# Define the conditions
cond1_day_dd = (mean_data['cond1'] == 'dd') & (mean_data['ztime'] == 'day')
cond1_day_ld = (mean_data['cond1'] == 'll') & (mean_data['ztime'] == 'day')

for feature_toplt in tqdm(all_features):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Filter data for day in dd
    day_dd_mean = mean_data[cond1_day_dd]
    day_dd_std = std_data[cond1_day_dd]

    # Filter data for day in ld
    day_ld_mean = mean_data[cond1_day_ld]
    day_ld_std = std_data[cond1_day_ld]

    # Plot day in dd
    sns.lineplot(
        data=day_dd_mean, x='time_ms', y=feature_toplt,
        label="Day (DD)", color="blue",
        markers=True, dashes=False, ax=ax
    )
    ax.fill_between(
        day_dd_mean['time_ms'],
        day_dd_mean[feature_toplt] - day_dd_std[feature_toplt],
        day_dd_mean[feature_toplt] + day_dd_std[feature_toplt],
        alpha=0.2, color="blue"
    )

    # Plot day in ld
    sns.lineplot(
        data=day_ld_mean, x='time_ms', y=feature_toplt,
        label="Day (LD)", color="red",
        markers=True, dashes=False, ax=ax
    )
    ax.fill_between(
        day_ld_mean['time_ms'],
        day_ld_mean[feature_toplt] - day_ld_std[feature_toplt],
        day_ld_mean[feature_toplt] + day_ld_std[feature_toplt],
        alpha=0.2, color="red"
    )

    ax.axvline(x=0, linewidth=1, color=".5", zorder=0)  # Add vertical line at x=0
    ax.set_title(f"Feature: {feature_toplt} | Day (DD) vs Day (LL)")  # Title
    ax.legend(title="Condition")  # Legend
    ax.grid(False)  # Turn off grid
    ax.set_xlabel("time_ms")
    ax.set_ylabel(feature_toplt)

    plt.suptitle(f"Feature: {feature_toplt} (Day-DD vs Day-LL)", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(fig_dir, f"{plot_ID}_{feature_toplt}_DayDD_vs_DayLL.pdf"), format='PDF')
    plt.show()
#%%
