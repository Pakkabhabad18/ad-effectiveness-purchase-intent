import pandas as pd
import numpy as np
import math
from rapidfuzz import fuzz, process

PARSED_CSV = "ParsedResponses.csv"
QUESTIONS_XLSX = "Urm survey questions_cleaned.xlsx"
OUTPUT_FILE = "Final_Filtered_Responses.xlsx"

AD_ORDER = ["CE", "AC", "PP", "BT", "ST"]

WATCH_THRESHOLDS = {
    "CE": 24,
    "AC": 33,
    "PP": 39,
    "BT": 72,
    "ST": 60
}

# ----------------- Helper -----------------
def extract_numeric(value):
    if pd.isna(value):
        return np.nan
    s = str(value)
    if "|" in s:
        s = s.split("|")[0].strip()
    else:
        s = s.split()[0]
    try:
        v = int(s)
        return v if 1 <= v <= 5 else np.nan
    except:
        return np.nan

def normalize(text):
    if not isinstance(text, str):
        return ""
    return (
        text.lower()
        .strip()
        .replace("–","-")
        .replace("—","-")
        .replace("’","'")
        .replace("“","'")
        .replace("”","'")
    )

# ----------------- Load parsed file -----------------
df = pd.read_csv(PARSED_CSV, dtype=str)
df["watchSeconds"] = pd.to_numeric(df["watchSeconds"], errors="coerce")

df["start_dt"] = pd.to_datetime(df["startTime"], errors="coerce")
df["end_dt"] = pd.to_datetime(df["endTime"], errors="coerce")
df["duration_sec"] = (df["end_dt"] - df["start_dt"]).dt.total_seconds()

# Identify question-text columns (everything except fixed metadata)
excluded = {
    "participantId","ageGroup","gender","assignedAdCode","watchSeconds",
    "startTime","endTime","start_dt","end_dt","duration_sec","consent",
    "moreInfoURL","clickedMoreInfo","timestamp","completionCode","assignedAdURL"
}

parsed_questions = [c for c in df.columns if c not in excluded]

# ----------------- Load cleaned question bank -----------------
qbank = pd.read_excel(QUESTIONS_XLSX, dtype=str)

qbank["Question Text"] = qbank["Question Text"].astype(str)
qbank["Question Code"] = qbank["Question Code"].astype(str).str.strip()
qbank["assignedAdCode"] = qbank["assignedAdCode"].astype(str).str.strip()

# unique A1..D4 sorted
question_codes = sorted(
    qbank["Question Code"].unique(),
    key=lambda x: (x[0], int(''.join(filter(str.isdigit, x))))
)

# ----------------- Fuzzy mapping -----------------
parsed_questions_norm = {normalize(p): p for p in parsed_questions}

mapping = {}   # (parsed_column, assignedAdCode) → A1..D4

for _, row in qbank.iterrows():
    target_norm = normalize(row["Question Text"])
    adcode = row["assignedAdCode"]
    qcode = row["Question Code"]

    # fuzzy match against parsed columns
    matched_norm, score, _ = process.extractOne(
        target_norm,
        list(parsed_questions_norm.keys()),
        scorer=fuzz.QRatio
    )

    if score >= 90:
        matched_col = parsed_questions_norm[matched_norm]
        mapping[(matched_col, adcode)] = qcode

# ----------------- Generate clean output -----------------
rows = []

for _, r in df.iterrows():
    ad = str(r["assignedAdCode"]).strip()

    base = {
        "participantId": r["participantId"],
        "ageGroup": r["ageGroup"],
        "gender": r["gender"],
        "assignedAdCode": ad,
        "watchSeconds": r["watchSeconds"],
        "duration_sec": r["duration_sec"],
        "attentionCheck": False,
    }

    # initialize A1..D4 as blank
    for qc in question_codes:
        base[qc] = np.nan

    # fill values using matched mapping
    for (col, adcode), qc in mapping.items():
        if adcode == ad:
            base[qc] = extract_numeric(r[col])

    rows.append(base)

out = pd.DataFrame(rows)

# ----------------- Deduplicate participants -----------------
out["watchSeconds_num"] = pd.to_numeric(out["watchSeconds"], errors="coerce").fillna(-1)
out = out.sort_values(["participantId","watchSeconds_num"], ascending=[True, False])
out = out.drop_duplicates("participantId", keep="first").reset_index(drop=True)
out = out.drop(columns=["watchSeconds_num"])

# ----------------- Attention check -----------------
median_dur = out["duration_sec"].dropna().median()
threshold = 0.25 * median_dur

out["attentionCheck"] = out["duration_sec"] < threshold
out = out[out["attentionCheck"] == False].reset_index(drop=True)

# ----------------- Watch time filter (>=) -----------------
def passes_watch(row):
    ad = row["assignedAdCode"]
    req = WATCH_THRESHOLDS.get(ad)
    try:
        return float(row["watchSeconds"]) >= req
    except:
        return False

out = out[out.apply(passes_watch, axis=1)].reset_index(drop=True)

# ----------------- Sort by ad type -----------------
out["assignedAdCode"] = pd.Categorical(out["assignedAdCode"], categories=AD_ORDER, ordered=True)
out = out.sort_values(["assignedAdCode","participantId"]).reset_index(drop=True)

# ----------------- Add Total & Mean rows -----------------
final_rows = []

for ad in AD_ORDER:
    block = out[out["assignedAdCode"] == ad]

    if block.empty:
        continue

    for _, r in block.iterrows():
        final_rows.append(r.to_dict())

    # totals
    sums = block[question_codes].apply(pd.to_numeric, errors="coerce").sum()
    total = {c: "" for c in out.columns}
    total["participantId"] = "Total"
    total["assignedAdCode"] = ad
    for qc in question_codes:
        total[qc] = int(sums[qc]) if not math.isnan(sums[qc]) else ""
    final_rows.append(total)

    # mean
    means = block[question_codes].apply(pd.to_numeric, errors="coerce").mean()
    mean = {c: "" for c in out.columns}
    mean["participantId"] = "Mean"
    mean["assignedAdCode"] = ad
    for qc in question_codes:
        mean[qc] = round(means[qc], 2) if not math.isnan(means[qc]) else ""
    final_rows.append(mean)

final_df = pd.DataFrame(final_rows)

# final column order
final_cols = ["participantId","ageGroup","gender","assignedAdCode",
              "watchSeconds","attentionCheck"] + question_codes

final_df = final_df[final_cols]

final_df.to_excel(OUTPUT_FILE, index=False)
print("Saved:", OUTPUT_FILE)
