import pandas as pd
import concurrent.futures
from pathlib import Path
import os
import numpy as np
from tqdm import tqdm
from diskcache import Cache
import math
import joblib

cache_dir = (
    Path(__file__).parent / "cache_load"
)  #'/home/samuel/Documents/Internship/STAGE/Data_analysis/data/'
os.makedirs(cache_dir, exist_ok=True)
cache = Cache(cache_dir, size_limit=math.inf)

cache_avg = Path(__file__).parent / "cache_avg"
os.makedirs(cache_dir, exist_ok=True)
memory = joblib.Memory(location=cache_avg, verbose=0)

# def reader(filename):
#     df = pd.read_csv(filename, skiprows=4, delimiter=";")
#     print(filename)
#     df.index = [int(filename.split("--")[-1].split(".")[0])] * len(df)
#     return df
def reader(filename):
    try:
        df = pd.read_csv(filename, skiprows=4, delimiter=";")
        #print(filename)
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

#cache.memoize()
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


#@cache.memoize()
def get_df(channel: str, folder: str):
    folder = Path(__file__).parent.parent.parent / Path("data") / folder
    file_list = tuple(
        [str(folder / i) for i in os.listdir(folder) if i.split("-")[0] == channel]
    )
    #print(file_list)
    dfs = create_dfs(file_list)
    df = pd.concat(dfs)
    df.index.name = "file_number"
    df.set_index("Time", append=True, inplace=True)
    df.sort_index(inplace=True)
    df.reset_index(inplace=True)
    df.columns = ["file_number", "time", "amplitude"]
    return df

#@memory.cache
def avg_amplitude(df: pd.DataFrame, window_size: int):
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

def bkgd(channel:str,data_path:str):
    path=Path(__file__).parent.parent/Path("data")/Path(data_path)
    filename=[str(path / i) for i in os.listdir(path) if i.split("-")[0] == channel if "BG1." in i][0]
    file_number="bkgd"
    df = pd.read_csv(filename, skiprows=4, delimiter=";")
    df.columns=['time','amplitude']
    df['file_number']=file_number
    return df

def inverted_bkgd(filename:str, data_path:str,df_discharge:pd.DataFrame, df_discharge_bkgd:pd.DataFrame):

    path=Path(__file__).parent.parent/Path("data")/Path(data_path)/filename
    path_to_write=f"{Path(__file__).parent.parent/Path('data')/Path(data_path)}/{filename.split('.')[0]}_inverted.{filename.split('.')[1]}"
    df=pd.read_csv(f"{str(path)}", delimiter=";", skiprows=4)
    df.columns=["time", "amplitude"]
    df["amplitude"]=-df['amplitude']
    df['time']=df['time']+df_discharge.time.max()-df_discharge_bkgd.time.iloc[0]
    header_text = "LECROYWR625Zi;61392;Waveform\nSegments;1;SegmentSize;2002\nSegment;TrigTime;TimeSinceSegment1\n#1date;0"
    with open(path_to_write, "w") as f:
        f.write(header_text + "\n")
    df.to_csv(path_to_write, sep=";", index=False, mode="a")

    return print(f"Background wrote to {path_to_write}")
