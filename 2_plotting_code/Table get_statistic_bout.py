# %%
import os
import pandas as pd
import numpy as np
from scipy.stats import median_test, ttest_ind, normaltest
from itertools import combinations
from get_visualization_ready import load_data

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
DATASETS = {
    "wt_2025": "wt_2025_all_Connected_bout_features_strict.csv",
    "haircell": "haircell_all_Connected_bout_features_strict.csv",
}

STATS_DIR = os.path.join(os.path.dirname(__file__), "../Statistics")
os.makedirs(STATS_DIR, exist_ok=True)  # Ensure output directory exists
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------
def significance_marker(p):
    """Add significance markers based on p-value."""
    if pd.isna(p):
        return "NA"
    elif p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return "ns"


def to_camel(s):
    """Convert string to CamelCase."""
    return ''.join(word.capitalize() for word in str(s).split('_'))


def clean_ztime(s):
    """Clean and format ztime for LaTeX macros."""
    return to_camel(str(s).replace("1", "One").replace("2", "Two").lower())


def clean_cond_name(cond_name, dataset_name):
    """Clean condition names by removing numbers for haircell dataset."""
    if dataset_name == "haircell":
        # Remove leading numbers from condition names
        return ''.join([c for c in cond_name if not c.isdigit()])
    return cond_name


def analyze_dataset(data, dataset_name):
    """Perform statistical analysis on a dataset."""
    # Convert categorical variables
    categorical_cols = ["cond0", "cond1", "ztime", "expNum"]
    for col in categorical_cols:
        data[col] = data[col].astype("category")

    # Target variables for analysis
    target_vars = ["spd_peak", "WHM", "displ_swim", "rot_total"]
    result_rows = []

    # Compare conditions within each ztime
    for zt in data["ztime"].cat.categories:
        data_sub = data[data["ztime"] == zt]
        conds = data_sub["cond1"].cat.categories

        for var in target_vars:
            for g1, g2 in combinations(conds, 2):
                group1 = data_sub[data_sub["cond1"] == g1][var].dropna()
                group2 = data_sub[data_sub["cond1"] == g2][var].dropna()

                if len(group1) < 3 or len(group2) < 3:
                    result_rows.append({
                        "variable": var,
                        "ztime": zt,
                        "cond1_group1": g1,
                        "cond1_group2": g2,
                        "median_group1": np.nan,
                        "median_group2": np.nan,
                        "IQR_group1": np.nan,
                        "IQR_group2": np.nan,
                        "p_value": np.nan,
                        "effect_size": np.nan,
                        "test_type": "too_few_samples",
                        "sig_level": "NA"
                    })
                    continue

                # # Check normality - disabled, bc no parameteric tests used
                # p_norm1 = normaltest(group1)[1]
                # p_norm2 = normaltest(group2)[1]
                # use_t_test = p_norm1 > 0.05 and p_norm2 > 0.05
                # if use_t_test:
                #     print(dataset_name, var)

                stat, p, _, _ = median_test(group1, group2)
                test_type = "median_test"
                total_n = len(group1) + len(group2)
                r = np.sqrt(stat / total_n) if total_n > 0 else np.nan

                med1, iqr1 = np.median(group1), np.percentile(group1, 75) - np.percentile(group1, 25)
                med2, iqr2 = np.median(group2), np.percentile(group2, 75) - np.percentile(group2, 25)

                result_rows.append({
                    "variable": var,
                    "ztime": zt,
                    "cond1_group1": g1,
                    "cond1_group2": g2,
                    "median_group1": med1,
                    "median_group2": med2,
                    "IQR_group1": iqr1,
                    "IQR_group2": iqr2,
                    "p_value": p,
                    "effect_size": r,
                    "test_type": str(test_type),
                    "sig_level": significance_marker(p)
                })

    # Compare day vs night for each condition
    for cond in data["cond1"].cat.categories:
        data_sub = data[data["cond1"] == cond]
        ztimes = data_sub["ztime"].cat.categories

        if "day" not in ztimes or "night" not in ztimes:
            continue

        day_data = data_sub[data_sub["ztime"] == "day"]
        night_data = data_sub[data_sub["ztime"] == "night"]

        for var in target_vars:
            group1 = day_data[var].dropna()
            group2 = night_data[var].dropna()

            if len(group1) < 3 or len(group2) < 3:
                result_rows.append({
                    "variable": var,
                    "ztime": "day_vs_night",
                    "cond1_group1": f"{cond}Day",
                    "cond1_group2": f"{cond}Night",
                    "median_group1": np.nan,
                    "median_group2": np.nan,
                    "IQR_group1": np.nan,
                    "IQR_group2": np.nan,
                    "p_value": np.nan,
                    "effect_size": np.nan,
                    "test_type": "too_few_samples",
                    "sig_level": "NA"
                })
                continue

            # p_norm1 = normaltest(group1)[1]
            # p_norm2 = normaltest(group2)[1]
            # use_t_test = p_norm1 > 0.05 and p_norm2 > 0.05

            stat, p, _, _ = median_test(group1, group2)
            test_type = "median_test"
            total_n = len(group1) + len(group2)
            r = np.sqrt(stat / total_n) if total_n > 0 else np.nan

            med1, iqr1 = np.median(group1), np.percentile(group1, 75) - np.percentile(group1, 25)
            med2, iqr2 = np.median(group2), np.percentile(group2, 75) - np.percentile(group2, 25)

            result_rows.append({
                "variable": var,
                "ztime": "day_vs_night",
                "cond1_group1": f"{cond}Day",
                "cond1_group2": f"{cond}Night",
                "median_group1": med1,
                "median_group2": med2,
                "IQR_group1": iqr1,
                "IQR_group2": iqr2,
                "p_value": p,
                "effect_size": r,
                "test_type": str(test_type),
                "sig_level": significance_marker(p)
            })

    return pd.DataFrame(result_rows)


