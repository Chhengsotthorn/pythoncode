from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from datetime import datetime, timedelta
import requests
# from apscheduler.schedulers.background import BackgroundScheduler
# import atexit

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_A_SECURE_SECRET_KEY"

EXCEL_FILE = "Deployment_Tracking_2026.xlsx"
TIMEZONE = "Asia/Phnom_Penh"

# =========================
# Simple Users (Demo)
# =========================
USERS = {
    "admin": "admin123",
    "ops": "ops123"
}

# =========================
# Telegram Configuration
# =========================
TELEGRAM_BOT_TOKEN = "8719941185:AAFH7fQ4dHKX6IL35Vo_34mlW4YDI03b-qI"
TELEGRAM_CHAT_ID = "-5182224921"


# =========================
# Telegram Sender
# =========================
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload, timeout=5)


# =========================
# Load Excel + Logic
# =========================
def load_data(send_alert=False):
    # ✅ Header is Excel row 2
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl", header=1)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ")
        .str.replace("\xa0", " ")
    )

    if "Execution Date/Time" not in df.columns:
        raise ValueError(f"Execution Date/Time not found. Columns: {list(df.columns)}")

    df["Execution Date/Time"] = pd.to_datetime(
        df["Execution Date/Time"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Execution Date/Time"].notna()]

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    df["DEPLOYMENT_FLAG"] = None
    df.loc[df["Execution Date/Time"].dt.date == today, "DEPLOYMENT_FLAG"] = "TODAY"
    df.loc[df["Execution Date/Time"].dt.date == tomorrow, "DEPLOYMENT_FLAG"] = "D-1"

    # =========================
    # Telegram Alerts
    # =========================
    if send_alert:

        # 🔴 TODAY alert
        today_df = df[df["DEPLOYMENT_FLAG"] == "TODAY"]
        if not today_df.empty:
            msg = "<b>🚨 TODAY Deployment Alert</b>\n\n"
            for _, r in today_df.iterrows():
                msg += (
                    f"🆔 <b>{r['Request ID']}</b>\n"
                    f"📦 {r['Request Description']}\n"
                    f"👤 {r['Executed By']}\n"
                    f"🌍 {r['Environment / Schema']}\n"
                    f"📅 {r['Execution Date/Time'].strftime('%d-%b-%Y')}\n"
                    f"——————————————\n"
                )
            send_telegram_alert(msg)

        # 🟡 D‑1 alert
        d1_df = df[df["DEPLOYMENT_FLAG"] == "D-1"]
        if not d1_df.empty:
            msg = "<b>⚠️ D‑1 Deployment Alert (Tomorrow)</b>\n\n"
            for _, r in d1_df.iterrows():
                msg += (
                    f"🆔 <b>{r['Request ID']}</b>\n"
                    f"📦 {r['Request Description']}\n"
                    f"👤 {r['Executed By']}\n"
                    f"🌍 {r['Environment / Schema']}\n"
                    f"📅 {r['Execution Date/Time'].strftime('%d-%b-%Y')}\n"
                    f"——————————————\n"
                )
            send_telegram_alert(msg)

    return df[df["DEPLOYMENT_FLAG"].notna()].to_dict("records")


# =========================
# Scheduler (08:00 Daily)
# =========================
# def scheduled_alert():
    # print("⏰ Running scheduled TODAY & D‑1 alerts...")
    # load_data(send_alert=True)


# scheduler = BackgroundScheduler(timezone=TIMEZONE)
# scheduler.add_job(scheduled_alert, "cron", hour=17, minute=21)
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())


# =========================
# Login Routes
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if USERS.get(username) == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# Dashboard (Protected)
# =========================
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    systems = load_data(send_alert=False)
    return render_template("dashboard.html", systems=systems)


# =========================
# Run App (NO reloader)
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )