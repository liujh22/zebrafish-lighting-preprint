"""
Vestibular circuit simulation and behavior generation program
"""

# Import packages
import matplotlib.pyplot as plt
from utils import *

# Load data
IEI_data = pd.read_csv("/Users/jiahuan/Desktop/NYU_Intern/R_Code/IBI_data_preprocessed_SD_removed.csv")
Bout_data = pd.read_csv("/Users/jiahuan/Desktop/NYU_Intern/R_Code/Bout_data_preprocessed_SD_removed.csv")

# Initialize condition list
conditions = ['dd_day', 'dd_night', 'ld_day', 'ld_night', 'll_day', 'll_night']

# Create dictionary to save data
condition_to_IEI_df = {}
condition_to_Bout_df = {}

# Calculate deviation from preferred pitch and bout rate in each condition
for condition in conditions:
    condition_to_IEI_df[condition] = calculate_deviation_bout_rate(IEI_data[IEI_data['label'] == condition])
    condition_to_Bout_df[condition] = Bout_data[Bout_data['label'] == condition]

# %%
# Calculate constants in different conditions
print("#########################################")
print("#### Welcome to the fish simulator! #####")
print("#########################################")
print("### Let's set some constants first :D ###")
print("#########################################")

(selected_max_abs_pitch_change,
 selected_condition,
 selected_pref_posture,
 selected_basal_bout_rate) = ask_constant_change(IEI_data, Bout_data)

# Adjustable parameters
PREFERRED_POSTURE = selected_pref_posture  # Pitch at stable posture, in degree.
BASAL_BOUTRATE = selected_basal_bout_rate  # Boutrate at stable posture, in Hz.
MAX_PITCH_CHANGE = selected_max_abs_pitch_change  # Max net rotation in deceleration process, in degree.

# %%
# Fixed parameters
SAMPLERATE = 166  # in Hz.
BOUT_TIME = 0.45  # How long takes a bout, in second.
MODEL_TIME = 3000  # How long takes a simulation, in second.
REFRACTORY_TIME = 0.25 # How long is the absolute refractory time, in second.
RECOVERY_TIME = 1.07025  # How long is the relativle refractory period, in second.
BOUT_DURATION = BOUT_TIME * SAMPLERATE  # How long takes a bout, in samples.
MODEL_DURATION = MODEL_TIME * SAMPLERATE  # How long takes one simulation, in samples.
REFRACTORY_DURATION = REFRACTORY_TIME * SAMPLERATE  # Absolute refractory period, in samples.
RECOVERY_DURATION = RECOVERY_TIME * SAMPLERATE  # Relativle refractory period, in samples.
ITERATIONS = 50  # How many simulations do you want?
BIN_NUMBER = 80  # Number of bins for IEI_pauseDur plotting.
SPEED_BOUNDARY = 1  # Speed below this are slow bouts, mm/s
IEI_BOUNDARY = 2  # IEI below this are short IEIs, in second

# Switches
SENSITIVITY_SWITCH = 1  # Set to 0, if you want to deactivate the sensitivity fitting.

# %%
print("")
print("##################################")
print("### Passive AngAcc Calculation ###")
print("##################################")
# Select slow speed and long IBI bouts
filtered_data = condition_to_IEI_df[selected_condition][
    (condition_to_IEI_df[selected_condition]['propBoutIEI'] >= IEI_BOUNDARY) & (
            condition_to_IEI_df[selected_condition]['propBoutIEI_spd'] <= SPEED_BOUNDARY)]

# Calculate passive AngAcc
PASSIVE_AngAcc = filtered_data['propBoutIEI_angAcc'].median()
PASSIVE_AngAcc_SD = filtered_data['propBoutIEI_angAcc'].std()
print()
print(f"Median of Passive AngAcc:, {PASSIVE_AngAcc:.2f}")
print(f"SD of Passive AngAcc:, {PASSIVE_AngAcc_SD:.2f}")

# %%
print("")
print("##################################")
print("### AngVel Sensitivity Fitting ###")
print("##################################")

filtered_df = condition_to_IEI_df[selected_condition]
x = filtered_df['propBoutIEI_angVel'].values
y = filtered_df['bout_rate'].values

# Calculate median of x
median_angVel = np.median(x)

# Split data into two segments
segment1 = filtered_df[filtered_df['propBoutIEI_angVel'] < median_angVel]
segment2 = filtered_df[filtered_df['propBoutIEI_angVel'] >= median_angVel]