def generate_latex_defs(summary_df, stats_df, dataset_name):
    """Generate LaTeX macro definitions from the analysis results."""
    lines = [f"% {dataset_name} bout feature"]

    # Determine prefix based on dataset
    prefix = ""  # No prefix for any dataset now

    # Generate summary macros (medians and IQRs)
    for _, row in summary_df.iterrows():
        var = to_camel(row["variable"])
        cond = clean_cond_name(row["cond1"], dataset_name)
        cond = to_camel(cond)
        ztime = clean_ztime(row["ztime"])

        lines.append(f"\\def\\{prefix}{var}{cond}{ztime}Median{{{row['median']:.3f}}}")
        lines.append(f"\\def\\{prefix}{var}{cond}{ztime}Iqr{{{row['iqr']:.3f}}}")

    # Generate statistics macros (p-values, effect sizes, significance)
    for _, row in stats_df.iterrows():
        var = to_camel(row["variable"])
        cond1 = clean_cond_name(row["cond1_group1"], dataset_name)
        cond1 = to_camel(cond1)
        cond2 = clean_cond_name(row["cond1_group2"], dataset_name)
        cond2 = to_camel(cond2)
        ztime = clean_ztime(row["ztime"])

        if row["ztime"] == "day_vs_night":
            orig1 = row["cond1_group1"]  # e.g. 'ddDay'
            orig2 = row["cond1_group2"]  # e.g. 'ddNight'
            base1 = clean_cond_name(orig1[:-3] if orig1.endswith("Day") else orig1, dataset_name)
            base2 = clean_cond_name(orig2[:-5] if orig2.endswith("Night") else orig2, dataset_name)
            b1 = to_camel(base1)
            b2 = to_camel(base2)

            lines.append(f"\\def\\{prefix}{var}{b1}DayVs{b2}NightPval{{{row['p_value']:.3e}}}")
            lines.append(f"\\def\\{prefix}{var}{b1}DayVs{b2}NightEffsize{{{row['effect_size']:.3f}}}")
            lines.append(f"\\def\\{prefix}{var}{b1}DayVs{b2}NightSig{{{row['sig_level']}}}")
        else:
            lines.append(f"\\def\\{prefix}{var}{cond1}{ztime}Vs{cond2}{ztime}Pval{{{row['p_value']:.3e}}}")
            lines.append(f"\\def\\{prefix}{var}{cond1}{ztime}Vs{cond2}{ztime}Effsize{{{row['effect_size']:.3f}}}")
            lines.append(f"\\def\\{prefix}{var}{cond1}{ztime}Vs{cond2}{ztime}Sig{{{row['sig_level']}}}")

    return lines


# --------------------------------------------------------------------------
# Main Processing
# --------------------------------------------------------------------------
for dataset_name, filename in DATASETS.items():
    print(f"\nProcessing dataset: {dataset_name} ({filename})")

    # Load data
    data = load_data(filename=filename)

    # Perform analysis
    final_table = analyze_dataset(data, dataset_name)

    # Build summary table
    summary_rows = []
    for _, row in final_table.iterrows():
        summary_rows.append({
            "variable": row["variable"],
            "ztime": row["ztime"],
            "cond1": row["cond1_group1"],
            "median": row["median_group1"],
            "iqr": row["IQR_group1"]
        })
        summary_rows.append({
            "variable": row["variable"],
            "ztime": row["ztime"],
            "cond1": row["cond1_group2"],
            "median": row["median_group2"],
            "iqr": row["IQR_group2"]
        })

    summary_df = pd.DataFrame(summary_rows).drop_duplicates()

    # Build stats table
    stats_cols = ["variable", "ztime", "cond1_group1", "cond1_group2",
                  "p_value", "effect_size", "test_type", "sig_level"]
    stats_df = final_table[stats_cols].copy()

    # Generate LaTeX macros
    latex_defs = generate_latex_defs(summary_df, stats_df, dataset_name)
    output_filename = os.path.join(STATS_DIR, f"Table_{dataset_name}_bout_macros.tex")

    with open(output_filename, "w") as f:
        f.write("\n".join(latex_defs))

    print(f"Successfully generated LaTeX macros at: {output_filename}")

print("\nAll datasets processed successfully!")
# %%
