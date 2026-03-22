"""
Script: Plot Suppl G Median pre_IBI_time
Description: Computes and visualizes median pre_IBI_time per bout under different experimental conditions.
"""
#%%
import os
from datetime import date
import numpy as np
from scipy import stats
from plotnine import (
    ggplot, aes, geom_jitter, stat_summary, facet_wrap,
    labs, theme_minimal, theme, element_line, element_blank
)
from get_visualization_ready import set_font_type, load_data, get_haircell_daytime_data
#%%

def main():
    
    
    #%
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "haircell_all_Connected_bout_features_strict.csv"
    Y_VAR = "pre_IBI_time"
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

    # Take absolute value of xdispl_swim
    raw_data['xdispl_swim'] = raw_data['xdispl_swim'].abs()

    combine_data = get_haircell_daytime_data(raw_data)

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
            + labs(x="Condition")
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
    output_filename = f"{plot_ID}_median_{Y_VAR}_by_{X_VAR}.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

    # --------------------------------------------------------------------------
    # Statistical Analysis
    # --------------------------------------------------------------------------
    # # Epoch-level analysis
    # pre_ibi_ctrl = combine_data.loc[combine_data[X_VAR] == "1ctrl", Y_VAR].dropna()
    # pre_ibi_cond = combine_data.loc[combine_data[X_VAR] == "2cond", Y_VAR].dropna()
    # t1, p1 = stats.ttest_ind(pre_ibi_ctrl, pre_ibi_cond, nan_policy='omit')

    # Experiment-level analysis
    med_ctrl = median_data.loc[median_data[X_VAR] == "1ctrl", 'median_value'].dropna()
    med_cond = median_data.loc[median_data[X_VAR] == "2cond", 'median_value'].dropna()
    t2, p2 = stats.ttest_ind(med_ctrl, med_cond, nan_policy='omit')

    # Print results
    # print("—— Independent samples t-test (epoch-level pre_IBI_time, ctrl vs cond) ——")
    # print(f"t = {t1:.3f}, p = {p1:.3e}")
    print("\n—— Independent samples t-test (expNum-median pre_IBI_time, ctrl vs cond) ——")
    print(f"t = {t2:.3f}, p = {p2:.3e}")

    # --------------------------------------------------------------------------
    # Statistics Summary and LaTeX Output
    # --------------------------------------------------------------------------
    # Create summary table
    summary_df = (median_data
                  .groupby('cond1')['median_value']
                  .agg(Mean='mean', SD='std')
                  .reset_index()
                  .rename(columns={'cond1': 'Condition'}))

    print("\nSummary Table:")
    print(summary_df.to_string(index=False))

    # Calculate effect size
    ctrl_stats = summary_df.loc[summary_df['Condition'] == '1ctrl']
    cond_stats = summary_df.loc[summary_df['Condition'] == '2cond']
    pooled_sd = np.sqrt((ctrl_stats['SD'].values[0] ** 2 + cond_stats['SD'].values[0] ** 2) / 2)
    effect_size = (ctrl_stats['Mean'].values[0] - cond_stats['Mean'].values[0]) / pooled_sd

    # Save LaTeX macros
    os.makedirs(STATS_DIR, exist_ok=True)
    macros_path = os.path.join(STATS_DIR, f"{plot_ID}_GroupedPreIBItimeMacros.tex")

    with open(macros_path, "w") as f:
        f.write(f"\\def\\GroupedPreIBItimeCtrlMean{{{ctrl_stats['Mean'].values[0]:.3f}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCtrlSD{{{ctrl_stats['SD'].values[0]:.3f}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCondMean{{{cond_stats['Mean'].values[0]:.3f}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCondSD{{{cond_stats['SD'].values[0]:.3f}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCtrlVsCondTvalue{{{t2:.3f}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCtrlVsCondPvalue{{{p2:.3e}}}\n")
        f.write(f"\\def\\GroupedPreIBItimeCtrlVsCondEffectSize{{{abs(effect_size):.3f}}}\n")

    print(f"\nSaved LaTeX macros to {macros_path}")
#%%

if __name__ == "__main__":
    main()