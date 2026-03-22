"""
Various mathematical functions used in zebra fish modelling
"""
from scipy.optimize import curve_fit
from sklearn.linear_model import RANSACRegressor, HuberRegressor, TheilSenRegressor
from sklearn.metrics import r2_score
from scipy.stats import norm
import numpy as np
from scipy.stats import lognorm
import pandas as pd


def calculate_deviation_bout_rate(df):
    """Deviation from Preferred Pitch & Bout Rate"""

    # Ensure df is a copy to avoid SettingWithCopyWarning
    df = df.copy()

    median_pitch = df['propBoutIEI_pitch'].median()
    df.loc[:, 'deviation_from_preferred_pitch'] = df['propBoutIEI_pitch'] - median_pitch
    df.loc[:, 'bout_rate'] = 1 / df['propBoutIEI']

    return df


def ask_constant_change(IEI_data, bout_data):
    """Get constant from different conditions"""
    conditions = ['dd_day', 'dd_night', 'ld_day', 'ld_night', 'll_day', 'll_night']

    # Calculate values from data
    pref_posture = tuple(
        IEI_data[IEI_data['label'] == condition]['propBoutIEI_pitch'].median() for condition in conditions)
    basal_bout_rate = tuple(
        1 / IEI_data[IEI_data['label'] == condition]['propBoutIEI'].median() for condition in conditions)
    max_abs_rot_full_decel = tuple(
        bout_data[bout_data['label'] == condition]['rot_full_decel'].abs().max() for condition in conditions)
    condition = input(f"Select condition ({', '.join(conditions)}): ").strip()

    if condition in conditions:
        index = conditions.index(condition)
    else:
        raise ValueError("Invalid input. Please select a valid condition.")

    selected_pref_posture = pref_posture[index]
    selected_basal_bout_rate = basal_bout_rate[index]
    selected_condition = condition
    selected_max_abs_pitch_change = max_abs_rot_full_decel[index]

    print(f"Selected condition is {selected_condition}")
    print(f"Preferred posture is {selected_pref_posture:.2f} degree")
    print(f"Max pitch change is {selected_max_abs_pitch_change:.2f} degree")
    print(f"Basal bout rate is {selected_basal_bout_rate:.2f} Hz")

    return selected_max_abs_pitch_change, selected_condition, selected_pref_posture, selected_basal_bout_rate


def quadratic(x, a, c):
    return a * x ** 2 + c


def quadratic_function(df, y_col, x_col):
    """Quadratic fitting and return coefficients"""
    # 从数据帧中提取 x 和 y 列的数据
    x_data = df[x_col].values
    y_data = df[y_col].values

    # Fit the quadratic model
    popt, pcov = curve_fit(quadratic, x_data, y_data)

    # 提取拟合参数
    a, c = popt
    print(f"Formular used: y = a * (x - b) ** 2 + c")
    print("")
    print(f"Fitted parameters: a={a:.2f}, c={c:.2f}")
    print("")

    # 计算预测值
    y_pred = quadratic(x_data, a, c)

    # 计算总平方和 (SST) 和残差平方和 (SSE)
    sst = np.sum((y_data - np.mean(y_data)) ** 2)
    sse = np.sum((y_data - y_pred) ** 2)

    # 计算 R-squared
    r_squared = 1 - (sse / sst)
    print(f"R-squared: {r_squared:.2f}")

    return a, c, r_squared


def linear(x, k, b):
    return k * x + b


def simple_linear_fit(df, y_col, x_col):
    """Compute linear regression and return coefficients"""
    # 从数据帧中提取 x 和 y 列的数据
    x = df[x_col].values
    y = df[y_col].values

    # 进行线性拟合
    popt, pcov = curve_fit(linear, x, y)

    k, b = popt

    # 打印拟合参数
    print("")
    print(f"Formular used: y = k * x + b")
    print("")
    print(f"Fitted parameters: k={k:.2f}, b={b:.2f}")
    print("")

    # 计算预测值
    y_pred = linear(x, k, b)

    # 计算R-squared
    sst = np.sum((y - np.mean(y)) ** 2)
    sse = np.sum((y - y_pred) ** 2)
    r_squared = 1 - (sse / sst)
    print(f"R-squared: {r_squared:.2f}")

    # 计算残差
    residuals = y - y_pred

    # 计算标准误差
    sd = np.std(residuals)
    print(f"Standard Deviation of residuals: {sd:.2f}")

    return (k, b, sd, r_squared)


def theil_linear_fit(df, y_col, x_col):
    """Compute Theil-Sen regression and return coefficients"""
    # 从数据帧中提取 x 和 y 列的数据
    x = df[x_col].values.reshape(-1, 1)
    y = df[y_col].values

    # 进行Theil-Sen回归拟合
    model = TheilSenRegressor()
    model.fit(x, y)

    k = model.coef_[0]
    b = model.intercept_

    # 打印拟合参数
    print("")
    print(f"Formular used: y = k * x + b")
    print("")
    print(f"Fitted parameters: k={k:.2f}, b={b:.2f}")
    print("")

    # 计算预测值
    y_pred = model.predict(x)

    # 计算R-squared
    r_squared = r2_score(y, y_pred)
    print(f"R-squared: {r_squared:.2f}")

    # 计算残差
    residuals = y - y_pred

    # 计算标准误差
    sd = np.std(residuals)
    print(f"Standard Deviation of residuals: {sd:.2f}")

    return k, b, sd, r_squared


def sigmoid(x, Asym, xmid, scal, c):
    return Asym / (1 + np.exp((xmid - x) / scal)) + c


def sigmoid_function(df, y_col, x_col):
    """Sigmoid fitting and return coefficients"""
    # Extract x and y data from the dataframe
    x_data = df[x_col].values
    y_data = df[y_col].values

    # Initial guess for the parameters
    initial_guess = [20, -2, -3, -10]

    # Fit the sigmoid model
    popt, pcov = curve_fit(sigmoid, x_data, y_data, p0=initial_guess)

    # Extract fitted parameters
    Asym, xmid, scal, c = popt
    print(f"Formula used: y = Asym / (1 + exp((xmid - x) / scal)) + c")
    print("")
    print(f"Fitted parameters: Asym={Asym:.2f}, xmid={xmid:.2f}, scal={scal:.2f}, c={c:.2f}")
    print("")

    # Calculate predicted values
    y_pred = sigmoid(x_data, Asym, xmid, scal, c)

    # Calculate residuals
    residuals = y_data - y_pred

    # Calculate standard deviation of residuals
    residual_SD = np.std(residuals)
    print(f"Residual standard deviation: {residual_SD:.2f}")

    # Calculate total sum of squares (SST) and residual sum of squares (SSE)
    sst = np.sum((y_data - np.mean(y_data)) ** 2)
    sse = np.sum((y_data - y_pred) ** 2)

    # Calculate R-squared
    r_squared = 1 - (sse / sst)
    print(f"R-squared: {r_squared:.2f}")

    return Asym, xmid, scal, c, r_squared, residual_SD
