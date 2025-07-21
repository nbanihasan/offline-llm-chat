import os
import subprocess
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, filedialog
import requests
from datetime import datetime

# Default models that might be available from Ollama's library
DEFAULT_MODELS = [
    "llama2",
    "llama2:13b",
    "mistral",
    "codellama",
]

LOG_DIR = "logs"


def list_installed_models():
    """Return a list of models installed via `ollama list`."""
    try:
        output = subprocess.check_output(["ollama", "list"], text=True)
    except FileNotFoundError:
        messagebox.showerror("Error", "Ollama command not found. Ensure Ollama is installed and in PATH.")
        return []
    lines = output.strip().splitlines()
    models = []
    for line in lines[1:]:  # skip header
        if line:
            models.append(line.split()[0])
    return models


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_message(conversation, speaker, text):
    ensure_log_dir()
    filename = os.path.join(LOG_DIR, f"{conversation}.txt")
    with open(filename, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {speaker}: {text}\n")


def send_prompt(model, prompt):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to communicate with Ollama: {e}")
        return ""


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat")
        self.conversation_name = "conversation"
        self.installed_models = list_installed_models()
        self.models = sorted(set(DEFAULT_MODELS + self.installed_models))
        self.current_model = tk.StringVar(value=self.models[0] if self.models else "")

        self.setup_widgets()

    def setup_widgets(self):
        # Model selection
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(frame_top, text="Model:").pack(side=tk.LEFT)
        self.model_menu = tk.OptionMenu(frame_top, self.current_model, *self.models)
        self.model_menu.pack(side=tk.LEFT)

        tk.Button(frame_top, text="New Chat", command=self.new_chat).pack(side=tk.RIGHT)

        # Chat history
        self.chat_area = scrolledtext.ScrolledText(self.root, state="disabled", wrap=tk.WORD, width=80, height=20)
        self.chat_area.pack(padx=5, pady=5)

        # User input
        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(fill=tk.X, padx=5, pady=5)

        self.entry = tk.Entry(frame_bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        tk.Button(frame_bottom, text="Send", command=self.send_message).pack(side=tk.RIGHT)

    def new_chat(self):
        name = simpledialog.askstring("New Chat", "Enter a name for the conversation:")
        if name:
            self.conversation_name = name
            self.chat_area.config(state="normal")
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state="disabled")

    def append_chat(self, speaker, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{speaker}: {text}\n")
        self.chat_area.yview(tk.END)
        self.chat_area.config(state="disabled")
        log_message(self.conversation_name, speaker, text)

    def send_message(self, event=None):
        prompt = self.entry.get().strip()
        if not prompt:
            return
        self.entry.delete(0, tk.END)
        model = self.current_model.get()
        self.append_chat("You", prompt)
        response = send_prompt(model, prompt)
        if response:
            self.append_chat("Bot", response)


def main():
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
