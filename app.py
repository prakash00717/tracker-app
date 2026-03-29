from flask import Flask, request, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import numpy as np

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
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(15px);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

h2 {
    text-align: center;
    margin-bottom: 20px;
}

/* Buttons */
.top-buttons {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

.btn {
    flex: 1;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    text-decoration: none;
    font-weight: bold;
}

.primary {
    background: #22c55e;
    color: white;
}

.secondary {
    background: #38bdf8;
    color: black;
}

/* Custom Dropdown */
.custom-dropdown {
    position: relative;
    margin-bottom: 15px;
}

.selected {
    padding: 12px;
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    cursor: pointer;
}

.dropdown-list {
    display: none;
    position: absolute;
    width: 100%;
    background: #1e3a8a;
    border-radius: 10px;
    margin-top: 5px;
    overflow: hidden;
    z-index: 1000;
}

.dropdown-list div {
    padding: 12px;
    cursor: pointer;
}

.dropdown-list div:hover {
    background: #9333ea;
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
    box-sizing: border-box;
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

/* Mobile */
@media (max-width: 480px) {
    .container {
        margin: 10px;
    }

    .top-buttons {
        flex-direction: column;
    }
}
</style>
</head>

<body>

<div class="container">
    <div class="card">

        <h2>🚀 Daily Tracker</h2>

        <!-- Buttons -->
        <div class="top-buttons">
            <a href="/data" class="btn secondary">📄 View Data</a>
            <a href="/dashboard" class="btn primary">📊 Dashboard</a>
        </div>

        <!-- Custom Dropdown -->
        <div class="custom-dropdown">
            <div class="selected" onclick="toggleDropdown()">
                Sheet: {{selected_sheet}}
            </div>

            <div class="dropdown-list" id="dropdown">
                {% for key in schema.keys() %}
                    <div onclick="selectSheet('{{key}}')">Sheet {{key}}</div>
                {% endfor %}
            </div>
        </div>

        <form id="sheetForm" method="GET">
            <input type="hidden" name="sheet" id="sheetInput">
        </form>

        <!-- Form -->
        <form method="POST">
            <input type="hidden" name="sheet" value="{{selected_sheet}}">

            {% for field in fields %}

                <label>{{field}}</label>

                {% if field == "Date" %}
                    <input type="date" name="{{field}}" required>
                {% else %}
                    <input name="{{field}}" required>
                {% endif %}

            {% endfor %}

            <button type="submit">Submit</button>
        </form>

        <div class="message">{{ message }}</div>

    </div>
</div>

<script>
function toggleDropdown() {
    const d = document.getElementById("dropdown");
    d.style.display = d.style.display === "block" ? "none" : "block";
}

function selectSheet(value) {
    document.getElementById("sheetInput").value = value;
    document.getElementById("sheetForm").submit();
}

/* Close dropdown if clicked outside */
window.onclick = function(e) {
    if (!e.target.matches('.selected')) {
        document.getElementById("dropdown").style.display = "none";
    }
}
</script>

</body>
</html>
"""

@app.route("/dashboard")
def dashboard():
    sheet1 = workbook.worksheet("daily_track_anu")
    sheet2 = workbook.worksheet("daily_track_pp")

    data1 = sheet1.get_all_records()
    data2 = sheet2.get_all_records()

    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)

    def time_to_hours(t):
        if not t:
            return None

        t = t.strip().upper()

        # Remove space before AM/PM if present
        t = t.replace(" ", "")

        try:
            dt = datetime.strptime(t, "%I:%M%p")
            return dt.hour + dt.minute / 60
        except:
            return None

    def adjust_sleep_wake(sleep, wake):
        if wake < sleep:
            wake += 24
        return sleep, wake


    # ---- Sheet 1 ----
    sleep_vals = []
    wake_vals = []

    for s, w in zip(df1["Sleep"], df1["Wake"]):
        s = time_to_hours(s)
        w = time_to_hours(w)

        s, w = adjust_sleep_wake(s, w)

        sleep_vals.append(s)
        wake_vals.append(w)

    df1["Sleep"] = sleep_vals
    df1["Wake"] = wake_vals


    # ---- Sheet 2 ----
    sleep_vals = []
    wake_vals = []

    for s, w in zip(df2["Sleep"], df2["Wake"]):
        s = time_to_hours(s)
        w = time_to_hours(w)

        s, w = adjust_sleep_wake(s, w)

        sleep_vals.append(s)
        wake_vals.append(w)

    df2["Sleep"] = sleep_vals
    df2["Wake"] = wake_vals
    df1["Duration"] = df1["Wake"] - df1["Sleep"]
    df2["Duration"] = df2["Wake"] - df2["Sleep"]
    df1["Date"] = pd.to_datetime(df1["Date"], errors='coerce', dayfirst=True)
    df2["Date"] = pd.to_datetime(df2["Date"], errors='coerce', dayfirst=True)
    df1 = df1.sort_values("Date")
    df2 = df2.sort_values("Date")

    # After df1, df2 processed and cleaned

    # Calculate metrics
    avg_sleep_1 = round(df1["Sleep"].mean(), 2) if not df1.empty else 0
    avg_wake_1 = round(df1["Wake"].mean(), 2) if not df1.empty else 0
    avg_duration_1 = round((df1["Wake"] - df1["Sleep"]).mean(), 2) if not df1.empty else 0

    avg_sleep_2 = round(df2["Sleep"].mean(), 2) if not df2.empty else 0
    avg_wake_2 = round(df2["Wake"].mean(), 2) if not df2.empty else 0
    avg_duration_2 = round((df2["Wake"] - df2["Sleep"]).mean(), 2) if not df2.empty else 0

    print("DF1:", df1)
    print("DF2:", df2)
    print("AVG1:", avg_sleep_1, avg_wake_1, avg_duration_1)
    print("AVG2:", avg_sleep_2, avg_wake_2, avg_duration_2)

    # Plot
    plt.figure(figsize=(10,5))
    if df1.empty and df2.empty:
        return "No valid data to display"

    plt.plot(df1["Date"], df1["Sleep"], marker='o', label="Anu's Sleep")
    plt.plot(df1["Date"], df1["Wake"], marker='o', label="Anu's Wake")

    plt.plot(df2["Date"], df2["Sleep"], marker='o', label="Pawan's Sleep")
    plt.plot(df2["Date"], df2["Wake"], marker='o', label="Pawan's Wake")

    plt.xlabel("Date")
    plt.ylabel("Time (Hours)")
    plt.title("Sleep vs Wake Comparison")
    plt.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Convert to image
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")

    return render_template_string("""
    <!doctype html>
    <html>
    <head>
    <title>Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
    body {
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #1e3a8a, #9333ea);
        color: white;
    }

    .container {
        max-width: 900px;
        margin: 20px auto;
        padding: 20px;
    }

    .cards {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }

    .card {
        background: rgba(255,255,255,0.2);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }

    .card p {
        font-size: 20px;
        font-weight: bold;
    }

    .chart {
        text-align: center;
    }

    img {
        max-width: 100%;
        border-radius: 12px;
    }

    .back {
        display: block;
        text-align: center;
        margin-top: 20px;
        padding: 10px;
        background: #38bdf8;
        border-radius: 10px;
        text-decoration: none;
        color: black;
        font-weight: bold;
    }
    </style>
    </head>

    <body>

    <div class="container">

    <h2>📊 Analytics Dashboard</h2>

    <div class="cards">

    <div class="card">
    <h3>Anu's Avg Sleep</h3>
    <p>{{avg_sleep_1}}</p>
    </div>

    <div class="card">
    <h3>Anu's Avg Wake</h3>
    <p>{{avg_wake_1}}</p>
    </div>

    <div class="card">
    <h3>Anu's Duration</h3>
    <p>{{avg_duration_1}}</p>
    </div>

    <div class="card">
    <h3>Pawan's Avg Sleep</h3>
    <p>{{avg_sleep_2}}</p>
    </div>

    <div class="card">
    <h3>Pawan's Avg Wake</h3>
    <p>{{avg_wake_2}}</p>
    </div>

    <div class="card">
    <h3>Pawan's Duration</h3>
    <p>{{avg_duration_2}}</p>
    </div>

    </div>

    <div class="chart">
    <img src="data:image/png;base64,{{img}}">
    </div>

    <a href="/" class="back">⬅ Back</a>

    </div>

    </body>
    </html>
    """,
    avg_sleep_1=avg_sleep_1,
    avg_wake_1=avg_wake_1,
    avg_duration_1=avg_duration_1,
    avg_sleep_2=avg_sleep_2,
    avg_wake_2=avg_wake_2,
    avg_duration_2=avg_duration_2,
    img=img
)

@app.route("/data")
def view_data():
    selected_sheet = request.args.get("sheet", "Pawan")

    sheet = workbook.worksheet(selected_sheet)
    data = sheet.get_all_records()

    if not data:
        return "No data available"

    headers = data[0].keys()

    return render_template_string("""
    <!doctype html>
    <html>
    <head>
    <title>Data Viewer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
    body {
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #1e3a8a, #9333ea);
        color: white;
    }

    .container {
        max-width: 900px;
        margin: 20px auto;
        padding: 20px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }

    th, td {
        padding: 10px;
        border-bottom: 1px solid #444;
        text-align: center;
    }

    th {
        background: rgba(255,255,255,0.1);
    }

    select {
        width: 100%;
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 8px;
        border: none;
    }

    .back {
        display: block;
        text-align: center;
        margin-top: 20px;
        padding: 10px;
        background: #38bdf8;
        border-radius: 10px;
        text-decoration: none;
        color: black;
        font-weight: bold;
    }
    </style>
    </head>

    <body>

    <div class="container">

    <h2>📄 Data Viewer</h2>

    <form method="GET">
        <select name="sheet" onchange="this.form.submit()">
            <option value="Pawan" {% if selected_sheet=="Pawan" %}selected{% endif %}>Pawan</option>
            <option value="Anu" {% if selected_sheet=="Anu" %}selected{% endif %}>Anu</option>
            <option value="daily_track_anu" {% if selected_sheet=="daily_track_anu" %}selected{% endif %}>daily_track_anu</option>
            <option value="daily_track_pp" {% if selected_sheet=="daily_track_pp" %}selected{% endif %}>daily_track_pp</option>                                            
        </select>
    </form>

    <table>
        <tr>
            {% for h in headers %}
                <th>{{h}}</th>
            {% endfor %}
        </tr>

        {% for row in data %}
        <tr>
            {% for h in headers %}
                <td>{{row[h]}}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>

    <a href="/" class="back">⬅ Back</a>

    </div>

    </body>
    </html>
    """,
    data=data,
    headers=headers,
    selected_sheet=selected_sheet
    )

# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    selected_sheet = request.args.get("sheet", "Pawan")

    fields = SCHEMA[selected_sheet]

    message = ""

    if request.method == "POST":
        sheet = workbook.worksheet(selected_sheet)

        row = [request.form.get(field) for field in fields]
        sheet.append_row(row)

        message = "✅ Data added successfully"

    return render_template_string(HTML_PAGE,
        schema=SCHEMA,
        selected_sheet=selected_sheet,
        fields=fields,
        message=message
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)