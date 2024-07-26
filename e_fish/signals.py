import pandas as pd
from pathlib import Path
from sklearn.neighbors import LocalOutlierFactor


def shift_laser_signal(df: pd.DataFrame, df_discharge: pd.DataFrame):
    df.loc[:, "time"] = (
        df["time"]
        - df_discharge.time.repeat(df.file_number.value_counts().sort_index()).values
    )
    return df


def find_pmt_max(df: pd.DataFrame):
    df_max = df[
        df.file_number.isin(
            df.groupby("file_number")["amplitude"]
            .agg(maxima=(max))
            .maxima.nlargest(20)
            .index
        )
    ]
    df_max = df_max[
        (
            df_max.amplitude
            == df_max.groupby("file_number")["amplitude"].transform(lambda x: x.max())
        )
    ]

    df_max = df_max[
        df_max.time
        == df_max.groupby("file_number")["time"].transform(lambda x: x.min())
    ]

    print("PMT maxima found")

    return df_max

def remove_outliers(df:pd.DataFrame):
    lof = LocalOutlierFactor(n_neighbors=100, contamination='auto')  # Adjust parameters as needed

# Fit the model and predict outliers
    outlier_labels = lof.fit_predict(df)

# Filter outliers (considering non-outliers as -1 and outliers as 1)
    df = df[outlier_labels == 1]
    return df

