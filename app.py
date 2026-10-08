import os
import sqlite3
import secrets
import string
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import string
import secrets
import psycopg2
import os
import os
from dotenv import load_dotenv
import smtplib

load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key-in-production")
DB = os.path.join(os.path.dirname(__file__), "learnhub.db")


def db():
    conn=psycopg2.connect(os.environ["DATABASE_URL"])
    
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


@app.route("/login/pass", methods=["GET","POST"])
def passe():
    if request.method=="POST":
        username=request.form["username"].strip().lower()
        oldpassword=request.form["old_password"]
        newpass=request.form["new_password"]
        conpass=request.form["confirm_password"]
        conn=db()
        user=conn.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()

        if not user:
            flash("Name glata hai sahi name daalo...")
            return redirect(url_for("passe"))
        if not check_password_hash(user["password_hash"],oldpassword):
            flash("Tumhara purana password galat hai sahi password daalo...")
            return redirect(url_for("passe"))
        if newpass!=conpass:
            flash("password aur confirm password mach nahi kar raha hai..")
            return redirect(url_for("passe"))
        NEWpass=generate_password_hash(newpass)
            
        conn.execute("UPDATE users SET password_hash=? WHERE id =?",(NEWpass,user["id"]))
        session["user_id"]=user["id"]
        session["username"]=user["username"]
        session["role"]=user["role"]
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("passe.html")



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
        gmail= request.form["gmail"]
        print(username)
        print(gmail)
        if not username or " " in username:
            flash("Username valid rakho, spaces nahi.", "error")
            return redirect(url_for("manage_users"))
        def create_password(length=8):
            return ''.join(secrets.choice(string.ascii_uppercase)
                for _ in range(length))
        create_password=create_password()

        print(create_password)

        conn = db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(create_password), "student")
            )
            conn.commit()
            try:
                sender=gmail
                apppass= os.environ.get("password_google","change-this-secret-key-in-production")
                receiver="Ritiklearnhub@gmail.com"
                massege=f"""
                    Subject: Your Password
                    Your Password Is: {create_password}
                    This is your tempary password
                """
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender, apppass)

                # Email bhejna
                server.sendmail(
                    sender,
                    receiver,
                    massege
                )

                # Connection close
                server.quit()

                print("Password is sucsessfully send")
            except:
                print("messege is not send...")

            flash(f"User {username} create ho gaya. Temporary password: {create_password} gmail= {gmail}", "success")
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
        return jsonify({
            "ok": False,
            "error": "Question empty hai."
        }), 400

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key or Groq is None:
        return jsonify({
            "ok": False,
            "error": "AI setup nahi hua. GROQ_API_KEY set karo aur 'pip install groq' chalao."
        }), 503

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=os.environ.get(
                "GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ritik LearnHub AI Assistant. "
                        "Help students with Python, programming, courses and study questions. "
                        "Explain concepts step-by-step in simple English. "
                        "Use examples and code when useful."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.6,
            max_completion_tokens=2048
        )

        answer = response.choices[0].message.content

        return jsonify({
            "ok": True,
            "answer": answer
        })

    except Exception as exc:
        print("GROQ AI ERROR:", repr(exc))

        return jsonify({
            "ok": False,
            "error": "AI response nahi aa saka. GROQ_API_KEY ya GROQ_MODEL check karo."
        }), 500


if __name__ == "__main__":
    init_db()

    app.run(debug=True)
    print("http://192.168.196.214:5000")
