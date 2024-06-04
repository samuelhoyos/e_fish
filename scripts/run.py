from e_fish import load, time
from pathlib import Path

if __name__ == "__main__":
    df_1 = load.get_df(channel="C1", folder=Path("2024_05_15/position_1"))
    df_2 = load.get_df(channel="C2", folder=Path("2024_05_15/position_1"))
    df_3 = load.get_df(channel="C3", folder=Path("2024_05_15/position_1"))
    df_td = time.get_td_df(df_1)
