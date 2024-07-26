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
def e_fish(df_signal: pd.DataFrame, df_stat:pd.DataFrame, position:int, voltage:int):
    plt.figure(figsize=(10, 5))
    plt.plot(df_signal.timens+45.8, df_signal.shg_single,"k.",label="Data points")
    # Adding error bars with enhanced style
    plt.errorbar(
        df_stat.binns+45.8,
        df_stat["mean"],
        xerr=0.2,
        yerr=df_stat["error"],
        ecolor="green",
        fmt='.',
        color="green",
        capsize=5,  # Adding cap size to error bars
        capthick=1,  # Adding cap thickness to error bars
        elinewidth=1.5,  # Line width of the error bars
        markeredgewidth=1,  # Width of the marker edge
        label="Average"
    )

    plt.xlabel("Time, ns", fontsize="18")
    plt.ylabel("E-FISH signal, a.u.", fontsize="18")
    ax = plt.gca()
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['bottom'].set_position(('outward', 10))
    ax.spines['left'].set_position(('outward', 10))

    # Move bottom spine to y=0 position


    # Only show ticks on the left and bottom spines
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plt.tick_params(labelsize="15")
    plt.title(f"E-FISH signal vs time, position {position}, U={voltage}kV", fontsize="25")
    plt.legend(loc="best", fontsize="15")

    plt.tight_layout()