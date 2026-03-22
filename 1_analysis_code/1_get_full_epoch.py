"""
"""

#%%

import os
import pandas as pd
import numpy as np
from get_analysis_ready import load_preprocessed_data


def extract_epochs(root):
    # below are all the properties can be plotted. 
    all_features = {
        'ang':'pitch', # (deg)',
        # 'absy':'y position (mm)'
        # 'deltaT', 
        'x':'x',
        'y':'y',
        'headx':'headx',# (mm)',
        'heady':'heady',# (mm)',
        # 'centeredAng':'centered angle (deg)',
        'xvel':'xvel', 
        'yvel':'yvel', 
        'dist':'distance', # (mm)',
        # 'displ':'displacement (mm)',
        'angVel':'angvel', #(deg*s-1)',
        # 'angVelSmoothed', 
        # 'angAccel':'ang accel (deg*s-2)',
        'swimSpeed':'speed',# (mm*s-1)',
        'velocity':'velocity',# (mm*s-1)'
    }

    # for each sub-folder, get the path
    all_dir = [ele[0] for ele in os.walk(root)]
    if len(all_dir) > 1:
        all_dir = all_dir[1:]
    else:
        raise Exception("No LD / DD epochs found in the Analyzed_data directory. \nPlease copy LD epoch and DD epoch folders from 0_Preprocess_raw_data and paste to Analyzed_data.")

    epoch_info_all = pd.DataFrame()
    epoch_data_all = pd.DataFrame()
    for exp_num, exp_path in enumerate(all_dir):
        # get pitch                
        all_data = pd.read_hdf(f"{exp_path}/all_data.h5", key='grabbed_all')


        exp_data = all_data.loc[:,all_features.keys()]
        exp_data = exp_data.rename(columns=all_features)
        exp_data = exp_data.assign(
            exp_num = exp_num,
            epochNum = all_data['epochNum'].values,
            deltaT = all_data['deltaT'].values
        )
        
        epoch_info = exp_data.groupby('epochNum').size().reset_index()

        epoch_info = epoch_info.rename(columns={
            'epochNum':'epoch_num',
            0:'frame_num',
        })
        epoch_info.reset_index(drop=True)
        epoch_info = epoch_info.assign(
            idx = np.arange(0,len(epoch_info))+1,
            duration = epoch_info['frame_num']/FRAME_RATE,
            exp_num = exp_num,
        )
        epoch_info_all = pd.concat([epoch_info_all,epoch_info], ignore_index=True)
        epoch_data_all = pd.concat([epoch_data_all,exp_data], ignore_index=True)
        
    epoch_info_all = epoch_info_all.sort_values(by='duration',ascending=False)
    epoch_info_all = epoch_info_all.reset_index(drop=True)
    return epoch_data_all, epoch_info_all

#%%
out_dir = os.path.join(os.path.dirname(__file__), "Analyzed_data")
datasets = ['LD epoch', 'DD epoch']

try:
    os.makedirs(out_dir, exist_ok=True)
except OSError as e:
    print(f"Error creating folder '{out_dir}': {e}")

#%
# Get data directory and frame rate, and process for each dataset
for pick_data in datasets:
    
    root, FRAME_RATE = load_preprocessed_data(pick_data)
    epoch_data_all, epoch_info_all = extract_epochs(root)

    # Out put in .csv
    output_file = os.path.join(out_dir, f'{pick_data}_epoch_data.csv')
    epoch_data_all.to_csv(output_file, index=False)
    output_file = os.path.join(out_dir, f'{pick_data}_epoch_info.csv')
    epoch_info_all.to_csv(output_file, index=False)

# %%
