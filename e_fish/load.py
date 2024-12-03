import pandas as pd
import concurrent.futures
from pathlib import Path
import os
import numpy as np
from tqdm import tqdm
from diskcache import Cache
import math
import joblib


# If a cache is desired
cache_dir = (
    Path(__file__).parent / "cache_load"
)  #'/home/samuel/Documents/Internship/STAGE/Data_analysis/data/'
os.makedirs(cache_dir, exist_ok=True)
cache = Cache(cache_dir, size_limit=math.inf)

cache_avg = Path(__file__).parent / "cache_avg"
os.makedirs(cache_dir, exist_ok=True)
memory = joblib.Memory(location=cache_avg, verbose=0)


def reader(filename) -> pd.DataFrame:
    """
    Reads a CSV file containing time series data, sets a custom index, and returns the data as a DataFrame.

    Parameters:
    -----------
    filename : str
        The path to the CSV file to be read.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the contents of the CSV file, with the file number as the index.

    Side Effects:
    -------------
    - Prints error messages if the file is not found, is empty, cannot be parsed, or encounters other issues.

    Notes:
    ------
    - Assumes that the CSV file has a semicolon (;) delimiter.
    - Skips the first four rows of the file when reading the data because of the oscilloscope header.
    - Sets the index of the DataFrame to the file number extracted from the filename.
    """

    try:
        df = pd.read_csv(filename, skiprows=4, delimiter=";")
        # print(filename)
        df.index = [int(filename.split("--")[-1].split(".")[0])] * len(df)
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{filename}' is empty.")
    except pd.errors.ParserError:
        print(f"Error: The file '{filename}' could not be parsed.")
    except ValueError as e:
        print(f"Error: There was a problem with the value conversion: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# cache.memoize()
def create_dfs(file_list: tuple) -> list:
    """
    Reads multiple CSV files in parallel and returns a list of DataFrames.

    Parameters:
    -----------
    file_list : tuple
        A tuple of file paths to be read, excluding any files containing "BG" in their names.

    Returns:
    --------
    list
        A list of DataFrames, each containing the data from one of the input files.

    Side Effects:
    -------------
    - Displays a progress bar using `tqdm` while reading files in parallel.

    Notes:
    ------
    - Uses a `ThreadPoolExecutor` to read files concurrently, improving performance when handling large datasets.
    - Relies on the `reader` function to read individual files.
    """

    file_list = [i for i in file_list if "BG" not in i]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Read files in parallel
        dfs = list(
            tqdm(
                executor.map(reader, file_list),
                total=len(file_list),
                desc="Reading files",
                unit="file",
            )
        )
    return dfs


# @cache.memoize()
def get_df(channel: str, folder: str) -> pd.DataFrame:
    """
    Creates a single concatenated DataFrame from multiple CSV files associated with a specific channel.

    Parameters:
    -----------
    channel : str
        The channel identifier used to filter the files to be read.
    folder : str
        The name of the folder containing the CSV files.

    Returns:
    --------
    pd.DataFrame
        A concatenated DataFrame containing the time series data from all relevant files,
        with columns ['file_number', 'time', 'amplitude'].

    Side Effects:
    -------------
    - Reads all files matching the `channel` identifier in the specified folder.
    - Concatenates the DataFrames from all files and resets the index.

    Notes:
    ------
    - The folder is assumed to be located in the `data` directory relative to the script's location.
    - Uses the `create_dfs` function to read and process the files in parallel.
    """

    folder = Path(__file__).parent.parent.parent / Path("data") / folder
    file_list = tuple(
        [str(folder / i) for i in os.listdir(folder) if i.split("-")[0] == channel]
    )
    # print(file_list)
    dfs = create_dfs(file_list)
    df = pd.concat(dfs)
    df.index.name = "file_number"
    df.set_index("Time", append=True, inplace=True)
    df.sort_index(inplace=True)
    df.reset_index(inplace=True)
    df.columns = ["file_number", "time", "amplitude"]
    return df


# @memory.cache
def avg_amplitude(df: pd.DataFrame, window_size: int):
    """
    Computes the rolling average of the amplitude column in the provided DataFrame and adds it as a new column.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing the columns `file_number` and `amplitude`.
    window_size : int
        The size of the rolling window used to compute the average amplitude.

    Returns:
    --------
    pd.DataFrame
        The input DataFrame with an additional column `avg_amplitude`, containing the rolling average values.

    Side Effects:
    -------------
    - Performs a groupby operation on the `file_number` column to calculate the rolling average separately for each file.
    - Fills missing values in the rolling average using backward fill (`bfill`).

    Notes:
    ------
    - The rolling average is computed with a minimum of 3 data points to avoid incomplete windows.
    - The function resets the `file_number` index before adding the new column to the original DataFrame.
    """

    df_avg = (
        df.groupby("file_number")
        .amplitude.rolling(window=window_size, min_periods=3)
        .mean()
        .bfill()
        .to_frame("avg_amplitude")
    )
    df_avg.reset_index(level="file_number", inplace=True)
    df["avg_amplitude"] = df_avg.avg_amplitude
    return df


def bkgd(channel: str, data_path: str):
    path = Path(__file__).parent.parent / Path("data") / Path(data_path)
    filename = [
        str(path / i)
        for i in os.listdir(path)
        if i.split("-")[0] == channel
        if "BG1." in i
    ][0]
    file_number = "bkgd"
    df = pd.read_csv(filename, skiprows=4, delimiter=";")
    df.columns = ["time", "amplitude"]
    df["file_number"] = file_number
    return df


def inverted_bkgd(
    filename: str,
    data_path: str,
    df_discharge: pd.DataFrame,
    df_discharge_bkgd: pd.DataFrame,
):

    path = Path(__file__).parent.parent / Path("data") / Path(data_path) / filename
    path_to_write = f"{Path(__file__).parent.parent/Path('data')/Path(data_path)}/{filename.split('.')[0]}_inverted.{filename.split('.')[1]}"
    df = pd.read_csv(f"{str(path)}", delimiter=";", skiprows=4)
    df.columns = ["time", "amplitude"]
    df["amplitude"] = -df["amplitude"]
    df["time"] = df["time"] + df_discharge.time.max() - df_discharge_bkgd.time.iloc[0]
    header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"
    with open(path_to_write, "w") as f:
        f.write(header_text + "\n")
    df.to_csv(path_to_write, sep=";", index=False, mode="a")

    return print(f"Background wrote to {path_to_write}")
