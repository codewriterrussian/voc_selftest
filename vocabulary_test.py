import sys
import os
import json
import random
import subprocess  # <-- for TTS
import tempfile
import requests    # <-- for JSONBin API calls
import re

from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QRadioButton,
    QPushButton, QButtonGroup, QComboBox, QDialog, QHBoxLayout,
    QLineEdit, QSpinBox, QColorDialog
)
from PyQt5.QtCore import Qt

# -----------------------------------------------------------------------------
# TTS Settings
# -----------------------------------------------------------------------------
tts_engine = '/Users/bladeruuner/opt/anaconda3/envs/epub/bin/edge-tts'

CATEGORY_TO_VOICE = {
    "russian": "ru-RU-DmitryNeural",
    "english": "en-GB-LibbyNeural",
    "dutch": "nl-NL-ColetteNeural",
    # etc...
}

def sanitize_text(text):
    """ Remove common markdown symbols (*, _, #, `) from text. """
    return re.sub(r"[\*\_#`]", "", text)

def speak_text(text, voice):
    if not text:
        return
    text = sanitize_text(text)  # Clean text before processing
    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            temp_audio_path = tmp_file.name

        tts_command = [
            tts_engine,
            "--text", text,
            "--voice", voice,
            "--write-media", temp_audio_path
        ]
        subprocess.run(tts_command, check=True)

        play_command = ["ffplay", "-autoexit", "-nodisp", temp_audio_path]
        subprocess.run(play_command, check=True)

    except Exception as e:
        print("Error running TTS command:", e)
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as cleanup_error:
                print("Error removing temporary file:", cleanup_error)

# -----------------------------------------------------------------------------
# JSONBin Settings
# -----------------------------------------------------------------------------
JSONBIN_API_KEY = "$2a$10$emdSh/thUg5xTvyY9z89UOy.BurV3ykvVjjUjodpvnJe2Xqc/WAAm"
JSONBIN_BIN_ID = "67a87edbacd3cb34a8db4700"
JSONBIN_BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

# -----------------------------------------------------------------------------
# Global Constants
# -----------------------------------------------------------------------------
BUTTON_STYLE = """
    font-size: 16px;
    color: white;
    background-color: #212121;
"""
ICON_WARNING = "⚠️"
ICON_INFO = "ℹ️"

# -----------------------------------------------------------------------------
# Functions for JSONBin I/O
# -----------------------------------------------------------------------------
def load_data_from_jsonbin():
    """
    Load JSON data from JSONBin by issuing a GET request to the bin's latest version.
    """
    headers = {
        "X-Master-Key": JSONBIN_API_KEY
    }
    url = f"{JSONBIN_BASE_URL}/latest"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()["record"]
            print("Data loaded successfully from JSONBin.")
            return data
        else:
            print("Error loading data from JSONBin:", response.text)
            return {}
    except Exception as e:
        print("Error loading data from JSONBin:", e)
        return {}

