
import os
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smartstudy-change-this-key")
DB = os.path.join(os.path.dirname(__file__), "smartstudy.db")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            start_time TEXT DEFAULT '16:00',
            end_time TEXT DEFAULT '21:00',
            study_hours INTEGER DEFAULT 4
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            difficulty INTEGER DEFAULT 3,
            priority INTEGER DEFAULT 3,
            color TEXT DEFAULT '#7657ff'
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER,
            study_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration INTEGER DEFAULT 60,
            completed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER,
            title TEXT NOT NULL,
            exam_date TEXT NOT NULL
        );
        """)


init_db()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return redirect(url_for("dashboard") if session.get("user_id")
                    else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            flash("Enter your details and a password of at least 8 characters.", "error")
            return render_template("auth.html", mode="register")

        try:
            with db() as con:
                cur = con.execute(
                    "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                    (name, email, generate_password_hash(password))
                )
                uid = cur.lastrowid
                con.execute(
                    "INSERT INTO settings(user_id) VALUES(?)", (uid,)
                )
            session.clear()
            session["user_id"] = uid
            session["name"] = name
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("This email is already registered.", "error")

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with db() as con:
            user = con.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]

    with db() as con:
        user = dict(con.execute(
            "SELECT id,name,email FROM users WHERE id=?", (uid,)
        ).fetchone())

        settings = dict(con.execute(
            "SELECT * FROM settings WHERE user_id=?", (uid,)
        ).fetchone())

        subjects = [dict(r) for r in con.execute(
            "SELECT * FROM subjects WHERE user_id=? ORDER BY priority DESC",
            (uid,)
        ).fetchall()]

        sessions = [dict(r) for r in con.execute("""
            SELECT s.*, sub.name AS subject_name, sub.color
            FROM sessions s
            LEFT JOIN subjects sub ON sub.id=s.subject_id
            WHERE s.user_id=?
            ORDER BY s.study_date,s.start_time
        """, (uid,)).fetchall()]

        exams = [dict(r) for r in con.execute("""
            SELECT e.*, sub.name AS subject_name
            FROM exams e
            LEFT JOIN subjects sub ON sub.id=e.subject_id
            WHERE e.user_id=?
            ORDER BY e.exam_date
        """, (uid,)).fetchall()]

    total = len(sessions)
    done = sum(s["completed"] for s in sessions)
    minutes = sum(s["duration"] for s in sessions if s["completed"])
    upcoming = sum(e["exam_date"] >= date.today().isoformat() for e in exams)
    progress = round(done / total * 100) if total else 0

    recommendations = []
    if subjects:
        hardest = max(subjects, key=lambda s: s["difficulty"])
        recommendations = [
            f"Give {hardest['name']} extra attention.",
            "Try 50-minute focused study sessions.",
            "Revise important topics using active recall."
        ]
    else:
        recommendations = ["Add subjects to get personalized study suggestions."]

    return render_template(
        "dashboard.html",
        user=user,
        today=date.today().strftime("%A, %d %B %Y"),
        total=total,
        done=done,
        minutes=minutes,
        upcoming=upcoming,
        sessions=sessions,
        subjects=subjects,
        exams=exams,
        progress=progress,
        recommendations=recommendations,
        settings=settings
    )


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    uid = session["user_id"]

    with db() as con:
        subjects = con.execute(
            "SELECT * FROM subjects WHERE user_id=? ORDER BY priority DESC,difficulty DESC",
            (uid,)
        ).fetchall()
        settings = con.execute(
            "SELECT * FROM settings WHERE user_id=?", (uid,)
        ).fetchone()

        if not subjects:
            flash("Add at least one subject first.", "error")
            return redirect(url_for("dashboard"))

        start = datetime.strptime(settings["start_time"], "%H:%M")
        end = datetime.strptime(settings["end_time"], "%H:%M")
        available = max(1, int((end-start).total_seconds() // 3600))
        hours = min(max(1, settings["study_hours"]), available, 10)

        con.execute("DELETE FROM sessions WHERE user_id=?", (uid,))

        for day_index in range(7):
            study_day = date.today() + timedelta(days=day_index)
            cursor = start

            for slot in range(hours):
                subject = subjects[(day_index * hours + slot) % len(subjects)]

                if cursor + timedelta(hours=1) > end:
                    break

                con.execute("""
                    INSERT INTO sessions
                    (user_id,subject_id,study_date,start_time,duration)
                    VALUES(?,?,?,?,?)
                """, (
                    uid, subject["id"], study_day.isoformat(),
                    cursor.strftime("%H:%M"), 60
                ))
                cursor += timedelta(minutes=75)

    flash("Your 7-day timetable is ready!", "success")
    return redirect(url_for("dashboard"))


@app.route("/toggle-session/<int:sid>", methods=["POST"])
@login_required
def toggle_session(sid):
    uid = session["user_id"]
    with db() as con:
        row = con.execute(
            "SELECT completed FROM sessions WHERE id=? AND user_id=?",
            (sid, uid)
        ).fetchone()

        if row:
            con.execute(
                "UPDATE sessions SET completed=? WHERE id=? AND user_id=?",
                (1 - row["completed"], sid, uid)
            )

    return redirect(url_for("dashboard"))


@app.route("/add-subject", methods=["POST"])
@login_required
def add_subject():
    uid = session["user_id"]
    name = request.form.get("name", "").strip()

    if name:
        with db() as con:
            con.execute("""
                INSERT INTO subjects(user_id,name,difficulty,priority,color)
                VALUES(?,?,?,?,?)
            """, (
                uid, name,
                max(1, min(5, int(request.form.get("difficulty", 3)))),
                max(1, min(5, int(request.form.get("priority", 3)))),
                request.form.get("color", "#7657ff")
            ))
        flash("Subject added!", "success")

    return redirect(url_for("dashboard"))


@app.route("/delete-subject/<int:sid>", methods=["POST"])
@login_required
def delete_subject(sid):
    uid = session["user_id"]
    with db() as con:
        con.execute(
            "DELETE FROM sessions WHERE subject_id=? AND user_id=?",
            (sid, uid)
        )
        con.execute(
            "DELETE FROM exams WHERE subject_id=? AND user_id=?",
            (sid, uid)
        )
        con.execute(
            "DELETE FROM subjects WHERE id=? AND user_id=?",
            (sid, uid)
        )
    return redirect(url_for("dashboard"))


@app.route("/add-exam", methods=["POST"])
@login_required
def add_exam():
    uid = session["user_id"]
    title = request.form.get("title", "").strip()
    exam_date = request.form.get("exam_date", "")
    subject_id = request.form.get("subject_id") or None

    if title and exam_date:
        with db() as con:
            con.execute("""
                INSERT INTO exams(user_id,subject_id,title,exam_date)
                VALUES(?,?,?,?)
            """, (uid, subject_id, title, exam_date))
        flash("Exam added!", "success")

    return redirect(url_for("dashboard"))


@app.route("/settings", methods=["POST"])
@login_required
def settings():
    uid = session["user_id"]
    start = request.form.get("start_time", "16:00")
    end = request.form.get("end_time", "21:00")
    hours = max(1, min(10, int(request.form.get("study_hours", 4))))

    try:
        valid_start = datetime.strptime(start, "%H:%M")
        valid_end = datetime.strptime(end, "%H:%M")
        if valid_end <= valid_start:
            raise ValueError()
    except ValueError:
        flash("Please enter a valid study time range.", "error")
        return redirect(url_for("dashboard"))

    with db() as con:
        con.execute("""
            UPDATE settings
            SET start_time=?,end_time=?,study_hours=?
            WHERE user_id=?
        """, (start, end, hours, uid))

    flash("Study preferences saved!", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
            
