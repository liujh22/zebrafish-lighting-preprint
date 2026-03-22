#%%
import os
import pandas as pd
import numpy as np
from plotnine import (
    ggplot, aes,
    geom_line, geom_ribbon,
    annotate,
    scale_x_continuous,
    labs,
    theme_minimal, theme,
    element_line, element_blank
)
from plotnine.themes.themeable import axis_ticks_minor
import matplotlib as mpl
from get_visualization_ready import set_font_type,load_data

#%%
# Call the function to set the font type
set_font_type()
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

# --- Path settings --- #
DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"
df = load_data(filename=DATA_FILENAME)

for col in ["cond1", "ztime", "cond0", "expNum"]:
    df[col] = df[col].astype("category")
df["bout_time"] = pd.to_datetime(df["bout_time"])

#%%
# Calculate the experiment start time (Day‑1 10 AM) for each expNum, and optionally filter the first 48 hours
df["exp_start_time"] = (
    df.groupby("expNum")["bout_time"]
      .transform(lambda x: x.min().floor("D") + pd.Timedelta(hours=10))
)
df["third_day_10am"] = df["exp_start_time"] + pd.Timedelta(days=2)
# Optional filtering:
# df = df[
#     (df["bout_time"] >= df["exp_start_time"]) &
#     (df["bout_time"] < df["third_day_10am"])
# ].copy()

#%%
# --- Time binning --- #
# Calculate hours elapsed since exp_start_time
df["time_offset_hours"] = (df["bout_time"] - df["exp_start_time"]).dt.total_seconds() / 3600
# Calculate the "left edge" of each bin
df["hour_bin_left"] = np.floor(df["time_offset_hours"] / 2) * 2
# Calculate the "bin center": left edge + 1 hour
df["hour_bin_center"] = df["hour_bin_left"] + 1

# --- Calculate the "median of medians" summary for WHM --- #
param = "WHM"
# Median WHM per expNum × bin × cond1
medians_by_exp = (
    df.groupby(["expNum", "hour_bin_center", "cond1"])[param]
      .median()
      .reset_index(name="median_value")
)
# Aggregate across experiments: mean, min, max of medians
summary = (
    medians_by_exp
      .groupby(["hour_bin_center", "cond1"])["median_value"]
      .agg(
          mean_of_medians="mean",
          lower_bound="min",
          upper_bound="max"
      )
      .reset_index()
)

# Nighttime shaded intervals (defined by bin centers)
shaded_intervals = [(13, 23), (37, 47)]  # These numbers represent "bin centers"

# --- Plot using plotnine --- #
p = (
    ggplot(summary, aes(x="hour_bin_center", y="mean_of_medians", color="cond1"))
    # Add nighttime shaded areas
    + annotate("rect",
               xmin=shaded_intervals[0][0], xmax=shaded_intervals[0][1],
               ymin=-np.inf, ymax=np.inf,
               fill="grey", alpha=0.5
              )
    + annotate("rect",
               xmin=shaded_intervals[1][0], xmax=shaded_intervals[1][1],
               ymin=-np.inf, ymax=np.inf,
               fill="grey", alpha=0.5
              )
    # Add ribbon and line
    + geom_ribbon(aes(ymin="lower_bound", ymax="upper_bound"),
                  fill="grey", alpha=0.5)
    + geom_line()
    # X-axis ticks and labels
    + scale_x_continuous(
        breaks=[14, 22, 38, 46],  # 13+1, 23+? etc. You can adjust based on actual bin centers
        labels=["11 PM", "9 AM", "11 PM", "9 AM"],
        limits=(1, 49)
      )
    + labs(
        title=f"Plot for {param}",
        x="Time (hours since Day‑1 10 AM, bin center)",
        y=param
      )
    + theme_minimal()
    + theme(
        axis_line=element_line(color="black"),
        axis_ticks_minor=element_blank(),
        axis_ticks=element_line(color="black"),
        panel_grid=element_blank()
      )
)
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Save and display plot
out_path = os.path.join(OUTPUT_DIR, f"{plot_ID}_{param}_circadian.pdf")
p.save(out_path, width=10, height=5)
print(f"Saved plot to {out_path}")
print(p)
# %%
