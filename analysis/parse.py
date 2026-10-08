import pandas as pd
import json
import unicodedata

def normalize(text):
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'")
    text = text.replace("\u00A0", " ")
    return text.strip()

# Load file
df = pd.read_excel("URM Survey Response.xlsx")

# Updated mapping based on your final codes
ad_groups = {
    "CE": "Celebrity_Endorsement_Responses.csv",
    "AC": "Ad_Creativity_Responses.csv",
    "PP": "Price_Perception_Responses.csv",
    "BT": "Brand_Trust_Responses.csv",
    "ST": "Story_Telling_Responses.csv"
}

# Storage bucket
grouped_rows = {k: [] for k in ad_groups}

# Process dataset
for idx, row in df.iterrows():
    raw_json = row["responses_json"]
    if pd.isna(raw_json):
        continue

    data = json.loads(raw_json)
    ad_code = data.get("assignedAdCode")

    # Skip if unknown ad type
    if ad_code not in grouped_rows:
        continue

    responses = data.get("responses", {})

    parsed = {
        "participantId": data.get("participantId", ""),
        "consent": data.get("consent", ""),
        "ageGroup": data.get("ageGroup", ""),
        "gender": data.get("gender", ""),
        "assignedAdCode": ad_code,
        "assignedAdURL": data.get("assignedAdURL", ""),
        "startTime": data.get("startTime", ""),
        "endTime": data.get("endTime", ""),
        "watchSeconds": data.get("watchSeconds", ""),
        "clickedMoreInfo": data.get("clickedMoreInfo", ""),
        "moreInfoURL": data.get("moreInfoURL", ""),
        "timestamp": data.get("timestamp", ""),
        "completionCode": data.get("completionCode", "")
    }

    # Add only the participant's own questions
    for q, ans in responses.items():
        q_norm = normalize(q)
        parsed[q_norm] = f"{ans.get('numeric', '')} | {ans.get('text', '')}"

    grouped_rows[ad_code].append(parsed)

# Export each group
for ad_code, rows in grouped_rows.items():
    if len(rows) == 0:
        continue

    out_df = pd.DataFrame(rows)
    out_df.to_csv(ad_groups[ad_code], index=False)
    print(f"{ad_groups[ad_code]} created successfully!")