# Perform linear fitting for each segment
k1, b1, sd1, r_squared1 = simple_linear_fit(segment1, 'bout_rate', 'propBoutIEI_angVel')
k2, b2, sd2, r_squared2 = simple_linear_fit(segment2, 'bout_rate', 'propBoutIEI_angVel')

# Assigning the results
m_up = k2  # Slope of the up-going branch (right of the center_angVel)
m_up_intercept = b2
m_up_r_squared = r_squared2
m_down = k1  # Slope of the down-going branch (left of the center_angVel)
m_down_intercept = b1
m_down_r_squared = r_squared1

# %%
print("")
print("#################################")
print("### Pitch Sensitivity Fitting ###")
print("#################################")
pitch_sensitivity_a, pitch_sensitivity_c, pitch_sensitivity_r_squared = quadratic_function(
    condition_to_IEI_df[selected_condition], 'bout_rate', 'deviation_from_preferred_pitch')

# %%
print("")
print("#################################")
print("### AngVel Correction Fitting ###")
print("#################################")
angvel_correction_k, angvel_correction_b, angvel_correction_SD, angvel_correction_r_squared = theil_linear_fit(
    condition_to_Bout_df[selected_condition], "angvel_chg", "angvel_initial_phase")

# %%
# Pitch Correction (-250ms to 0ms)
print("")
print("#################################################")
print("### Pitch Correction Part 1 (Initial -> Peak) ###")
print("#################################################")
peak_pitch_k, peak_pitch_b, peak_pitch_SD, peak_pitch_r_squared = theil_linear_fit(
    condition_to_Bout_df[selected_condition], "pitch_peak", "pitch_initial")

# %%
# Pitch Correction (0ms to 200ms)
print("")
print("#############################################################")
print("### Pitch Correction Part 2 (Peak -> Full Deceleration) #####")
print("#############################################################")
righting_Asym, righting_xmid, righting_scal, righting_c, righting_r_squared, righting_SD = sigmoid_function(
    condition_to_Bout_df[selected_condition], "rot_full_decel", "pitch_initial")

# %%
# Define histogram boundaries for plotting
edges_Pitch = np.arange(-90, 95, 5)
edges_av = np.arange(-100, 102, 1)
edges_IEI = np.linspace(0, 20, BIN_NUMBER + 1)

# Predefined arrays for holding histogram data
All_Counts_IEI = np.zeros((ITERATIONS, len(edges_IEI) - 1))
All_Counts_Pitch = np.zeros((ITERATIONS, len(edges_Pitch) - 1))
All_Counts_AngVel = np.zeros((ITERATIONS, len(edges_av) - 1))
All_Counts_IEI_Pitch = np.zeros((ITERATIONS, len(edges_Pitch) - 1))

