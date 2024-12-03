import pandas as pd
import numpy as np
from pathlib import Path
import os
import joblib


# If a cache is desired
cache_dis = Path(__file__).parent / "cache_dis"
os.makedirs(cache_dis, exist_ok=True)
memory_dis = joblib.Memory(location=cache_dis, verbose=0)

cache_transmitted = Path(__file__).parent / "cache_transmitted"
os.makedirs(cache_transmitted, exist_ok=True)
memory = joblib.Memory(location=cache_transmitted, verbose=0)

cache_complete = Path(__file__).parent / "cache_complete"
os.makedirs(cache_complete, exist_ok=True)
memory_complete = joblib.Memory(location=cache_complete, verbose=0)


# @memory.cache
def compute_pulse(
    df: pd.DataFrame, df_shifted: pd.DataFrame, df_time: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes the transmitted pulse from incident and reflected pulses measured by the back current shunt.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing incident pulse data with columns: `file_number`, `time`, and `avg_amplitude`.
    df_shifted : pd.DataFrame
        DataFrame containing shifted reflected pulse data with columns: `file_number`, `time`, and `amplitude`.
    df_time : pd.DataFrame
        DataFrame containing the time shift for each `file_number` with a column `delta_t`.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the transmitted pulse data with the following columns:
        - `file_number`.
        - `time`: The corrected time for each data point.
        - `incident`: The amplitude of the incident pulse.
        - `reflected`: The amplitude of the reflected pulse.
        - `transmitted`: The calculated transmitted pulse.

    Notes:
    ------
    - The transmitted pulse is computed as the negative difference between the incident and reflected pulses.
    - The function aligns and merges the incident and reflected pulses using `pd.merge_asof()`, which finds the closest matching times between the two DataFrames.
    - The time is corrected by adding the time shift (`delta_t`) from the `df_time` DataFrame.
    """

    # Group by file number
    df_grouped = df.groupby("file_number")
    df_shifted_grouped = df_shifted.groupby("file_number")

    # Merge the incident and reflected data, aligning by the nearest time points
    df_transmitted = pd.concat(
        [
            pd.merge_asof(
                # Select incident data within the time range of the corresponding shifted data
                group.loc[
                    group.time <= df_shifted_grouped.get_group(number).time.max()
                ][["file_number", "time", "avg_amplitude"]],
                # Select reflected data within the time range of the corresponding incident data
                df_shifted_grouped.get_group(number).loc[
                    df_shifted_grouped.get_group(number).time >= group.time.min()
                ][["file_number", "time", "amplitude"]],
                by="file_number",  # Merge on file_number
                on="time",
                direction="nearest",  # Merge based on nearest time
            )
            for number, group in df_grouped
        ]
    )

    # Rename columns for clarity
    df_transmitted.columns = ["file_number", "time", "incident", "reflected"]

    # Calculate the transmitted pulse as the negative difference between incident and reflected pulses
    df_transmitted["transmitted"] = -(
        df_transmitted.incident - df_transmitted.reflected
    )

    # Correct the time by adding the delta_t for each file_number
    df_transmitted["time"] = (
        df_transmitted["time"].values
        + df_time.delta_t.repeat(
            df_transmitted.file_number.value_counts().sort_index()
        ).values
    )

    return df_transmitted


def compute_pulse_lap(df_shifted: pd.DataFrame, df_time: pd.DataFrame) -> pd.DataFrame:
    df_shifted["time"] = (
        df_shifted["time"]
        + df_time.delta_t.repeat(
            df_shifted.file_number.value_counts().sort_index()
        ).values
    )
    df_shifted["amplitude"] = -df_shifted["amplitude"]

    return df_shifted


# @memory_complete.cache
def complete_signal(df: pd.DataFrame, n_elements: int = 2002) -> pd.DataFrame:
    """
    Complete the signal data by adding rows to each `file_number` group
    until each group contains the specified number of elements.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing columns `file_number`, `time`, and `transmitted`.

    n_elements : int, optional
        The target number of rows for each `file_number` group. Default is 2002.

    Returns
    -------
    pd.DataFrame
        DataFrame with additional rows added to each `file_number` group to
        meet the required number of elements, sorted by `file_number` and `time`.

    Notes
    -----
    - The added rows contain `transmitted` values set to zero
    """
    # Count occurrences of each file_number
    grouped = df.groupby("file_number").size()
    additional_rows = n_elements - grouped

    # Create arrays for the additional rows
    file_numbers = np.repeat(grouped.index, additional_rows)
    min_times = df.groupby("file_number")["time"].min().reindex(file_numbers).values
    times = (
        min_times
        - (np.arange(additional_rows.sum()) % additional_rows.max() + 1) * 1e-10
    )
    transmitted_values = np.zeros_like(times)

    # Create the dataframe for the additional rows
    df_additional = pd.DataFrame(
        {"file_number": file_numbers, "time": times, "transmitted": transmitted_values}
    )

    # Concatenate the additional rows with the original dataframe
    df = pd.concat([df, df_additional], ignore_index=True)
    df.sort_values(["file_number", "time"], inplace=True)

    return df


# @memory_dis.cache
def get_discharge_times(df: pd.DataFrame, trigger: float) -> pd.DataFrame:
    """
    Identify the discharge times based on the transmitted signal and a given trigger level.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing columns `file_number`, `time`, and `transmitted`.

    trigger : float
        The trigger level used to determine the discharge event.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the first discharge time for each `file_number`, with columns:
        - `file_number`: Identifier for the signal group.
        - `time`: Time at which the discharge event occurred.
        - `transmitted`: Transmitted signal value at the discharge time.

    Notes
    -----
    - A discharge candidate is identified when:
      * The threshold is greater than or equal to 0.05.
      * The time is less than or equal to 0.95e-7 seconds.
    - The closest transmitted signal to the trigger level is selected as the discharge event.
    - Only one discharge event per `file_number` is returned.
    """

    # Compute the threshold for each `file_number` as the mean transmitted signal
    df["threshold"] = (
        (df.groupby("file_number").transmitted.mean().to_frame("threshold"))
        .threshold.repeat(df.file_number.value_counts().sort_index())
        .values
    )

    # Reset the index to ensure compatibility with further operations
    df.reset_index(drop=True, inplace=True)

    # Identify discharge candidates based on the transmitted signal:
    # - Condition 1: The threshold must be >= 0.05 (to avoid noise or artifacts).
    # - Condition 2: The time must be <= 0.95e-7 seconds (to limit the search window, arbitrary).
    # The absolute difference between the transmitted signal and the trigger is used
    # to find the closest value to the trigger level.
    df.loc[(df.threshold >= 0.05) & (df.time <= 0.95e-7), "dis_candidates"] = (
        -trigger + df["transmitted"]
    ).abs()

    # Drop rows that do not meet the conditions
    df = df.dropna()

    # Group by `file_number` and select the minimum candidate value (closest to the trigger)
    df_grouped = (
        df.groupby("file_number")["dis_candidates"].min().to_frame().reset_index()
    )

    # Merge the selected minimum candidate back with the original DataFrame to retrieve
    # the corresponding `time` and `transmitted` values
    df = df_grouped.merge(df, on=["file_number", "dis_candidates"], how="left")[
        ["file_number", "time", "transmitted"]
    ]

    # Drop duplicate rows, retaining only the first discharge event for each `file_number`
    df = df.drop_duplicates(subset="file_number")

    return df