def update_jsonbin_data(data):
    """
    Update the JSONBin bin with new data via a PUT request.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_API_KEY
    }
    try:
        response = requests.put(JSONBIN_BASE_URL, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print("JSONBin updated successfully!")
        else:
            print("Update failed:", response.text)
    except Exception as e:
        print("Error updating JSONBin:", e)

# -----------------------------------------------------------------------------
# Custom Dialog Function
# -----------------------------------------------------------------------------
def show_custom_dialog(parent, title, message, icon="", buttons=None):
    if buttons is None:
        buttons = ["OK"]

    class CustomDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.clicked_button_label = None

        def keyPressEvent(self, event):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                self.clicked_button_label = buttons[0]
                self.accept()
            else:
                super().keyPressEvent(event)

    dlg = CustomDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setModal(True)
    dlg.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
    dlg.setFocusPolicy(Qt.StrongFocus)
    dlg.setFocus()

    layout = QVBoxLayout(dlg)

    icon_text_layout = QHBoxLayout()
    if icon:
        icon_label = QLabel()
        icon_label.setStyleSheet("font-size: 40px; color: yellow;")
        icon_label.setText(icon)
        icon_text_layout.addWidget(icon_label, alignment=Qt.AlignTop)

    msg_label = QLabel()
    msg_label.setStyleSheet("font-size: 16px;")
    # Also sanitize the dialog message:
    msg_label.setText(sanitize_text(message))
    msg_label.setWordWrap(True)
    icon_text_layout.addWidget(msg_label)
    layout.addLayout(icon_text_layout)

    button_layout = QHBoxLayout()
    button_layout.addStretch(1)
    clicked_button = {"label": None}

    def on_button_click(label):
        clicked_button["label"] = label
        dlg.clicked_button_label = label
        dlg.accept()

    for label in buttons:
        btn = QPushButton(label)
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(lambda _, x=label: on_button_click(x))
        button_layout.addWidget(btn)
    button_layout.addStretch(1)
    layout.addLayout(button_layout)

    dlg.exec_()
    return dlg.clicked_button_label or clicked_button["label"]

# -----------------------------------------------------------------------------
# StyleSettingsWindow - for changing style across the entire app
# -----------------------------------------------------------------------------
class StyleSettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Style Settings")
        self.resize(400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(18)
        layout.addWidget(QLabel("Font Size:"))
        layout.addWidget(self.font_size_spin)

        text_color_box = QHBoxLayout()
        text_color_label = QLabel("Text Color:")
        self.text_color_input = QLineEdit("#ffffff")
        text_color_box.addWidget(text_color_label)
        text_color_box.addWidget(self.text_color_input)
        text_color_btn = QPushButton("Pick")
        text_color_btn.setStyleSheet(BUTTON_STYLE)
        text_color_btn.clicked.connect(self.pick_text_color)
        text_color_box.addWidget(text_color_btn)
        layout.addLayout(text_color_box)

        bg_color_box = QHBoxLayout()
        bg_color_label = QLabel("Background Color:")
        self.bg_color_input = QLineEdit("#555555")
        bg_color_box.addWidget(bg_color_label)
        bg_color_box.addWidget(self.bg_color_input)
        bg_color_btn = QPushButton("Pick")
        bg_color_btn.setStyleSheet(BUTTON_STYLE)
        bg_color_btn.clicked.connect(self.pick_bg_color)
        bg_color_box.addWidget(bg_color_btn)
        layout.addLayout(bg_color_box)

        btn_box = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(BUTTON_STYLE)
        apply_btn.clicked.connect(self.apply_style)
        btn_box.addWidget(apply_btn)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(BUTTON_STYLE)
        close_btn.clicked.connect(self.close)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def pick_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color_input.setText(color.name())

    def pick_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color_input.setText(color.name())

    def apply_style(self):
        font_size = self.font_size_spin.value()
        text_color = self.text_color_input.text().strip()
        bg_color = self.bg_color_input.text().strip()
        self.main_window.apply_custom_style(bg_color, text_color, font_size)

# -----------------------------------------------------------------------------
# CategorySelectionWindow - "Main Page"
# -----------------------------------------------------------------------------
class CategorySelectionWindow(QWidget):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Select a Category")
        self.resize(1000, 600)
        self.data = data
        self.categories = data.get("categories", {})
        self.current_bg_color = "#555555"
        self.current_text_color = "#FFFFFF"
        self.current_font_size = 18
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        self.label = QLabel("Please select a language/category:")
        layout.addWidget(self.label, alignment=Qt.AlignLeft)
        self.combo_box = QComboBox()
        layout.addWidget(self.combo_box, alignment=Qt.AlignLeft)
        for cat_name in self.categories.keys():
            self.combo_box.addItem(cat_name)

        start_button = QPushButton("Start Quiz")
        start_button.setStyleSheet(BUTTON_STYLE)
        start_button.clicked.connect(self.start_quiz)
        layout.addWidget(start_button, alignment=Qt.AlignLeft)

        exit_button = QPushButton("Exit Program")
        exit_button.setStyleSheet(BUTTON_STYLE)
        exit_button.clicked.connect(self.exit_program)
        layout.addWidget(exit_button, alignment=Qt.AlignLeft)

        settings_button = QPushButton("Settings")
        settings_button.setStyleSheet(BUTTON_STYLE)
        settings_button.clicked.connect(self.open_style_settings)
        layout.addWidget(settings_button, alignment=Qt.AlignLeft)

        self.apply_custom_style(self.current_bg_color, self.current_text_color, self.current_font_size)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.exit_program()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.start_quiz()
        else:
            super().keyPressEvent(event)

    def start_quiz(self):
        selected_category = self.combo_box.currentText()
        if not selected_category:
            show_custom_dialog(self, "No Category", "Please select a category.", icon=ICON_WARNING)
            return

        questions = self.categories.get(selected_category, [])
        if not questions:
            show_custom_dialog(
                self,
                "No Questions",
                f"No questions found for category '{selected_category}'.",
                icon=ICON_WARNING
            )
            return

        random.shuffle(questions)
        tts_voice = CATEGORY_TO_VOICE.get(selected_category.lower(), "en-GB-LibbyNeural")
        self.quiz_window = QuizWindow(questions, selected_category, tts_voice, self)
        self.quiz_window.show()
        self.hide()

    def exit_program(self):
        QApplication.instance().quit()

    def open_style_settings(self):
        self.style_window = StyleSettingsWindow(self)
        self.style_window.show()

    def apply_custom_style(self, bg_color, text_color, font_size):
        self.current_bg_color = bg_color
        self.current_text_color = text_color
        self.current_font_size = font_size

        global_style = f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                font-size: {font_size}px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator::unchecked {{
                border: 2px solid {text_color};
                background-color: {bg_color};
            }}
            QRadioButton::indicator::checked {{
                background-color: {text_color};
            }}
            QPushButton {{
                font-size: 16px;
                color: white; 
                background-color: #212121;
            }}
        """
        QApplication.instance().setStyleSheet(global_style)

    def upload_data_on_exit(self):
        """
        Call this method on program exit to update JSONBin with any changes.
        """
        update_jsonbin_data(self.data)

