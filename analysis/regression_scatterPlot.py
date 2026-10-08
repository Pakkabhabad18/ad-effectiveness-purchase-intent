import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os

INPUT_FILE = "Final_Filtered_Responses.xlsx"

AD_CODES = ["CE", "AC", "PP", "BT", "ST"]

QUESTION_B = ["B1", "B2", "B3", "B4"]
QUESTION_D = ["D1", "D2", "D3", "D4"]

df = pd.read_excel(INPUT_FILE)

# Remove Total / Mean rows
df = df[~df["participantId"].isin(["Total", "Mean"])]

# Convert B and D columns to numeric
for col in QUESTION_B + QUESTION_D:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Create output folder
os.makedirs("regression_output", exist_ok=True)

for ad in AD_CODES:
    print(f"Processing regression for: {ad} ...")

    subset = df[df["assignedAdCode"] == ad].copy()

    if subset.empty:
        print(f"No data for {ad}, skipping...")
        continue

    # Compute totals
    subset["assignedadcode_total"] = subset[QUESTION_B].mean(axis=1)
    subset["PI_total"] = subset[QUESTION_D].mean(axis=1)

    subset_clean = subset.dropna(subset=["assignedadcode_total", "PI_total"])

    if len(subset_clean) < 3:
        print(f"Not enough data for regression in {ad}, skipping...")
        continue

    # Regression
    X = subset_clean[["assignedadcode_total"]].values
    y = subset_clean["PI_total"].values

    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]
    intercept = model.intercept_
    r2 = model.score(X, y)

    # Save regression dataset
    subset_clean.to_excel(f"regression_output/{ad}_regression_dataset.xlsx", index=False)

    # Save regression summary
    with open(f"regression_output/{ad}_regression_results.txt", "w") as f:
        f.write(f"Regression results for {ad}\n")
        f.write(f"Slope (β1): {slope}\n")
        f.write(f"Intercept (β0): {intercept}\n")
        f.write(f"R-squared: {r2}\n")
        f.write(f"Samples used: {len(subset_clean)}\n")

    # Scatter plot with regression line
    plt.figure(figsize=(7, 5))
    plt.scatter(subset_clean["assignedadcode_total"], subset_clean["PI_total"], label="Participants")
    
    x_range = np.linspace(subset_clean["assignedadcode_total"].min(),
                          subset_clean["assignedadcode_total"].max(), 100)
    plt.plot(x_range, model.predict(x_range.reshape(-1, 1)),
             label="Trend Line")

    plt.xlabel("assignedadcode_total (mean of B1–B4)")
    plt.ylabel("PI_total (mean of D1–D4)")
    plt.title(f"Regression: assignedadcode_total → PI_total ({ad})")
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"regression_output/{ad}_scatter_plot.png")
    plt.close()

print("All regression files created in ./regression_output/")
