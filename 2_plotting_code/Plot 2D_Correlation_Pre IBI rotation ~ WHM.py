"""
Correlation rot_total vs WHM
Description: Computes and visualizes relationship between rotation and bout duration with binned medians and IQR.
"""

#%%

import os
from datetime import date
import pandas as pd
import numpy as np
from plotnine import (
    ggplot, aes, geom_segment, geom_errorbar, geom_point,
    labs, theme_minimal, theme, element_line, element_blank
)
from get_visualization_ready import set_font_type, load_data, get_daytime_data

#%%
def main():
    #%%
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Connected_bout_features_strict.csv"
    X_VAR = "WHM"
    Y_VAR = "rot_total"
    NUM_BINS = 4
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    PLOT_DIMS = (4, 3)  # width, height in inches
    WHM_CLIP = (0.01, 0.99)  # Percentile range for WHM clipping
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    raw_data = load_data(filename=DATA_FILENAME)

    # Filter daytime data and remove NAs
    combine_data = get_daytime_data(raw_data).dropna(subset=["spd_peak", "displ_swim"])

    # Clip WHM values
    whm_lower, whm_upper = combine_data[X_VAR].quantile(WHM_CLIP).values
    combine_data = combine_data[
        (combine_data[X_VAR] >= whm_lower) &
        (combine_data[X_VAR] <= whm_upper)
        ]

    # --------------------------------------------------------------------------
    # Binned Data Calculation
    # --------------------------------------------------------------------------
    # Create quantile bins for WHM within each condition
    combine_data['bin'] = combine_data.groupby("cond1")[X_VAR].transform(
        lambda s: pd.qcut(s, q=NUM_BINS, labels=False, duplicates='drop') + 1
    )

    # Calculate summary statistics for each bin
    binned_data = combine_data.groupby(
        ["cond1", "bin"], as_index=False, observed=True
    ).agg(
        x_central=(X_VAR, "median"),
        y_central=(Y_VAR, "median"),
        x_lower=(X_VAR, lambda s: float(s.quantile(0.25))),
        x_upper=(X_VAR, lambda s: float(s.quantile(0.75))),
        y_lower=(Y_VAR, lambda s: float(s.quantile(0.25))),
        y_upper=(Y_VAR, lambda s: float(s.quantile(0.75)))
    )

    # --------------------------------------------------------------------------
    # Create Visualization (preserving your exact plotting specifications)
    # --------------------------------------------------------------------------
    plot = (
            ggplot(binned_data, aes(x="x_central", y="y_central", color="cond1"))
            + geom_segment(aes(x="x_lower", xend="x_upper", y="y_central", yend="y_central"))
            + geom_errorbar(aes(ymin="y_lower", ymax="y_upper"), width=0.1)
            + geom_point(shape="o", size=1)
            + labs(x="bout duration (ms)",
                   y="Total rotation (deg)",
                   title="Rotation vs bout duration")
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
    output_filename = f"{plot_ID}_correlation_{Y_VAR}_{X_VAR}_bins.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

#%%
if __name__ == "__main__":
    main()