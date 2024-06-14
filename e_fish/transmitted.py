import pandas as pd

def compute_pulse(
    df: pd.DataFrame, df_shifted: pd.DataFrame
) -> pd.DataFrame:

    df_grouped=df.groupby("file_number")
    df_shifted_grouped=df_shifted.groupby("file_number")
    df_transmitted = pd.concat(
        [
            pd.merge_asof(
                group.loc[
                    group.time
                    <= df_shifted_grouped.get_group(number).time.max()
                ][["file_number", "time", "avg_amplitude"]],
                df_shifted_grouped
                .get_group(number)
                .loc[
                    df_shifted_grouped.get_group(number).time
                    >= group.time.min()
                ][["file_number", "time", "amplitude"]],
                by="file_number",
                on="time",
                direction="nearest",
            )
            for number, group in df_grouped
        ]
    )
    df_transmitted.columns=['file_number','time','incident','reflected']
    df_transmitted['transmitted']=-(df_transmitted.incident-df_transmitted.reflected)
    return df_transmitted