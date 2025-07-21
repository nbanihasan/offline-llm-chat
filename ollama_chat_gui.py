import os
import subprocess
import json
import threading
from pathlib import Path

import requests
from PyQt5 import QtWidgets, QtCore

LOG_DIR = Path("logs")
OLLAMA_HOST = "http://localhost:11434"
REMOTE_MODELS_API = "https://ollama.ai/api/models"


def list_installed_models():
    """Return a list of installed models using `ollama list`."""
    try:
        output = subprocess.check_output(["ollama", "list"], text=True)
    except Exception:
        return []
    lines = output.strip().splitlines()
    models = []
    for line in lines[1:]:
        if line:
            models.append(line.split()[0])
    return models


def fetch_remote_models():
    """Fetch available models from Ollama library."""
    try:
        resp = requests.get(REMOTE_MODELS_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("models", [])
    except Exception:
        return []


def install_model(name):
    subprocess.run(["ollama", "pull", name])


def ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)


def log_message(conversation, speaker, text):
    ensure_log_dir()
    fname = LOG_DIR / f"{conversation}.txt"
    with open(fname, "a", encoding="utf-8") as f:
        timestamp = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        f.write(f"[{timestamp}] {speaker}: {text}\n")


def list_logs():
    ensure_log_dir()
    files = sorted(LOG_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [f.stem for f in files]


def load_log(name):
    path = LOG_DIR / f"{name}.txt"
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ModelDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Available Models")
        self.resize(400, 300)
        layout = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget()
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.install_btn = QtWidgets.QPushButton("Install")
        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.install_btn)
        layout.addLayout(btns)

        self.refresh_btn.clicked.connect(self.load_models)
        self.install_btn.clicked.connect(self.install_selected)
        self.load_models()

    def load_models(self):
        self.list.clear()
        installed = set(list_installed_models())
        models = fetch_remote_models()
        for m in models:
            name = m.get("name")
            size = m.get("size", "?")
            text = f"{name} ({size})"
            item = QtWidgets.QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, name)
            if name in installed:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
                item.setText(text + " - installed")
            self.list.addItem(item)

    def install_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.UserRole)
        install_model(name)
        self.load_models()


class ChatWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama Chat")
        self.resize(800, 600)

        self.current_conversation = None
        self.models = list_installed_models()
        self.current_model = self.models[0] if self.models else ""

        self.init_ui()
        self.refresh_logs()

    def init_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)

        # Left sidebar for conversations
        sidebar = QtWidgets.QVBoxLayout()
        self.log_list = QtWidgets.QListWidget()
        sidebar.addWidget(self.log_list)
        new_btn = QtWidgets.QPushButton("New Chat")
        sidebar.addWidget(new_btn)
        main_layout.addLayout(sidebar, 1)

        # Right side for chat
        right = QtWidgets.QVBoxLayout()
        top = QtWidgets.QHBoxLayout()
        self.model_box = QtWidgets.QComboBox()
        self.model_box.addItems(self.models)
        top.addWidget(QtWidgets.QLabel("Model:"))
        top.addWidget(self.model_box)
        self.model_btn = QtWidgets.QPushButton("Models...")
        top.addWidget(self.model_btn)
        right.addLayout(top)

        self.chat_view = QtWidgets.QTextEdit(readOnly=True)
        right.addWidget(self.chat_view, 1)

        bottom = QtWidgets.QHBoxLayout()
        self.entry = QtWidgets.QLineEdit()
        self.send_btn = QtWidgets.QPushButton("Send")
        bottom.addWidget(self.entry, 1)
        bottom.addWidget(self.send_btn)
        right.addLayout(bottom)

        main_layout.addLayout(right, 3)

        # signals
        new_btn.clicked.connect(self.new_chat)
        self.log_list.itemClicked.connect(self.load_selected_log)
        self.send_btn.clicked.connect(self.send_message)
        self.entry.returnPressed.connect(self.send_message)
        self.model_btn.clicked.connect(self.open_model_dialog)

    def refresh_logs(self):
        self.log_list.clear()
        for name in list_logs():
            self.log_list.addItem(name)

    def load_selected_log(self, item):
        name = item.text()
        self.current_conversation = name
        text = load_log(name)
        self.chat_view.setPlainText(text)

    def new_chat(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "New Chat", "Conversation name:")
        if ok and name:
            self.current_conversation = name
            self.chat_view.clear()
            log_message(name, "system", "Started conversation")
            self.refresh_logs()
            items = self.log_list.findItems(name, QtCore.Qt.MatchExactly)
            if items:
                self.log_list.setCurrentItem(items[0])

    def open_model_dialog(self):
        dlg = ModelDialog(self)
        dlg.exec_()
        self.models = list_installed_models()
        self.model_box.clear()
        self.model_box.addItems(self.models)

    def append_chat(self, speaker, text):
        self.chat_view.append(f"<b>{speaker}:</b> {text}")
        if self.current_conversation:
            log_message(self.current_conversation, speaker, text)

    def send_message(self):
        text = self.entry.text().strip()
        if not text or not self.current_conversation:
            return
        self.entry.clear()
        self.append_chat("You", text)
        model = self.model_box.currentText()
        thread = threading.Thread(target=self._request_response, args=(model, text), daemon=True)
        thread.start()

    def _request_response(self, model, prompt):
        try:
            url = f"{OLLAMA_HOST}/api/generate"
            payload = {"model": model, "prompt": prompt, "stream": False}
            resp = requests.post(url, json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response", "")
        except Exception as e:
            response = f"Error: {e}"
        QtCore.QMetaObject.invokeMethod(self, "_append_response", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, response))

    @QtCore.pyqtSlot(str)
    def _append_response(self, text):
        self.append_chat("Bot", text)


def main():
    app = QtWidgets.QApplication([])
    window = ChatWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
