import os
import sqlite3
import secrets
import string
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import os
import os
import os
from dotenv import load_dotenv

load_dotenv()



try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

app = Flask(__name__)
@app.route("/google1c9c43f38f755c77.html")
def google_verification():
    return send_from_directory(
        os.path.dirname(__file__),
        "google1c9c43f38f755c77.html"
    )



app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key-in-production")
DB = os.path.join(os.path.dirname(__file__), "learnhub.db")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        youtube_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    admin = conn.execute("SELECT id FROM users WHERE username = ?", ("ritik",)).fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("ritik", generate_password_hash(os.environ.get("ADMIN_PASSWORD", "Ritik@1234")), "admin")
        )
    if conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO courses (title, description, youtube_url) VALUES (?, ?, ?)",
            [
                ("Python Basics", "Variables, loops, functions aur beginner Python.", "https://www.youtube.com/watch?v=rfscVS0vtbw"),
                ("Python OOP", "Classes, objects aur OOP concepts.", "https://www.youtube.com/watch?v=JeznW_7DlB0"),
            ]
        )
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


def make_password(length=10):
    alphabet = string.ascii_letters + string.digits + "!@#$"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def youtube_embed(url):
    if not url:
        return ""
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
    elif "watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]
    elif "youtube.com/embed/" in url:
        video_id = url.split("youtube.com/embed/")[-1].split("?")[0]
    else:
        return ""
    return f"https://www.youtube.com/embed/{video_id}"


@app.context_processor
def inject_helpers():
    return {"youtube_embed": youtube_embed}


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Username ya password galat hai.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return render_template("dashboard.html", courses=courses, users_count=users_count)


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        if not username or " " in username:
            flash("Username valid rakho, spaces nahi.", "error")
            return redirect(url_for("manage_users"))
        password = make_password()
        conn = db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), "student")
            )
            conn.commit()
            flash(f"User {username} create ho gaya. Temporary password: {password}", "success")
        except sqlite3.IntegrityError:
            flash("Ye username already exist karta hai.", "error")
        finally:
            conn.close()
        return redirect(url_for("manage_users"))

    conn = db()
    users = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("users.html", users=users)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    conn = db()
    conn.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("User delete kar diya.", "success")
    return redirect(url_for("manage_users"))


@app.route("/admin/courses", methods=["GET", "POST"])
@admin_required
def manage_courses():
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        youtube_url = request.form["youtube_url"].strip()
        if not title:
            flash("Course title required hai.", "error")
            return redirect(url_for("manage_courses"))
        conn = db()
        conn.execute(
            "INSERT INTO courses (title, description, youtube_url) VALUES (?, ?, ?)",
            (title, description, youtube_url)
        )
        conn.commit()
        conn.close()
        flash("Course add ho gaya.", "success")
        return redirect(url_for("manage_courses"))

    conn = db()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("courses.html", courses=courses)


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@admin_required
def delete_course(course_id):
    conn = db()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course delete kar diya.", "success")
    return redirect(url_for("manage_courses"))


@app.route("/api/ask-ai", methods=["POST"])
@login_required
def ask_ai():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"ok": False, "error": "Question empty hai."}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return jsonify({
            "ok": False,
            "error": "AI setup nahi hua. OPENAI_API_KEY set karo aur 'pip install openai' chalao."
        }), 503

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
            instructions=(
                "You are Ritik LearnHub AI Assistant. "
                "Help students with Python, programming, courses and study questions. "
                "Answer clearly, safely and in simple Hinglish when appropriate."
            ),
            input=question
        )
        return jsonify({"ok": True, "answer": response.output_text})
    except Exception as exc:
        print("AI ERROR:", exc)
        return jsonify({"ok": False, "error": "AI response nahi aa saka. API key/model check karo."}), 500


if __name__ == "__main__":
    init_db()

    app.run(debug=True)
    print("http://192.168.196.214:5000")
