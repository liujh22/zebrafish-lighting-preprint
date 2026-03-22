"""
Function used to simulate the bout initiation process
"""
# Import packages
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# %%
# Some parameters
Fitting_independent = 1  # Set to 0, if you want to deactivate the U and V fitting
num_Iterations = 50  # How many times is the simulation run?
Model_Duration = 3000  # How long takes one simulation, in sec?
num_Bins = 160  # number of bins for output (probability distribution of IEIs)
samplerate = 40  # in Hz
SwimBout_Duration = round(
    0.125 * samplerate)  # duration of swim bouts in sec (how far is simulation advanced upon bout initiation? empirical match to nefma 7dpf control)
t_offset = 10  # absolute refractory period for bout initiation, from initiation of previous bout, in samples.
tEnd = 42.81  # Recovery period, in samples.
pref_posture = 10.660074074074076  # median(dd_day$propBoutIEI_pitch)
abs_max_pitch_change = 60  # Within one bout, fish can't correct more than this ceiling degree (max net rotation seen at 7 dpf in either condition
linear_portion_pitch_change = [-30,
                               40]  # Only the center part of righting rotation (rot_l_decel ~ pitch_initial) is linear

# Passive model
passive_AngAcc = -0.901472148479809
passive_AccSD = 7.515498758471889

# hemi-parabola function coefficients, parameter of parabolic fitting
pitch_sensitivity = 2.664794080497863e-04

# angular velocity coefficients
basal_boutrate = 0.357  # params[9]
center_angVel = -0.580221009445083  # median(dd_day$angVel)
m_up = 0.061106574699115  # Slop of the up-going branch (right of the center_angVel)
m_down = -0.044633756598217  # Slop of the down-going branch (left of the center_angVel)

# CI variables
baseline_boutrate_CI = [0.419474842814575, 0.468256562350952]
pitch_sensitivity_CI = [2.477381585195960e-04, 2.852206575799766e-04]
AV_sensitivity_Up_CI = [0.050467605807540, 0.071122219328921]
AV_sensitivity_Down_CI = [-0.048168880991735, -0.041328517376250]

# Rotation Correction
Net_Bout_Rotation_Fit = [-0.298006703122244, 4.901825013229847]
Net_Bout_Rotation_Mean = 2.575541320293400
Net_Bout_Rotation_SD = 8.831573788552541
Net_Bout_RotFit_r = -0.545444210848182

# Angel Acceleration Correction
AngAcc_Fit = [-0.795717502604982, 1.016319564107047]
Net_Bout_AngAcc_Mean = 2.341246712845489
Net_Bout_AngAcc_SD = 4.949190816532414
AngAcc_r = -0.713359140295740
SliceAngAcc_SD = 4.141779617694424

# 定义直方图边界
edges_Pitch = np.arange(-90, 95, 5)
edges_av = np.arange(-100, 102, 1)
num_Bins = 20
edges_IEI = np.linspace(0, 20, num_Bins + 1)

# 预定义用于保存直方图数据的数组
All_Counts_IEI = np.zeros((num_Iterations, len(edges_IEI) - 1))
All_Counts_Pitch = np.zeros((num_Iterations, len(edges_Pitch) - 1))
All_Counts_AngVel = np.zeros((num_Iterations, len(edges_av) - 1))
All_Counts_IEI_Pitch = np.zeros((num_Iterations, len(edges_Pitch) - 1))

