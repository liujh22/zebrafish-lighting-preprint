"""
Main Simulation Program:
1. Using empirical data to fit functions
2. Using coefficient from functions as model parameters
3. Simulate Pitch based on model
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import multivariate_normal
#from Bout_Initiation import bout_simulation
from utils import calculate_deviation_bout_rate, quadratic_function, V_function

# %%
# Load the data
data = pd.read_csv("/Users/jiahuan/Desktop/NYU_Intern/R_Code/IBI_data_preprocessed.csv")
dd_day = data[data['label'] == 'dd_day']
dd_night = data[data['label'] == 'dd_night']
ld_day = data[data['label'] == 'ld_day']
dd = pd.merge(dd_night, dd_day)

# %%
# calculate bout rate and deviation from preferred pitch
dd_day = calculate_deviation_bout_rate(dd_day)
dd_night = calculate_deviation_bout_rate(dd_night)
ld_day = calculate_deviation_bout_rate(ld_day)

# %%
# Fit U and V functions
a, b, c, r_square_U = quadratic_function(dd_day, 'bout_rate', 'deviation_from_preferred_pitch')
median_angVel, k1, b1, r_squared1, k2, b2, r_squared2 = V_function(dd_day, 'bout_rate', 'propBoutIEI_angVel')


# %%
# 计算A和B的相关系数
correlation_AB = dd_day['deviation_from_preferred_pitch'].corr(dd_day['propBoutIEI_angVel'])

# 定义联合分布参数
mean = [0, 0]
cov = [[1, correlation_AB], [correlation_AB, 1]]
rv = multivariate_normal(mean, cov)

# 定义C的条件分布
def conditional_C(a, b):
    if b < median_angVel:
        return a * (a - b) ** 2 + k1 * b + np.random.normal(0, 0.1)
    else:
        return a * (a - b) ** 2 + k2 * b + np.random.normal(0, 0.1)

# 计算C的期望值
samples = 10000
A, B = rv.rvs(samples).T
C = [conditional_C(a, b) for a, b in zip(A, B)]
expected_C = np.mean(C)

print(f"期望值 E(C) = {expected_C:.4f}")


# %%
# Bout Simulation
# bout_simulation(dd_day)
# bout_simulation(dd_night)
# bout_simulation(ld_day)

