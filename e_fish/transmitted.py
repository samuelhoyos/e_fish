import pandas as pd


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
        - df_time.time_bcs.repeat(
            df_transmitted.file_number.value_counts().sort_index()
        ).values
    )
    return df_transmitted

def get_discharge_times(df:pd.DataFrame):
   df["threshold"]= (df.groupby("file_number")
    .transmitted.mean()
    .to_frame("threshold")
    ).threshold.repeat(
            df.file_number.value_counts().sort_index()
        ).values
   df.reset_index(drop=True, inplace=True)
   df.loc[(df.threshold >= 0.05) & (df.time <= 0.9e-7), "dis_candidates"] = (
    -0.05 + df["transmitted"]
).abs()
   df=df.dropna()
   df_grouped=df.groupby("file_number")["dis_candidates"].min().to_frame().reset_index()
   df=df_grouped.merge(df, on=["file_number","dis_candidates"], how="left")[['file_number','time','transmitted']]
   return dfdef get_discharge_times(df: pd.DataFrame, trigger: float):
    df["threshold"] = (
        (df.groupby("file_number").transmitted.mean().to_frame("threshold"))
        .threshold.repeat(df.file_number.value_counts().sort_index())
        .values
    )
    df.reset_index(drop=True, inplace=True)
    df.loc[(df.threshold >= trigger) & (df.time <= 0.9e-7), "dis_candidates"] = (
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
