# %%
import os
import pandas as pd # pandas library
import numpy as np # numpy
import seaborn as sns
import matplotlib.pyplot as plt

import statsmodels.api as sm
import statsmodels.robust.norms as norms
from sklearn.metrics import r2_score
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.robust.norms as norms
from sklearn.metrics import r2_score
from get_visualization_ready import set_font_type, load_data, get_daytime_data
from scipy.stats import median_abs_deviation
from scipy import stats

#%%

# %%
DATA_FILENAME = "otog_all_Consecutive_bout_2_strict.csv"
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
set_font_type()
raw_data = load_data(filename=DATA_FILENAME)

sel_consecutive_bouts = raw_data
all_cond1 = sel_consecutive_bouts['cond1'].unique().tolist()
all_cond1.sort()
# IMPORTANT: because did the above calculation in the messy way, we can only pick the middle bouts. Drop the first and last bout of each series
middle_bout_df = sel_consecutive_bouts.loc[sel_consecutive_bouts['lag']==1].reset_index(drop=True)
middle_bout_df = middle_bout_df.loc[middle_bout_df['ztime'].isin(['day'])].reset_index(drop=True)

middle_bout_df['IBI_group'] = 'pre_short'
IBI_threshold = middle_bout_df.loc[middle_bout_df['cond1']==all_cond1[0],'pre_IBI_time'].median()
middle_bout_df.loc[(middle_bout_df['pre_IBI_time']>IBI_threshold), 'IBI_group'] = 'pre_long'

# --- Colors
palette = ["#4CB9CC", "#D3917D"]


middle_bout_df['compensation_residual'] = middle_bout_df['rot_total'] + middle_bout_df['pre_B2B_rot']
df_toplt = middle_bout_df.query("IBI_group == 'pre_long'")
# remove extreme values
df_toplt_filter = df_toplt.loc[
    (df_toplt['compensation_residual'] > df_toplt['compensation_residual'].quantile(0.005)) &
    (df_toplt['compensation_residual'] < df_toplt['compensation_residual'].quantile(0.995))
    ].reset_index(drop=True)

plt.figure(figsize=(3,3))
g = sns.histplot(
    color=palette,
    data=df_toplt_filter,
    x='compensation_residual',
    hue='cond1',
    stat='probability',
    element='poly',
    bins='scott',
    # log_scale=True,
)
plt.savefig(os.path.join(OUTPUT_DIR, f"{plot_ID}_Density_compensationResidual_otog.pdf"), format='pdf', bbox_inches='tight')

#%%


# calculate STD per condition per IBI group per expNum
IBI_angles_cond = middle_bout_df.groupby(['cond0','cond1','expNum','IBI_group'], as_index=False).agg(
    ineffectiveness = ('compensation_residual',    lambda x: median_abs_deviation(x)   # MAD
),
)   

# %%
g = sns.FacetGrid(IBI_angles_cond.query("IBI_group == 'pre_long'"), col="IBI_group", height=3, sharey=True)

# Plot raw data as dots
g.map_dataframe(
    sns.stripplot,
    x="cond1",
    y="ineffectiveness",
    palette=palette,
    hue="cond1",
    dodge=True,
    jitter=True,
    alpha=0.6,
)

# Plot mean as diamonds
g.map_dataframe(
    sns.pointplot,
    x="cond1",
    y="ineffectiveness",
    hue="cond1",
    dodge=0.5,
    join=False,
    markers="D",  # diamond
    ci=None,
    palette="Set2"
)
plt.savefig(os.path.join(OUTPUT_DIR, f"{plot_ID}_Point_compensationResidual_MAD_otog.pdf"), format='pdf', bbox_inches='tight')

#%%
stats_df = IBI_angles_cond.query("IBI_group == 'pre_long'")

val_hets = stats_df.loc[stats_df['cond1']==all_cond1[0]].ineffectiveness.dropna()
val_otog = stats_df.loc[stats_df['cond1']==all_cond1[1]].ineffectiveness.dropna()

t2, p2 = stats.ttest_ind(val_hets, val_otog, nan_policy='omit')

summary_df = (stats_df
                .groupby('cond1')['ineffectiveness']
                .agg(Mean='mean', SD='std')
                .reset_index()
                .rename(columns={'cond1': 'Condition'}))

# Add test results
test_row = pd.DataFrame([{
    'Condition': 'hets vs otog',
    'Mean': None,
    'SD': None,
    't': t2,
    'p': p2
}])

result_table = pd.concat([summary_df, test_row], ignore_index=True)
print("\nSummary Table:")
print(result_table.to_string(index=False))
# %%
# Calculate effect size
stats1 = summary_df.loc[summary_df['Condition'] == 'hets']
stats2 = summary_df.loc[summary_df['Condition'] == 'otog']
pooled_sd = np.sqrt((stats1['SD'].values[0] ** 2 + stats2['SD'].values[0] ** 2) / 2)
effect_size = (stats1['Mean'].values[0] - stats2['Mean'].values[0]) / pooled_sd

# Convert y_var to camelCase (remove underscores and capitalize following letters)
latex_var = ''.join(word.capitalize() for word in 'residual_variability'.split('_'))

# Save LaTeX macros
os.makedirs(STATS_DIR, exist_ok=True)
macros_path = os.path.join(STATS_DIR, f"{plot_ID}_Grouped{latex_var}Macros.tex")

macros = [
    f"\\def\\Grouped{latex_var}hetsDayMean{{{stats1['Mean'].values[0]:.3f}}}",
    f"\\def\\Grouped{latex_var}hetsDaySD{{{stats1['SD'].values[0]:.3f}}}",
    f"\\def\\Grouped{latex_var}mutDayMean{{{stats2['Mean'].values[0]:.3f}}}",
    f"\\def\\Grouped{latex_var}mutDaySD{{{stats2['SD'].values[0]:.3f}}}",
    f"\\def\\Grouped{latex_var}hetsDayVsmutDayTvalue{{{t2:.3f}}}",
    f"\\def\\Grouped{latex_var}hetsDayVsmutDayPvalue{{{p2:.3e}}}",
    f"\\def\\Grouped{latex_var}hetsDayVsmutDayEffectSize{{{abs(effect_size):.3f}}}"
]

with open(macros_path, "w") as f:
    f.write("\n".join(macros))
    
    
#%% Calculate parameters for tables

print(df_toplt.groupby('cond1')['compensation_residual'].median())
print("IQR")
print(df_toplt.groupby('cond1')['compensation_residual'].apply(
     stats.iqr
))
print("MAD")
print(df_toplt.groupby('cond1')['compensation_residual'].apply(
     stats.median_abs_deviation
))

# %%
