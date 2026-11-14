import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from pathlib import Path
import prompt_toolkit


#region MENU
def run_menu(console, title, options, back_label="BACK"):
    """options is a list of (label, action) tuples.
    Loops until the user picks the back/quit entry."""
    while True:
        try:
            console.print(f"\n[bold cyan]{title}[/bold cyan]")

            for i, (label, _) in enumerate(options, start=1):
                console.print(f"  {i}. {label}")

            back_num = len(options) + 1
            console.print(f"  {back_num}. {back_label}")

            choice = Prompt.ask(
                "Choose",
                choices=[str(n) for n in range(1, back_num + 1)]
            )

            if int(choice) == back_num:
                return

            _, action = options[int(choice) - 1]
            action()
        
        except (KeyboardInterrupt, EOFError):
            break

def main_menu(console, client, model, system_settings):
    run_menu(console, "Menu", [
        ("Chat",            lambda: chat_loop(console, client, model, system_settings)),
        ("System settings", lambda: system_settings_menu(console, system_settings)),
        ("Role settings",   lambda: role_settings_menu(console, system_settings))
    ], back_label="Quit")

def system_settings_menu(console, system_settings):
    run_menu(console, "System Settings", [
        ("View system prompt", lambda: view_system_prompt(console, system_settings)),
        ("Edit system prompt", lambda: edit_system_prompt(console, system_settings)),
    ])

def role_settings_menu(console, system_settings):
    run_menu(console, "Role Settings", [
        ("Create a new role", lambda: console.print("Not implemented yet!")),
        ("View roles",        lambda: console.print("Not implemented yet!")),
        ("Edit a role",       lambda: console.print("Not implemented yet!")),
        ("Delete a role",     lambda: console.print("Not implemented yet!"))
    ])
#endregion

#region SYSTEM PROMPT FUNCS
def get_system_prompt(system_settings):
    system_prompt_path = system_settings["system_prompt_path"]
    try:
        system_prompt_text = system_prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        system_prompt_text = ""
    return system_prompt_text

def set_system_prompt(system_settings, new_prompt):
    system_prompt_path = system_settings["system_prompt_path"]
    system_prompt_path.parent.mkdir(parents=True, exist_ok=True)
    system_prompt_path.write_text(new_prompt, encoding="utf-8")

def view_system_prompt(console, system_settings):
    system_prompt_text = get_system_prompt(system_settings)
    if system_prompt_text != "":
        console.print(Panel(Text(system_prompt_text), title="System prompt"))
    else:
        console.print(Panel("[yellow]No System Prompt is given[/yellow]"))

def edit_system_prompt(console, system_settings):
    current_system_prompt = get_system_prompt(system_settings)

    console.print("[dim]Enter adds a new line. Esc then Enter saves. Ctrl+C cancels.[/dim]")
    try:
        new_system_prompt_text = prompt_toolkit.prompt(
            "", multiline=True, default=current_system_prompt
        )
    except (KeyboardInterrupt, EOFError):
        console.print("[yellow]Cancelled, nothing changed.[/yellow]")
        return
    
    set_system_prompt(system_settings, new_system_prompt_text)
    console.print("[green]System prompt updated.[/green]")
#endregion

#region CHAT
def ask_to_model(client, model, history):
    response = client.chat.completions.create(
        model=model,
        messages=history
    )
    return response.choices[0].message.content

def add_to_chat_history(history_list, role, message):
    history_list.append({
        "role": role,
        "content": message
    })

def chat_loop(console, client, model, system_settings):
    
    chat_history = []

    system_prompt_text = get_system_prompt(system_settings)
    if system_prompt_text:
        add_to_chat_history(
            chat_history,
            "system",
            system_prompt_text
        )

    while True:
        try:
            user_prompt = input("\n> ")
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print(Panel(
                "Goodbye!",
                title=model,
                border_style="cyan"
            ))
            break

        if not user_prompt:
            continue

        add_to_chat_history(chat_history, "user", user_prompt)

        try:
            with console.status("Thinking"):
                model_response = ask_to_model(client, model, chat_history)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            chat_history.pop() # Remove the latest user prompt from the chat history
            continue

        add_to_chat_history(chat_history, "assistant", model_response)
        console.print(Panel(
            Markdown(model_response),
            title=model,
            border_style="cyan"
        ))
#endregion

def main():
    
    load_dotenv() # load config from .env file

    model = os.getenv("MODEL")
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")

    if not all([model, base_url, api_key]):
        raise SystemExit("Missing MODEL, BASE_URL or API_KEY in .env")

    # Create a clien that communicates with Ollama
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    # System Related
    BASE = Path(__file__).resolve().parent
    system_settings = {
        "system_prompt_path": BASE / "system_files" / "system_prompt",
    }

    console = Console()
    main_menu(console, client, model, system_settings)

if __name__ == "__main__":
    main()