# %%
import os
import pandas as pd # pandas library
import numpy as np # numpy
import seaborn as sns
import matplotlib.pyplot as plt
from get_visualization_ready import set_font_type, load_data


'''
Plots single epoch that contains one or more bouts
'''

plot_ID = os.path.basename(__file__).split("_")[0]  # e.g. 'Plot 1A'
#%%
INFO_FILENAME = "LD epoch_epoch_info.csv"
DATA_FILENAME = "LD epoch_epoch_data.csv"
epoch_data_all = load_data(filename=DATA_FILENAME)
epoch_info_all = load_data(filename=INFO_FILENAME)

# %%

sec5frames = int(166 * 5 /5)

downsampled_df = epoch_data_all.iloc[::5, :]

#%

epoch_combined = pd.DataFrame()
for epoch_num in [17449, 27299, 18694,9487]:
    toplt = epoch_info_all.loc[epoch_info_all['epoch_num']==epoch_num,:]
    data_toplt = downsampled_df.loc[(downsampled_df['exp_num']==toplt['exp_num'].values[0]) & (downsampled_df['epochNum']==epoch_num), :]

    if epoch_num == 17449:
        data_toplt = data_toplt.iloc[
            40:40+sec5frames
        ]
        data_toplt['x'] = data_toplt['x'] * -1
        
    
    if epoch_num == 27299:
        i0 = 10
        print(len(data_toplt))
        data_toplt = data_toplt.iloc[
            i0:i0+sec5frames
        ]        
        data_toplt['x'] = data_toplt['x'] * -1
        
    
    if epoch_num == 9487:
        i0 = 10
        data_toplt = data_toplt.iloc[
            i0:i0+sec5frames
        ]        
        data_toplt['x'] = data_toplt['x'] * -1

    if epoch_num == 18694:
        i0 = 70
        data_toplt = data_toplt.iloc[
            i0:i0+sec5frames
        ]        

    data_toplt[['x','y']] = data_toplt[['x','y']] - data_toplt[['x','y']].values[0]
    data_toplt = data_toplt.assign(
        epoch_num = epoch_num
    )
    epoch_combined = pd.concat([epoch_combined,data_toplt],ignore_index=True)



plt.figure(figsize=(4,4))

p = sns.scatterplot(
    data = epoch_combined, x = 'x', y = 'y', alpha = 0.5, linewidths=0,legend='full',
    s=10,
    # hue='epoch_num',
    )
plt.axis('equal')
p.set(
    xlim=(-2,12),
    ylim=(-6,10),
)
# ------------------------------
# Save plot
# ------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(OUTPUT_DIR, exist_ok=True)

output_filename = f"{plot_ID}_Traces_Light.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)
plt.savefig(output_path,format='PDF')

# %%
INFO_FILENAME = "DD epoch_epoch_info.csv"
DATA_FILENAME = "DD epoch_epoch_data.csv"
epoch_data_all = load_data(filename=DATA_FILENAME)
epoch_info_all = load_data(filename=INFO_FILENAME)

sec5frames = int(166 * 5 /5)

downsampled_df = epoch_data_all.iloc[::5, :]

#%%

#  [62133, 58213, 36133, 3257]
# epochs_list = [4040, 36133, 17216, 3257,30892]


epoch_combined = pd.DataFrame()
for epoch_num in [1154, 171,4846, 482]:
    toplt = epoch_info_all.loc[epoch_info_all['epoch_num']==epoch_num,:]
    data_toplt = downsampled_df.loc[(downsampled_df['exp_num']==toplt['exp_num'].values[0]) & (downsampled_df['epochNum']==epoch_num), :]

    
    if epoch_num == 1154:
        i0 = 220
        if i0+sec5frames < len(data_toplt):
            data_toplt = data_toplt.iloc[
                i0:i0+sec5frames
            ]     
        else:
            break
            
    if epoch_num == 171:
        i0 = 80
        if i0+sec5frames < len(data_toplt):
            data_toplt = data_toplt.iloc[
                i0:i0+sec5frames
            ]     
        else:
            break
    if epoch_num == 4846:
        i0 = 240
        if i0+sec5frames < len(data_toplt):
            data_toplt = data_toplt.iloc[
                i0:i0+sec5frames
            ]     
        else:
            break
    if epoch_num == 482:
        i0 = 20
        if i0+sec5frames < len(data_toplt):
            data_toplt = data_toplt.iloc[
                i0:i0+sec5frames
            ]     
        else:
            break

    data_toplt[['x','y']] = data_toplt[['x','y']] - data_toplt[['x','y']].values[0]
    data_toplt = data_toplt.assign(
        epoch_num = epoch_num
    )
    epoch_combined = pd.concat([epoch_combined,data_toplt],ignore_index=True)

plt.figure(figsize=(4,4))

p = sns.scatterplot(
    data = epoch_combined, x = 'x', y = 'y', alpha = 0.5, linewidths=0,legend='full',
    s=10,
    # hue='epoch_num',
    )
plt.axis('equal')
p.set(
    xlim=(-2,12),
    ylim=(-6,10),
)
# ------------------------------
# Save plot
# ------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.getcwd()), "Plots_folder")
os.makedirs(OUTPUT_DIR, exist_ok=True)

output_filename = f"{plot_ID}_Traces_Dark.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)
plt.savefig(output_path,format='PDF')
########################

# %%
