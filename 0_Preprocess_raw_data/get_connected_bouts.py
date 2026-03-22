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
import sys

# Get Yunlu's modules
module_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",  # up from Preprocessing_code to project root
        "SAMPL_src",
        "src"  # add 'src' so that SAMPL_visualization is found
    )
)
if module_path not in sys.path:
    sys.path.append(module_path)

from SAMPL_visualization.plot_functions import get_bout_features
from SAMPL_visualization.plot_functions import get_bout_correlation
from SAMPL_visualization.plot_functions import get_bout_consecutive_features
from SAMPL_visualization.plot_functions import get_data_dir
from SAMPL_visualization.plot_functions import get_IBIangles
from SAMPL_visualization.plot_functions import get_index
from SAMPL_visualization.plot_functions import plt_functions
from SAMPL_visualization.plot_functions import plt_stats
from SAMPL_visualization.plot_functions import plt_tools

######################################
##### Parameters for data import #####
######################################
plt_tools.set_font_type()  # Set font type and default plotting style
plt_tools.defaultPlotting()
out_dir = '../Preprocessed_data'  # Save .csv results in this folder

datasets = ['haircell', 'wt_2025']
which_ztime = 'all'  # 'day' or 'night', does not support 'all'

# Get data directory and frame rate
for pick_data in datasets:
    root, FRAME_RATE = get_data_dir.get_data_dir(pick_data)

    peak_idx, total_aligned = get_index.get_index(FRAME_RATE)  # Calculate frame of peak speed,
    idxRANGE = [peak_idx - plt_tools.round_half_up(0.3 * FRAME_RATE), peak_idx + plt_tools.round_half_up(0.2 * FRAME_RATE)]

    ####################################
    # Get only Connected Bout features #
    ####################################
    all_features_strict, all_cond0, all_cond1 = get_bout_features.get_connected_bouts(root, FRAME_RATE, ztime=which_ztime, day_light_narrow_bin=True)

    # Out put in .csv
    output_file = os.path.join(out_dir, f'{pick_data}_{which_ztime}_Connected_bout_features_strict.csv')
    all_features_strict.to_csv(output_file, index=False)


    # Not strict z-time
    # all_features, all_cond0, all_cond1 = get_bout_features.get_connected_bouts(root, FRAME_RATE, ztime=which_ztime, day_light_narrow_bin=False)
    #
    # output_file = os.path.join(out_dir, f'{pick_data}_{which_ztime}_Connected_bout_features.csv')
    # all_features.to_csv(output_file, index=False)
