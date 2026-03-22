#%%
import os
import numpy as np
import pandas as pd
from datetime import timedelta
import matplotlib as mpl
from plotnine import (
    ggplot, aes, geom_line, geom_ribbon,
    scale_y_continuous, scale_x_continuous,
    labs, theme_minimal, facet_grid,
    theme, element_line, element_blank
)
from get_visualization_ready import set_font_type, load_data


# ------------------------------
# Configuration
# ------------------------------
# Ensure PDF text remains vectorized
set_font_type()
# Working directory and I/O paths
output_folder = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(output_folder, exist_ok=True)

plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

# ------------------------------
# Load and prepare data
# ------------------------------
DATA_FILENAME="wt_2025_all_Connected_bout_features_strict.csv"
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
numeric_params = ["WHM"]

# ------------------------------
# Loop over parameters
# ------------------------------
for param in numeric_params:
    # Copy and parse times
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

    # 3) Summarize across experiments: mean and range of z-scores
    summary = (
        medians
        .groupby(['hour_interval_shifted', 'cond1'])
        .agg(
            mean_of_medians=('median_z', 'mean'),
            lower_bound=('median_z', 'min'),
            upper_bound=('median_z', 'max')
        )
        .reset_index()
    )

    # ------------------------------
    # Plot
    # ------------------------------
    p = (
        ggplot(summary, aes(x='hour_interval_shifted', y='mean_of_medians', color='cond1'))
        + geom_line()
        + geom_ribbon(aes(ymin='lower_bound', ymax='upper_bound'),
                      fill='gray', alpha=0.5)
        #+ scale_y_continuous(breaks=pretty_breaks(n=3))
        + scale_x_continuous(
            breaks=[13, 23, 37, 47],
            limits=(0, 48),
            labels=["11pm", "9am", "11pm", "9am"]
        )
        + labs(
            title=f"Z-transformed Plot for {param}",
            x="Time (Starting from 10:00)",
            y=f"z-score of {param}"
        )
        + theme_minimal()
        + facet_grid('~cond1')
        + theme(
            axis_line=element_line(color="black"),
            axis_ticks=element_line(color="black"),
            panel_grid=element_blank()
        )
    )

    # Save the figure
    filename = os.path.join(output_folder, f"{plot_ID}_{param}_ztransformed.pdf")
    p.save(filename, width=10, height=5)
    print(f"Saved: {filename}")
# %%
