import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import f_oneway
import os

# =======================================================
#  Setup folders
# =======================================================
BASE_FOLDER = "Regression_ScatterPlot_All/anova"
os.makedirs(BASE_FOLDER, exist_ok=True)

# =======================================================
#  Load Data
# =======================================================
df = pd.read_excel("Final_Filtered_Responses.xlsx")

# Remove summary rows
df = df[~df["participantId"].isin(["Total", "Mean"])]

# Convert D1-D4 to numeric
for col in ["D1", "D2", "D3", "D4"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Compute PI_total
df["PI_total"] = df[["D1","D2","D3","D4"]].mean(axis=1)

ADS = ["CE", "AC", "PP", "BT", "ST"]

# Extract PI_total for each group
groups = {ad: df[df["assignedAdCode"] == ad]["PI_total"].dropna() for ad in ADS}

# =======================================================
#  ANOVA TEST
# =======================================================
anova_stat, p_value = f_oneway(*groups.values())

print("ANOVA F-statistic:", anova_stat)
print("ANOVA p-value:", p_value)

# Save result to Excel
anova_out = pd.DataFrame({
    "ANOVA_F": [anova_stat],
    "p_value": [p_value]
})
anova_out.to_excel(f"{BASE_FOLDER}/anova_results.xlsx", index=False)

# =======================================================
#  BOXPLOT
# =======================================================
plt.figure(figsize=(10, 6))
plt.boxplot(groups.values(), tick_labels=groups.keys())
plt.title("PI_total Distribution Across Ad Conditions (ANOVA)")
plt.ylabel("PI_total")
plt.xlabel("Ad Category")
plt.grid(axis="y", linestyle="--", alpha=0.5)

plt.savefig(f"{BASE_FOLDER}/anova_boxplot.png", dpi=300)
plt.close()

# =======================================================
#  OPTIONAL: Violin Plot
# =======================================================
plt.figure(figsize=(10, 6))
plt.violinplot(groups.values(), showmedians=True)
plt.xticks(np.arange(1, len(ADS) + 1), ADS)
plt.title("PI_total Violin Plot Across Ad Conditions")
plt.ylabel("PI_total")
plt.grid(axis="y", linestyle="--", alpha=0.5)

plt.savefig(f"{BASE_FOLDER}/anova_violin.png", dpi=300)
plt.close()

print("ANOVA outputs saved in:", BASE_FOLDER)
