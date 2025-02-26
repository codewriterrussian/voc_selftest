import sys
import os
import json
import random
import webbrowser
import requests

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session  # Import Flask-Session for server-side sessions

# -----------------------------------------------------------------------------
# Global Constants
# -----------------------------------------------------------------------------
JSONBIN_API_KEY = "$2a$10$emdSh/thUg5xTvyY9z89UOy.BurV3ykvVjjUjodpvnJe2Xqc/WAAm"  # Replace with your actual API key
BIN_ID = "67a87edbacd3cb34a8db4700"  # Replace with your actual JSONBin Bin ID
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

# -----------------------------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "some_secret_key_for_session"  # Needed for sessions in Flask

# Configure server-side sessions
app.config["SESSION_TYPE"] = "filesystem"  # Options include 'filesystem', 'redis', etc.
Session(app)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def fetch_json_from_bin():
    """Fetch JSON data from JSONBin.io."""
    headers = {"X-Master-Key": JSONBIN_API_KEY}
    response = requests.get(JSONBIN_URL, headers=headers)

    if response.status_code == 200:
        return response.json().get("record", {"categories": {}})
    else:
        print(f"Error fetching JSON: {response.text}")
        return {"categories": {}}


def write_json_to_bin(data_dict):
    """Update the JSON data in JSONBin.io."""
    headers = {
        "X-Master-Key": JSONBIN_API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data_dict))

    if response.status_code != 200:
        print(f"Error updating JSON: {response.text}")


# Load JSON from API at startup
data = fetch_json_from_bin()
categories = data.get("categories", {})

# Default style settings
DEFAULT_STYLE = {
    "bg_color": "#555555",
    "text_color": "#ffffff",
    "font_size": 18
}


def get_style():
    """Returns the user-selected style or the default style."""
    return session.get("style", DEFAULT_STYLE.copy())


def get_current_quiz():
    """Returns the current quiz session."""
    return session.get("quiz", None)


def save_current_quiz(quiz):
    """Saves the current quiz to the session."""
    session["quiz"] = quiz


# -----------------------------------------------------------------------------
# Flask Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Home page with quiz categories."""
    style = get_style()
    return render_template("index.html", categories=list(categories.keys()), style=style)


@app.route("/start_quiz", methods=["POST"])
def start_quiz():
    """Starts a new quiz with the selected category."""
    category_name = request.form.get("category_name", "").strip()
    if not category_name or category_name not in categories:
        return redirect(url_for("index"))

    questions = categories.get(category_name, [])
    random.shuffle(questions)

    # Save only the necessary quiz info in the session.
    session["quiz"] = {
        "category": category_name,
        "questions": questions,
        "current_index": 0
    }

    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    """Displays the quiz question and processes answers."""
    quiz_data = get_current_quiz()
    if not quiz_data:
        return redirect(url_for("index"))

    questions = quiz_data["questions"]
    current_index = quiz_data["current_index"]
    style = get_style()

    if current_index >= len(questions):
        return render_template("finished.html", style=style)

    current_q = questions[current_index]
    question_text = current_q.get("question", "")
    options_dict = current_q.get("options", {})
    correct_answer = current_q.get("correct_answer", "").strip()
    explanation = current_q.get("explanation", "")

    if request.method == "POST":
        selected_letter = request.form.get("selected_letter", "").strip()
        is_correct = (selected_letter == correct_answer)

        return render_template(
            "quiz_answer.html",
            question=question_text,
            options=options_dict,
            correct_answer=correct_answer,
            selected_letter=selected_letter,
            explanation=explanation,
            style=style
        )

    return render_template("quiz.html", question=question_text, options=options_dict, style=style)


@app.route("/next_question", methods=["POST"])
def next_question():
    """Moves to the next question in the quiz."""
    quiz_data = get_current_quiz()
    if not quiz_data:
        return redirect(url_for("index"))

    quiz_data["current_index"] += 1
    save_current_quiz(quiz_data)
    return redirect(url_for("quiz"))


@app.route("/delete_question", methods=["POST"])
def delete_question():
    """Deletes the current question permanently from the quiz."""
    quiz_data = get_current_quiz()
    if not quiz_data:
        return redirect(url_for("index"))

    questions = quiz_data["questions"]
    idx = quiz_data["current_index"]

    if 0 <= idx < len(questions):
        questions.pop(idx)

    data["categories"][quiz_data["category"]] = questions
    write_json_to_bin(data)  # Update JSONBin.io with the new data

    save_current_quiz(quiz_data)
    return redirect(url_for("quiz"))


@app.route("/back_to_main", methods=["POST"])
def back_to_main():
    """Clears the quiz session and returns to the main menu."""
    session.pop("quiz", None)
    return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Allows the user to customize the quiz appearance."""
    current_style = get_style()

    if request.method == "POST":
        new_style = {
            "bg_color": request.form.get("bg_color", current_style["bg_color"]),
            "text_color": request.form.get("text_color", current_style["text_color"]),
            "font_size": int(request.form.get("font_size", current_style["font_size"]))
        }
        session["style"] = new_style
        return redirect(url_for("index"))

    return render_template("settings.html", style=current_style)


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def open_browser():
    """Open the default web browser at the specified URL."""
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Optionally, open the browser automatically (uncomment next line if desired)
    # open_browser()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
