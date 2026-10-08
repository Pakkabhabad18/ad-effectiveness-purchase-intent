import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load data
df = pd.read_excel("Final_Filtered_Responses.xlsx")
df = df[~df["participantId"].isin(["Total","Mean"])]

# Compute PI_total
for col in ["D1","D2","D3","D4"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["PI_total"] = df[["D1","D2","D3","D4"]].mean(axis=1)

ADS = ["CE","AC","PP","BT","ST"]

# Output folder
os.makedirs("Regression_ScatterPlot_All/boxplots", exist_ok=True)

# Create boxplots for each category vs all others
for ad in ADS:
    group_cat = df[df["assignedAdCode"] == ad]["PI_total"].dropna()
    group_other = df[df["assignedAdCode"] != ad]["PI_total"].dropna()

    plt.figure(figsize=(6,5))
    plt.boxplot([group_cat, group_other], labels=[f"{ad}", f"Not {ad}"])

    plt.title(f"PI_total: {ad} vs Not-{ad}")
    plt.ylabel("PI_total")

    path = f"Regression_ScatterPlot_All/boxplots/{ad}_vs_others_boxplot.png"
    plt.savefig(path, dpi=300)
    plt.close()

print("Saved all boxplots to: Regression_ScatterPlot_All/boxplots/")
