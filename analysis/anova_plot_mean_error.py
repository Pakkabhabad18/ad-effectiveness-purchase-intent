import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

# =======================================================
# Setup folders
# =======================================================
BASE_FOLDER = "Regression_ScatterPlot_All/anova"
os.makedirs(BASE_FOLDER, exist_ok=True)

# =======================================================
# Load Data
# =======================================================
df = pd.read_excel("Final_Filtered_Responses.xlsx")

# Remove summary rows
df = df[~df["participantId"].isin(["Total","Mean"])]

# Convert D values to numeric
for col in ["D1","D2","D3","D4"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Compute PI_total
df["PI_total"] = df[["D1","D2","D3","D4"]].mean(axis=1)

ADS = ["CE","AC","PP","BT","ST"]

means = []
errors = []  # SEM or 95% CI width

for ad in ADS:
    data = df[df["assignedAdCode"] == ad]["PI_total"].dropna()
    mean = data.mean()
    sem = stats.sem(data)          # Standard error of the mean
    ci95 = sem * 1.96              # optional: 95% CI
    means.append(mean)
    errors.append(ci95)            # change to sem if you want SEM instead

# =======================================================
# Mean Plot with Error Bars
# =======================================================
plt.figure(figsize=(10, 6))

x_pos = np.arange(len(ADS))

plt.errorbar(
    x_pos,
    means,
    yerr=errors,
    fmt='o-',
    capsize=8,
    linewidth=2,
    markersize=8,
)

plt.xticks(x_pos, ADS)
plt.xlabel("Ad Category")
plt.ylabel("Mean PI_total")
plt.title("Mean PI_total Across Ad Categories with 95% CI Error Bars")
plt.grid(axis="y", linestyle="--", alpha=0.5)

out_path = f"{BASE_FOLDER}/mean_plot_error_bars.png"
plt.savefig(out_path, dpi=300)
plt.close()

print("Saved mean plot with error bars:", out_path)
