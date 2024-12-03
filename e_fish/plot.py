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


# Simple name for a proper namespace
def e_fish(df_signal: pd.DataFrame, df_stat: pd.DataFrame, position: int, voltage: int):
    """
    Plots the E-FISH signal as a function of time with data points and statistical averages, including error bars.

    Parameters:
    -----------
    df_signal : pd.DataFrame
        DataFrame containing the E-FISH signal data with the following columns:
        - `timens`: Time in nanoseconds.
        - `shg_single`: Measured E-FISH signal in arbitrary units (a.u.).
    df_stat : pd.DataFrame
        DataFrame containing statistical data with the following columns:
        - `binns`: Time bins in nanoseconds.
        - `mean`: Mean E-FISH signal for each bin.
        - `error`: Standard error for each bin.
    position : int
        The point at which measurements where performed in the experimental setup.
    voltage : int
        The applied voltage in kilovolts (kV) during the measurement.

    Returns:
    --------
    None
        The function generates a plot but does not return any value.

    Side Effects:
    -------------
    - Displays a plot of the E-FISH signal as a function of time.
    - The plot includes data points (`df_signal`) and the average signal with error bars (`df_stat`).

    Notes:
    ------
    - The error bars are styled with green color, a capsize of 5, and enhanced line thickness.
    - The plot title indicates the position and voltage used in the experiment.
    - The function modifies the appearance of the plot by hiding the top and right spines and positioning the bottom and left spines outward.
    - Tick labels and axis labels are styled with increased font sizes for better readability.
    """

    plt.figure(figsize=(10, 5))
    plt.plot(df_signal.timens, df_signal.shg_single, "k.", label="Data points")
    # Adding error bars with enhanced style
    plt.errorbar(
        df_stat.binns,
        df_stat["mean"],
        xerr=0.2,
        yerr=df_stat["error"],
        ecolor="green",
        fmt=".",
        color="green",
        capsize=5,
        capthick=1,
        elinewidth=1.5,  # Line width of the error bars
        markeredgewidth=1,
        label="Average",
    )

    plt.xlabel("Time, ns", fontsize="18")
    plt.ylabel("E-FISH signal, a.u.", fontsize="18")
    ax = plt.gca()
    ax.spines["top"].set_color("none")
    ax.spines["right"].set_color("none")
    ax.spines["bottom"].set_position(("outward", 10))
    ax.spines["left"].set_position(("outward", 10))

    # Move bottom spine to y=0 position

    # Only show ticks on the left and bottom spines
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("left")
    plt.tick_params(labelsize="15")
    plt.title(
        f"E-FISH signal vs time, position {position}, U={voltage}kV", fontsize="25"
    )
    plt.legend(loc="best", fontsize="15")

    plt.tight_layout()
