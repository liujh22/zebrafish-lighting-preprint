"""
Description: Computes and visualizes normalized density distribution of rot_total under different lighting conditions.
"""
#%%
import os
from datetime import date
import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
from get_visualization_ready import set_font_type, load_data, get_daytime_data
from scipy.stats import median_abs_deviation,iqr

#%%

def main():
    #%%
    # --------------------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------------------
    DATA_FILENAME = "wt_2025_all_Consecutive_bout_3_strict.csv"
    Y_VAR = "rot_total"
    X_VAR = "cond1"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
    plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'

    # --------------------------------------------------------------------------
    # Data Loading & Preprocessing
    # --------------------------------------------------------------------------
    set_font_type()
    raw_data = load_data(filename=DATA_FILENAME)
    dd_data = get_daytime_data(raw_data)
    dd_data = dd_data[dd_data['cond1'] == "dd"].copy()


    # =========================
    # PRE-IBI grouping
    # =========================

    median_pre_ibi = dd_data['pre_IBI_time'].median()

    dd_data['IBI_group_pre'] = np.where(
        dd_data['pre_IBI_time'] >= median_pre_ibi,
        "Long IBI",
        "Short IBI"
    )
    #%%
    dd_data['compensation_residual_pre'] = dd_data['rot_total'] + dd_data['preIBI_rot']
    # filter by IBI group
    data_toplt = dd_data[dd_data['IBI_group_pre'] == "Long IBI"].copy()
    # exclude extreme values
    data_toplt = data_toplt.loc[
        (data_toplt['compensation_residual_pre'] > data_toplt['compensation_residual_pre'].quantile(0.005)) &
        (data_toplt['compensation_residual_pre'] < data_toplt['compensation_residual_pre'].quantile(0.995))
    ].reset_index(drop=True)
    plt.figure(figsize=(3,3))
    g = sns.histplot(
        data=data_toplt,
        x='compensation_residual_pre',
        hue='cond1',
        stat='probability',
        element='poly',
        bins='scott',
        # log_scale=True,
    )
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{plot_ID}_density_{'compensation_residual_pre'}.pdf"
    plt.savefig(os.path.join(OUTPUT_DIR, output_filename), bbox_inches='tight')
    #%%
    print(f"median  {data_toplt['compensation_residual_pre'].median()}")
    print("IQR")
    print(f" {iqr(data_toplt['compensation_residual_pre'])}")
    print("MAD")
    print(f"{median_abs_deviation(data_toplt['compensation_residual_pre'])}")

#%%
if __name__ == "__main__":
    main()