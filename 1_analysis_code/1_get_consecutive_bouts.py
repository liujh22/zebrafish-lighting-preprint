"""
Input: .h5 file from SAMPL recording
Output: .csv file

Terminology:
    Features -> average swim parameter value (in a period of time)
    Time series -> instantaneous swim parameter value (one sample)
    Bout -> a swimming period when speed > 5mm/s
    IBI (Inter-Bout-Interval) -> period outside of Bout
    Connected Bout -> bouts organized in consecutive order (but contain less data)
    Aligned -> arrange time series data around the center of peak speed

Description of output:
    Bout_features -> each row is average features in one bout
    IBI_features -> each row is average features in one IBI
    Connected_bout_features -> each row is an average features in one bout (connected with each other)
    Bout_timeseries -> each row is an instantaneous feature at one timestamp (during bout)
    All_timeseries -> each row is an instantaneous feature at one timestamp (bout and IBI )
"""

#%%

import os
import pandas as pd
from ana_dependencies.get_bout_features import get_connected_bouts
from ana_dependencies.get_index import get_index
from ana_dependencies.plt_tools import round_half_up
from ana_dependencies.get_bout_consecutive_features import extract_consecutive_bout_features
from get_analysis_ready import load_preprocessed_data

######################################
##### Parameters for data import #####
######################################

out_dir = os.path.join(os.path.dirname(__file__), "Analyzed_data")
datasets = ['wt_2025','haircell']
which_ztime = 'all'  # 'day' or 'night', does not support 'all'

try:
    os.makedirs(out_dir, exist_ok=True)
except OSError as e:
    print(f"Error creating folder '{out_dir}': {e}")

#%%
# Get data directory and frame rate, and process for each dataset
for pick_data in datasets:
    # Get data directory and frame rate
    root, FRAME_RATE = load_preprocessed_data(pick_data)

    peak_idx, total_aligned = get_index(FRAME_RATE)  # Calculate frame of peak speed,
    idxRANGE = [peak_idx - round_half_up(0.3 * FRAME_RATE), peak_idx + round_half_up(0.2 * FRAME_RATE)]

    ####################################
    # Get Consecutive Bout features #
    ####################################

    for consecutive_bout_num in [3,5]:
        if datasets == 'haircell' and consecutive_bout_num == 5:
            print("Skip haircell dataset with 5 consecutive bouts. Not needed.")
            continue
        else:
            all_features, all_cond0, all_cond1 = get_connected_bouts(root, FRAME_RATE, ztime=which_ztime,day_light_narrow_bin=True)

            # %% std of directions of consecutive bouts
            list_of_features = ['traj_peak', 'pitch_peak', 'spd_peak','rot_full_accel','rot_l_decel',
                                'pitch_end', 'pitch_initial','post_IBI_time','pre_IBI_time','rot_total',
                                'ydispl_swim','y_pre_swim','y_post_swim','x_initial','pre_IBI_align_time',
                                'y_initial','y_end','xdispl_swim','bout_time','bout_trajectory_Pre2Post','WHM']



            # %% Connect consecutive bouts
            max_lag = consecutive_bout_num - 1
            consecutive_bout_features, _ = extract_consecutive_bout_features(all_features, list_of_features, max_lag)
            pitch_bins = [-90,0,20, 90]
            sel_consecutive_bouts = consecutive_bout_features.sort_values(by=['cond1','cond0','id','lag','ztime']).reset_index(drop=True)
            sel_consecutive_bouts = sel_consecutive_bouts.assign(
                pitch_peak_bins = pd.cut(sel_consecutive_bouts['pitch_peak_first'], bins=pitch_bins, labels=['dive','flat','climb']).values,
                bouts = sel_consecutive_bouts['lag'] + 1
            )

            # Compare current y_initial with next bout's y_initial
            sel_consecutive_bouts['bout_direction'] = sel_consecutive_bouts.apply(
                lambda row: 'climb' if row['y_initial'] < row['y_end'] else 'dive',
                axis=1
            )

            selected_data = (
                sel_consecutive_bouts
                .groupby(["cond1",  "ztime", "expNum","id"], as_index=False)
                .apply(lambda group: group.assign(
                    preIBI_y_displ=group["y_initial"]-group["y_end"].shift(1)  ,  # preIBI_y_displ = y end from last bout - y initial from current bout
                    postIBI_y_displ=group["y_initial"].shift(-1) - group["y_end"],   # postIBI_y_displ = y initial from next bout - y end from current bout
                    preIBI_rot=group["pitch_initial"] - group["pitch_end"].shift(1),
                    postIBI_rot=group["pitch_initial"].shift(-1) - group["pitch_end"]
                ), include_groups=False)
                .reset_index(drop=True)  # Reset index after apply()
            )
            

            # Out put in .csv
            output_file = os.path.join(out_dir, f'{pick_data}_{which_ztime}_Consecutive_bout_{consecutive_bout_num}_strict.csv')
            selected_data.to_csv(output_file, index=False)
