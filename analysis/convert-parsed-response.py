import pandas as pd
import json

# Load your file (Excel or CSV)
df = pd.read_excel("URM Survey Response.xlsx")

parsed_rows = []
all_questions = set()

# 1. Extract all questions from all rows
for idx, row in df.iterrows():
    raw_json = row["responses_json"]
    if pd.isna(raw_json): 
        continue

    data = json.loads(raw_json)

    # Pull questions
    responses = data.get("responses", {})
    all_questions.update(responses.keys())

# Sort for consistency
all_questions = sorted(list(all_questions))

# 2. Parse each row
for idx, row in df.iterrows():
    raw_json = row["responses_json"]
    if pd.isna(raw_json):
        continue

    data = json.loads(raw_json)

    parsed = {
        "participantId": data.get("participantId", ""),
        "consent": data.get("consent", ""),
        "ageGroup": data.get("ageGroup", ""),
        "gender": data.get("gender", ""),
        "assignedAdCode": data.get("assignedAdCode", ""),
        "assignedAdURL": data.get("assignedAdURL", ""),
        "startTime": data.get("startTime", ""),
        "endTime": data.get("endTime", ""),
        "watchSeconds": data.get("watchSeconds", ""),
        "clickedMoreInfo": data.get("clickedMoreInfo", ""),
        "moreInfoURL": data.get("moreInfoURL", ""),
        "timestamp": data.get("timestamp", ""),
        "completionCode": data.get("completionCode", "")
    }

    # Add all questions
    responses = data.get("responses", {})
    for q in all_questions:
        ans = responses.get(q, {})
        numeric = ans.get("numeric", "")
        text = ans.get("text", "")
        parsed[q] = f"{numeric} | {text}"

    parsed_rows.append(parsed)

# Convert to DataFrame
parsed_df = pd.DataFrame(parsed_rows)

# Save output
parsed_df.to_csv("ParsedResponses.csv", index=False)

print("ParsedResponses.csv created successfully!")
