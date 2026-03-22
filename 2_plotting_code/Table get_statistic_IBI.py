# %%
import os
import pandas as pd
import numpy as np
from scipy.stats import median_test
from itertools import combinations
from get_visualization_ready import load_data

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
DATASETS = {
    "wt_2025": "wt_2025_all_Consecutive_bout_3_strict.csv",
    "haircell": "haircell_all_Consecutive_bout_3_strict.csv"
}

STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
os.makedirs(STATS_DIR, exist_ok=True)


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
    if str(s).lower() == "day_vs_night":
        return ""
    return to_camel(str(s).replace("1", "One").replace("2", "Two").lower())


def clean_cond_name(cond_name, dataset_name):
    """Clean condition names by removing numbers for haircell dataset."""
    if dataset_name == "haircell":
        return ''.join([c for c in cond_name if not c.isdigit()])
    return cond_name


def analyze_ibi_dataset(data, dataset_name):
    """Perform statistical analysis on IBI dataset."""
    target_vars = ["preIBI_rot", "postIBI_rot", "pre_IBI_time", "post_IBI_time"]
    categorical_cols = ["cond0", "cond1", "ztime", "expNum"]

    for col in categorical_cols:
        data[col] = data[col].astype("category")

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
                        "variable": var, "ztime": zt,
                        "cond1_group1": g1, "cond1_group2": g2,
                        "median_group1": np.nan, "median_group2": np.nan,
                        "IQR_group1": np.nan, "IQR_group2": np.nan,
                        "p_value": np.nan, "effect_size": np.nan,
                        "test_type": "too_few_samples", "sig_level": "NA"
                    })
                    continue

                stat, p, _, _ = median_test(group1, group2)
                total_n = len(group1) + len(group2)
                r = np.sqrt(stat / total_n) if total_n > 0 else np.nan  # Effect size calculation

                med1 = np.median(group1)
                iqr1 = np.percentile(group1, 75) - np.percentile(group1, 25)
                med2 = np.median(group2)
                iqr2 = np.percentile(group2, 75) - np.percentile(group2, 25)

                result_rows.append({
                    "variable": var, "ztime": zt,
                    "cond1_group1": g1, "cond1_group2": g2,
                    "median_group1": med1, "median_group2": med2,
                    "IQR_group1": iqr1, "IQR_group2": iqr2,
                    "p_value": p, "effect_size": r,
                    "test_type": "median_test",
                    "sig_level": significance_marker(p)
                })

    # Compare day vs night for each condition
    for cond in data["cond1"].cat.categories:
        data_sub = data[data["cond1"] == cond]
        if "day" not in data_sub["ztime"].cat.categories or "night" not in data_sub["ztime"].cat.categories:
            continue

        day_data = data_sub[data_sub["ztime"] == "day"]
        night_data = data_sub[data_sub["ztime"] == "night"]

        for var in target_vars:
            group1 = day_data[var].dropna()
            group2 = night_data[var].dropna()

            if len(group1) < 3 or len(group2) < 3:
                result_rows.append({
                    "variable": var, "ztime": "day_vs_night",
                    "cond1_group1": f"{cond}Day", "cond1_group2": f"{cond}Night",
                    "median_group1": np.nan, "median_group2": np.nan,
                    "IQR_group1": np.nan, "IQR_group2": np.nan,
                    "p_value": np.nan, "effect_size": np.nan,
                    "test_type": "too_few_samples", "sig_level": "NA"
                })
                continue

            stat, p, _, _ = median_test(group1, group2)
            total_n = len(group1) + len(group2)
            r = np.sqrt(stat / total_n) if total_n > 0 else np.nan  # Effect size calculation

            med1 = np.median(group1)
            iqr1 = np.percentile(group1, 75) - np.percentile(group1, 25)
            med2 = np.median(group2)
            iqr2 = np.percentile(group2, 75) - np.percentile(group2, 25)

            result_rows.append({
                "variable": var, "ztime": "day_vs_night",
                "cond1_group1": f"{cond}Day", "cond1_group2": f"{cond}Night",
                "median_group1": med1, "median_group2": med2,
                "IQR_group1": iqr1, "IQR_group2": iqr2,
                "p_value": p, "effect_size": r,
                "test_type": "median_test",
                "sig_level": significance_marker(p)
            })

    return pd.DataFrame(result_rows)


