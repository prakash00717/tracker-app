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
    "Pawan": ["Date", "Minoxidil (Daily) M & N", "Shampoo (Daily) M", "Body Lotion (Daily) M & N", "Leg Cream(Daily for 20 days) M & N", "Vitamin A&D (Mon-Sat) M & N", "Dutaprost Tablet(Mon/Wed/Fri) M"],
    "daily_track_anu": ["Date", "Sleep", "Wake", "Gym", "Study", "Food"],
    "daily_track_pp": ["Date", "Sleep", "Wake", "Gym", "Study"],
    "Anu": ["Date", "Sporamiz SB Capsules (Daily) M & N", "Teczine Tablet (Daily) E", "Body Lotion (Daily) M & E & N", "Hand Cream(Daily) M & N"]
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
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #1e3a8a, #9333ea);
    color: white;
}

.container {
    max-width: 400px;
    margin: 40px auto;
    padding: 20px;
}

.card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(15px);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

h2 {
    text-align: center;
    margin-bottom: 20px;
}

/* Dropdown */
select {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    border: none;
    margin-bottom: 20px;
    background: rgba(255,255,255,0.2);
    color: white;
}

/* Inputs */
label {
    font-size: 14px;
}

input {
    width: 100%;
    padding: 12px;
    margin-top: 5px;
    margin-bottom: 15px;
    border-radius: 10px;
    border: none;
    outline: none;
    background: rgba(255,255,255,0.2);
    color: white;
}

input:focus {
    background: rgba(255,255,255,0.3);
}

/* Button */
button {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(90deg, #22c55e, #4ade80);
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    transform: scale(1.03);
}

/* Message */
.message {
    text-align: center;
    margin-top: 10px;
    color: #a7f3d0;
}
</style>
</head>

<body>

<div class="container">
    <div class="card">

        <h2>🚀 Daily Tracker</h2>

        <!-- Dropdown -->
        <form method="GET">
            <select name="sheet" onchange="this.form.submit()">
                {% for key in schema.keys() %}
                    <option value="{{key}}" {% if key == selected_sheet %}selected{% endif %}>
                        Sheet {{key}}
                    </option>
                {% endfor %}
            </select>
        </form>

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