# -----------------------------------------------------------------------------
# QuizWindow
# -----------------------------------------------------------------------------
class QuizWindow(QWidget):
    def __init__(self, questions, category_name, tts_voice, main_window):
        super().__init__()
        self.setWindowTitle(f"Vocabulary Quiz - {category_name}")
        self.resize(1000, 600)
        self.questions = questions
        self.current_question_index = 0
        self.category_name = category_name
        self.main_window = main_window
        self.tts_voice = tts_voice
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.init_ui()

        if self.questions:
            self.show_question(0)
        else:
            show_custom_dialog(
                self,
                "No Questions",
                "No questions found for this category.",
                icon=ICON_WARNING
            )
            self.disable_quiz_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        self.question_label = QLabel("Question will appear here.")
        layout.addWidget(self.question_label)

        self.button_group = QButtonGroup(self)
        self.radio_buttons = []
        for i in range(4):
            row_layout = QHBoxLayout()
            rb = QRadioButton()
            self.button_group.addButton(rb)
            self.radio_buttons.append(rb)
            speak_btn = QPushButton("Speak")
            speak_btn.setStyleSheet(BUTTON_STYLE)
            speak_btn.clicked.connect(lambda _, idx=i: self.speak_option(idx))
            row_layout.addWidget(rb)
            row_layout.addWidget(speak_btn)
            layout.addLayout(row_layout)

        self.next_button = QPushButton("Next Question")
        self.next_button.setStyleSheet(BUTTON_STYLE)
        self.next_button.clicked.connect(self.check_and_next)
        layout.addWidget(self.next_button)

        self.delete_button = QPushButton("Delete This Question")
        self.delete_button.setStyleSheet(BUTTON_STYLE)
        self.delete_button.clicked.connect(self.delete_question)
        layout.addWidget(self.delete_button)

        self.back_button = QPushButton("Back to Main")
        self.back_button.setStyleSheet(BUTTON_STYLE)
        self.back_button.clicked.connect(self.back_to_main)
        layout.addWidget(self.back_button)

    def show_question(self, index):
        # -- Reset state of buttons before showing a new question --
        self.button_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
            rb.setStyleSheet("")
            rb.hide()
        self.button_group.setExclusive(True)

        # Optionally, also ensure the Next button is not stuck:
        self.next_button.setDown(False)
        self.next_button.setChecked(False)
        self.next_button.clearFocus()

        # -- Now populate the next question --
        q_data = self.questions[index]
        question_text = sanitize_text(q_data.get("question", ""))
        self.question_label.setText(question_text)

        options_dict = q_data.get("options", {})
        sorted_keys = sorted(options_dict.keys())
        for i, key in enumerate(sorted_keys):
            if i < len(self.radio_buttons):
                option_text = sanitize_text(options_dict[key])
                text = f"{key}) {option_text}"
                self.radio_buttons[i].setText(text)
                self.radio_buttons[i].show()

    def speak_option(self, index):
        full_text = self.radio_buttons[index].text()
        # The text is something like "A) Some Option Text"
        if ") " in full_text:
            just_answer_text = full_text.split(") ", 1)[1].strip()
        else:
            just_answer_text = full_text
        speak_text(just_answer_text, self.tts_voice)

    def check_and_next(self):
        if not self.questions:
            return

        selected_rb = self.button_group.checkedButton()
        if not selected_rb:
            show_custom_dialog(
                self,
                "No Selection",
                "Please select an option before continuing.",
                icon=ICON_WARNING
            )
            return

        selected_text = selected_rb.text()
        selected_letter = selected_text.split(")")[0].strip()

        q_data = self.questions[self.current_question_index]
        correct_letter = q_data.get("correct_answer", "").strip()

        # Sanitize the explanation text
        explanation = sanitize_text(q_data.get("explanation", ""))

        if selected_letter == correct_letter:
            selected_rb.setStyleSheet("font-size: 16px; color: green; font-weight: bold;")
            show_custom_dialog(
                self,
                "Correct",
                explanation or "Good job!",
                icon=ICON_INFO,
                buttons=["OK"]
            )
        else:
            selected_rb.setStyleSheet("font-size: 16px; color: red; font-weight: bold;")
            # Highlight the correct radio button in green
            for rb in self.radio_buttons:
                if rb.text().startswith(correct_letter + ")"):
                    rb.setStyleSheet("font-size: 16px; color: green; font-weight: bold;")
                    break
            msg = f"正確答案是：{correct_letter}\n\n{explanation}"
            show_custom_dialog(self, "Incorrect", msg, icon=ICON_WARNING, buttons=["OK"])

        self.go_next_question()

    def go_next_question(self):
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            self.show_question(self.current_question_index)
        else:
            show_custom_dialog(
                self,
                "Quiz Finished",
                "You have reached the end of the quiz!",
                icon=ICON_INFO,
                buttons=["OK"]
            )
            self.back_to_main()


    def delete_question(self):
        if not self.questions:
            return

        answer = show_custom_dialog(
            self,
            "Delete Question?",
            "Are you sure you want to PERMANENTLY delete this question from the JSON data?",
            icon=ICON_WARNING,
            buttons=["Yes", "No"]
        )
        if answer != "Yes":
            return

        # Remove from in-memory data only
        self.questions.pop(self.current_question_index)
        self.main_window.categories[self.category_name] = self.questions
        self.main_window.data["categories"] = self.main_window.categories

        if self.current_question_index >= len(self.questions):
            show_custom_dialog(
                self,
                "Deleted",
                "Question deleted. No more questions remain.",
                icon=ICON_INFO,
                buttons=["OK"]
            )
            self.back_to_main()
        else:
            self.show_question(self.current_question_index)

    def back_to_main(self):
        if self.main_window is not None:
            self.main_window.show()
        self.close()

    def disable_quiz_ui(self):
        self.question_label.setText("No more questions.")
        for rb in self.radio_buttons:
            rb.hide()
        self.next_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_1 and len(self.radio_buttons) > 0:
            self.radio_buttons[0].setChecked(True)
        elif key == Qt.Key_2 and len(self.radio_buttons) > 1:
            self.radio_buttons[1].setChecked(True)
        elif key == Qt.Key_3 and len(self.radio_buttons) > 2:
            self.radio_buttons[2].setChecked(True)
        elif key == Qt.Key_4 and len(self.radio_buttons) > 3:
            self.radio_buttons[3].setChecked(True)
        elif key == Qt.Key_Space:
            self.check_and_next()
        else:
            super().keyPressEvent(event)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set a dark palette.
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))
    dark_palette.setColor(QtGui.QPalette.WindowText, Qt.white)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QtGui.QPalette.Text, Qt.white)
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(55, 55, 55))
    dark_palette.setColor(QtGui.QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QtGui.QPalette.BrightText, Qt.red)
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    # Slightly bigger base font.
    font = QtGui.QFont()
    font.setPointSize(20)
    app.setFont(font)

    # Load data from JSONBin.
    data = load_data_from_jsonbin()
    categories = data.get("categories", {})

    if not categories:
        error_win = QWidget()
        error_win.setWindowTitle("Error")
        layout = QVBoxLayout(error_win)
        lbl = QLabel("No categories found in the JSON data.")
        lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(lbl)
        error_win.show()
        sys.exit(app.exec_())
    else:
        window = CategorySelectionWindow(data)
        window.show()
        # Connect the application's exit signal to upload the updated data.
        app.aboutToQuit.connect(window.upload_data_on_exit)
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
