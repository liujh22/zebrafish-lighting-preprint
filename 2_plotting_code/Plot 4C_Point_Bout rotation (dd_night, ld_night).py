"""
Script: Plot 4C Median rot_total by Condition (Night)
Description: Computes and visualizes median rot_total per bout under different lighting conditions (night data).
"""
#%%

import os
from datetime import date
import pandas as pd
import numpy as np
from scipy import stats
from plotnine import (
    ggplot, aes, geom_jitter, stat_summary, facet_wrap,
    labs, theme_minimal, theme,
    element_line, element_blank
)
from get_visualization_ready import set_font_type, load_data, get_nighttime_data

#%%
def main():
    
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"
    Y_VAR = "rot_total"
    X_VAR = "cond1"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
    PLOT_DIMS = (2, 3)  # width, height in inches
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    raw_data = load_data(filename=DATA_FILENAME)

    # Take absolute value of xdispl_swim and filter night data
    raw_data['xdispl_swim'] = raw_data['xdispl_swim'].abs()
    combine_data = get_nighttime_data(raw_data)

    # --------------------------------------------------------------------------
    # Compute Grouped Medians
    # --------------------------------------------------------------------------
    median_data = (combine_data
                   .groupby(['expNum', 'cond1', 'cond0', 'ztime'],
                            as_index=False, observed=True)
                   .agg(median_value=(Y_VAR, "median"))
                   .assign(median_type=Y_VAR))

    # --------------------------------------------------------------------------
    # Create Visualization
    # --------------------------------------------------------------------------
    plot = (
            ggplot(median_data, aes(x=X_VAR, y='median_value', color=X_VAR))
            + geom_jitter(shape="o", width=0.15, height=0, size=3, alpha=0.7)
            + stat_summary(aes(group=X_VAR), fun_y=np.mean,
                           geom="point", size=5, shape="D", color="black")
            + facet_wrap('~median_type', scales='free_y')
            + labs(x="Condition",
                   y="Median Rotation (deg)",
                   title="Nighttime Rotation by Condition")
            + theme_minimal()
            + theme(
                    axis_ticks_minor=element_blank(),
                    axis_line=element_line(color="black"),
                    axis_ticks=element_line(color="black"),
                    panel_grid=element_blank()
                    )
    )

    print(plot)

    # --------------------------------------------------------------------------
    # Save Plot
    # --------------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_median_{Y_VAR}_by_{X_VAR}.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

    # --------------------------------------------------------------------------
    # Statistical Analysis
    # --------------------------------------------------------------------------
    # Epoch-level analysis
    rot_dd = combine_data.loc[combine_data[X_VAR] == "dd", Y_VAR].dropna()
    rot_ld = combine_data.loc[combine_data[X_VAR] == "ld", Y_VAR].dropna()
    t1, p1 = stats.ttest_ind(rot_dd, rot_ld, nan_policy='omit')

    # Experiment-level analysis
    med_dd = median_data.loc[median_data[X_VAR] == "dd", 'median_value'].dropna()
    med_ld = median_data.loc[median_data[X_VAR] == "ld", 'median_value'].dropna()
    t2, p2 = stats.ttest_ind(med_dd, med_ld, nan_policy='omit')

    # Print results
    print_results(t1, p1, t2, p2)

    # Create summary and save stats
    summary_stats(median_data, t2, p2, STATS_DIR)


def print_results(t1, p1, t2, p2):
    """Print formatted statistical test results."""
    print("—— Independent samples t-test (epoch-level rot_total, dd vs ld) ——")
    print(f"t = {t1:.3f}, p = {p1:.3e}")
    print("\n—— Independent samples t-test (expNum-median rot_total, dd vs ld) ——")
    print(f"t = {t2:.3f}, p = {p2:.3e}")


def summary_stats(median_data, t_value, p_value, stats_dir):
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
    """Generate summary statistics and save LaTeX macros."""
    # Create summary table
    summary_df = (median_data
                  .groupby('cond1')['median_value']
                  .agg(Mean='mean', SD='std')
                  .reset_index()
                  .rename(columns={'cond1': 'Condition'}))

    # Add test results
    test_row = pd.DataFrame([{
        'Condition': 'expNum-median dd vs ld',
        'Mean': None,
        'SD': None,
        't': t_value,
        'p': p_value
    }])

    result_table = pd.concat([summary_df, test_row], ignore_index=True)
    print("\nSummary Table:")
    print(result_table.to_string(index=False))

    # Calculate effect size
    dd_stats = summary_df.loc[summary_df['Condition'] == 'dd']
    ld_stats = summary_df.loc[summary_df['Condition'] == 'ld']
    pooled_sd = np.sqrt((dd_stats['SD'].values[0] ** 2 + ld_stats['SD'].values[0] ** 2) / 2)
    effect_size = (dd_stats['Mean'].values[0] - ld_stats['Mean'].values[0]) / pooled_sd

    # Save LaTeX macros
    os.makedirs(stats_dir, exist_ok=True)
    macros_path = os.path.join(stats_dir, f"{plot_ID}_GroupedRotTotalNightMacros.tex")

    macros = [
        f"\\def\\GroupedRotTotalNightDdMean{{{dd_stats['Mean'].values[0]:.3f}}}",
        f"\\def\\GroupedRotTotalNightDdSD{{{dd_stats['SD'].values[0]:.3f}}}",
        f"\\def\\GroupedRotTotalNightLdMean{{{ld_stats['Mean'].values[0]:.3f}}}",
        f"\\def\\GroupedRotTotalNightLdSD{{{ld_stats['SD'].values[0]:.3f}}}",
        f"\\def\\GroupedRotTotalNightDdVsLdTvalue{{{t_value:.3f}}}",
        f"\\def\\GroupedRotTotalNightDdVsLdPvalue{{{p_value:.3e}}}",
        f"\\def\\GroupedRotTotalNightDdVsLdEffectSize{{{abs(effect_size):.3f}}}"
    ]

    with open(macros_path, "w") as f:
        f.write("\n".join(macros))

    print(f"\nSaved LaTeX macros to {macros_path}")


if __name__ == "__main__":
    main()
# %%
