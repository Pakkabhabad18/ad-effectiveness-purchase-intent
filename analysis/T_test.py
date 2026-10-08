import pandas as pd
from scipy.stats import ttest_ind
import numpy as np

# Load your cleaned file
df = pd.read_excel("Final_Filtered_Responses.xlsx")

# Remove summary rows
df = df[~df["participantId"].isin(["Total","Mean"])]

# Convert PI questions
for col in ["D1", "D2", "D3", "D4"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Compute PI_total
df["PI_total"] = df[["D1","D2","D3","D4"]].mean(axis=1)

# List of ad categories
ADS = ["CE","AC","PP","BT","ST"]

results = []

for ad1 in ADS:
    for ad2 in ADS:
        if ad1 >= ad2:
            continue

        g1 = df[df["assignedAdCode"] == ad1]["PI_total"].dropna()
        g2 = df[df["assignedAdCode"] == ad2]["PI_total"].dropna()

        if len(g1) > 1 and len(g2) > 1:
            t_stat, p_val = ttest_ind(g1, g2, equal_var=False)
            results.append([ad1, ad2, t_stat, p_val, g1.mean(), g2.mean()])

# Save results
out = pd.DataFrame(results, columns=[
    "Group1", "Group2", "T-statistic", "P-value", "PI_mean_Group1", "PI_mean_Group2"
])

out.to_excel("Regression_ScatterPlot_All/t_test_between_groups.xlsx", index=False)

print("Saved t-test results → Regression_ScatterPlot_All/t_test_between_groups.xlsx")