# %%
### Start Simulation ###
for model_Iteration in range(ITERATIONS):

    # Initialize lists for appending simulated bout properties
    Pitch_list = []  # Pitch in each frame
    AngVel_list = []  # AngVel in each frame
    Pre_Bout_Pitch = []  # Pitch before a bout initiation
    Pre_Bout_AngVel = []  # AngVel before a bout initiation
    Net_Bout_Rotation = []  # Rotation change during a bout
    Net_Bout_AngVel_Change = []  # AngVel change during a bout
    Bout_Index = []  # Start framerate of a bout
    IBI = []  # Inter Bout Interval (time between two bout initiations)

    # Initialize values for the first frame
    Current_Pitch = np.random.randint(-90, 91)  # current pitch, randomly start between -90 and 90
    Current_AngVel = 0  # current angvel, begins at horizontal and with no angular velocity

    # Append initial values to lists
    Pitch_list.append(Current_Pitch)
    AngVel_list.append(Current_AngVel)
    Bout_Index.append(0)
    IBI.append(0)  # The simulation begins as though a bout was just terminated

    # Frame index
    t = 1

    # The simulation advances time-steps using a while loop
    while t < MODEL_DURATION:

        # Current acceleration is generated from a normal distribution
        acc = np.random.normal(PASSIVE_AngAcc, PASSIVE_AngAcc_SD, 1)[0]

        # Calculate Angel Velocity and Pitch
        Current_AngVel = AngVel_list[-1] + np.cos(
            np.deg2rad(Pitch_list[-1])) * acc / SAMPLERATE  # Update Angel Velocity
        Current_Pitch = Pitch_list[-1] + Current_AngVel / SAMPLERATE  # Update Pitch

        # Limit pitch between +/- 180 degree
        if Current_Pitch < -180:
            Current_Pitch += 360
        elif Current_Pitch > 180:
            Current_Pitch -= 360

        # Append new values into list after passive process
        Pitch_list.append(Current_Pitch)
        AngVel_list.append(Current_AngVel)

        # Bout Initiation Section
        if SENSITIVITY_SWITCH == 0:
            """ (Optional) Deactivate Sensitivity fitting """
            if t - Bout_Index[-1] <= REFRACTORY_DURATION:
                P_bout = 0  # No bout within refactory period
            elif t - Bout_Index[-1] < RECOVERY_DURATION:
                P_bout = (BASAL_BOUTRATE / SAMPLERATE) * (
                        t - Bout_Index[-1]) * 1 / RECOVERY_DURATION  # Limited probability in recovery period
            else:
                P_bout = (BASAL_BOUTRATE / SAMPLERATE)  # Normal probability of bouts per sample

        else:
            """ (Default) Calculate a posture-variant P_bout """
            # AngVel sensitivity dependent P_bout
            if Current_AngVel > median_angVel:
                # Double used basal bout rate, in AngVel and Pitch sensitivity, should minus half
                angvel_pbout = (((m_up * Current_AngVel) + m_up_intercept) / SAMPLERATE)
            else:
                # Devided by sample rate to get pure probability
                angvel_pbout = (((m_down * Current_AngVel) + m_down_intercept) / SAMPLERATE)

                # Pitch sensitivity dependent P_bout
            pitch_pbout = ((pitch_sensitivity_a * (
                    Current_Pitch - PREFERRED_POSTURE) ** 2 + pitch_sensitivity_c) / SAMPLERATE)

            basal_pbout = BASAL_BOUTRATE/SAMPLERATE
            # Refactory, Recovery dependent P_bout
            if t - Bout_Index[-1] <= REFRACTORY_DURATION:
                P_bout = 0
            elif t - Bout_Index[-1] < RECOVERY_DURATION:
                P_bout = (pitch_pbout + angvel_pbout-basal_pbout) * (t - Bout_Index[-1]) * 1 / RECOVERY_DURATION
            else:
                P_bout = (pitch_pbout + angvel_pbout - basal_pbout)

        # Initiate bout if a random number is smaller than P_bout
        if np.random.rand() < P_bout:
            Bout_Index.append(t)  # Record current frame index "t" as bout start frame

            # Append pre-bout posture for diagnostics
            Pre_Bout_Pitch.append(Current_Pitch)
            Pre_Bout_AngVel.append(Current_AngVel)

            ### Calculate AngVel change in a bout
            Net_Bout_AngAcc_Change = np.random.normal(angvel_correction_k * Current_AngVel + angvel_correction_b,
                                                      angvel_correction_SD)
            # Add AngVel change into a list
            Net_Bout_AngVel_Change.append(Net_Bout_AngAcc_Change)

            # Calculate post bout AngVel
            Post_bout_AngVel = Current_AngVel + Net_Bout_AngVel_Change[-1]

            # Calculate and interpolate AngVel in a bout
            interpolated_angvels = np.linspace(Current_AngVel, Post_bout_AngVel, int(BOUT_DURATION + 1))
            AngVel_list.extend(interpolated_angvels[1:])

            # Update current AngVel
            Current_AngVel = Post_bout_AngVel

            ### Calculate Pitch_peak using Current pitch
            Pitch_peak = np.random.normal((peak_pitch_k * Current_Pitch + peak_pitch_b), peak_pitch_SD)

            # From initial to peak Pitch takes 0.25s of a 0.45s bout
            interpolated_pitches = np.linspace(Current_Pitch, Pitch_peak,
                                               round(BOUT_DURATION * (0.25 / BOUT_TIME) + 1))
            Pitch_list.extend(interpolated_pitches[1:])
            Current_Pitch = Pitch_peak
            t += round(BOUT_DURATION * (0.25 / BOUT_TIME))  # Update time, 更新时间, 跳过已经插值的部分

            ### Calculate full deceleration righting rotation
            netrot = np.random.normal(
                ((righting_Asym / (1 + np.exp((righting_xmid - Current_Pitch) / righting_scal))) + righting_c),
                righting_SD)

            # If net rotation as calculated is greater than absolute value of the max bout pitch change then change it to that ceiling
            if abs(netrot) < MAX_PITCH_CHANGE:  # Small is fine
                Net_Bout_Rotation.append(netrot)
            elif netrot > MAX_PITCH_CHANGE:
                # Rotation is 60 degree or larger
                Net_Bout_Rotation.append(MAX_PITCH_CHANGE)  # Only append the maximum degree (60)
            else:
                # Rotation is -60 degree or larger
                Net_Bout_Rotation.append(-MAX_PITCH_CHANGE)  # Only append -60

            # Apply net bout rotation and net bout angular acceleration across bout
            Post_righting_Pitch = Current_Pitch + Net_Bout_Rotation[-1]

            # 使用np.linspace插补数据, # rot_full_decel takes 0.2s of a 0.45s bout
            interpolated_pitches = np.linspace(Current_Pitch, Post_righting_Pitch,
                                               round(BOUT_DURATION * (0.2 / BOUT_TIME) + 1))
            Pitch_list.extend(interpolated_pitches[1:])
            Current_Pitch = Post_righting_Pitch  # Update Pitch
            t += round(BOUT_DURATION * (0.2 / BOUT_TIME))  # 更新时间索引以跳过已经插值的时间步
        else:
            t += 1

    # Calculate IEIs from bout initiation times
    IBI.extend(np.diff(Bout_Index) / SAMPLERATE)  # difference between initiation of two bouts is IEI

    # Crop pitch and angular velocity if bout advanced past MODEL_DURATION (for plotting)
    if len(Pitch_list) > MODEL_DURATION:
        # If list longer than limit, set everything after as NAs
        Pitch_list[MODEL_DURATION + 1: -1] = []
    if len(AngVel_list) > MODEL_DURATION:
        AngVel_list[MODEL_DURATION + 1: -1] = []

    # Calculate IEI mean pitches and angular velocities in one simulation
    IEI_pitch = []
    IEI_angVel = []

    for ii in range(len(Bout_Index) - 1):
        # In each IEI, calculate IEI_pitch and IEI_AngVel
        start_idx = int(Bout_Index[ii] + 4)
        end_idx = int(Bout_Index[ii + 1] - 2)
        IEI_pitch.append(np.median(Pitch_list[start_idx:end_idx]))
        IEI_angVel.append(np.median(AngVel_list[start_idx:end_idx]))

    # Convert list to NumPy array
    IEI_pitch = np.array(IEI_pitch)
    IEI_angVel = np.array(IEI_angVel)

    ###
    # Calculate Pitch and IEI_Pitch histogram
    # "_hist" saves counts number of points in each bin, _bin_edges saves bond of each bin
    edges_Pitch = np.arange(-90, 95, 5)
    Pitch_hist, _ = np.histogram(Pitch_list, bins=edges_Pitch,
                                 density=True)  # Histogram for pitch_list (within one iteration)
    IEI_pitch_hist, _ = np.histogram(IEI_pitch, bins=edges_Pitch, density=True)  # Histogram for IEI_Pitch

    # Calculate angel velocity histogram
    edges_av = np.arange(-100, 102, 1)
    AngVel_hist, _ = np.histogram(AngVel_list, bins=edges_av,
                                  density=True)  # Generate histogram for AngVel (within one iteration)

    # Calculate IEI histogram
    edges_IEI = np.linspace(0, 10, BIN_NUMBER + 1)
    IEI_hist, _ = np.histogram(IBI, bins=edges_IEI)  # Generate histogram for IEI (within one iteration)
    IEI_hist = IEI_hist / np.sum(IEI_hist)  # Make probability distribution

    # 保存直方图数据到数组中
    All_Counts_IEI[model_Iteration, :] = IEI_hist  # IEI 的直方图
    All_Counts_Pitch[model_Iteration, :] = Pitch_hist  # Pitch 的直方图
    All_Counts_AngVel[model_Iteration, :] = AngVel_hist  # 角速度的直方图
    All_Counts_IEI_Pitch[model_Iteration, :] = IEI_pitch_hist  # IEI_Pitch 的直方图

    # Generate probability distribution across simulations
    if ITERATIONS > 1:
        Pitch_dist_mean = np.nanmean(All_Counts_Pitch, axis=0)
        Pitch_dist_stdev = np.nanstd(All_Counts_Pitch, axis=0)
        IEI_Pitch_dist_mean = np.nanmean(All_Counts_IEI_Pitch, axis=0)
        IEI_Pitch_dist_stdev = np.nanstd(All_Counts_IEI_Pitch, axis=0)
        AV_dist_mean = np.nanmean(All_Counts_AngVel, axis=0)
        AV_dist_stdev = np.nanstd(All_Counts_AngVel, axis=0)
        IEI_dist_mean = np.nanmean(All_Counts_IEI, axis=0)
        IEI_dist_stdev = np.nanstd(All_Counts_IEI, axis=0)

