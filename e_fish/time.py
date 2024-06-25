from scipy.signal import find_peaks_cwt, find_peaks, peak_widths
import pandas as pd



def find_discharge(group: pd.core.groupby.generic.DataFrameGroupBy):
    peaks = find_peaks_cwt(group, widths=10)
    df = group.iloc[peaks].to_frame()
    time = df.loc[
        df.assign(shifted=lambda df: df.amplitude.shift(-1))
        .fillna(0)
        .assign(difference=lambda df: df.amplitude - df.shifted)
        .difference.idxmax()
    ]
    return time


def calculate_df_time(
    df: pd.DataFrame, trigger_up: float, trigger_down: float
) -> pd.DataFrame:
    df.loc[
        (((df.avg_amplitude <= trigger_down) | (df.avg_amplitude >= trigger_up)))
        & (df.time < 1e-7),
        "bcs_candidates",
    ] = (trigger_down - df["avg_amplitude"]).abs()
    df.loc[
        ((df.avg_amplitude <= trigger_down) | (df.avg_amplitude >= trigger_up)),
        "electrode_candidates",
    ] = (-trigger_up + df["avg_amplitude"]).abs()
    df_electrode = df.loc[
        df.groupby("file_number")["electrode_candidates"]
        .nsmallest(5)
        .droplevel("file_number")
        .index,
        ["file_number", "time"],
    ].rename(columns={"time": "time_electrode"})
    df_bcs = df.loc[
        df.groupby("file_number")["bcs_candidates"]
        .nsmallest(5)
        .droplevel("file_number")
        .index,
        ["file_number", "time"],
    ].rename(columns={"time": "time_bcs"})
    df_time = (
        df_bcs.groupby(["file_number"])
        .time_bcs.min()
        .to_frame()
        .join(df_electrode.groupby(["file_number"]).time_electrode.min().to_frame())
    )
    df_time["delta_t"] = (df_time.time_electrode - df_time.time_bcs) / 2

    return df_time


def shift_reflected_pulse(df: pd.DataFrame, df_time: pd.DataFrame) -> pd.DataFrame:
    df_shifted = pd.DataFrame()

    df_shifted["file_number"] = (
        pd.Series(df_time.index).repeat(df.file_number.value_counts().sort_index()).values
    )
    df_shifted["time"] = (
        df["time"] - 2 * df_time.delta_t.repeat(df.file_number.value_counts().sort_index()).values
    )
    df_shifted["amplitude"] = -df["avg_amplitude"]

    return df_shifted


def get_td_df(df: pd.DataFrame):
    amplitudes = (
        df.query("time>0")
        .groupby("file_number")[["time", "amplitude"]]
        .agg(amplitude=("amplitude", find_discharge))
        .reset_index()
    )
    df = df.merge(
        amplitudes, how="inner", on=["file_number", "amplitude"]
    ).drop_duplicates(subset=["file_number", "amplitude"])
    return df



