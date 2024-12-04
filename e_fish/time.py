from scipy.signal import find_peaks_cwt
import pandas as pd
import numpy as np



def calculate_df_time(
    df: pd.DataFrame, trigger_up: float, trigger_down: float
) -> pd.DataFrame:
    """
    Calculate time intervals between significant amplitude changes in a DataFrame.

    This function identifies two sets of candidate time points ('bcs' and 'electrode') based on amplitude
    thresholds ('trigger_up' and 'trigger_down'). It selects the five smallest amplitude
    differences for each file and computes the time difference between two specific
    events: 'electrode' and 'bcs'.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing columns 'avg_amplitude', 'time', and 'file_number'.
    trigger_up : float
    trigger_down : float

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the earliest 'time_bcs' and 'time_electrode' events
        for each file number, along with their corresponding time difference 'delta_t'.

    Notes
    -----
    - 'time_bcs' represents the time when the pulse reaches the bqck current shunt.
    - 'time_electrode' represents the time when thereflected pulse reaches the back curren shunt.
    - The time difference 'delta_t' is calculated as half the difference between 'time_bcs' and 'time_electrode'.
    """
    
    # Identify candidates where the amplitude falls below trigger_down or exceeds trigger_up within a short time.
    df.loc[
        (((df.avg_amplitude <= trigger_down) | (df.avg_amplitude >= trigger_up)))
        & (df.time < 1e-7),
        "bcs_candidates",
    ] = (trigger_down - df["avg_amplitude"]).abs()  # Compute the absolute difference for BCS candidates.

    # Identify candidates where amplitude either falls below trigger_down or exceeds trigger_up.
    df.loc[
        ((df.avg_amplitude <= trigger_down) | (df.avg_amplitude >= trigger_up)),
        "electrode_candidates",
    ] = (-trigger_up + df["avg_amplitude"]).abs()  # Compute the absolute difference for electrode candidates.

    # Select the 5 smallest differences for electrode candidates, grouped by file_number.
    df_electrode = df.loc[
        df.groupby("file_number")["electrode_candidates"]
        .nsmallest(5)
        .droplevel("file_number")
        .index,
        ["file_number", "time"],
    ].rename(columns={"time": "time_electrode"})  # Rename time column to indicate electrode event times.

    # Select the 5 smallest differences for BCS candidates, grouped by file_number.
    df_bcs = df.loc[
        df.groupby("file_number")["bcs_candidates"]
        .nsmallest(5)
        .droplevel("file_number")
        .index,
        ["file_number", "time"],
    ].rename(columns={"time": "time_bcs"})  # Rename time column to indicate BCS event times.

    # Combine the earliest bcs and electrode event times for each file_number.
    df_time = (
        df_bcs.groupby(["file_number"])
        .time_bcs.min()
        .to_frame()  # Compute minimum BCS time per file.
        .join(df_electrode.groupby(["file_number"]).time_electrode.min().to_frame())  # Join with electrode time.
    )

    # Calculate half the difference between the earliest electrode time and BCS time.
    df_time["delta_t"] = (df_time.time_electrode - df_time.time_bcs) / 2

    return df_time


def shift_reflected_pulse(df: pd.DataFrame, df_time: pd.DataFrame) -> pd.DataFrame:
    """
    Shift and invert the amplitude of a reflected pulse based on calculated time intervals.

    This function adjusts the time and amplitude of a reflected pulse in a DataFrame
    by shifting the time according to the 'delta_t' values in another DataFrame and 
    inverting the amplitude.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the original pulse data with columns:
        - 'file_number': Identifier for each file or measurement group.
        - 'time': Time values of the pulse.
        - 'avg_amplitude': Average amplitude of the pulse.
    df_time : pd.DataFrame
        DataFrame containing the calculated time shifts with columns:
        - 'delta_t': Time shift values for each file number.
        - The index represents 'file_number'.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with the shifted and inverted reflected pulse data, containing:
        - 'file_number': File or measurement group identifier.
        - 'time': Adjusted time values of the reflected pulse.
        - 'amplitude': Inverted amplitude of the original pulse.
    
    Notes
    -----
    - The time shift is calculated as 'time - 2 * delta_t' for each corresponding file number.
    - The amplitude is inverted by multiplying the original average amplitude by -1.
    """
    
    # Create an empty DataFrame to store the shifted and inverted pulse data.
    df_shifted = pd.DataFrame()

    # Assign file numbers to the new DataFrame, repeating each file number according to its occurrence in the original DataFrame.
    df_shifted["file_number"] = (
        pd.Series(df_time.index)  # Index of df_time represents file_number.
        .repeat(df.file_number.value_counts().sort_index())  # Repeat file_number based on its count in df.
        .values
    )

    # Shift the time by subtracting twice the delta_t for each file number.
    df_shifted["time"] = (
        df["time"]
        - 2 * df_time.delta_t.repeat(df.file_number.value_counts().sort_index()).values
    )

    # Invert the amplitude of the original pulse.
    df_shifted["amplitude"] = -df["avg_amplitude"]

    return df_shifted