# %%
# Define bin centers
bin_centers_pitch = (edges_Pitch[:-1] + edges_Pitch[1:]) / 2

# Plot the overlaid IEI Pitch distributions
plt.figure(figsize=(10, 6))

# Overlay each iteration's result
for i in range(All_Counts_IEI_Pitch.shape[0]):
    plt.plot(bin_centers_pitch, All_Counts_IEI_Pitch[i, :], alpha=0.3)

# Calculate and plot the mean and standard deviation
IEI_Pitch_dist_mean = np.nanmean(All_Counts_IEI_Pitch, axis=0)
IEI_Pitch_dist_stdev = np.nanstd(All_Counts_IEI_Pitch, axis=0)

plt.errorbar(bin_centers_pitch, IEI_Pitch_dist_mean, yerr=IEI_Pitch_dist_stdev,
             fmt='o-', color='red', capsize=5, label='Mean Distribution')

plt.xlabel('IEI Pitch')
plt.ylabel('Probability Density')
plt.title(f'IEI Pitch Distribution across {ITERATIONS} simulations ({selected_condition})')
plt.grid(True)
plt.legend()
plt.show()

# %%
# Define bin centers for the histograms
bin_centers_pitch = (edges_Pitch[:-1] + edges_Pitch[1:]) / 2
bin_centers_av = (edges_av[:-1] + edges_av[1:]) / 2
bin_centers_iei = (edges_IEI[:-1] + edges_IEI[1:]) / 2

