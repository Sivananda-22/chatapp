from flask import Flask, render_template, request,session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection ,init_messages_table
app = Flask(__name__)
app.secret_key = "change-this-later"

def init_db():
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

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if user and check_password_hash(user["password"], password):

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("chat"))

    return "Invalid username or password!"

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "Username already exists!"

        connection.close()

        return "Registration successful!"

    return render_template("register.html")


@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("home"))

    return render_template(
        "chat.html",
        username=session["username"]
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return redirect(url_for("home"))

    message = request.form.get("message", "").strip()

    if not message:
        return redirect(url_for("chat"))

    if len(message) > 1000:
        return "Message must be 1000 characters or fewer.", 400

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO messages (user_id, username, message)
        VALUES (?, ?, ?)
        """,
        (session["user_id"], session["username"], message)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("chat"))


@app.route("/get_messages")
def get_messages():
    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    connection = get_db_connection()

    messages = connection.execute(
        """
        SELECT username, message, created_at
        FROM messages
        ORDER BY id ASC
        """
    ).fetchall()

    connection.close()

    return [
        {
            "username": message["username"],
            "message": message["message"],
            "created_at": message["created_at"]
        }
        for message in messages
    ]


if __name__ == "__main__":
    init_db()
    init_messages_table()
    app.run(debug=True)