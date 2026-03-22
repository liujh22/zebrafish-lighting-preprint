import os
def load_preprocessed_data(dataset_name):
    """load raw data from the data folder

    Args:
        dataset_name (string): name of the dataset to load. Should be the folder name that contains the data 

    Raises:
        Exception: if the directory of analyzed raw data is not set

    Returns:
        string: the path to the dataset folder containing .h5 files
        and the frame rate of the data (which is 166Hz)
    """
    # Change to directory containing raw data that contains .h5 files
    ##########   ||   ###############
    ########## \ || / ##############
    ##########  \||/  ###############
    directory_of_analyzed_raw_data = '/Volumes/LabDataPro/SAMPL_data_v5/WT_daylight_2025'
    if directory_of_analyzed_raw_data is None:
        raise Exception("Hey you forgot to do something! \nPlease set the path of the raw behavior data folder under function get_analysis_ready.load_preprocessed_data()")
    else:
        return os.path.join(directory_of_analyzed_raw_data, dataset_name), 166  # 166 is the frame rate of the data, you can change it if needed