# Plot the distributions with bin centers
fig, axs = plt.subplots(2, 2, figsize=(15, 10))

# Pitch Distribution
axs[0, 0].bar(bin_centers_pitch, Pitch_dist_mean, width=(edges_Pitch[1] - edges_Pitch[0]), alpha=0.6, color='blue',
              yerr=Pitch_dist_stdev, capsize=5, label='Mean Distribution')
axs[0, 0].set_xlabel('Pitch (degrees)')
axs[0, 0].set_ylabel('Probability Density')
axs[0, 0].set_title(f'Pitch Distribution across all simulations ({selected_condition})')
axs[0, 0].grid(True)
axs[0, 0].legend()

# IEI Pitch Distribution
axs[0, 1].bar(bin_centers_pitch, IEI_Pitch_dist_mean, width=(edges_Pitch[1] - edges_Pitch[0]), alpha=0.6, color='green',
              yerr=IEI_Pitch_dist_stdev, capsize=5, label='Mean Distribution')
axs[0, 1].set_xlabel('Pitch (degrees)')
axs[0, 1].set_ylabel('Probability Density')
axs[0, 1].set_title(f'IEI Pitch Distribution across all simulations ({selected_condition})')
axs[0, 1].grid(True)
axs[0, 1].legend()

# Angular Velocity Distribution
axs[1, 0].bar(bin_centers_av, AV_dist_mean, width=(edges_av[1] - edges_av[0]), alpha=0.6, color='purple',
              yerr=AV_dist_stdev, capsize=5, label='Mean Distribution')
axs[1, 0].set_xlabel('Angular Velocity (degrees/s)')
axs[1, 0].set_ylabel('Probability Density')
axs[1, 0].set_title(f'Angular Velocity Distribution across all simulations ({selected_condition})')
axs[1, 0].grid(True)
axs[1, 0].legend()

# IEI Distribution
axs[1, 1].bar(bin_centers_iei, IEI_dist_mean, width=(edges_IEI[1] - edges_IEI[0]), alpha=0.6, color='red',
              yerr=IEI_dist_stdev, capsize=5, label='Mean Distribution')
axs[1, 1].set_xlabel('IEI (seconds)')
axs[1, 1].set_ylabel('Probability Density')
axs[1, 1].set_title(f'IEI Distribution across all simulations ({selected_condition})')
axs[1, 1].grid(True)
axs[1, 1].legend()

plt.tight_layout()
plt.show()