def generate_ibi_latex_defs(summary_df, stats_df, dataset_name):
    """Generate LaTeX macro definitions for IBI analysis."""
    lines = [f"% {dataset_name} IBI feature"]

    # Generate summary macros
    for _, row in summary_df.iterrows():
        var = to_camel(row["variable"])
        cond = clean_cond_name(row["cond1"], dataset_name)
        cond = to_camel(cond)
        ztime = clean_ztime(row["ztime"])

        lines.append(f"\\def\\{var}{cond}{ztime}Median{{{row['median']:.3f}}}")
        lines.append(f"\\def\\{var}{cond}{ztime}Iqr{{{row['iqr']:.3f}}}")

    # Generate statistics macros
    for _, row in stats_df.iterrows():
        var = to_camel(row["variable"])
        cond1 = clean_cond_name(row["cond1_group1"], dataset_name)
        cond1 = to_camel(cond1)
        cond2 = clean_cond_name(row["cond1_group2"], dataset_name)
        cond2 = to_camel(cond2)
        ztime = clean_ztime(row["ztime"])

        if row["ztime"] == "day_vs_night":
            orig = row["cond1_group1"]
            base = clean_cond_name(orig[:-3] if orig.endswith("Day") else orig, dataset_name)
            base_camel = to_camel(base)

            lines.extend([
                f"\\def\\{var}{base_camel}DayVs{base_camel}NightPval{{{row['p_value']:.3e}}}",
                f"\\def\\{var}{base_camel}DayVs{base_camel}NightEffsize{{{row['effect_size']:.3f}}}",
                f"\\def\\{var}{base_camel}DayVs{base_camel}NightSig{{{row['sig_level']}}}"
            ])
        else:
            lines.extend([
                f"\\def\\{var}{cond1}{ztime}Vs{cond2}{ztime}Pval{{{row['p_value']:.3e}}}",
                f"\\def\\{var}{cond1}{ztime}Vs{cond2}{ztime}Effsize{{{row['effect_size']:.3f}}}",
                f"\\def\\{var}{cond1}{ztime}Vs{cond2}{ztime}Sig{{{row['sig_level']}}}"
            ])

    return lines


# --------------------------------------------------------------------------
# Main Processing
# --------------------------------------------------------------------------
for dataset_name, filename in DATASETS.items():
    print(f"\nProcessing dataset: {dataset_name} ({filename})")

    data = load_data(filename=filename)
    final_table = analyze_ibi_dataset(data, dataset_name)

    # Build summary table
    summary_rows = []
    for _, row in final_table.iterrows():
        summary_rows.extend([
            {
                "variable": row["variable"], "ztime": row["ztime"],
                "cond1": row["cond1_group1"],
                "median": row["median_group1"], "iqr": row["IQR_group1"]
            },
            {
                "variable": row["variable"], "ztime": row["ztime"],
                "cond1": row["cond1_group2"],
                "median": row["median_group2"], "iqr": row["IQR_group2"]
            }
        ])

    summary_df = pd.DataFrame(summary_rows).drop_duplicates()

    # Build stats table
    stats_df = final_table[[
        "variable", "ztime", "cond1_group1", "cond1_group2",
        "p_value", "effect_size", "test_type", "sig_level"
    ]].copy()

    # Generate LaTeX macros
    latex_defs = generate_ibi_latex_defs(summary_df, stats_df, dataset_name)
    output_filename = os.path.join(STATS_DIR, f"Table_{dataset_name}_IBI_macros.tex")

    with open(output_filename, "w") as f:
        f.write("\n".join(latex_defs))

    print(f"Successfully generated LaTeX macros at: {output_filename}")

print("\nAll datasets processed successfully!")
# %%