import pandas as pd
import concurrent.futures
from numba import jit
from pathlib import Path
import os
import numpy as np
from tqdm import tqdm
from diskcache import Cache

cache_dir = Path(
    __file__
).parent  #'/home/samuel/Documents/Internship/STAGE/Data_analysis/data/'
os.makedirs(cache_dir, exist_ok=True)
cache = Cache(cache_dir)


def reader(filename):
    df = pd.read_csv(filename, skiprows=4, delimiter=";")
    df.index = [int(filename.split("--")[-1].split(".")[0])] * len(df)
    return df


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
    dfs = create_dfs(file_list[0:1000])
    df = pd.concat(dfs)
    df.reset_index(inplace=True)
    df.columns = ["file_number", "time", "amplitude"]
    df.sort_values(["file_number", "time"], inplace=True)
    return df
