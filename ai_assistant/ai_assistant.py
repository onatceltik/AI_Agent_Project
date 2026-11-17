import os
import json
import prompt_toolkit
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from pathlib import Path


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
        ("Create a new role", lambda: create_role(console, system_settings)),
        ("View roles",        lambda: view_roles(console, system_settings)),
        ("Edit a role",       lambda: console.print("Not implemented yet!")),
        ("Delete a role",     lambda: console.print("Not implemented yet!"))
    ])
#endregion

#region MENU HELPERS
def edit_text(console, curr_text=""):
    console.print("[dim]Enter adds a new line. Esc then Enter saves. Ctrl+C cancels.[/dim]")
    try:
        return prompt_toolkit.prompt(
            "", multiline=True, default=curr_text
        )
    except (KeyboardInterrupt, EOFError):
        return None

def print_warning(console, text):
    console.print(Panel(f"[yellow]{text}[/yellow]"))

def print_ok(console, text):
    console.print(Panel(f"[green]{text}[/green]"))

def print_error(console, text):
    console.print(Panel(f"[red]{text}[/red]"))
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
        print_warning(console, "No System Prompt is given")

def edit_system_prompt(console, system_settings):
    current_system_prompt = get_system_prompt(system_settings)
    new_system_prompt_text = edit_text(console, current_system_prompt)
    
    if new_system_prompt_text:
        set_system_prompt(system_settings, new_system_prompt_text)
        print_ok(console, "System prompt updated")
    else:
        print_warning(console, "Cancelled, nothing changed")
#endregion

#region ROLE FUNCS
def get_role_dict(console, system_settings):
    role_dict_path = system_settings["role_dict_path"]
    try:
        role_dict = json.loads(role_dict_path.read_text(encoding="utf-8"))
        return role_dict
    except FileNotFoundError:
        role_dict_path.parent.mkdir(parents=True, exist_ok=True)
        role_dict_path.write_text(json.dumps({}), encoding="utf-8")
        return {}
    except json.JSONDecodeError:
        corrupt_file_path = role_dict_path.with_suffix(".corrupt_json")
        role_dict_path.replace(corrupt_file_path)
        role_dict_path.write_text(json.dumps({}), encoding="utf-8")
        print_warning(console, "File holding role information was corrupt and a new one created!")
        return {}

def save_role_dict(system_settings, new_role_dict):
    try:
        role_dict_path = system_settings["role_dict_path"]
        role_dict_path.parent.mkdir(parents=True, exist_ok=True)
        role_dict_path.write_text(json.dumps(
            new_role_dict, indent=2, ensure_ascii=False
        ), encoding="utf-8")
        return (True, "")
    except Exception as e:
        return (False, str(e))

def view_roles(console, system_settings):
    role_dict = get_role_dict(console, system_settings)
    if not role_dict:
        print_warning(console, "No role defined yet!")
        return
    else:
        roles_table = Table(box=None, show_header=False)
        for r_name, r_def in role_dict.items():
            flat_prompt = " ".join(r_def.split())
            roles_table.add_row(f"[bold]{r_name}[/bold]", ": ", Text(flat_prompt[:50] + "..."))

    console.print(Panel(roles_table, title="Roles", border_style="cyan"))

def create_role(console, system_settings):
    role_dict = get_role_dict(console, system_settings)

    try:
        while True:
            role_name = Prompt.ask("Role name").strip().lower()
            if not role_name:
                print_warning(console, "Role name cannot be empty!")
            elif role_name in role_dict.keys():
                print_warning(console, "There is already a role with the same name!")
            else:
                break
    except KeyboardInterrupt:
        console.print("\n")
        print_warning(console, "Cancelled")
        return
    
    while True:
        role_definition = edit_text(console)
        if not role_definition:
            print_warning(console, "Role definition cannot be empty!")
            return
        else:
            break

    role_dict[role_name] = role_definition
    is_saved, save_status = save_role_dict(system_settings, role_dict)
    if is_saved:
        print_ok(console, f"Role '{role_name}' created successfully!")
    else:
        print_error(save_status)
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
        "role_dict_path": BASE / "system_files" / "role_dict",
    }

    console = Console()
    main_menu(console, client, model, system_settings)

if __name__ == "__main__":
    main()