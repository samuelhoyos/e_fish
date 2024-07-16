import matplotlib.pyplot as plt
import pandas as pd


def plot_signals(df: pd.DataFrame, file_number: int):
    df = df.query(f"file_number=={file_number}")

    plt.figure(figsize=(10, 5))
    plt.plot(
        df.time * 1e9,
        df.incident,
        color="#D17E00",
        linestyle="-",
        linewidth=3,
        label="Incident",
    )
    plt.plot(
        df.time * 1e9,
        df.reflected,
        color="#4A90E2",
        linestyle="-",
        linewidth=3,
        label="Reflected",
    )
    plt.hlines(
        0.05,
        xmin=df.time.min() * 1e9,
        xmax=df.time.max() * 1e9,
        color="k",
        linestyle="-.",
        label="Trigger value",
    )
    plt.plot(
        df.time * 1e9, df.transmitted, color="g", linestyle="--", label="Deposited"
    )
    plt.legend(loc="best", fontsize=15)
    # plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.xlabel("Time, ns", fontsize=20)
    plt.ylabel("Voltage, a.u.", fontsize=20)
    plt.tight_layout()
    plt.title("No deposited pulse", fontsize=25)
    return 0
