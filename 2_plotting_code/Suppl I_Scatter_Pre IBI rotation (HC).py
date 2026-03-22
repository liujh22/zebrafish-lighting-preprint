#%%

import os
import numpy as np
import pandas as pd
from datetime import date
from plotnine import (
    ggplot, aes, geom_point, geom_line, geom_text, facet_grid,
    scale_color_manual, theme_minimal, theme, xlim, ylim, labs,
    element_line, element_blank
)
import matplotlib as mpl
from plotnine.themes.themeable import axis_ticks_minor
import scipy.stats as st
from get_visualization_ready import set_font_type, load_data, get_haircell_daytime_data
from scipy import stats as ss

# Ensure text remains selectable in saved PDF plots
set_font_type()
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
# ------------------------------
# Set the working directory to the folder containing preprocessed CSVs
# ------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")

os.makedirs(STATS_DIR, exist_ok=True)
# ------------------------------
# Load the data and retain only the middle bout of consecutive bouts
# ------------------------------
DATA_FILENAME = "haircell_all_Consecutive_bout_3_strict.csv"

raw_data = load_data(filename=DATA_FILENAME)
for col in ['cond1', 'ztime', 'cond0', 'expNum']:
    raw_data[col] = raw_data[col].astype('category')

ctrl_day = raw_data[(raw_data['cond1'] == "1ctrl") & (raw_data['ztime'] == "day")]
cond_day = raw_data[(raw_data['cond1'] == "2cond") & (raw_data['ztime'] == "day")]
combine_data  = pd.concat([ctrl_day, cond_day], ignore_index=True)
combine_data = combine_data.loc[combine_data['bouts']==2].reset_index(drop=True)
# ------------------------------
# Specify the predictor and response variables
# ------------------------------
x_var = "preIBI_rot"
y_var = "rot_total"

ctrl_data = combine_data[combine_data['cond1'] == "1ctrl"].copy()
lesion_data = combine_data[combine_data['cond1'] == "2cond"].copy()

# ------------------------------
# Compute the median pre-IBI time in the dark-day data for splitting groups
# ------------------------------
median_pre_ibi = ctrl_data['pre_IBI_time'].quantile(0.5)

# ------------------------------
# Label each observation as 'Long IBI' or 'Short IBI' based on the median cutoff
# ------------------------------
ctrl_data['IBI_group'] = np.where(
    ctrl_data['pre_IBI_time'] >= median_pre_ibi,
    "Long IBI",
    "Short IBI"
)
# Preserve group ordering for plotting
ctrl_data['IBI_group'] = pd.Categorical(
    ctrl_data['IBI_group'],
    categories=["Long IBI", "Short IBI"],
    ordered=True
)

lesion_data['IBI_group'] = np.where(
    lesion_data['pre_IBI_time'] >= median_pre_ibi,
    "Long IBI",
    "Short IBI"
)
# Preserve group ordering for plotting
lesion_data['IBI_group'] = pd.Categorical(
    lesion_data['IBI_group'],
    categories=["Long IBI", "Short IBI"],
    ordered=True
)

#%%
# ------------------------------
# Fit robust regression (Tukey's Biweight) for each IBI group
# ------------------------------
import statsmodels.api as sm
import statsmodels.robust.norms as norms
from sklearn.metrics import r2_score


data_toplt = lesion_data
predictions = []
r2_labels = []

for group_name, group_df in data_toplt.groupby("IBI_group"):
    subset = group_df[[x_var, y_var]].dropna()
    if len(subset) > 1:
        # Add constant term for intercept
        X = sm.add_constant(subset[x_var])
        y = subset[y_var]

        # Fit the robust linear model
        model = sm.RLM(y, X, M=norms.TukeyBiweight())
        results = model.fit()
        intercept, slope = results.params['const'], results.params[x_var]

        # Create a grid over the central 99% of x values for plotting the fit
        x_min = subset[x_var].quantile(0.005)
        x_max = subset[x_var].quantile(0.995)
        x_grid = np.linspace(x_min, x_max, 100)
        y_grid = intercept + slope * x_grid

        # Compute R² for annotation
        y_fit = intercept + slope * subset[x_var]
        r2 = r2_score(subset[y_var], y_fit)

        r2_labels.append({
            'IBI_group': group_name,
            'x': subset[x_var].quantile(0.95),
            'y': subset[y_var].quantile(0.95),
            'label': f"R² = {r2:.3f}"
        })

        predictions.append(pd.DataFrame({
            x_var: x_grid,
            y_var: y_grid,
            'IBI_group': group_name
        }))

