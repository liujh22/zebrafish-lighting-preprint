"""
Script: Plot Suppl C rot_total vs preIBI_rot relationship (Light condition)
Description: Analyzes and visualizes the relationship between rotation and pre-IBI rotation,
             stratified by IBI duration groups in light condition data, using robust regression.
"""
#%%
import os
from datetime import date
import numpy as np
import pandas as pd
from plotnine import (
    ggplot, aes, geom_point, geom_line, geom_text, facet_grid,
    scale_color_manual, theme_minimal, theme, xlim, ylim, labs,
    element_line, element_blank
)
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.robust.norms as norms
from sklearn.metrics import r2_score
from get_visualization_ready import set_font_type, load_data, get_daytime_data


def main():
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Consecutive_bout_3_strict.csv"
    X_VAR = "preIBI_rot"
    Y_VAR = "rot_total"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")

    PLOT_DIMS = (6, 3)  # width, height in inches
    SAMPLE_SIZE = 10000  # Number of points to sample for plotting
    BOUT_NUMBER = 2  # Middle bout of consecutive bouts
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    raw_data = load_data(filename=DATA_FILENAME)

    # Filter for middle bout of consecutive bouts
    raw_data = raw_data[raw_data['bouts'] == BOUT_NUMBER].copy()

    combine_data = get_daytime_data(raw_data)
    ld_data = combine_data[combine_data['cond1'] == "ld"].copy()

    # Sample data for plotting efficiency
    ld_data = ld_data.sample(min(SAMPLE_SIZE, len(ld_data)), random_state=42)

    # --------------------------------------------------------------------------
    # Create IBI Duration Groups
    # --------------------------------------------------------------------------
    median_pre_ibi = combine_data[combine_data['cond1'] == "dd"]['pre_IBI_time'].quantile(0.5)
    ld_data['IBI_group'] = np.where(
        ld_data['pre_IBI_time'] >= median_pre_ibi,
        "Long IBI",
        "Short IBI"
    )
    ld_data['IBI_group'] = pd.Categorical(
        ld_data['IBI_group'],
        categories=["Long IBI", "Short IBI"],
        ordered=True
    )

    # --------------------------------------------------------------------------
    # Fit Robust Regression Models
    # --------------------------------------------------------------------------
    predictions = []
    r2_labels = []
    stats_results = []

    for group_name, group_df in ld_data.groupby("IBI_group"):
        subset = group_df[[X_VAR, Y_VAR]].dropna()
        if len(subset) > 1:
            X = sm.add_constant(subset[X_VAR])
            y = subset[Y_VAR]

            # Robust regression
            model = sm.RLM(y, X, M=norms.TukeyBiweight())
            results = model.fit()
            intercept, slope = results.params['const'], results.params[X_VAR]

            # Create prediction line
            x_min = subset[X_VAR].quantile(0.005)
            x_max = subset[X_VAR].quantile(0.995)
            x_grid = np.linspace(x_min, x_max, 100)
            y_grid = intercept + slope * x_grid

            # Compute R²
            y_fit = intercept + slope * subset[X_VAR]
            r2 = r2_score(subset[Y_VAR], y_fit)

            # Store for plotting
            predictions.append(pd.DataFrame({
                X_VAR: x_grid,
                Y_VAR: y_grid,
                'IBI_group': group_name
            }))

            r2_labels.append({
                'IBI_group': group_name,
                'x': subset[X_VAR].quantile(0.95),
                'y': subset[Y_VAR].quantile(0.95),
                'label': f"R² = {r2:.3f}"
            })

            # Calculate p-value
            boot_slopes = []
            for _ in range(1000):
                boot_subset = subset.sample(frac=1, replace=True)
                X_boot = sm.add_constant(boot_subset[X_VAR])
                y_boot = boot_subset[Y_VAR]
                try:
                    boot_model = sm.RLM(y_boot, X_boot, M=norms.TukeyBiweight())
                    boot_results = boot_model.fit()
                    boot_slopes.append(boot_results.params[X_VAR])
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

            stats_results.append({
                'IBI_group': group_name,
                'Slope': slope,
                'Rsquare': r2,
                'pvalue': p_value
            })

    pred_df = pd.concat(predictions, ignore_index=True)
    r2_df = pd.DataFrame(r2_labels)
    stats_df = pd.DataFrame(stats_results)

    # --------------------------------------------------------------------------
    # Create Visualization
    # --------------------------------------------------------------------------
    plot = (
            ggplot(ld_data, aes(x=X_VAR, y=Y_VAR, color='IBI_group'))
            + geom_point(alpha=0.05, size=3)
            + geom_line(data=pred_df, mapping=aes(x=X_VAR, y=Y_VAR, color='IBI_group'), size=1.2)
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

    # Set axis limits
    x_lower, x_upper = ld_data[X_VAR].quantile(0.005), ld_data[X_VAR].quantile(0.995)
    y_lower, y_upper = ld_data[Y_VAR].quantile(0.005), ld_data[Y_VAR].quantile(0.995)

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
            + labs(x=X_VAR, y=Y_VAR)
    )

    print(plot)

    # --------------------------------------------------------------------------
    # Save Plot
    # --------------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_scatter_{Y_VAR}_by_{X_VAR}_light.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

    # --------------------------------------------------------------------------
    # Statistical Results Output
    # --------------------------------------------------------------------------
    print("\nLight Pre-IBI: Slope, Rsquare and p-value Table:")
    print(stats_df.to_string(index=False))

    # --------------------------------------------------------------------------
    # LaTeX Macros Output
    # --------------------------------------------------------------------------
    os.makedirs(STATS_DIR, exist_ok=True)
    macros_path = os.path.join(STATS_DIR, f"{plot_ID}_GroupedScatterLightBoutRotationPreIBIMacros.tex")

    with open(macros_path, "w") as tex_file:
        for row in stats_results:
            grp = row['IBI_group'].replace(" ", "")
            tex_file.write(f"\\def\\GroupedScatterLightBoutRotationPreIBI{grp}AbsSlope{{{abs(row['Slope']):.3f}}}\n")
            tex_file.write(f"\\def\\GroupedScatterLightBoutRotationPreIBI{grp}Slope{{{row['Slope']:.3f}}}\n")
            tex_file.write(f"\\def\\GroupedScatterLightBoutRotationPreIBI{grp}Rsquare{{{row['Rsquare']:.3f}}}\n")
            tex_file.write(f"\\def\\GroupedScatterLightBoutRotationPreIBI{grp}Pvalue{{{row['pvalue']:.3e}}}\n")

    print(f"\nSaved LaTeX macros to {macros_path}")


if __name__ == "__main__":
    main()