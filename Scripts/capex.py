"""
TODO
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

#########################################################
# LOADING THE DATA
##########################################################

# loading the data file
script_dir = os.path.dirname(os.path.abspath(__file__))
rwe = pd.read_csv(os.path.join(script_dir, "../Data", "RWE_capex.csv"))
eon = pd.read_csv(os.path.join(script_dir, "../Data", "EON_capex.csv"))

# converting Years to Integer
rwe["Year"] = rwe["Year"].astype(int)
eon["Year"] = eon["Year"].astype(int)

# Cleaning
rwe["PP&E_intangibles_mln_EUR"] = pd.to_numeric(
    rwe["PP&E_intangibles_mln_EUR"], errors="coerce"
)
rwe["Capex_total_mln_EUR"] = pd.to_numeric(
    rwe["Capex_total_mln_EUR"], errors="coerce"
)

# mln -> bln
rwe["capex_total_bn"]  = rwe["Capex_total_mln_EUR"] / 1000
rwe["capex_ppe_bn"]    = rwe["PP&E_intangibles_mln_EUR"] / 1000
eon["invest_bn"]       = eon["Investments_mln_EUR"] / 1000


# get shared years
all_years = sorted(set(rwe["Year"]) | set(eon["Year"]))

#########################################################
# COLORS
##########################################################
COLOR_RWE_TOTAL = "#2ecc71"
COLOR_RWE_PPE = "#27ae60"
COLOR_EON = "#3498db"
COLOR_OUTLIER = "#e74c3c"
ALPHA_BAR = 0.85

#########################################################
# Creating the chart
##########################################################

# initialization
fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=False)

# setting the title
fig.suptitle(
    "Capex / Investments: RWE vs E.ON  (2015–2024)\nSource: companies annual reports",
    fontsize=15, fontweight="bold", y=0.98
)


fig.patch.set_facecolor("#2b2b2b")
for ax in axes:
    ax.set_facecolor("#3a3a3a")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.grid(axis="y", color="white", alpha=0.15)

#########################################################
# SUBPLOT RWE
##########################################################

ax1 = axes[0]
rwe_plot = rwe.dropna(subset=["capex_total_bn"]).sort_values("Year")

x = np.arange(len(rwe_plot))
w = 0.38

bars_total = ax1.bar(x - w/2, rwe_plot["capex_total_bn"],
                     width=w, color=COLOR_RWE_TOTAL, alpha=0.85,
                     label="Capex total (mld EUR)")
bars_ppe = ax1.bar(x + w/2, rwe_plot["capex_ppe_bn"],
                     width=w, color=COLOR_RWE_PPE, alpha=0.85,
                     label="PP&E + intangible (mld EUR)")


ax1.set_xticks(x)
ax1.set_xticklabels(rwe_plot["Year"].astype(str), fontsize=10, color="white")
ax1.set_ylabel("mld EUR", fontsize=11, color="white")
ax1.set_title("RWE – Capital Expenditure", fontsize=13, fontweight="500",
              pad=8, color="white")
ax1.legend(fontsize=10, loc="upper left",
           facecolor="#3a3a3a", edgecolor="white", labelcolor="white")
ax1.set_ylim(0, rwe_plot["capex_total_bn"].max() * 1.25)

# NO PP&E 2020
ax1.annotate("no division\nPP&E (2020)",
             xy=(rwe_plot["Year"].tolist().index(2020) + w/2, 0.2),
             fontsize=7.5, color="white", ha="center")

#########################################################
# SUBPLOT E.ON
##########################################################

ax2 = axes[1]
eon_plot = eon[eon["Year"] <= 2024].dropna(subset=["invest_bn"]).sort_values("Year")

x2 = np.arange(len(eon_plot))
bars_eon = ax2.bar(x2, eon_plot["invest_bn"],
                   width=0.6, color=COLOR_EON, alpha=0.85,
                   label="Investments (mld EUR)")


ax2.set_xticks(x2)
ax2.set_xticklabels(eon_plot["Year"].astype(str), fontsize=10, color="white")
ax2.set_ylabel("mld EUR", fontsize=11, color="white")
ax2.set_title("E.ON – Investments", fontsize=13, fontweight="500",
              pad=8, color="white")
ax2.legend(fontsize=10, loc="upper left",
           facecolor="#3a3a3a", edgecolor="white", labelcolor="white")
ax2.set_ylim(0, eon_plot["invest_bn"].max() * 1.25)

#########################################################
# Saving to a file
##########################################################

plt.tight_layout(rect=[0, 0, 1, 0.96])
file_path = "../Plots/capex_RWE_EON.png"

plt.savefig(file_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.show()
