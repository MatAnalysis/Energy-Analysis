"""
This script reads, transforms and plots the price data.
It shows the difference between France and Germany prices from the 2015 to 2026

Chart of wholesale electricity prices: Germany vs. France (2015–2026)
Input file: european_wholesale_electricity_price_data_monthly.csv
"""
#########################################################
# Transform the data
#########################################################
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import os

#########################################################
# Import of the data
#########################################################

# define location
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "..", "Data")
data_dir = os.path.abspath(data_dir)

# read the data
df = pd.read_csv(
    os.path.join(data_dir, "european_wholesale_electricity_price_data_monthly.csv")
)


#########################################################
# Transform the data
#########################################################

# transform Date column
df["Date"] = pd.to_datetime(df["Date"])
# sort columns
df = df[df["Country"].isin(["Germany", "France"])].sort_values("Date")

# Get the data for the France and Germany
de = df[df["Country"] == "Germany"].set_index("Date")["Price (EUR/MWhe)"]
fr = df[df["Country"] == "France"].set_index("Date")["Price (EUR/MWhe)"]

# Create annual mean by Years
de_annual = de.resample("YE").mean()
fr_annual = fr.resample("YE").mean()

#########################################################
# Prepare the chart variables
#########################################################

# Colors
COLOR_DE = "#E8A020"
COLOR_FR = "#2B6CB0"
COLOR_BG = "#F9F8F6"
COLOR_GRID = "#E2DDD8"
COLOR_ANNO = "#C0392B"
FIG_BG = "#2b2b2b"
PLOT_BG = "#3a3a3a"
# Fonts
plt.rcParams.update({
    "font.family":  "DejaVu Sans",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
})
#########################################################
# Chart Fig
##########################################################

# define the fig
fig = plt.figure(figsize=(14, 10))

# fig settings
fig.patch.set_facecolor(FIG_BG)
fig.suptitle(
    "Wholesale electricity prices\nGermany vs. France  (2015–2026)",
    fontsize=16, fontweight="bold", y=0.98, color="white"
)
gs = fig.add_gridspec(2, 1, hspace=0.45, top=0.90, bottom=0.07,
                      left=0.07, right=0.96)

#########################################################
# Chart Plot 1
##########################################################

# define plot
ax1 = fig.add_subplot(gs[0])
ax1.set_facecolor(PLOT_BG)

#
ax1.plot(de.index, de.values, color=COLOR_DE, linewidth=1.8,
         label="Germany (DE)", zorder=3)
ax1.plot(fr.index, fr.values, color=COLOR_FR, linewidth=1.8,
         label="France (FR)", zorder=3, alpha=0.9)

# fill between lines
ax1.fill_between(de.index, de.values, fr.values,
                 where=(de.values >= fr.values),
                 alpha=0.12, color=COLOR_DE, label="_nolegend_")
ax1.fill_between(de.index, de.values, fr.values,
                 where=(de.values < fr.values),
                 alpha=0.12, color=COLOR_FR, label="_nolegend_")

# Add the events
events = [
    ("2020-03", "2020-06", "#CCCCCC", "COVID-19"),
    ("2021-09", "2023-06", "#FF6666", "Energy\nCrisis"),
]
# plot the events
for start, end, color, label in events:
    ax1.axvspan(pd.Timestamp(start), pd.Timestamp(end),
                alpha=0.10, color=color, zorder=1)
    mid = pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) / 2
    ax1.text(mid, ax1.get_ylim()[1] - 10,
             label, fontsize=8, color="white", ha="center", va="top",
             fontweight="500", alpha=0.9)

# Add peak annotation
peak_de_date = de.idxmax()
peak_fr_date = fr.idxmax()
for val, date, color, label in [
    (de.max(), peak_de_date, COLOR_DE, f"DE peak\n€{de.max():.0f}"),
    (fr.max(), peak_fr_date, COLOR_FR, f"FR peak\n€{fr.max():.0f}"),
]:
    ax1.annotate(
        label,
        xy=(date, val),
        xytext=(date + pd.DateOffset(months=3), val - 60),
        fontsize=8, color="white", fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="white", lw=1.2),
    )

# set label and legend settings
ax1.set_ylabel("EUR/MWh", fontsize=10, color="white")
ax1.set_title("Montly prices", fontsize=11, fontweight="500",
              color="white", pad=6, loc="left")
ax1.legend(fontsize=10, loc="upper left",
           facecolor="#3a3a3a", edgecolor="white", labelcolor="white")
ax1.grid(axis="y", color="white", alpha=0.15)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.tick_params(labelsize=9, colors="white")
ax1.set_xlim(de.index.min(), de.index.max())
ax1.set_ylim(-10, 530)

#########################################################
# Chart Plot 2
##########################################################

# define second plot
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor(PLOT_BG)

# variable for the plot
years = de_annual.index.year
x = np.arange(len(years))
w = 0.35

# bars creation
bars_de = ax2.bar(x - w/2, de_annual.values, width=w,
                  color=COLOR_DE, alpha=0.88, label="Germany (DE)", zorder=3)
bars_fr = ax2.bar(x + w/2, fr_annual.values, width=w,
                  color=COLOR_FR, alpha=0.88, label="France (FR)", zorder=3)

# add values above the bars
for bar in list(bars_de) + list(bars_fr):
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, h + 2,
             f"{h:.0f}", ha="center", va="bottom",
             fontsize=8, color="white")

# set label and legend settings
ax2.set_xticks(x)
ax2.set_xticklabels([str(y) for y in years], fontsize=9, color="white")
ax2.set_ylabel("EUR/MWh (year's mean)", fontsize=10, color="white")
ax2.set_title("Mean Year's price", fontsize=11, fontweight="500",
              color="white", pad=6, loc="left")

ax2.legend(fontsize=10, loc="upper left",
           facecolor="#3a3a3a", edgecolor="white", labelcolor="white")

ax2.grid(axis="y", color="white", alpha=0.15)
ax2.tick_params(labelsize=9, colors="white")
ax2.set_ylim(0, max(de_annual.max(), fr_annual.max()) * 1.22)

#########################################################
# Saving to a file
##########################################################


chart_picture = os.path.join(script_dir, "..", "Plots", "electricity_prices_DE_FR.png")
chart_picture = os.path.abspath(chart_picture)
plt.savefig(chart_picture, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.show()