pred_df = pd.concat(predictions, ignore_index=True)
r2_df = pd.DataFrame(r2_labels)

# ------------------------------
# Create a scatter plot with robust regression lines and R² annotations
# ------------------------------
plot = (
    ggplot(data_toplt, aes(x=x_var, y=y_var, color='IBI_group'))
    + geom_point(alpha=0.05, size=3)
    + geom_line(data=pred_df, mapping=aes(x=x_var, y=y_var, color='IBI_group'), size=1.2)
    + facet_grid('~IBI_group')
    + scale_color_manual(values=["#4CB9CC", "#D3917D"])
    + theme_minimal()
)

plot += geom_text(
    data=r2_df,
    mapping=aes(x='x', y='y', label='label'),
    inherit_aes=False,
    size=9,
    ha='right',
    va='top'
)

# ------------------------------
# Determine plot axis limits from data quantiles
# ------------------------------
x_lower, x_upper = (
    data_toplt[x_var].quantile(0.005),
    data_toplt[x_var].quantile(0.995)
)
y_lower, y_upper = (
    data_toplt[y_var].quantile(0.005),
    data_toplt[y_var].quantile(0.995)
)

plot = (
    plot
    + xlim(x_lower, x_upper)
    + ylim(y_lower, y_upper)
    + theme(
        panel_grid=element_blank(),
        axis_ticks_minor=element_blank(),
        axis_line=element_line(color="black"),
        axis_ticks=element_line(color="black")
    )
    + labs(x=x_var, y=y_var)
)

# Display the plot in a Jupyter notebook
print(plot)

# ------------------------------
# Save the figure to the Plots_folder with today's date in the filename
# ------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
filename = f"{plot_ID}_scatter_{y_var}_by_{x_var}.pdf"
output_path = os.path.join(OUTPUT_DIR, filename)
plot.save(output_path, width=6, height=3)




#%%

# ------------------------------
# Compute slope, R², and p-value for each IBI group and print a summary table
# ------------------------------
stats = []
for group_name, group_df in ctrl_data.groupby("IBI_group"):
    subset = group_df[[x_var, y_var]].dropna()
    if len(subset) > 1:
        X = sm.add_constant(subset[x_var])
        y = subset[y_var]
        model = sm.RLM(y, X, M=norms.TukeyBiweight())
        results = model.fit()
        slope = results.params[x_var]
        se = results.bse[x_var]
        y_pred = results.predict(X)
        rsq = r2_score(subset[y_var], y_pred)
        # Calculate p-value
        boot_slopes = []
        for _ in range(1000):
            boot_subset = subset.sample(frac=1, replace=True)
            X_boot = sm.add_constant(boot_subset[x_var])
            y_boot = boot_subset[y_var]
            try:
                boot_model = sm.RLM(y_boot, X_boot, M=norms.TukeyBiweight())
                boot_results = boot_model.fit()
                boot_slopes.append(boot_results.params[x_var])
            except:
                continue

        boot_slopes = np.array(boot_slopes)

        # Confidence interval
        ci_lower = np.percentile(boot_slopes, 2.5)
        ci_upper = np.percentile(boot_slopes, 97.5)

        # Is 0 inside the 95% CI? → not significant if so
        zero_in_ci = (ci_lower <= 0 <= ci_upper)

        # Two-tailed p-value: proportion of bootstrap slopes on the opposite side of 0
        p_value = 2 * min(
            np.mean(np.array(boot_slopes) <= 0),
            np.mean(np.array(boot_slopes) >= 0)
        )
        stats.append({
            'IBI_group': group_name,
            'Slope': slope,
            'Rsquare': rsq,
            'pvalue': p_value
        })

