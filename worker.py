import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from app import load_data, TIMEZONE

def scheduled_alert():
    print(f"⏰ [{datetime.now()}] Running scheduled TODAY & D‑1 alerts...")
    load_data(send_alert=True)

scheduler = BlockingScheduler(timezone=TIMEZONE)

# ✅ Your existing schedule
scheduler.add_job(
    scheduled_alert,
    "cron",
    hour=17,
    minute=21
)

print("✅ Background worker started...")

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass