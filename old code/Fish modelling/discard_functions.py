# %%
# Fitting determined parameters
print("")
print("##############################")
print("### Passive AngAcc Fitting ###")
print("##############################")

# 筛选出 pauseDur > 1 的数据
filtered_df = condition_to_IEI_df[selected_condition][condition_to_IEI_df[selected_condition]['propBoutIEI_pauseDur'] >= 1]
# 进行线性回归
k, b, sd, r_squared =  quantile_linear_fit(filtered_df, 'propBoutIEI_strict_angAcc', 'propBoutIEI_pauseDur')
passive_AngAcc_fit_k = k  # Caused by gravity
passive_AngAcc_fit_b = b  # Caused by gravity
passive_AngAcc_fit_SD = sd  # Caused by gravity
passive_AngAcc_fit_r_squared = r_squared  # Caused by gravity



# %%
import random
def add_constant_to_list(lst, constant):
    return [x + constant for x in lst]

pause_start_index = add_constant_to_list(Bout_Index, BOUT_DURATION+1)

def get_pitch_slices(pitch, indices, length):
    slices = []
    debug_counter = 0
    for index in indices:
        index = int(index)
        if debug_counter < 20:
            print(f"Processing index: {index}")
        if index >= 0 and index < len(pitch):
            if debug_counter < 20:
                print(f"Index {index} is valid")
            if index + length <= len(pitch):
                slices.append(pitch[index:index + length])
                if debug_counter < 20:
                    print(f"Slice added: {pitch[index:index + length]}")
            else:
                slices.append(pitch[index:])
                if debug_counter < 20:
                    print(f"Slice added: {pitch[index:]}")
        else:
            if debug_counter < 20:
                print(f"Index {index} is invalid")
        debug_counter += 1
    return slices

# Get the pitch slices for plotting
pitch_slices = get_pitch_slices(Pitch_list, pause_start_index, 300)

# Check the resulting pitch slices
if len(pitch_slices) > 0:
    print(f"Pitch slices (showing up to 20): {pitch_slices[:20]}")

# Randomly select up to 20 pitch slices for plotting
if pitch_slices:
    if len(pitch_slices) > 20:
        pitch_slices = random.sample(pitch_slices, 20)

    plt.figure(figsize=(10, 6))
    for i, pitch_slice in enumerate(pitch_slices):
        plt.plot(pitch_slice, label=f'Start index {pause_start_index[i]}')

    plt.xlabel('Index')
    plt.ylabel('Pitch')
    plt.title('Pitch values starting from specified indices')
    #plt.legend()
    plt.show()
else:
    print("No valid pitch slices to plot.")