def calculate_int_interval(df: pd.DataFrame) -> float:
    """
    Calculate the median full width at half maximum (FWHM) of the amplitude signal across multiple files.

    This function identifies the top 20 files with the largest maximum amplitude, 
    filters the data to include only points where the amplitude is greater than or equal 
    to half of the maximum amplitude for each file, and computes the FWHM for each file. 
    Finally, it returns the median FWHM across all files.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the following columns:
        - 'file_number'
        - 'amplitude'
        - 'time'
    Returns
    -------
    float
        The median full width at half maximum (FWHM) of the amplitude signal across all selected files.

    Notes
    -----
    - The FWHM is calculated as the difference between the maximum and minimum 'time' 
      where the amplitude is greater than or equal to half of the maximum amplitude 
      for each file.
    """
    # Filter the DataFrame to include only the top 20 files with the highest maximum amplitude.
    df = df[
        df.file_number.isin(
            df.groupby("file_number")["amplitude"]
            .agg(maxima=(max))  # Calculate the maximum amplitude for each file.
            .maxima.nlargest(20)  # Select the top 20 files with the largest maxima.
            .index
        )
    ]

    # Further filter the DataFrame to include only points where the amplitude 
    # is greater than or equal to half of the maximum amplitude for each file.
    df = df[
        df.amplitude
        >= df.groupby("file_number")["amplitude"].transform(lambda x: x.max() / 2.0)
    ]

    # Calculate the full width at half maximum (FWHM) for each file as the difference
    # between the maximum and minimum time where the amplitude is above half its maximum.
    fwhm = (
        df.groupby("file_number")["time"].max()  # Maximum time for each file.
        - df.groupby("file_number")["time"].min()  # Minimum time for each file.
    ).median()  # Compute the median FWHM across all selected files.

    return fwhm



def calculate_pd_pmt_diff(df_3_max: pd.DataFrame, df_2: pd.DataFrame) -> float:

    """
    Calculate the median time difference between PD and PMT.

    This function computes the time difference between the maximum amplitude events 
    in two DataFrames ('df_3_max' and 'df_2') for matching 'file_number' values, and 
    returns the median of those differences.

    Parameters
    ----------
    df_3_max : pd.DataFrame
        DataFrame containing the peak amplitude events in PMT signals with columns:
        - 'file_number'
        - 'time'
    df_2 : pd.DataFrame
        DataFrame containing amplitude data with columns:
        - 'file_number'
        - 'time'
        - 'amplitude'

    Returns
    -------
    float
        The median time difference between the peak amplitude events in 'df_3_max' and 'df_2'.

    Notes
    -----
    - The function selects the maximum amplitude event for each 'file_number' in 'df_2',
      compares it with the corresponding peak time in 'df_3_max', and calculates the median difference.
    """
    
    # Filter df_2 to include only the files that are present in df_3_max.
    df_2_max = df_2.loc[df_2.file_number.isin(df_3_max.file_number)]

    # Add a new column 'max_amplitude' with the maximum amplitude for each file.
    df_2_max["max_amplitude"] = df_2_max.groupby("file_number")["amplitude"].transform(
        lambda x: x.max()  # Calculate the maximum amplitude for each file.
    )

    # Calculate the time difference between the peak times in df_3_max and the times
    # corresponding to the maximum amplitude in df_2_max.
    difference = (
        df_3_max.time.values
        - df_2_max[df_2_max.amplitude == df_2_max.max_amplitude].time.values
    )

    # Return the median of the time differences.
    return np.median(difference)
