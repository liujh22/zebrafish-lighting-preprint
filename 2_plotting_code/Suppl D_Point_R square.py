"""
Script: Plot Suppl D R² comparison between pre/post IBI rotation under DD vs LD
Description: Compares the goodness-of-fit (R²) between pre-IBI and post-IBI rotation relationships
             under dark (DD) and light (LD) conditions using robust regression.
"""
#%%
import os
from datetime import date
import numpy as np
import pandas as pd
from plotnine import (
    ggplot, aes, geom_jitter, stat_summary, scale_color_manual,
    theme_minimal, theme, element_line, element_blank, labs
)
import matplotlib as mpl
import statsmodels.api as sm
import statsmodels.robust.norms as norms
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from get_visualization_ready import set_font_type, load_data


def main():
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Consecutive_bout_3_strict.csv"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")

    PLOT_DIMS = (4, 3)  # width, height in inches
    BOUT_NUMBER = 2  # Middle bout of consecutive bouts
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    data_raw = load_data(filename=DATA_FILENAME)

    # Filter for middle bout of consecutive bouts
    df = data_raw[data_raw['bouts'] == BOUT_NUMBER].copy()

    # Convert categorical variables
    for col in ['cond1', 'ztime', 'cond0', 'expNum']:
        df[col] = df[col].astype('category')

    # --------------------------------------------------------------------------
    # Prepare Condition Data (Long IBI only)
    # --------------------------------------------------------------------------
    def prepare_condition_data(df, condition):
        """Filter data for specific condition (DD/LD) and create IBI groups"""
        sub = df[(df['cond1'] == condition) & (df['ztime'] == "day")].copy()
        median_ibi = sub['pre_IBI_time'].quantile(0.5)
        sub['IBI_group'] = np.where(
            sub['pre_IBI_time'] >= median_ibi,
            "Long IBI",
            "Short IBI"
        )
        sub['IBI_group'] = pd.Categorical(
            sub['IBI_group'],
            categories=["Long IBI", "Short IBI"],
            ordered=True
        )
        return sub[sub['IBI_group'] == "Long IBI"].copy()

    dd_data = prepare_condition_data(df, "dd")
    ld_data = prepare_condition_data(df, "ld")

    # --------------------------------------------------------------------------
    # Robust R² Calculation
    # --------------------------------------------------------------------------
    def robust_r2(x, y):
        """Calculate robust R² using Tukey's Biweight regression"""
        if len(x) < 2:
            return np.nan
        X = sm.add_constant(x)
        model = sm.RLM(y, X, M=norms.TukeyBiweight())
        res = model.fit()
        yhat = res.predict(X)
        sse = np.sum((y - yhat) ** 2)
        sst = np.sum((y - np.mean(y)) ** 2)
        return 1 - sse / sst

    def calculate_r2_table(sub, condition):
        """Calculate R² for pre and post IBI rotation by experiment"""
        # Pre-IBI
        pre = (
            sub.groupby("expNum", observed=True)
            .apply(lambda g: pd.Series({'r2': robust_r2(g['preIBI_rot'], g['rot_total'])}))
            .reset_index()
        )
        pre['timepoint'] = "pre"

        # Post-IBI
        post = (
            sub.groupby("expNum", observed=True)
            .apply(lambda g: pd.Series({'r2': robust_r2(g['postIBI_rot'], g['rot_total'])}))
            .reset_index()
        )
        post['timepoint'] = "post"

        # Combine and label
        df_r2 = pd.concat([pre, post], ignore_index=True)
        df_r2['cond1'] = condition
        return df_r2

    r2_dd = calculate_r2_table(dd_data, "dd")
    r2_ld = calculate_r2_table(ld_data, "ld")
    r2_all = pd.concat([r2_dd, r2_ld], ignore_index=True)

    # --------------------------------------------------------------------------
    # Statistical Analysis
    # --------------------------------------------------------------------------
    # Two-way ANOVA
    model = ols('r2 ~ C(cond1) * C(timepoint)', data=r2_all).fit()
    anova_results = sm.stats.anova_lm(model, typ=2)

    # Tukey HSD post-hoc tests
    r2_all['group'] = r2_all['cond1'] + "_" + r2_all['timepoint']
    tukey = pairwise_tukeyhsd(endog=r2_all['r2'], groups=r2_all['group'], alpha=0.05)

    # Summary statistics
    summary_r2 = (
        r2_all
        .groupby(['cond1', 'timepoint'])['r2']
        .agg(Mean='mean', SD='std')
        .reset_index()
    )

    # --------------------------------------------------------------------------
    # Create Visualization
    # --------------------------------------------------------------------------
    plot = (
            ggplot(r2_all, aes(x="timepoint", y="r2", color="cond1"))
            + geom_jitter(width=0.15, size=3, alpha=0.7)
            + stat_summary(aes(group="cond1"), fun_y=np.mean, geom="point", size=5, shape="D")
            + scale_color_manual(values={"dd": "#1f78b4", "ld": "#33a02c"}, name="Condition")
            + theme_minimal()
            + theme(
        axis_line=element_line(color="black"),
        axis_ticks_minor=element_blank(),
        axis_ticks=element_line(color="black"),
        panel_grid=element_blank()
    )
            + labs(x="Timepoint", y="R²", title="R² for Pre/Post under DD vs LD")
    )

    print(plot)

    # --------------------------------------------------------------------------
    # Save Plot
    # --------------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_r2_pre_post_dd_ld.pdf"
    plot.save(os.path.join(OUTPUT_DIR, output_filename),
              width=PLOT_DIMS[0], height=PLOT_DIMS[1])

    # --------------------------------------------------------------------------
    # Statistical Results Output
    # --------------------------------------------------------------------------
    print("\nTwo-way ANOVA results:")
    print(anova_results)

    print("\nTukey HSD post-hoc results:")
    print(tukey.summary())

    print("\nSummary statistics (Mean ± SD):")
    print(summary_r2.to_string(index=False))

    # --------------------------------------------------------------------------
    # LaTeX Macros Output
    # --------------------------------------------------------------------------
    os.makedirs(STATS_DIR, exist_ok=True)
    macros_path = os.path.join(STATS_DIR, f"{plot_ID}_R2ComparisonMacros.tex")

    with open(macros_path, "w") as f:
        # Group means and SD macros
        for _, row in summary_r2.iterrows():
            tp = row['timepoint'].capitalize()
            cond = row['cond1'].upper()
            f.write(f"\\def\\GroupedRsqure{tp}{cond}Mean{{{row['Mean']:.3f}}}\n")
            f.write(f"\\def\\GroupedRsqure{tp}{cond}SD{{{row['SD']:.3f}}}\n")

        # ANOVA result macros
        for effect, vals in anova_results[['sum_sq', 'df', 'F', 'PR(>F)']].iterrows():
            key = effect.replace('C(', '').replace(')', '').replace(':', 'x')
            f.write(f"\\def\\ANOVA{key}SumSq{{{vals['sum_sq']:.3e}}}\n")
            f.write(f"\\def\\ANOVA{key}DF{{{int(vals['df'])}}}\n")
            f.write(f"\\def\\ANOVA{key}F{{{vals['F']:.3f}}}\n")
            f.write(f"\\def\\ANOVA{key}P{{{vals['PR(>F)']:.3e}}}\n")

        # Tukey HSD macros
        tukey_df = pd.DataFrame(data=tukey._results_table.data[1:],
                                columns=tukey._results_table.data[0])
        for _, row in tukey_df.iterrows():
            g1 = row['group1'].replace('_', '').capitalize()
            g2 = row['group2'].replace('_', '').capitalize()
            f.write(f"\\def\\Tukey{g1}vs{g2}MeanDiff{{{float(row['meandiff']):.3f}}}\n")
            f.write(f"\\def\\Tukey{g1}vs{g2}Padj{{{float(row['p-adj']):.3f}}}\n")

    print(f"\nSaved LaTeX macros to {macros_path}")


if __name__ == "__main__":
    main()