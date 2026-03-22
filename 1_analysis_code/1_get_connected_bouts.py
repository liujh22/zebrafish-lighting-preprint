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
import os
from ana_dependencies.get_bout_features import get_connected_bouts
from ana_dependencies.get_index import get_index
from ana_dependencies.plt_tools import round_half_up
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

# Get data directory and frame rate
for pick_data in datasets:
    root, FRAME_RATE = load_preprocessed_data(pick_data)

    peak_idx, total_aligned = get_index(FRAME_RATE)  # Calculate frame of peak speed,
    idxRANGE = [peak_idx - round_half_up(0.3 * FRAME_RATE), peak_idx + round_half_up(0.2 * FRAME_RATE)]

    ####################################
    # Get only Connected Bout features #
    ####################################
    all_features_strict, all_cond0, all_cond1 = get_connected_bouts(root, FRAME_RATE, ztime=which_ztime, day_light_narrow_bin=True)

    # Out put in .csv
    output_file = os.path.join(out_dir, f'{pick_data}_{which_ztime}_Connected_bout_features_strict.csv')
    all_features_strict.to_csv(output_file, index=False)


