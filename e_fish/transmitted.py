import pandas as pd
import numpy as np
from diskcache import Cache
from pathlib import Path
import os
import math
import joblib

cache_dis = Path(__file__).parent / "cache_dis"
os.makedirs(cache_dis, exist_ok=True)
memory_dis = joblib.Memory(location=cache_dis, verbose=0)

cache_transmitted = Path(__file__).parent / "cache_transmitted"
os.makedirs(cache_transmitted, exist_ok=True)
memory = joblib.Memory(location=cache_transmitted, verbose=0)

cache_complete = Path(__file__).parent / "cache_complete"
os.makedirs(cache_complete, exist_ok=True)
memory_complete = joblib.Memory(location=cache_complete, verbose=0)


@memory.cache
def compute_pulse(
    df: pd.DataFrame, df_shifted: pd.DataFrame, df_time: pd.DataFrame
) -> pd.DataFrame:
    df_grouped = df.groupby("file_number")
    df_shifted_grouped = df_shifted.groupby("file_number")
    df_transmitted = pd.concat(
        [
            pd.merge_asof(
                group.loc[
                    group.time <= df_shifted_grouped.get_group(number).time.max()
                ][["file_number", "time", "avg_amplitude"]],
                df_shifted_grouped.get_group(number).loc[
                    df_shifted_grouped.get_group(number).time >= group.time.min()
                ][["file_number", "time", "amplitude"]],
                by="file_number",
                on="time",
                direction="nearest",
            )
            for number, group in df_grouped
        ]
    )
    df_transmitted.columns = ["file_number", "time", "incident", "reflected"]
    df_transmitted["transmitted"] = -(
        df_transmitted.incident - df_transmitted.reflected
    )
    df_transmitted["time"] = (
        df_transmitted["time"].values
        + df_time.delta_t.repeat(
            df_transmitted.file_number.value_counts().sort_index()
        ).values
    )
    return df_transmitted

@memory_complete.cache
def complete_signal(df: pd.DataFrame, n_elements: int = 2002):
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



@memory_dis.cache
def get_discharge_times(df: pd.DataFrame, trigger: float):
    df["threshold"] = (
        (df.groupby("file_number").transmitted.mean().to_frame("threshold"))
        .threshold.repeat(df.file_number.value_counts().sort_index())
        .values
    )
    df.reset_index(drop=True, inplace=True)
    df.loc[(df.threshold >= 0.05) & (df.time <= 0.95e-7), "dis_candidates"] = (
        -trigger + df["transmitted"]
    ).abs()
    df = df.dropna()
    df_grouped = (
        df.groupby("file_number")["dis_candidates"].min().to_frame().reset_index()
    )
    df = df_grouped.merge(df, on=["file_number", "dis_candidates"], how="left")[
        ["file_number", "time", "transmitted"]
    ]
    return df
