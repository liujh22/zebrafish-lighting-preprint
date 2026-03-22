#%%

import os
import numpy as np
import pandas as pd
from datetime import date
from plotnine import (
    ggplot, aes, theme_minimal, 
    theme, element_line, element_blank, geom_jitter, stat_summary, facet_wrap
)
from get_visualization_ready import set_font_type, load_data
import matplotlib as mpl
# ———— Start statistical tests ————
from scipy import stats
# Define your set_font_type() function

plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

#========================#
# 0. Set working directory & load data
#========================#

DATA_FILENAME = "wt_2025_all_Consecutive_bout_5_strict.csv"
data = load_data(filename=DATA_FILENAME)

# Convert bout_time to datetime type (similar to R's ymd_hms)
data["bout_time"] = pd.to_datetime(data["bout_time"])

# Convert specified columns to categorical type
for col in ['cond1', 'ztime', 'cond0', 'expNum']:
    data[col] = data[col].astype('category')

#%%
#========================#
# Filter data to retain only rows where cond1 is "dd" or "ld" and ztime is "day"
#========================#
def filter_data(df):
    dd_day = df[(df["cond1"] == "dd") & (df["ztime"] == "day")]
    ld_day = df[(df["cond1"] == "ld") & (df["ztime"] == "day")]
    return pd.concat([dd_day, ld_day], ignore_index=True)

filtered = filter_data(data)

#========================#
# 1) Compute metrics for each epoch
#========================#
# Group by expNum, cond1, ztime, id
group_keys = ["expNum", "cond1", "ztime", "id"]

#%%
# For each group, sort by bout_time and compute metrics
def summarise_epoch(grp):
    # Sort by bout_time in ascending order to ensure correct sequence of consecutive bouts
    grp = grp.sort_values("bout_time")

    # Ensure the group has at least 5 rows (5 consecutive bouts)
    if len(grp) < 5:
        return pd.Series({
            "total_time": np.nan,
            "distance_x": np.nan,
            "distance_y": np.nan,
            "distance_total": np.nan,
            "epoch_speed": np.nan,
            "veering_total": np.nan,
            "veering_speed": np.nan
        })

    # Take the first 5 bouts (indices 0 to 4)
    # Compute total displacement using the initial position of the 5th bout minus the 1st bout
    distance_x = grp["x_initial"].iloc[4] - grp["x_initial"].iloc[0]
    distance_y = grp["y_initial"].iloc[4] - grp["y_initial"].iloc[0]
    distance_total = np.sqrt(distance_x**2 + distance_y**2)

    # Compute total time interval between start times of the 1st and 5th bouts (in seconds)
    total_time = (grp["bout_time"].iloc[4] - grp["bout_time"].iloc[0]).total_seconds()

    # Compute speed = total displacement / total time
    epoch_speed = distance_total / total_time if total_time > 0 else np.nan

    # Compute veering_total: sum of absolute differences of traj_peak across consecutive bouts
    veering_total = np.abs(np.diff(grp["traj_peak"].iloc[0:4])).sum()
    # Compute veering_speed
    veering_speed = veering_total / total_time if total_time > 0 else np.nan

    return pd.Series({
        "total_time": total_time,
        "distance_x": distance_x,
        "distance_y": distance_y,
        "distance_total": distance_total,
        "epoch_speed": epoch_speed,
        "veering_total": veering_total,
        "veering_speed": veering_speed
    })

# Group and apply summarise_epoch function
epoch_summary = filtered.groupby(group_keys, as_index=False, observed=True).apply(summarise_epoch)
epoch_summary = epoch_summary.reset_index(drop=True)

# Now each row in epoch_summary represents one epoch (5 consecutive bouts),
# with computed metrics: total displacement, total time, speed, veering metrics.
# Note: epoch_speed is in units of displacement/sec;
# veering_speed is in units of angle/sec.

#========================#
# Generate 1-second scaled dataset
#========================#
# Assuming constant speed and veering speed, 1s movement and veering would be:
# 1s distance = epoch_speed * 1
# 1s veering = veering_speed * 1
df_1s = epoch_summary.copy()
df_1s["1s_distance_total"] = df_1s["epoch_speed"] * 1
df_1s["1s_veering"] = df_1s["veering_speed"] * 1

