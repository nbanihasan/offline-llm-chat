# Offline LLM Chat GUI

This project provides a small desktop client for interacting with local models served by [Ollama](https://ollama.ai/).  The application is built with **PyQt5** and stores chat logs on disk.

## Requirements

- Python 3
- `PyQt5` and `requests` (install via `pip install PyQt5 requests`)
- The Ollama server running locally (`ollama serve`)

## Usage

1. Start the Ollama server in a terminal:

   ```bash
   ollama serve
   ```

2. Launch the GUI:

   ```bash
   python ollama_chat_gui.py
   ```

The left sidebar shows previous conversations in most-recent order.  New chats can be created from the sidebar.  Use the **Models...** button to browse available models from Ollama's library and install them directly from the app.

Chat transcripts are stored in the `logs/` directory.