# %%
# Simulate swimming
for model_Iteration in range(num_Iterations):

    # Initialize variables for appending simulated bout properties
    Pitch_list = []  # List of pitches at every single time point
    AngVel_list = []
    Pre_Bout_Pitch = []  # List of all pre-bout pitches in one simulation
    Pre_Bout_AngVel = []
    Net_Bout_Rotation = []  # List of all rotation change during a bout
    Net_Bout_AngAcc = []
    Bout_Index = []
    # Initialize pitch and angular velocity variables (once each simulation)
    Current_Pitch = np.random.randint(-90, 91)  # current pitch， randomly between -90 and 90
    Current_AngVel = 0  # current angvel，begins at horizontal and with no angular velocity).
    t = 1  # time index

    # Append initial value into list
    Pitch_list.append(Current_Pitch)
    AngVel_list.append(Current_AngVel)

    # The simulation begins as though a bout was just terminated, required for determining time-variant bout initiation.
    # 'Bout_Index' is appended with the initiation time of each bout and is used to calculated IEIs.
    Bout_Index.append(-1)

    # The simulation advances time-steps using a while loop.
    # advance until the simulation reaches the set duration
    while t < (Model_Duration * samplerate):
        t = t+1
        # Passive Section
        # Each time-step, angular acceleration is used to calculate new angular velocity
        # Current acceleration is generated from a normal distribution
        acc = np.random.normal(passive_AngAcc, passive_AccSD, 1)[0]
        # Current_AngVel = AngVel_list[-1] + np.cos((Pitch_list[-1])*np.pi/180) * acc / SAMPLERATE  # Update Angel Velocity
        Current_AngVel = AngVel_list[-1] + np.cos(np.deg2rad(Pitch_list[-1])) * acc / samplerate  # Update Angel Velocity

        Current_Pitch = Pitch_list[-1] + Current_AngVel / samplerate  # Update Pitch

        # Limit pitches to +/- 180 degree
        if Current_Pitch < -180:
            Current_Pitch += 360
        elif Current_Pitch > 180:
            Current_Pitch -= 360

        Pitch_list.append(Current_Pitch)  # Append new pitch after passive process
        AngVel_list.append(Current_AngVel)  # Append new AngVel

        # Bout Initiation Section
        # (Optional) Deactivate U and V fitting
        if Fitting_independent == 0:
            # Refactory, Recovery period dependent bout probability
            if t - Bout_Index[-1] <= t_offset:
                # No bout within refactory period
                P_bout = 0
            elif t - Bout_Index[-1] < tEnd:
                # Limited probability in recovery period
                P_bout = (basal_boutrate / samplerate) * (
                        t - Bout_Index[-1]) * 1 / tEnd
            else:
                # Normal probability of bouts per sample
                P_bout = (basal_boutrate / samplerate)

        # Activate U and V fitting
        else:
            # Calculate a posture-variant P_bout
            # V-function dependent P_bout
            if Current_AngVel > center_angVel:
                angvel_pbout = (m_up * (Current_AngVel - center_angVel)) / samplerate
            else:
                angvel_pbout = (m_down * (Current_AngVel - center_angVel)) / samplerate

            # U-function dependent P_bout
            pitch_pbout = (basal_boutrate + pitch_sensitivity * ((Current_Pitch - pref_posture) ** 2)) / samplerate

            # Refactory, Recovery dependent P_bout
            if t - Bout_Index[-1] <= t_offset:
                P_bout = 0
            elif t - Bout_Index[-1] < tEnd:
                P_bout = (pitch_pbout + angvel_pbout) * (t - Bout_Index[-1]) * 1 / tEnd
            else:
                P_bout = (pitch_pbout + angvel_pbout)

        # Initiate bout if a random number is smaller than P_bout
        if np.random.rand() < P_bout:
            # Calculate net pitch change across bout
            # Net bout rotation is correlated with pre-bout pitch
            # (-30, 40) is the linear portion of a pitch correction
            if linear_portion_pitch_change[0] <= Current_Pitch and Current_Pitch <= linear_portion_pitch_change[1]:
                # If in linear portion, take rotaion change from a normal distribution
                # rotation is generated from a distribution
                netrot = np.random.normal(Net_Bout_Rotation_Fit[0]*Current_Pitch + Net_Bout_Rotation_Fit[1], Net_Bout_Rotation_SD)

            elif Current_Pitch > linear_portion_pitch_change[1]:
                # If not in linear portion, random distribution around mu=maximum pitch change and same SD as above
                netrot = np.random.normal(
                    Net_Bout_Rotation_Fit[0] * linear_portion_pitch_change[1] + Net_Bout_Rotation_Fit[1],
                    Net_Bout_Rotation_SD * (1 - Net_Bout_RotFit_r ** 2))
            else:
                # If not in linear portion, random distribution around mu=minimum pitch change and same SD as above
                netrot = np.random.normal(
                    Net_Bout_Rotation_Fit[0] * linear_portion_pitch_change[0] + Net_Bout_Rotation_Fit[1],
                    Net_Bout_Rotation_SD * (1 - Net_Bout_RotFit_r ** 2))

            # If net rotation as calculated is greater than absolute value of the max bout pitch change then change it to that ceiling
            if abs(netrot) < abs_max_pitch_change:  # Small is fine
                Net_Bout_Rotation.append(netrot)
            elif netrot > abs_max_pitch_change:
                # Rotation is 60 degree or larger
                Net_Bout_Rotation.append(abs_max_pitch_change)  # Only append the maximum degree (60)
            else:
                # Rotation is -60 degree or larger
                Net_Bout_Rotation.append(-abs_max_pitch_change)  # Only append -60

            # Calculate net angular velocity change across bout
            Net_Bout_AngAcc_new = np.random.normal(AngAcc_Fit[0] * Current_AngVel + AngAcc_Fit[1],
                                                   Net_Bout_AngAcc_SD * (1 - AngAcc_r ** 2))
            Net_Bout_AngAcc.append(Net_Bout_AngAcc_new)

            # Record time index "t" as bout index
            Bout_Index.append(t)

            # Append pre-bout posture for diagnostics
            Pre_Bout_Pitch.append(Current_Pitch)
            Pre_Bout_AngVel.append(Current_AngVel)

            # Apply net bout rotation and net bout angular acceleration across bout
            Post_bout_Pitch = Current_Pitch + Net_Bout_Rotation[-1]
            Post_bout_AngVel = Current_AngVel + Net_Bout_AngAcc[-1]

            # 使用np.linspace插补数据
            interpolated_pitches = np.linspace(Current_Pitch, Post_bout_Pitch, SwimBout_Duration + 1)
            interpolated_angvels = np.linspace(Current_AngVel, Post_bout_AngVel, SwimBout_Duration + 1)

            Pitch_list.extend(interpolated_pitches[1:])
            AngVel_list.extend(interpolated_angvels[1:])

            Current_Pitch = Post_bout_Pitch
            Current_AngVel = Post_bout_AngVel

            t += SwimBout_Duration  # 更新时间索引以跳过已经插值的时间步

        # 继续时间步的增加
        #t += 1  # 时间索引增加


    # Calculate IEIs from bout initiation times
    modelIEIs = np.diff(Bout_Index) / samplerate  # difference between t-index is the inter-bout-interval

    # Crop pitch and angular velocity if bout advanced past MODEL_DURATION (for plotting)
    if len(Pitch_list) > Model_Duration * samplerate:
        # If list longer than limit, set everything after as NAs
        Pitch_list[Model_Duration * samplerate + 1: -1] = []
    if len(AngVel_list) > Model_Duration * samplerate:
        AngVel_list[Model_Duration * samplerate + 1: -1] = []

    # Calculate IEI mean pitches and angular velocities in one simulation
    IEI_pitch = []
    IEI_angVel = []

    for ii in range(len(Bout_Index) - 1):
        # In each IEI, calculate IEI_pitch and IEI_AngVel
        start_idx = Bout_Index[ii] + 4
        end_idx = Bout_Index[ii + 1] - 2
        IEI_pitch.append(np.mean(Pitch_list[start_idx:end_idx]))
        IEI_angVel.append(np.mean(AngVel_list[start_idx:end_idx]))

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
    edges_IEI = np.linspace(0, 20, num_Bins + 1)
    IEI_hist, _ = np.histogram(modelIEIs, bins=edges_IEI)  # Generate histogram for IEI (within one iteration)
    IEI_hist = IEI_hist / np.sum(IEI_hist)  # Make probability distribution

    # 保存直方图数据到数组中
    All_Counts_IEI[model_Iteration, :] = IEI_hist  # IEI 的直方图
    All_Counts_Pitch[model_Iteration, :] = Pitch_hist  # Pitch 的直方图
    All_Counts_AngVel[model_Iteration, :] = AngVel_hist  # 角速度的直方图
    All_Counts_IEI_Pitch[model_Iteration, :] = IEI_pitch_hist  # IEI_Pitch 的直方图


    # Generate probability distribution across simulations
    if num_Iterations > 1:
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

