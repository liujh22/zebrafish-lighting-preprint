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
DATA_FILENAME = "wt_2025_all_Consecutive_bout_3_strict.csv"
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
STATS_DIR = os.path.join(os.path.dirname(os.getcwd()), "Statistics")
plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
set_font_type()
raw_data = load_data(filename=DATA_FILENAME)

sel_consecutive_bouts = raw_data
all_cond1 = sel_consecutive_bouts['cond1'].unique().tolist()
all_cond1.sort()
# IMPORTANT: because did the above calculation in the messy way, we can only pick the middle bouts. Drop the first and last bout of each series
middle_bout_df = sel_consecutive_bouts.loc[sel_consecutive_bouts['lag']>0].reset_index(drop=True)

# --- Colors
palette = ["#4CB9CC", "#D3917D"]


middle_bout_df['compensation_residual'] = middle_bout_df['rot_total'] + middle_bout_df['preIBI_rot']
df_toplt = middle_bout_df
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
middle_bout_df_sel = middle_bout_df.query("cond1 == 'dd'")

middle_bout_df_sel = middle_bout_df_sel.drop(middle_bout_df_sel.loc[middle_bout_df_sel.traj_peak.diff() == 0].index).reset_index(drop=True)

#%%
# splipt by whm into 4 quartiles
quartiles = middle_bout_df_sel['WHM'].quantile([0.25, 0.5, 0.75]).values
# use pd.cut
middle_bout_df_sel['bout_width_cat'] = pd.cut(
    middle_bout_df_sel['WHM'],
    bins=[-np.inf, quartiles[0], quartiles[1], quartiles[2], np.inf],
    labels=['Q1', 'Q2', 'Q3', 'Q4']
)

#%%
plt.figure(figsize=(3,3))
g = sns.histplot(
    color=palette,
    data=middle_bout_df_sel,
    x='compensation_residual',
    hue='bout_width_cat',
    stat='probability',
    element='poly',
    bins='scott',
    # log_scale=True,
)

#%%
# calculate STD per condition per IBI group per expNum
IBI_angles_cond = middle_bout_df_sel.groupby(['bout_width_cat','expNum'], as_index=False).agg(
    ineffectiveness = ('compensation_residual',    lambda x: median_abs_deviation(x)   # MAD
),
)   

# %%
g = sns.FacetGrid(IBI_angles_cond, height=3, sharey=True)

# Plot raw data as dots
g.map_dataframe(
    sns.lineplot,
    x="bout_width_cat",
    y="ineffectiveness",
    palette=palette,
    units='expNum',
    estimator=None,
    alpha=0.6,
    color='gray'
)

# Plot mean as diamonds
g.map_dataframe(
    sns.pointplot,
    x="bout_width_cat",
    y="ineffectiveness",
    hue="bout_width_cat",
    dodge=0.5,
    join=False,
    markers="D",  # diamond
    ci=None,
    palette="Set2"
)
plt.savefig(os.path.join(OUTPUT_DIR, f"{plot_ID}_Point_compensationResidual_MAD_otog.pdf"), format='pdf', bbox_inches='tight')

#%%
# calculate STD per condition per IBI group per expNum
IBI_angles_cond = middle_bout_df_sel.groupby(['ztime','expNum'], as_index=False).agg(
    ineffectiveness = ('compensation_residual',    lambda x: median_abs_deviation(x)   # MAD
),
)   

# %
g = sns.FacetGrid(IBI_angles_cond.loc[IBI_angles_cond['ztime'].isin(['day','night'])], height=3, sharey=True)

# Plot raw data as dots
g.map_dataframe(
    sns.lineplot,
    x="ztime",
    y="ineffectiveness",
    palette=palette,
    units='expNum',
    estimator=None,
    alpha=0.6,
    color='gray'
)

# Plot mean as diamonds
g.map_dataframe(
    sns.pointplot,
    x="ztime",
    y="ineffectiveness",
    hue="ztime",
    dodge=0.5,
    markers="D",  # diamond
    palette="Set2"
)
plt.savefig(os.path.join(OUTPUT_DIR, f"{plot_ID}_Point_compensationResidual_MAD_otog.pdf"), format='pdf', bbox_inches='tight')

# %%
