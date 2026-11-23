# Terminal AI Assistant

A simple terminal chat assistant for local LLMs. It works with any OpenAI-compatible endpoint (tested with [Ollama](https://ollama.com)) and lets you manage a global system prompt and reusable roles from an interactive menu.

## Features

- Interactive nested menu
- Global system prompt, saved between runs
- Roles (create, view, edit, delete) that are added on top of the system prompt
- Multi-line prompt editing in the terminal
- Markdown-rendered replies

## Setup

```bash
git clone https://github.com/onatceltik/AI_Agent_Project.git
cd  AI_Agent_Project
pip install openai python-dotenv rich prompt_toolkit
```

Create a `.env` file next to `ai_assistant.py`:

```env
BASE_URL=http://localhost:11434/v1
API_KEY=ollama
MODEL=qwen3:8b
```

## Usage

```bash
python ai_assistant.py
```

Pick menu options by number:

```
Menu
├── Chat
├── System settings  (view / edit the global system prompt)
└── Role settings    (create / view / edit / delete roles)
```

- **Editing prompts:** Enter adds a line, Esc then Enter saves, Ctrl+C cancels.
- **Chatting:** press Ctrl+C to end the chat and go back to the menu.
- **Roles:** the selected role is appended to the system prompt. Choose "No role" to use the system prompt alone.

Your system prompt and roles are saved in a `system_files/` folder next to the script.