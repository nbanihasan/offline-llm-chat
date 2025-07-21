# Offline LLM Chat GUI

This repository contains a simple Python GUI application for chatting with local models served by [Ollama](https://ollama.ai/).

## Requirements

- Python 3
- `requests` library (`pip install requests`)
- Running `ollama serve` on your machine (Ollama should already be installed on Windows)

## Usage

1. Start the Ollama server in a terminal:

   ```bash
   ollama serve
   ```

2. Run the GUI application:

   ```bash
   python ollama_chat_gui.py
   ```

The app lists installed models (via `ollama list`) and lets you select one to chat with. Conversations are saved under the `logs/` directory.
