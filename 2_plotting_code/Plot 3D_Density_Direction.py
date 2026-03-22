"""
Description: Computes median and IQR for 1s distance in DD, LD, and LL conditions.
Outputs: LaTeX macros with median and IQR for all conditions and median test p-value.
Added: Effect size calculation for DD vs LD comparison
"""
#%%
import os
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from get_visualization_ready import set_font_type, load_data
from get_visualization_ready import *
from plotnine import (
    ggplot, aes, geom_line, labs,
    theme_minimal, theme, element_line, element_blank
)
import math
import matplotlib.pyplot as plt

#%%
def main():
    #%%
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"
    Y_VAR = "traj_peak"
    X_VAR = "cond1"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    PLOT_DIMS = (1.5, 3)  # width, height in inches
    STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    raw_data = load_data(filename=DATA_FILENAME)
    combine_data = get_daytime_data(raw_data)

    # --------------------------------------------------------------------------
    # Density Plot Calculation
    # --------------------------------------------------------------------------
    # Calculate bin width using Scott's rule
    sigma = combine_data[Y_VAR].std()
    n = combine_data[Y_VAR].count()
    bin_width = 3.5 * sigma / (n ** (1/3))
    
    #%%
    combine_data['N0E_' + Y_VAR] =  -1*(90 + combine_data[Y_VAR]) + 180

    # %% 
    col_toplt = 'N0E_' + Y_VAR
    # col_toplt = col_to_adj
    df_toplt = combine_data.copy()

    min_val = 0
    max_val = 360
    step = bin_width
    bins = np.arange(min_val,max_val+step,step)

    angle_counts = df_toplt.groupby(['cond1']).apply(
        lambda g: np.histogram(g[col_toplt], bins)[0]/len(g)
    )

    bin_mid = (bins[1:] + bins[:-1])/2
    # %
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    for i, cond in enumerate(df_toplt.cond1.unique()):
        ax.plot(np.radians(bin_mid), angle_counts[i])
    # --------------------------------------------------------------------------
    # Save Plot
    # --------------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_density_{Y_VAR}_by_{X_VAR}.pdf"
    plt.savefig(os.path.join(OUTPUT_DIR, output_filename), format='pdf')

    # --------------------------------------------------------------------------
    # Statistical Analysis (Optional)
    # --------------------------------------------------------------------------
    # Add statistical tests here if needed
    # For density plots, KS test is often appropriate
    dd_whm = combine_data.loc[combine_data[X_VAR] == "dd", Y_VAR].dropna()
    ld_whm = combine_data.loc[combine_data[X_VAR] == "ld", Y_VAR].dropna()

    ks_stat, ks_p = scipy_stats.ks_2samp(dd_whm, ld_whm)
    print(f"\nKolmogorov-Smirnov test (dd vs ld): D = {ks_stat:.3f}, p = {ks_p:.3e}")
#%%

    # --------------------------------------------------------------------------
    # Calculate Statistics for All Conditions
    # --------------------------------------------------------------------------
    # Initialize results dictionary
    condition_stats = {}
    stats_data = raw_data.query("ztime == 'day'")
    # Calculate for each condition
    for condition in ["dd", "ld", "ll"]:
        condition_data = stats_data.loc[stats_data["cond1"] == condition, Y_VAR].dropna()
        condition_stats[condition] = {
            "median": np.median(condition_data),
            "iqr": scipy_stats.iqr(condition_data),
            "n": len(condition_data)
        }

    # Perform median test between DD and LD and calculate effect size
    dd_data = stats_data.loc[stats_data["cond1"] == "dd", Y_VAR].dropna()
    ld_data = stats_data.loc[stats_data["cond1"] == "ld", Y_VAR].dropna()
    stat, p_value, _, _ = scipy_stats.median_test(dd_data, ld_data)

    # Calculate effect size (r)
    total_n = len(dd_data) + len(ld_data)
    effect_size = np.sqrt(stat / total_n) if total_n > 0 else np.nan

    # Print results
    print("\n—— Bout-Level Analysis ——")
    for condition, stats in condition_stats.items():
        print(f"{condition.upper()}: Median = {stats['median']:.3f}, IQR = {stats['iqr']:.3f}, N = {stats['n']}")
    print(f"\nMedian Test (DD vs LD) p-value = {p_value:.3e}")
    print(f"Effect size (r) = {effect_size:.3f}")

    # --------------------------------------------------------------------------
    # Save LaTeX Macros
    # --------------------------------------------------------------------------
    os.makedirs(STATS_DIR, exist_ok=True)
    macros_path = os.path.join(STATS_DIR, f"{plot_ID}_BoutStats.tex")

    with open(macros_path, "w") as f:
        # DD condition
        f.write(f"\\def\\MedianDirectionDDDay{{{condition_stats['dd']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRDirectionDDDay{{{condition_stats['dd']['iqr']:.3f}}}\n")

        # LD condition
        f.write(f"\\def\\MedianDirectionLDDay{{{condition_stats['ld']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRDirectionLDDay{{{condition_stats['ld']['iqr']:.3f}}}\n")

        # LL condition
        f.write(f"\\def\\MedianDirectionLLDay{{{condition_stats['ll']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRDirectionLLDay{{{condition_stats['ll']['iqr']:.3f}}}\n")

        # p-value and effect size
        f.write(f"\\def\\DirectionMedianTestPvalue{{{p_value:.3e}}}\n")
        f.write(f"\\def\\DirectionMedianTestEffectSize{{{effect_size:.3f}}}\n")

    print(f"\nSaved LaTeX macros to {macros_path}")
#%%

if __name__ == "__main__":
    main()