# Optionally compute 1s displacement in x and y directions:
df_1s["1s_distance_x"] = (df_1s["distance_x"] / df_1s["total_time"]) * 1
df_1s["1s_distance_y"] = (df_1s["distance_y"] / df_1s["total_time"]) * 1

# Now df_1s contains per-epoch data rescaled to a 1-second time window,
# including 1s displacement and veering.

# ------------------------------
# Compute median (grouped)
# ------------------------------
y_var = "1s_distance_total"
x_var = "cond1"

median_data = df_1s.groupby(
    ['expNum', 'cond1', 'ztime'], as_index=False, observed=True
).agg(median_value=(y_var, "median"))

median_data['median_type'] = y_var

# ------------------------------
# Plot
# ------------------------------
p = (ggplot(median_data, aes(x='cond1', y='median_value', color='cond1'))
     + geom_jitter(shape="o", width=0.15, height=0, size=3, alpha=0.7)
     + stat_summary(aes(group="cond1"), fun_y=np.mean, geom="point",
                    size=5, shape="D", color="black")
     + facet_wrap('~median_type', scales='free_y')
     + theme_minimal()
     + theme(
         axis_ticks_minor = element_blank(),
         axis_line=element_line(color="black"),
         axis_ticks=element_line(color="black"),
         panel_grid=element_blank()
     )
)

print(p)

# ------------------------------
# Save plot
# ------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(OUTPUT_DIR, exist_ok=True)

output_filename = f"{plot_ID}_median_{y_var}_by_{x_var}.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)

p.save(output_path, width=2, height=3)


# 1) Independent samples t-test (treat each epoch's 1s_distance_total as an independent observation)
veering_dd = df_1s.loc[df_1s['cond1']=="dd",   '1s_distance_total'].dropna()
veering_ld = df_1s.loc[df_1s['cond1']=="ld",   '1s_distance_total'].dropna()

t_ind, p_ind = stats.ttest_ind(veering_dd, veering_ld, nan_policy='omit')
print("—— Independent samples t-test (epoch-level 1s_distance_total, dd vs ld) ——")
print(f"t = {t_ind:.3f}, p = {p_ind:.3e}")

# 2) Independent t-test on expNum-median level (pivot by expNum, then test paired medians)
pivot = (
    median_data
    .pivot(index='expNum', columns='cond1', values='median_value')
    .dropna()
)

t_rel, p_rel = stats.ttest_ind(pivot['dd'], pivot['ld'])
print("\n—— Independent t-test (expNum-median 1s_distance_total, dd vs ld) ——")
print(f"t = {t_rel:.3f}, p = {p_rel:.3e}")
# ———— End of statistical tests ————

# --- Create summary table for expNum medians ---
summary_df = median_data.groupby('cond1')['median_value'] \
    .agg(Mean='mean', SD='std') \
    .reset_index() \
    .rename(columns={'cond1': 'Condition'})

print("\nSummary Table:")
print(summary_df.to_string(index=False))

# --- Compute effect size (Cohen's d) for dd vs ld ---
dd_mean = summary_df.loc[summary_df['Condition'] == 'dd', 'Mean'].values[0]
ld_mean = summary_df.loc[summary_df['Condition'] == 'ld', 'Mean'].values[0]
dd_sd = summary_df.loc[summary_df['Condition'] == 'dd', 'SD'].values[0]
ld_sd = summary_df.loc[summary_df['Condition'] == 'ld', 'SD'].values[0]
pooled_sd = np.sqrt((dd_sd**2 + ld_sd**2) / 2)
effect_size = (dd_mean - ld_mean) / pooled_sd

# --- Write LaTeX macro definitions to Desktop ---
macros_path = os.path.join(os.path.expanduser("../Statistics"), f"{plot_ID}_Grouped1sDistanceTotalMacros.tex")
with open(macros_path, "w") as f:
    f.write(f"\\def\\GroupedDistanceTotalDdDayMean{{{dd_mean:.3f}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalDdDaySD{{{dd_sd:.3f}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalLdDayMean{{{ld_mean:.3f}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalLdDaySD{{{ld_sd:.3f}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalDdDayVsLdDayTvalue{{{t_rel:.3f}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalDdDayVsLdDayPvalue{{{p_rel:.3e}}}\n")
    f.write(f"\\def\\GroupedDistanceTotalDdDayVsLdDayEffectSize{{{abs(effect_size):.3f}}}\n")
print(f"Saved LaTeX macros to {macros_path}")
# %%
