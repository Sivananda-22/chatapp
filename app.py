
import os
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection, init_messages_table

app = Flask(__name__)

# Use a strong SECRET_KEY environment variable when deploying.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-key-change-before-deployment"
)


def init_db():
    """Create the users table if it does not exist."""
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return "Username and password are required.", 400

        hashed_password = generate_password_hash(password)
        connection = get_db_connection()

        try:
            connection.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password),
            )
            connection.commit()

        except sqlite3.IntegrityError:
            return "Username already exists!", 409

        finally:
            connection.close()

        return "Registration successful!"

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    connection = get_db_connection()

    try:
        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    finally:
        connection.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("chat"))

    return "Invalid username or password!", 401


@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("home"))

    return render_template(
        "chat.html",
        username=session["username"],
    )


@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return "Please log in first.", 401

    message = request.form.get("message", "").strip()

    if not message:
        return "Message cannot be empty.", 400

    if len(message) > 1000:
        return "Message is too long.", 400

    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO messages (user_id, username, message)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                session["username"],
                message,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return redirect(url_for("chat"))



@app.route("/get_messages")
def get_messages():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first."}), 401

    connection = get_db_connection()

    try:
        messages = connection.execute(
            """
            SELECT username, message
            FROM messages
            ORDER BY id
            """
        ).fetchall()

        result = [
            {
                "username": row["username"],
                "message": row["message"],
            }
            for row in messages
        ]
    finally:
        connection.close()

    return jsonify(result)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    init_messages_table()
    app.run(debug=False)