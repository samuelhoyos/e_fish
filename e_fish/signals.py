import pandas as pd
from sklearn.neighbors import LocalOutlierFactor


def shift_laser_signal(df: pd.DataFrame, df_discharge: pd.DataFrame) -> pd.DataFrame:
    """
    Adjusts the time of the laser signal relative to the discharge time.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the laser signal data with the following columns:
        - `time`: Time of the laser signal.
        - `file_number`: Identifier for the measurement file.
    df_discharge : pd.DataFrame
        DataFrame containing the discharge times with the following column:
        - `time`: Time of the discharge corresponding to each `file_number`.

    """

    df.loc[:, "time"] = (
        df["time"]
        - df_discharge.time.repeat(df.file_number.value_counts().sort_index()).values
    )
    return df


def find_pmt_max(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies the time and amplitude of the 20 highest peaks from photomultiplier signals.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing PMT signal data with the following columns:
        - `file_number`.
        - `time`.
        - `amplitude`.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the rows corresponding to the 20 highest PMT signal peaks, including their times and amplitudes.

    Notes:
    ------
    - If there are multiple points with the same maximum amplitude within a file, the smallest time is chosen.
    """

    # Identify the file numbers of the 20 highest amplitude peaks across all files
    df_max = df[
        df.file_number.isin(
            df.groupby("file_number")["amplitude"]  # Group by file number
            .agg(maxima=(max))  # Find the maximum amplitude in each file
            .maxima.nlargest(20)  # Select the 20 largest amplitudes
            .index  # Get the corresponding file numbers
        )
    ]

    # Retain only the rows where the amplitude is the maximum for each file number
    df_max = df_max[
        df_max.amplitude
        == df_max.groupby("file_number")["amplitude"].transform(lambda x: x.max())
    ]

    # If multiple maxima exist in a file, keeps the one with the smallest time value
    df_max = df_max[
        df_max.time
        == df_max.groupby("file_number")["time"].transform(lambda x: x.min())
    ]

    print("PMT maxima found")

    return df_max


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes outliers from a DataFrame using the Local Outlier Factor (LOF) method.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing numerical data.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with the outliers removed.

    Notes:
    ------
    - The Local Outlier Factor (LOF) identifies outliers based on the local density deviation of a data point compared to its neighbors.
    - Outliers are labeled as -1, while inliers (non-outliers) are labeled as 1.
    """

    lof = LocalOutlierFactor(
        n_neighbors=100, contamination="auto"
    )  # Adjust parameters as needed

    # Fit the model and predict outliers
    outlier_labels = lof.fit_predict(df)

    # Filter out the outliers, keeping only the inliers (where label == 1)
    df = df[outlier_labels == 1]
    return df
