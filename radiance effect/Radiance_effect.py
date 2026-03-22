# %%
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

# %% 1. 读取 radiance 数据
radiance_data = pd.read_csv("../Box Radiance.csv")
radiance_data.columns = ["boxNum", "radiance(mW)"]
print("=== Radiance Data ===")
print(radiance_data.head())

# %% 2. 读取实验数据
wt_bout_feature_data = pd.read_csv("../Analyzed_data/wt_2025_all_Connected_bout_features_strict.csv")
print(f"\nTotal rows: {len(wt_bout_feature_data)}")

# %% 3. 合并 radiance 信息
merged_data = wt_bout_feature_data.merge(radiance_data, on='boxNum', how='left')
# Ensure radiance is numeric for downstream stats/plotting
merged_data['radiance(mW)'] = pd.to_numeric(merged_data['radiance(mW)'], errors='coerce')
print(f"Merged rows: {len(merged_data)}")

# %% 4. 准备绘图参数
parameter_candidates = [
    ['rot_bout'],
    ['spd_peak'],
    ['displ_swim'],
    ['WHM'],
    ['IBI_time', 'pre_IBI_time', 'post_IBI_time'],
    ['rot_total'],
]
available_params = []
for candidates in parameter_candidates:
    selected = next((p for p in candidates if p in merged_data.columns), None)
    if selected is not None:
        available_params.append(selected)

# %% 5. 数据清理（仅做数值与缺失处理，不删除离群值）
merged_data_clean = merged_data.copy()
for param in available_params:
    merged_data_clean[param] = pd.to_numeric(merged_data_clean[param], errors='coerce')
merged_data_clean = merged_data_clean.replace([np.inf, -np.inf], np.nan)
required_cols = ['radiance(mW)', 'cond1', 'ztime']
missing_required_cols = [col for col in required_cols if col not in merged_data_clean.columns]
if missing_required_cols:
    raise ValueError(f"Missing required columns: {missing_required_cols}")
merged_data_clean = merged_data_clean.dropna(subset=required_cols)
print(f"\n清理后剩余 {len(merged_data_clean)} 行 (原始: {len(merged_data)} 行)")

# %% 6. 按 boxNum + experimental repeat + cond1 + ztime 聚合（使用中位数），再绘制散点+回归线
repeat_cols = [col for col in ['expNum', 'exp'] if col in merged_data_clean.columns]
if not repeat_cols:
    print("Warning: no experimental repeat column found among ['expNum', 'exp']; fallback to box-level aggregation.")
group_cols = ['boxNum'] + repeat_cols + ['cond1', 'ztime', 'radiance(mW)']
agg_dict = {param: 'median' for param in available_params}
aggregated_data = (
    merged_data_clean
    .groupby(group_cols, as_index=False)
    .agg(agg_dict)
)
print(f"聚合后共有 {len(aggregated_data)} 行")

target_conditions = ['ll', 'ld', 'dd']
ztime_order = ['day', 'night', 'transition1', 'transition2']

for condition in target_conditions:
    condition_data = aggregated_data[aggregated_data['cond1'].astype(str) == condition].copy()
    if condition_data.empty:
        print(f"\n{condition}: no data after aggregation, skip.")
        continue

    ztime_values = condition_data['ztime'].astype(str).unique().tolist()
    ordered_ztime = [z for z in ztime_order if z in ztime_values]
    remaining_ztime = [z for z in sorted(ztime_values) if z not in ordered_ztime]
    ztime_values = ordered_ztime + remaining_ztime

    for ztime in ztime_values:
        ztime_data = condition_data[condition_data['ztime'].astype(str) == ztime].copy()
        if ztime_data.empty:
            continue

        n_params = len(available_params)
        n_cols = 3
        n_rows = int(np.ceil(n_params / n_cols))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 5))
        axes = axes.flatten() if n_params > 1 else [axes]

        for idx, param in enumerate(available_params):
            ax = axes[idx]
            plot_data = ztime_data[['radiance(mW)', param]].dropna()
            if plot_data.empty:
                ax.set_title(f'{param}\nNo valid data', fontsize=11, fontweight='bold')
                ax.set_axis_off()
                continue

            x_unique = plot_data['radiance(mW)'].nunique()
            if len(plot_data) >= 3 and x_unique >= 2:
                sns.regplot(
                    data=plot_data,
                    x='radiance(mW)',
                    y=param,
                    scatter_kws={'s': 35, 'alpha': 0.8},
                    line_kws={'color': '#d1495b', 'linewidth': 2},
                    ci=95,
                    ax=ax
                )
                r_val, p_val = stats.pearsonr(plot_data['radiance(mW)'], plot_data[param])
                ax.set_title(
                    f'{param}\nr={r_val:.3f}, p={p_val:.4f}, n={len(plot_data)}',
                    fontsize=11,
                    fontweight='bold'
                )
            else:
                sns.scatterplot(
                    data=plot_data,
                    x='radiance(mW)',
                    y=param,
                    s=35,
                    alpha=0.8,
                    ax=ax
                )
                ax.set_title(
                    f'{param}\nNot enough variation/data (n={len(plot_data)})',
                    fontsize=11,
                    fontweight='bold'
                )

            ax.set_xlabel('Radiance (mW)', fontsize=10)
            ax.set_ylabel(param, fontsize=10)
            ax.grid(True, alpha=0.3)

        for idx in range(n_params, len(axes)):
            axes[idx].set_visible(False)

        plt.suptitle(
            f'Radiance Effect Correlation - {condition} - {ztime}',
            fontsize=14,
            fontweight='bold'
        )
        plt.tight_layout()
        safe_ztime = str(ztime).replace(' ', '_').replace('/', '_')
        plt.savefig(
            f'Plots_folder/radiance_effect_correlation_{condition}_{safe_ztime}.png',
            dpi=300,
            bbox_inches='tight'
        )
        plt.show()
        plt.close(fig)

# %% 7. 保存数据
merged_data_clean.to_csv('Statistics/radiance_merged_data_clean.csv', index=False)
aggregated_data.to_csv('Statistics/radiance_merged_data_agg_box_repeat_cond1_ztime_median.csv', index=False)
print("\n结果已保存：")
print("- Statistics/radiance_merged_data_clean.csv")
print("- Statistics/radiance_merged_data_agg_box_repeat_cond1_ztime_median.csv")

# %% 8. 交互项检验：parameter ~ radiance * cond1 + ztime
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError as exc:
    raise ImportError("statsmodels is required for interaction analysis. Install with: pip install statsmodels") from exc

model_df = aggregated_data.rename(columns={"radiance(mW)": "radiance_mW"}).copy()
model_df["cond1"] = model_df["cond1"].astype("category")
model_df["ztime"] = model_df["ztime"].astype("category")

if available_params:
    param = "rot_bout" if "rot_bout" in available_params else available_params[0]
    m = smf.ols(
        f"{param} ~ radiance_mW * C(cond1) + C(ztime)",
        data=model_df
    ).fit()
    print(f"\n=== Interaction model for {param} ===")
    print(m.summary())
    print("\n=== ANOVA (Type II) ===")
    print(sm.stats.anova_lm(m, typ=2))
else:
    print("\nNo available parameters for interaction model.")
