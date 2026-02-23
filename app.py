import sqlite3, os, webbrowser
from flask import Flask, render_template, request, redirect, session, flash
from threading import Timer
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS home_content (
            id INTEGER PRIMARY KEY,
            banner_title TEXT,
            banner_subtitle TEXT,
            banner_image TEXT,
            vision TEXT,
            mission TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS about_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            image TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            description TEXT,
            link TEXT
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO home_content
        VALUES (1,'Welcome to Our NGO','together for a better future',
        'default.jpg',
        'Our vision is to empower communities.',
        'Our mission is to create sustainable change.')
    """)

    db.commit()
    db.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        action = request.form["action"]

        if not username or not password:
            flash("Username and password are required", "error")
            return redirect("/")

        db = get_db()
        cur = db.cursor()

        if action == "login":
            cur.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            if cur.fetchone():
                session["user"] = username
                flash("Login successful", "success")
                return redirect("/home")
            else:
                flash("Invalid username or password", "error")

        if action == "register":
            cur.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            )
            if cur.fetchone():
                flash("Username already exists", "error")
            else:
                cur.execute(
                    "INSERT INTO users VALUES (?, ?)",
                    (username, password)
                )
                db.commit()
                flash("Registration successful. Please login.", "success")

    return render_template("auth.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM home_content WHERE id=1")
    row = cur.fetchone()

    content = {
        "banner_title": row[1],
        "banner_subtitle": row[2],
        "banner_image": row[3],
        "vision": row[4],
        "mission": row[5]
    }

    return render_template("home.html", content=content)

@app.route("/about")
def about():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM about_content")
    data = cur.fetchall()

    return render_template("about.html", data=data)

@app.route("/work")
def work():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()

    return render_template("work.html", projects=projects)

@app.route("/media")
def media():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM media")
    media_items = cur.fetchall()

    return render_template("media.html", media=media_items)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin/dashboard")
    return render_template("admin_login.html")

@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        filename = request.form["current_image"]

        if "banner_image" in request.files:
            file = request.files["banner_image"]
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cur.execute("""
            UPDATE home_content SET
            banner_title=?, banner_subtitle=?, banner_image=?, vision=?, mission=?
            WHERE id=1
        """, (
            request.form["banner_title"],
            request.form["banner_subtitle"],
            filename,
            request.form["vision"],
            request.form["mission"]
        ))

        db.commit()

    cur.execute("SELECT * FROM home_content WHERE id=1")
    row = cur.fetchone()

    content = {
        "banner_title": row[1],
        "banner_subtitle": row[2],
        "banner_image": row[3],
        "vision": row[4],
        "mission": row[5]
    }

    cur.execute("SELECT * FROM about_content")
    about_list = cur.fetchall()

    cur.execute("SELECT * FROM projects")
    project_list = cur.fetchall()

    cur.execute("SELECT * FROM media")
    media_list = cur.fetchall()

    return render_template(
        "admin_dashboard.html",
        content=content,
        about_list=about_list,
        project_list=project_list,
        media_list=media_list
    )
    
    
    return render_template("admin_dashboard.html", content=content)

@app.route("/admin/about", methods=["POST"])
def admin_about():
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO about_content (title, content) VALUES (?, ?)",
                (request.form["title"], request.form["content"]))
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/project", methods=["POST"])
def admin_project():
    if "admin" not in session:
        return redirect("/admin")

    image = ""
    if "image" in request.files:
        file = request.files["image"]
        if file.filename:
            image = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image))

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO projects (title, description, image) VALUES (?, ?, ?)",
                (request.form["title"], request.form["description"], image))
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/media", methods=["POST"])
def admin_media():
    if "admin" not in session:
        return redirect("/admin")

    media_type = request.form["type"]
    title = request.form["title"]
    description = request.form["description"]
    link = ""

    if media_type == "image":
        file = request.files.get("image")
        if file and file.filename:
            link = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], link))
    else:
        link = request.form["link"]

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO media (type, title, description, link) VALUES (?, ?, ?, ?)",
        (media_type, title, description, link)
    )
    db.commit()

    return redirect("/admin/dashboard")

@app.route("/admin/about/edit/<int:id>", methods=["POST"])
def edit_about(id):
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE about_content SET title=?, content=? WHERE id=?",
        (request.form["title"], request.form["content"], id)
    )
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/about/delete/<int:id>")
def delete_about(id):
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM about_content WHERE id=?", (id,))
    db.commit()
    return redirect("/admin/dashboard")


@app.route("/admin/project/edit/<int:id>", methods=["POST"])
def edit_project(id):
    if "admin" not in session:
        return redirect("/admin")

    image = request.form["current_image"]

    if "image" in request.files:
        file = request.files["image"]
        if file.filename:
            image = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image))

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE projects SET title=?, description=?, image=? WHERE id=?",
        (request.form["title"], request.form["description"], image, id)
    )
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/project/delete/<int:id>")
def delete_project(id):
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM projects WHERE id=?", (id,))
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/media/edit/<int:id>", methods=["POST"])
def edit_media(id):
    if "admin" not in session:
        return redirect("/admin")

    media_type = request.form["type"]
    title = request.form["title"]
    description = request.form["description"]
    link = request.form["current_link"]

    if media_type == "image":
        file = request.files.get("image")
        if file and file.filename:
            link = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], link))
    else:
        link = request.form["link"]

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE media SET type=?, title=?, description=?, link=? WHERE id=?",
        (media_type, title, description, link, id)
    )
    db.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/media/delete/<int:id>")
def delete_media(id):
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM media WHERE id=?", (id,))
    db.commit()
    return redirect("/admin/dashboard")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)