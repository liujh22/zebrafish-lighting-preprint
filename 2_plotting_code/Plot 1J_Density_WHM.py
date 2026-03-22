"""
Description: Computes and visualizes normalized density distribution of WHM under different lighting conditions.
"""
#%%
import os
from datetime import date
import pandas as pd
import numpy as np
from scipy import stats
from plotnine import (
    ggplot, aes, geom_line, labs,
    theme_minimal, theme, element_line, element_blank
)
from get_visualization_ready import set_font_type, load_data, get_daytime_data

#%%
def main():
    #%%
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"
    Y_VAR = "WHM"
    X_VAR = "cond1"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    PLOT_DIMS = (1.5, 3)  # width, height in inches

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
    print(f"Scott's rule computed bin width for {Y_VAR}: {bin_width:.4f}")

    # Create binned data
    combine_data['bin'] = np.floor(combine_data[Y_VAR] / bin_width) * bin_width

    # Group and normalize frequencies
    grouped = (combine_data
               .groupby([X_VAR, 'bin'])
               .size()
               .reset_index(name='count'))
    grouped['freq'] = grouped.groupby(X_VAR)['count'].transform(lambda x: x / x.sum())

    # --------------------------------------------------------------------------
    # Create Visualization
    # --------------------------------------------------------------------------
    plot = (
        ggplot(grouped, aes(x='bin', y='freq', color=X_VAR))
        + geom_line(size=1)
        + labs(x="bout duration (ms)",
               y="Normalized Frequency",
               title="Duration Distribution by Condition")
        + theme_minimal()
        + theme(axis_line=element_line(color="black"),
                axis_ticks=element_line(color="black"),
                panel_grid=element_blank())

    )

    print(plot)

    # --------------------------------------------------------------------------
    # Save Plot
    # --------------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_density_{Y_VAR}_by_{X_VAR}.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

    # --------------------------------------------------------------------------
    # Statistical Analysis (Optional)
    # --------------------------------------------------------------------------
    # Add statistical tests here if needed
    # For density plots, KS test is often appropriate
    dd_whm = combine_data.loc[combine_data[X_VAR] == "dd", Y_VAR].dropna()
    ld_whm = combine_data.loc[combine_data[X_VAR] == "ld", Y_VAR].dropna()

    ks_stat, ks_p = stats.ks_2samp(dd_whm, ld_whm)
    print(f"\nKolmogorov-Smirnov test (dd vs ld): D = {ks_stat:.3f}, p = {ks_p:.3e}")
    #%%

if __name__ == "__main__":
    main()