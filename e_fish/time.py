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