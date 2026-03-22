import os
import pandas as pd
import matplotlib as mpl

def load_data(filename="wt_2025_all_Connected_bout_features_strict.csv"):
    """Load and preprocess the raw data file.

    Parameters
    ----------
    filename : str, optional
        Name of the CSV file to load (default is
        "wt_2025_all_Connected_bout_features_strict.csv")

    Returns
    -------
    pd.DataFrame
        Loaded data as a pandas DataFrame
    """
    # Change to directory containing preprocessed CSV files
    ##########   ||   ###############
    ########## \ || / ##############
    ##########  \||/  ###############
    directory_of_Analyzed_data = '/Users/yunluzhu/Documents/Lab2/Manuscripts/2025 swim strategy/code/Analyzed_data'
    # e.g. directory_of_Analyzed_data = "/path/to/Analyzed_data"

    if directory_of_Analyzed_data is None:
        raise Exception("Hey you forgot to do something! \nPlease set the path of the Analyzed_data folder under function get_visualization_ready.load_data()")
    elif os.path.exists(directory_of_Analyzed_data) is False:
        raise Exception(f"Hey you forgot to do something! \nPlease set the path of the Analyzed_data folder under function get_visualization_ready.load_data() \nThe current path is {directory_of_Analyzed_data}")
    
    print("Loading data from:", directory_of_Analyzed_data)
    os.chdir(directory_of_Analyzed_data)
    load_file = pd.read_csv(filename)
    
    return load_file


def set_font_type():
    """Configure matplotlib to save PDFs with editable text.

    This ensures text in saved PDFs remains as text rather than being converted to paths.
    """
    mpl.rcParams['pdf.fonttype'] = 42


def get_daytime_data(data):
    """Preprocess the raw data for daytime analysis.

    Parameters
    ----------
    data : pd.DataFrame
        Raw data to be processed

    Returns
    -------
    pd.DataFrame
        Filtered data containing only daytime dd and ld bouts with
        categorical columns converted and NA values removed
    """
    # Convert specified columns to categorical
    categorical_cols = ['cond1', 'ztime', 'cond0', 'expNum']
    data[categorical_cols] = data[categorical_cols].astype('category')

    # Filter for daytime dd and ld bouts
    daytime_mask = (
            ((data['cond1'] == "dd") & (data['ztime'] == "day")) |
            ((data['cond1'] == "ld") & (data['ztime'] == "day"))
    )
    return data[daytime_mask].dropna()

def get_nighttime_data(data):
    """Preprocess the raw data for nighttime analysis.

    Parameters
    ----------
    data : pd.DataFrame
        Raw data to be processed

    Returns
    -------
    pd.DataFrame
        Filtered data containing only nighttime dd and ld bouts with
        categorical columns converted and NA values removed
    """
    # Convert specified columns to categorical
    categorical_cols = ['cond1', 'ztime', 'cond0', 'expNum']
    data[categorical_cols] = data[categorical_cols].astype('category')

    # Filter for nighttime dd and ld bouts
    nighttime_mask = (
            ((data['cond1'] == "dd") & (data['ztime'] == "night")) |
            ((data['cond1'] == "ld") & (data['ztime'] == "night"))
    )
    return data[nighttime_mask].dropna()


def get_haircell_daytime_data(raw_data):
    """Filter hair cell data for specific conditions and daytime."""
    # Convert specified columns to categorical
    for col in ['cond1', 'ztime', 'cond0', 'expNum']:
        raw_data[col] = raw_data[col].astype('category')

    ctrl_day = raw_data[(raw_data['cond1'] == "1ctrl") & (raw_data['ztime'] == "day")]
    cond_day = raw_data[(raw_data['cond1'] == "2cond") & (raw_data['ztime'] == "day")]
    return pd.concat([ctrl_day, cond_day], ignore_index=True)
