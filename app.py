from flask import Flask, request, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

app = Flask(__name__)

# ---------------- GOOGLE SHEETS SETUP ----------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

workbook = client.open("Book")

# ---------------- SCHEMA DEFINITION ----------------
SCHEMA = {
    "Pawan": ["Days", "Minoxidil (Daily) M & N", "Shampoo (Daily) M", "Body Lotion (Daily) M & N", "Leg Cream(Daily for 20 days) M & N", "Vitamin A&D (Mon-Sat) M & N", "Dutaprost Tablet(Mon/Wed/Fri) M"],
    "daily_track_anu": ["Date", "Sleep", "Wake", "Gym", "Study", "Food"],
    "daily_track_pp": ["Date", "Sleep", "Wake", "Gym", "Study"],
    "Anu": ["Days", "Sporamiz SB Capsules (Daily) M & N", "Teczine Tablet (Daily) E", "Body Lotion (Daily) M & E & N", "Hand Cream(Daily) M & N"]
}

# ---------------- HTML TEMPLATE ----------------
HTML_PAGE = """
<!doctype html>
<html>
<head>
<title>Tracker</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
    font-family: Arial, sans-serif;
    background: #0f172a;
    color: white;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 400px;
    margin: 40px auto;
    background: #1e293b;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 0 20px rgba(0,0,0,0.3);
}

h2 {
    text-align: center;
}

.tabs {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}

.tab {
    flex: 1;
    padding: 10px;
    margin: 2px;
    text-align: center;
    background: #334155;
    border-radius: 8px;
    cursor: pointer;
    text-decoration: none;
    color: white;
}

.tab.active {
    background: #3b82f6;
}

input, select {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    margin-bottom: 15px;
    border-radius: 8px;
    border: none;
    outline: none;
}

button {
    width: 100%;
    padding: 12px;
    background: #22c55e;
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    background: #16a34a;
}

.message {
    text-align: center;
    margin-top: 10px;
    color: #22c55e;
}
</style>
</head>

<body>

<div class="container">
    <h2>Daily Tracker</h2>

    <!-- Tabs -->
    <div class="tabs">
        {% for key in schema.keys() %}
            <a href="/?sheet={{key}}" 
               class="tab {% if key == selected_sheet %}active{% endif %}">
               {{key}}
            </a>
        {% endfor %}
    </div>

    <!-- Form -->
    <form method="POST">
        <input type="hidden" name="sheet" value="{{selected_sheet}}">

        {% for field in fields %}
            <label>{{field}}</label>
            <input name="{{field}}" required>
        {% endfor %}

        <button type="submit">Submit</button>
    </form>

    <div class="message">{{ message }}</div>
</div>

</body>
</html>
"""
# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    selected_sheet = request.args.get("sheet", "Pawan")

    if request.method == "POST":
        selected_sheet = request.form["sheet"]
        sheet = workbook.worksheet(selected_sheet)

        fields = SCHEMA[selected_sheet]

        row = []
        for field in fields:
            value = request.form.get(field, "")
            row.append(value)

        sheet.append_row(row)

        message = f"✅ Data logged in Sheet {selected_sheet}"

    fields = SCHEMA.get(selected_sheet, [])

    return render_template_string(
        HTML_PAGE,
        schema=SCHEMA,
        selected_sheet=selected_sheet,
        fields=fields,
        message=message
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)