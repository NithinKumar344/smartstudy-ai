from flask import Flask, render_template, request, jsonify
import sqlite3, json, os
from datetime import date, datetime, timedelta

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "students.db")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id=1), name TEXT, hours INTEGER,
            start_time TEXT, end_time TEXT, exam_date TEXT, exam_subject TEXT
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
            difficulty INTEGER, priority INTEGER
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, start TEXT,
            end TEXT, subject TEXT, kind TEXT, done INTEGER DEFAULT 0
        )""")
        con.execute("INSERT OR IGNORE INTO settings (id,name,hours,start_time,end_time,exam_date,exam_subject) VALUES (1,'Student',4,'16:00','21:00','','')")
init_db()

def get_data():
    with db() as con:
        settings = dict(con.execute("SELECT * FROM settings WHERE id=1").fetchone())
        subjects = [dict(x) for x in con.execute("SELECT * FROM subjects ORDER BY priority DESC, difficulty DESC")]
        tasks = [dict(x) for x in con.execute("SELECT * FROM tasks ORDER BY day,start")]
    return settings, subjects, tasks

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/data")
def data():
    settings, subjects, tasks = get_data()
    total = len(tasks)
    completed = sum(t["done"] for t in tasks)
    return jsonify(settings=settings, subjects=subjects, tasks=tasks,
                   total=total, completed=completed,
                   progress=round(completed/total*100) if total else 0)

@app.post("/api/settings")
def save_settings():
    d = request.get_json()
    with db() as con:
        con.execute("""UPDATE settings SET name=?,hours=?,start_time=?,end_time=?,exam_date=?,exam_subject=? WHERE id=1""",
                    (d.get("name","Student"), int(d.get("hours",4)), d.get("start_time","16:00"),
                     d.get("end_time","21:00"), d.get("exam_date",""), d.get("exam_subject","")))
    return jsonify(ok=True)

@app.post("/api/subjects")
def add_subject():
    d = request.get_json()
    name = d.get("name","").strip()
    if not name:
        return jsonify(error="Enter a subject name."), 400
    with db() as con:
        con.execute("INSERT INTO subjects(name,difficulty,priority) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET difficulty=excluded.difficulty, priority=excluded.priority",
                    (name, int(d.get("difficulty",3)), int(d.get("priority",3))))
    return jsonify(ok=True)

@app.delete("/api/subjects/<int:sid>")
def delete_subject(sid):
    with db() as con:
        con.execute("DELETE FROM subjects WHERE id=?", (sid,))
    return jsonify(ok=True)

@app.post("/api/generate")
def generate():
    settings, subjects, _ = get_data()
    if not subjects:
        return jsonify(error="Add at least one subject before generating a timetable."), 400

    # Weighted round-robin: harder and higher-priority subjects appear more often.
    ranked = sorted(subjects, key=lambda s: (s["difficulty"] * 0.65 + s["priority"] * 0.35), reverse=True)
    hours = max(1, min(int(settings["hours"]), 10))
    start = datetime.strptime(settings["start_time"], "%H:%M")
    end = datetime.strptime(settings["end_time"], "%H:%M")
    available = max(1, int((end-start).total_seconds() // 3600))
    sessions = min(hours, available)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    slots = []
    for day_index, day in enumerate(days):
        cursor = start
        for n in range(sessions):
            subject = ranked[(day_index * sessions + n) % len(ranked)]
            finish = cursor + timedelta(hours=1)
            slots.append((day, cursor.strftime("%H:%M"), finish.strftime("%H:%M"), subject["name"], "Study"))
            cursor = finish + timedelta(minutes=15)
            if cursor >= end:
                break
        # A short revision block is included on the weekend.
        if day in ("Sat", "Sun"):
            slots.append((day, "19:00", "19:30", ranked[0]["name"], "Revision"))
    with db() as con:
        con.execute("DELETE FROM tasks")
        con.executemany("INSERT INTO tasks(day,start,end,subject,kind) VALUES(?,?,?,?,?)", slots)
    return jsonify(ok=True, count=len(slots))

@app.patch("/api/tasks/<int:tid>")
def toggle_task(tid):
    with db() as con:
        row = con.execute("SELECT done FROM tasks WHERE id=?", (tid,)).fetchone()
        if not row:
            return jsonify(error="Task not found"), 404
        con.execute("UPDATE tasks SET done=? WHERE id=?", (0 if row["done"] else 1, tid))
    return jsonify(ok=True)

@app.get("/api/recommendations")
def recommendations():
    settings, subjects, tasks = get_data()
    tips = []
    if subjects:
        weak = max(subjects, key=lambda s: s["difficulty"])
        tips.append(f"Give {weak['name']} extra attention because you rated it difficult.")
        tips.append("Try focused 50-minute sessions followed by a 10-minute break.")
        tips.append("End each study day with 15 minutes of active recall.")
    else:
        tips.append("Add your subjects to receive personalized study recommendations.")
    if settings.get("exam_date"):
        try:
            days = (date.fromisoformat(settings["exam_date"]) - date.today()).days
            if days >= 0:
                tips.insert(0, f"{settings.get('exam_subject') or 'Your exam'} is in {days} day(s). Start with the highest-priority topics.")
        except ValueError:
            pass
    return jsonify(tips=tips)

if __name__ == "__main__":
    app.run(debug=True)