plt.xlabel('Pitch (degrees)')
plt.ylabel('Probability Density')
plt.title('IEI Pitch Distribution across all simulations')
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
axs[0, 0].bar(bin_centers_pitch, Pitch_dist_mean, width=(edges_Pitch[1] - edges_Pitch[0]), alpha=0.6, color='blue', yerr=Pitch_dist_stdev, capsize=5, label='Mean Distribution')
axs[0, 0].set_xlabel('Pitch (degrees)')
axs[0, 0].set_ylabel('Probability Density')
axs[0, 0].set_title('Pitch Distribution across all simulations')
axs[0, 0].grid(True)
axs[0, 0].legend()

# IEI Pitch Distribution
axs[0, 1].bar(bin_centers_pitch, IEI_Pitch_dist_mean, width=(edges_Pitch[1] - edges_Pitch[0]), alpha=0.6, color='green', yerr=IEI_Pitch_dist_stdev, capsize=5, label='Mean Distribution')
axs[0, 1].set_xlabel('Pitch (degrees)')
axs[0, 1].set_ylabel('Probability Density')
axs[0, 1].set_title('IEI Pitch Distribution across all simulations')
axs[0, 1].grid(True)
axs[0, 1].legend()

# Angular Velocity Distribution
axs[1, 0].bar(bin_centers_av, AV_dist_mean, width=(edges_av[1] - edges_av[0]), alpha=0.6, color='purple', yerr=AV_dist_stdev, capsize=5, label='Mean Distribution')
axs[1, 0].set_xlabel('Angular Velocity (degrees/s)')
axs[1, 0].set_ylabel('Probability Density')
axs[1, 0].set_title('Angular Velocity Distribution across all simulations')
axs[1, 0].grid(True)
axs[1, 0].legend()

# IEI Distribution
axs[1, 1].bar(bin_centers_iei, IEI_dist_mean, width=(edges_IEI[1] - edges_IEI[0]), alpha=0.6, color='red', yerr=IEI_dist_stdev, capsize=5, label='Mean Distribution')
axs[1, 1].set_xlabel('IEI (seconds)')
axs[1, 1].set_ylabel('Probability Density')
axs[1, 1].set_title('IEI Distribution across all simulations')
axs[1, 1].grid(True)
axs[1, 1].legend()

plt.tight_layout()
plt.show()

