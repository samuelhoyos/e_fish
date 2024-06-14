import pandas as pd
import concurrent.futures
from numba import jit
from pathlib import Path
import os
import numpy as np
from tqdm import tqdm
from diskcache import Cache
import math


cache_dir = (
    Path(__file__).parent / "cache_load"
)  #'/home/samuel/Documents/Internship/STAGE/Data_analysis/data/'
os.makedirs(cache_dir, exist_ok=True)
cache = Cache(cache_dir, size_limit=math.inf)


def reader(filename):
    df = pd.read_csv(filename, skiprows=4, delimiter=";")
    df.index = [int(filename.split("--")[-1].split(".")[0])] * len(df)
    return df


cache.memoize()
def create_dfs(file_list: tuple):
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


@cache.memoize()
def get_df(channel: str, folder: str):
    folder = Path(__file__).parent.parent / Path("data") / folder
    file_list = tuple(
        [str(folder / i) for i in os.listdir(folder) if i.split("-")[0] == channel]
    )

    dfs = create_dfs(file_list)
    df = pd.concat(dfs)
    df.index.name = "file_number"
    df.set_index("Time", append=True, inplace=True)
    df.sort_index(inplace=True)
    df.reset_index(inplace=True)
    df.columns = ["file_number", "time", "amplitude"]
    return df


def avg_amplitude(df: pd.DataFrame, window_size: int):
    df_avg = (
        df.groupby("file_number")
        .amplitude.rolling(window=window_size, min_periods=3)
        .mean()
        .fillna(method="bfill")
        .to_frame("avg_amplitude")
    )
    df_avg.reset_index(level="file_number", inplace=True)
    df["avg_amplitude"] = df_avg.avg_amplitude
    return df
