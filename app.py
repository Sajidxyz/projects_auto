# app.py
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# ---- your code -------------------------------------------------------
from automation import run_automation

app = Flask(__name__, template_folder='templates')

# ---------- prevent overlapping runs  ----------------------------------
run_lock = threading.Lock()
is_running = False

# ---------- scheduler -------------------------------------------------
scheduler = BackgroundScheduler()
scheduler.start()


def scheduled_job():
    global is_running
    with run_lock:
        if is_running:
            print("[SCHED] Already running – skipping.")
            return
        is_running = True

    print(f"[SCHED] Daily run @ {datetime.now()}")
    result = run_automation()

    with run_lock:
        is_running = False
    print(f"[SCHED] Finished → {result}")


# every day at 06:30
scheduler.add_job(
    func=scheduled_job,
    trigger="cron",
    hour=6,
    minute=30,
    id="daily_yt_short",
    replace_existing=True,
)

# ---------- web pages -------------------------------------------------
@app.route("/")
def index():
    job = scheduler.get_job("daily_yt_short")
    next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M") if job.next_run_time else "—"
    return render_template("index.html", next_run=next_run)


@app.route("/run-now", methods=["POST"])
def run_now():
    global is_running
    with run_lock:
        if is_running:
            return jsonify({"status": "error", "message": "Already running"})

        is_running = True

    def bg():
        global is_running
        try:
            res = run_automation()
            print("[MANUAL] Done →", res)
        finally:
            with run_lock:
                is_running = False

    threading.Thread(target=bg, daemon=True).start()
    return jsonify({"status": "started", "message": "Automation started"})


@app.route("/status")
def status():
    job = scheduler.get_job("daily_yt_short")
    nxt = job.next_run_time.strftime("%Y-%m-%d %H:%M") if job.next_run_time else "—"
    return jsonify({"next_scheduled": nxt, "running": is_running})


# ---------- graceful shutdown -----------------------------------------
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    # debug=True is fine for local testing
    app.run()