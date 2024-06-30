import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from data import load_funding_rate_data, prepare_heatmap_data

FIGURE_SIZE = (20, 10)
NUM_COINS = 30
NUM_DAYS = 90
FUNDING_DIR = "data/funding_rate"
BACKGROUND_COLOR = "#0d1117"
TEXT_COLOR = "#b9babc"


def plot_heatmap(data: pd.DataFrame):
    # Set the style for a dark background
    plt.style.use("dark_background")
    sns.set_theme(style="darkgrid")

    # Create a figure and axis with a dark background
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    fig.patch.set_facecolor(BACKGROUND_COLOR)  # Dark background color for the figure
    ax.set_facecolor(BACKGROUND_COLOR)  # Dark background color for the axes

    # Plot the heatmap
    heatmap = sns.heatmap(
        data,
        cmap="viridis",
        cbar=True,  # Enable the color bar
        ax=ax,
        cbar_kws={
            "orientation": "horizontal"
        },  # Set the color bar orientation to horizontal
        linewidths=0,
    )

    # Customize the text colors
    ax.title.set_color("white")
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.tick_params(colors=TEXT_COLOR, which="both")

    # Setting x-axis labels at 4-day intervals
    datetime_index = data.iloc[0].index
    interval = 24  # each date has 3 values
    xticks = datetime_index[::interval]
    xtick_labels = [date.strftime("%d %b") for date in xticks]

    ax.set_xticks(np.arange(0, len(datetime_index), interval))
    ax.set_xticklabels(xtick_labels, rotation=0, ha="right")

    # Remove x-axis label
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Adjust layout to reduce empty space around the plot
    plt.subplots_adjust(left=0.075, right=0.975, top=0.875, bottom=-0.15)

    # Get the color bar and reposition it below the heatmap
    cbar = heatmap.collections[0].colorbar
    cbar.ax.set_position([0.25, 0.075, 0.5, 0.02])  # [left, bottom, width, height]

    # Customize color bar labels and ticks
    cbar.ax.xaxis.set_ticks_position("bottom")
    cbar.ax.set_xlabel("")
    cbar.ax.tick_params(colors=TEXT_COLOR)

    # Add min and max text annotations
    min_val = data.values.min()
    max_val = data.values.max()
    cbar.ax.text(
        -0.1,
        0.5,
        f"{min_val:.2f}%",
        ha="center",
        va="center",
        color=TEXT_COLOR,
        transform=cbar.ax.transAxes,
    )
    cbar.ax.text(
        1.1,
        0.5,
        f"{max_val:.2f}%",
        ha="center",
        va="center",
        color=TEXT_COLOR,
        transform=cbar.ax.transAxes,
    )

    # Format ticks to show percentage
    def percent_formatter(x, pos) -> str:
        return f"{x:.2f}%"

    cbar.ax.xaxis.set_major_formatter(FuncFormatter(percent_formatter))

    plt.xticks(rotation=0)
    plt.yticks(rotation=0)

    # Add the title in the top left corner
    plt.text(
        -0.06,
        1.125,
        "Funding Rate Heatmap",
        transform=ax.transAxes,
        fontsize=14,
        verticalalignment="top",
        horizontalalignment="left",
        color="white",
        weight="bold",
    )

    plt.show()


def main():

    # Load data
    df = load_funding_rate_data(
        FUNDING_DIR,
    )

    # Prepare heatmap data
    heatmap_data = prepare_heatmap_data(df, NUM_DAYS)

    # Plot heatmap
    plot_heatmap(heatmap_data)


if __name__ == "__main__":
    main()
