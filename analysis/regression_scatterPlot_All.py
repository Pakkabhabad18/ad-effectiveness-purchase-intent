import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from fpdf import FPDF
import os
import re

# -----------------------------
# SANITIZE TEXT FOR PDF (IMPORTANT)
# -----------------------------
def sanitize_text(s):
    if not isinstance(s, str):
        return s

    replacements = {
        "–": "-",  # en dash
        "—": "-",  # em dash
        "−": "-",  # minus sign
        "→": "->", # arrow
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "°": "",
        "²": "2",
    }

    for bad, good in replacements.items():
        s = s.replace(bad, good)

    # Remove any non-ASCII characters left
    s = re.sub(r'[^\x00-\x7F]+', '', s)
    return s

# -----------------------------
# FOLDERS
# -----------------------------
BASE_FOLDER = "Regression_ScatterPlot_All"
PLOTS_FOLDER = f"{BASE_FOLDER}/plots"

os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

# -----------------------------
# FILE PATHS
# -----------------------------
INPUT_FILE = "Final_Filtered_Responses.xlsx"
TEXT_FILE = f"{BASE_FOLDER}/all_interpretations.txt"
PDF_FILE = f"{BASE_FOLDER}/Full_Regression_Report.pdf"
COMBINED_PNG = f"{BASE_FOLDER}/All_Regression_Plots.png"

AD_CODES = ["CE", "AC", "PP", "BT", "ST"]
QUESTION_B = ["B1", "B2", "B3", "B4"]
QUESTION_D = ["D1", "D2", "D3", "D4"]

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_excel(INPUT_FILE)
df = df[~df["participantId"].isin(["Total", "Mean"])]

for col in QUESTION_B + QUESTION_D:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# -----------------------------
# INTERPRETATION HELPERS
# -----------------------------
def slope_interp(beta):
    if beta > 1: return "Very strong positive effect"
    if beta > 0.5: return "Strong positive effect"
    if beta > 0.2: return "Moderate positive effect"
    if beta > 0: return "Weak positive effect"
    return "No positive or negative effect"

def r2_interp(r2):
    if r2 > 0.50: return "Strong predictive power"
    if r2 > 0.25: return "Moderate predictive power"
    if r2 > 0.10: return "Weak predictive power"
    return "Very weak predictive power"


interpretations = []
plot_files = []

# --------------------------------------------------------
# PROCESS EACH AD GROUP
# --------------------------------------------------------
for ad in AD_CODES:

    sub = df[df["assignedAdCode"] == ad].copy()
    if sub.empty:
        continue

    sub["assignedadcode_total"] = sub[QUESTION_B].mean(axis=1)
    sub["PI_total"] = sub[QUESTION_D].mean(axis=1)
    clean = sub.dropna(subset=["assignedadcode_total", "PI_total"])

    if len(clean) < 2:
        continue

    # Regression
    X = clean[["assignedadcode_total"]].values
    y = clean["PI_total"].values
    model = LinearRegression().fit(X, y)

    slope = model.coef_[0]
    intercept = model.intercept_
    r2 = model.score(X, y)

    # --------------------------------------------------------
    # CREATE INDIVIDUAL PLOT
    # --------------------------------------------------------
    plt.figure(figsize=(6,4))
    plt.scatter(clean["assignedadcode_total"], clean["PI_total"], label="Participants")

    x_range = np.linspace(clean["assignedadcode_total"].min(),
                          clean["assignedadcode_total"].max(), 100)
    plt.plot(x_range, model.predict(x_range.reshape(-1,1)), label="Trendline")

    plt.xlabel("assignedadcode_total (B1–B4 mean)")
    plt.ylabel("PI_total (D1–D4 mean)")
    plt.title(f"{ad} Regression\nSlope={slope:.2f}, R2={r2:.2f}")  # removed unicode R²
    plt.legend()

    plot_path = f"{PLOTS_FOLDER}/{ad}_plot.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    plot_files.append(plot_path)

    # --------------------------------------------------------
    # BUILD INTERPRETATION
    # --------------------------------------------------------
    interpretation = f"""
==========================
Regression Interpretation - {ad}
==========================

Slope (beta1): {slope:.4f}
R-squared: {r2:.4f}

Interpretation:
{slope_interp(slope)}: higher ad evaluation -> higher purchase intention.
{r2_interp(r2)} (R2 = {r2:.2f}).

Overall Meaning:
A 1-point increase in ad evaluation (B1–B4)
results in a {slope:.2f}-point change in PI_total (D1–D4).
The model explains {r2*100:.1f}% of the variance in purchase intention for {ad}.
"""
    interpretations.append(interpretation)


# -----------------------------
# SAVE TEXT FILE
# -----------------------------
with open(TEXT_FILE, "w") as f:
    for block in interpretations:
        f.write(sanitize_text(block))
        f.write("\n\n")


# -----------------------------
# CREATE COMBINED PNG (1×5 FIGURE)
# -----------------------------
fig, axes = plt.subplots(1, 5, figsize=(30, 5), sharey=True)

for ax, ad in zip(axes, AD_CODES):

    sub = df[df["assignedAdCode"] == ad].copy()
    if sub.empty:
        ax.set_title(f"{ad} (No Data)")
        continue

    sub["assignedadcode_total"] = sub[QUESTION_B].mean(axis=1)
    sub["PI_total"] = sub[QUESTION_D].mean(axis=1)
    clean = sub.dropna(subset=["assignedadcode_total","PI_total"])

    if len(clean) < 2:
        ax.set_title(f"{ad} (Insufficient Data)")
        continue

    X = clean[["assignedadcode_total"]].values
    y = clean["PI_total"].values
    model = LinearRegression().fit(X, y)

    slope = model.coef_[0]
    r2 = model.score(X, y)

    ax.scatter(clean["assignedadcode_total"], clean["PI_total"])
    x_range = np.linspace(clean["assignedadcode_total"].min(),
                          clean["assignedadcode_total"].max(), 100)
    ax.plot(x_range, model.predict(x_range.reshape(-1,1)))

    ax.set_title(f"{ad}\nSlope={slope:.2f}, R2={r2:.2f}", fontsize=12)
    ax.set_xlabel("assignedadcode_total")
    ax.set_ylabel("PI_total")

plt.tight_layout()
plt.savefig(COMBINED_PNG, dpi=300)
plt.close()


# -----------------------------
# CREATE PDF REPORT (Unicode-safe)
# -----------------------------
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

for plot_path, interp in zip(plot_files, interpretations):

    ad = os.path.basename(plot_path).replace("_plot.png","")

    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, sanitize_text(f"{ad} - Regression Analysis"), ln=True)

    pdf.image(plot_path, w=180)
    pdf.ln(10)

    pdf.set_font("Arial", size=11)
    for line in sanitize_text(interp).split("\n"):
        pdf.multi_cell(0, 6, line)

pdf.output(PDF_FILE)

print("DONE! Outputs saved in:", BASE_FOLDER)
