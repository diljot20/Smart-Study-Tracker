from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import date, datetime, timedelta

app = Flask(__name__)

DB_NAME = "database.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT,
            duration INTEGER,
            breaks INTEGER,
            break_time INTEGER,
            focus_level TEXT,
            points INTEGER
        )
    """)

    conn.commit()
    conn.close()


def calculate_points(duration, breaks, focus_level):
    base = max(duration, 0)

    bonus = 0
    if focus_level == "High":
        bonus = 4
    elif focus_level == "Medium":
        bonus = 2

    penalty = breaks

    return max(base + bonus - penalty, 0)


def generate_feedback(duration, breaks, focus_level):
    if breaks >= 3:
        return "You are taking too many breaks."
    if focus_level == "High" and duration >= 1:
        return "Great focus! Keep it up."
    if focus_level == "Low":
        return "Try minimizing distractions."
    return "Good session."


def get_today_stats():
    today = str(date.today())

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
        SELECT COALESCE(SUM(duration), 0),
               COALESCE(COUNT(*), 0),
               COALESCE(SUM(points), 0)
        FROM study_sessions
        WHERE session_date = ?
    """,
        (today,),
    )

    result = c.fetchone()
    conn.close()

    total_time = result[0]
    total_sessions = result[1]
    total_points = result[2]

    return total_time, total_sessions, total_points


def get_streak():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT DISTINCT session_date
        FROM study_sessions
        ORDER BY session_date DESC
    """)

    rows = c.fetchall()
    conn.close()

    if not rows:
        return 0

    saved_dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in rows]

    from datetime import timedelta

    streak = 0
    current_day = date.today()

    if saved_dates[0] == current_day - timedelta(days=1):
        current_day = current_day - timedelta(days=1)

    for d in saved_dates:
        if d == current_day:
            streak += 1
            current_day = current_day.fromordinal(current_day.toordinal() - 1)
        else:
            break

    return streak


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/save_session", methods=["POST"])
def save_session():
    try:
        data = request.json

        duration = int(data["duration"])
        breaks = int(data["breaks"])
        break_time = int(data.get("break_time", 0))
        focus_level = data["focus_level"]

        if duration < 0 or breaks < 0 or break_time < 0:
            return (
                jsonify({"error": "Duration and break values cannot be negative."}),
                400,
            )

        if focus_level not in ["High", "Medium", "Low"]:
            return jsonify({"error": "Invalid focus level."}), 400

        points = calculate_points(duration, breaks, focus_level)
        feedback = generate_feedback(duration, breaks, focus_level)

        today = str(date.today())

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO study_sessions
            (session_date, duration, breaks, break_time, focus_level, points)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (today, duration, breaks, break_time, focus_level, points),
        )

        conn.commit()
        conn.close()

        return jsonify({"points": points, "feedback": feedback})

    except Exception as e:
        print("SAVE_SESSION ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/get_dashboard", methods=["GET"])
def get_dashboard():
    total_time, total_sessions, total_points = get_today_stats()
    streak = get_streak()

    return jsonify(
        {
            "total_time": total_time,
            "total_sessions": total_sessions,
            "total_points": total_points,
            "streak": streak,
        }
    )


@app.route("/get_sessions", methods=["GET"])
def get_sessions():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT session_date, duration, breaks, break_time, focus_level, points
        FROM study_sessions
        ORDER BY id DESC
        LIMIT 10
    """)

    rows = c.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        sessions.append(
            {
                "date": row[0],
                "duration": row[1],
                "breaks": row[2],
                "break_time": row[3],
                "focus_level": row[4],
                "points": row[5],
            }
        )

    return jsonify(sessions)

@app.route("/get_weekly_stats", methods=["GET"])
def get_weekly_stats():
    today = date.today()
    start_date = today - timedelta(days=6)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_date, SUM(duration)
        FROM study_sessions
        WHERE session_date BETWEEN ? AND ?
        GROUP BY session_date
    """, (str(start_date), str(today)))

    results = dict(cursor.fetchall())
    conn.close()

    labels = []
    durations = []

    for i in range(7):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime("%a"))
        durations.append(results.get(str(day), 0))

    return jsonify({
        "labels": labels,
        "durations": durations
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
