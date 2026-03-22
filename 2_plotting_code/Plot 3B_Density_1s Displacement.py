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
#%%

def main():
    #%%
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Consecutive_bout_5_strict.csv"
    Y_VAR = "1s_distance_total"

    STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
    set_font_type()
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    PLOT_DIMS = (1.5, 3)  # width, height in inches
    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    raw_data = load_data(filename=DATA_FILENAME)

    # Data conversions
    raw_data["bout_time"] = pd.to_datetime(raw_data["bout_time"])
    for col in ['cond1', 'ztime', 'cond0', 'expNum']:
        raw_data[col] = raw_data[col].astype('category')

    # Filter data (include LL condition)
    combine_data = raw_data[(raw_data["cond1"].isin(["dd", "ld", "ll"])) &
                          (raw_data["ztime"] == "day")].copy()

    # --------------------------------------------------------------------------
    # Compute Epoch Metrics
    # --------------------------------------------------------------------------
    def summarise_epoch(grp):
        grp = grp.sort_values("bout_time")
        if len(grp) < 5:
            return pd.Series([np.nan]*3, index=[
                "total_time", "distance_total", "epoch_speed"
            ])

        distance_x = grp["x_initial"].iloc[4] - grp["x_initial"].iloc[0]
        distance_y = grp["y_initial"].iloc[4] - grp["y_initial"].iloc[0]
        distance_total = np.sqrt(distance_x**2 + distance_y**2)
        total_time = (grp["bout_time"].iloc[4] - grp["bout_time"].iloc[0]).total_seconds()
        epoch_speed = distance_total / total_time if total_time > 0 else np.nan

        return pd.Series({
            "total_time": total_time,
            "distance_total": distance_total,
            "epoch_speed": epoch_speed
        })

    epoch_summary = (combine_data
                    .groupby(["expNum", "cond1", "ztime", "id"], observed=True)
                    .apply(summarise_epoch, include_groups=False)
                    .reset_index())

    # Compute 1-second scaled distance
    df_1s = epoch_summary.copy()
    df_1s[Y_VAR] = df_1s["epoch_speed"] * 1


    #%%
    X_VAR = 'cond1'
    # plot
    df_toplt = df_1s.loc[df_1s[Y_VAR] < 6].copy()  # remove extreme outliers
    sigma = df_toplt[Y_VAR].std()
    n = df_toplt[Y_VAR].count()
    bin_width = 3.5 * sigma / (n ** (1/3))
    print(f"Scott's rule computed bin width for {Y_VAR}: {bin_width:.4f}")

    # Create binned data
    df_toplt['bin'] = np.floor(df_toplt[Y_VAR] / bin_width) * bin_width

    # Group and normalize frequencies
    grouped = (df_toplt
               .groupby([X_VAR, 'bin'])
               .size()
               .reset_index(name='count'))
    grouped['freq'] = grouped.groupby(X_VAR)['count'].transform(lambda x: x / x.sum())


    # --------------------------------------------------------------------------
    # Create Visualization (preserving your exact plotting code)
    # --------------------------------------------------------------------------
    plot = (
        ggplot(grouped, aes(x='bin', y='freq', color=X_VAR))
        + geom_line(stat='identity')
        + labs(
            x=Y_VAR,
            y="Normalized Frequency",
            title=f"Density of {Y_VAR} by Condition"
        )
        + theme_minimal()
        + theme(
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
    output_filename = f"{plot_ID}_density_{Y_VAR}_by_{X_VAR}.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])
    #%%
    # --------------------------------------------------------------------------
    # Statistical Analysis (Optional)
    # --------------------------------------------------------------------------
    # Add statistical tests here if needed
    # For density plots, KS test is often appropriate
    dd_whm = df_1s.loc[df_1s[X_VAR] == "dd", Y_VAR].dropna()
    ld_whm = df_1s.loc[df_1s[X_VAR] == "ld", Y_VAR].dropna()

    ks_stat, ks_p = scipy_stats.ks_2samp(dd_whm, ld_whm)
    print(f"\nKolmogorov-Smirnov test (dd vs ld): D = {ks_stat:.3f}, p = {ks_p:.3e}")


    # --------------------------------------------------------------------------
    # Calculate Statistics for All Conditions
    # --------------------------------------------------------------------------
    # Initialize results dictionary
    condition_stats = {}

    # Calculate for each condition
    for condition in ["dd", "ld", "ll"]:
        condition_data = df_1s.loc[df_1s["cond1"] == condition, Y_VAR].dropna()
        condition_stats[condition] = {
            "median": np.median(condition_data),
            "iqr": scipy_stats.iqr(condition_data),
            "n": len(condition_data)
        }

    # Perform median test between DD and LD and calculate effect size
    dd_data = df_1s.loc[df_1s["cond1"] == "dd", Y_VAR].dropna()
    ld_data = df_1s.loc[df_1s["cond1"] == "ld", Y_VAR].dropna()
    stat, p_value, _, _ = scipy_stats.median_test(dd_data, ld_data)

    # Calculate effect size (r)
    total_n = len(dd_data) + len(ld_data)
    effect_size = np.sqrt(stat / total_n) if total_n > 0 else np.nan

    # Print results
    print("\n—— Epoch-Level Analysis ——")
    for condition, stats in condition_stats.items():
        print(f"{condition.upper()}: Median = {stats['median']:.3f}, IQR = {stats['iqr']:.3f}, N = {stats['n']}")
    print(f"\nMedian Test (DD vs LD) p-value = {p_value:.3e}")
    print(f"Effect size (r) = {effect_size:.3f}")

    # --------------------------------------------------------------------------
    # Save LaTeX Macros
    # --------------------------------------------------------------------------
    os.makedirs(STATS_DIR, exist_ok=True)
    macros_path = os.path.join(STATS_DIR, f"{plot_ID}_EpochLevelStats.tex")

    with open(macros_path, "w") as f:
        # DD condition
        f.write(f"\\def\\MedianPerSecondDistDDDay{{{condition_stats['dd']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRPerSecondDistDDDay{{{condition_stats['dd']['iqr']:.3f}}}\n")

        # LD condition
        f.write(f"\\def\\MedianPerSecondDistLDDay{{{condition_stats['ld']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRPerSecondDistLDDay{{{condition_stats['ld']['iqr']:.3f}}}\n")

        # LL condition
        f.write(f"\\def\\MedianPerSecondDistLLDay{{{condition_stats['ll']['median']:.3f}}}\n")
        f.write(f"\\def\\IQRPerSecondDistLLDay{{{condition_stats['ll']['iqr']:.3f}}}\n")

        # p-value and effect size
        f.write(f"\\def\\DistancePerSecondMedianTestPvalue{{{p_value:.3e}}}\n")
        f.write(f"\\def\\DistancePerSecondMedianTestEffectSize{{{effect_size:.3f}}}\n")

    print(f"\nSaved LaTeX macros to {macros_path}")
#%%

if __name__ == "__main__":
    main()