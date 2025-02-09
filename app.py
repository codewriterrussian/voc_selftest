import sys
import os
import json
import random
import webbrowser
import threading

from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# -----------------------------------------------------------------------------
# Global Constants
# -----------------------------------------------------------------------------
JSON_FILE = "questions.json"

# -----------------------------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "some_secret_key_for_session"  # Needed for sessions in Flask

# Load data once at startup
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"categories": {}}, f, indent=4, ensure_ascii=False)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

categories = data.get("categories", {})

# Default style
DEFAULT_STYLE = {
    "bg_color": "#555555",
    "text_color": "#ffffff",
    "font_size": 18
}

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def write_json_to_file(data_dict):
    """Writes the in-memory data back to the JSON file."""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)


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
    write_json_to_file(data)

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
# Main Entry Point (without PyQt6)
# -----------------------------------------------------------------------------
def open_browser():
    """Open the default web browser at the specified URL."""
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Optional: Start a thread to open the browser automatically
    threading.Timer(1.0, open_browser).start()

    # Run the Flask app on port 5000
    app.run(port=5000)