stats_df = pd.DataFrame(stats)
print("\nDark Pre-IBI: Slope, Rsquare and p-value Table:")
print(stats_df.to_string(index=False))




# ------------------------------
# Write LaTeX macro definitions for each statistic to file
# ------------------------------
macros_path = os.path.join(STATS_DIR, f"{plot_ID}_GroupedScatterHCBoutRotationPreIBIMacros.tex")

with open(macros_path, "w") as tex_file:
    for row in stats:
        grp = row['IBI_group'].replace(" ", "")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCCtrlAbsSlope{{{abs(row['Slope']):.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCCtrlSlope{{{row['Slope']:.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCCtrlRsquare{{{row['Rsquare']:.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCCtrlPvalue{{{row['pvalue']:.3e}}}\n")

print(f"Saved LaTeX macros to {macros_path}")


stats = []
for group_name, group_df in lesion_data.groupby("IBI_group"):
    subset = group_df[[x_var, y_var]].dropna()
    if len(subset) > 1:
        X = sm.add_constant(subset[x_var])
        y = subset[y_var]
        model = sm.RLM(y, X, M=norms.TukeyBiweight())
        results = model.fit()
        slope = results.params[x_var]
        se = results.bse[x_var]
        y_pred = results.predict(X)
        rsq = r2_score(subset[y_var], y_pred)
        # Calculate p-value
        boot_slopes = []
        for _ in range(1000):
            boot_subset = subset.sample(frac=1, replace=True)
            X_boot = sm.add_constant(boot_subset[x_var])
            y_boot = boot_subset[y_var]
            try:
                boot_model = sm.RLM(y_boot, X_boot, M=norms.TukeyBiweight())
                boot_results = boot_model.fit()
                boot_slopes.append(boot_results.params[x_var])
            except:
                continue

        boot_slopes = np.array(boot_slopes)

        # Confidence interval
        ci_lower = np.percentile(boot_slopes, 2.5)
        ci_upper = np.percentile(boot_slopes, 97.5)

        # Is 0 inside the 95% CI? → not significant if so
        zero_in_ci = (ci_lower <= 0 <= ci_upper)

        # Two-tailed p-value: proportion of bootstrap slopes on the opposite side of 0
        p_value = 2 * min(
            np.mean(np.array(boot_slopes) <= 0),
            np.mean(np.array(boot_slopes) >= 0)
        )
        stats.append({
            'IBI_group': group_name,
            'Slope': slope,
            'Rsquare': rsq,
            'pvalue': p_value
        })

stats_df = pd.DataFrame(stats)
print("\nDark Pre-IBI: Slope, Rsquare and p-value Table:")
print(stats_df.to_string(index=False))

# ------------------------------
# Write LaTeX macro definitions for each statistic to file
# ------------------------------
macros_path = os.path.join(STATS_DIR, "Suppl I_GroupedScatterHCBoutRotationPreIBIMacros.tex")

with open(macros_path, "a") as tex_file:
    for row in stats:
        grp = row['IBI_group'].replace(" ", "")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCLesionAbsSlope{{{abs(row['Slope']):.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCLesionSlope{{{row['Slope']:.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCLesionRsquare{{{row['Rsquare']:.3f}}}\n")
        tex_file.write(f"\\def\\GroupedScatterBoutRotationPreIBI{grp}HCLesionPvalue{{{row['pvalue']:.3e}}}\n")

print(f"Saved LaTeX macros to {macros_path}")


# %%
print_data = pd.concat([ctrl_data, lesion_data], ignore_index=True)
print_data['compensation_residual'] = print_data['rot_total'] + print_data['preIBI_rot']

print_data = print_data.loc[
    (print_data['IBI_group'] == "Long IBI")
].reset_index(drop=True)

print(print_data.groupby('cond1')['compensation_residual'].median())
print("IQR")
print(print_data.groupby('cond1')['compensation_residual'].apply(
     ss.iqr
))
print("MAD")
print(print_data.groupby('cond1')['compensation_residual'].apply(
     ss.median_abs_deviation
))
# %%

# %%
