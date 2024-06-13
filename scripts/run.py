from e_fish import load, time
from pathlib import Path
import pandas as pd

trigger_up=0.15
trigger_down=-trigger_up

if __name__ == "__main__":
    df_1 = load.get_df(channel="C1", folder=Path("2024_05_16/pos2_45kV"))
    # df_2 = load.get_df(channel="C2", folder=Path("2024_05_16/pos2_45kV"))
    # df_3 = load.get_df(channel="C3", folder=Path("2024_05_16/pos2_45kV"))
    # df_td = time.get_td_df(df_1)
    df_1 = load.avg_amplitude(df=df_1, window_size=10)
    df_time=pd.read_parquet("/home/samuel/Documents/Internship/STAGE/e_fish/PARQUET/df_time.parquet")# time.calculate_df_time(df_1,trigger_up,trigger_down)
    df_shifted=time.shift_reflected_pulse(df_1,df_time)

