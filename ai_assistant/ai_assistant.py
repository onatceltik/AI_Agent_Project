import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

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

def main_menu(console, client, model):
    run_menu(console, "Menu", [
        ("Chat", lambda: chat_loop(console, client, model)),
        ("System settings", lambda: system_settings_menu(console)),
        ("Role settings", lambda: role_settings_menu(console))
    ], back_label="Quit")

def system_settings_menu(console):
    run_menu(console, "System Settings", [
        ("View system prompt", console.print("Not implemented yet!")),
        ("Edit system prompt", console.print("Not implemented yet!")),
    ])

def role_settings_menu(console):
    run_menu(console, "Role Settings", [
        ("Create a new role", console.print("Not implemented yet!")),
        ("View roles", console.print("Not implemented yet!")),
        ("Edit a role", console.print("Not implemented yet!")),
        ("Delete a role", console.print("Not implemented yet!"))
    ])
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

def chat_loop(console, client, model):
    
    chat_history = []
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

    chat_history = []
    role=None

    console = Console()

    main_menu(console, client, model)
    # chat_loop(client, model, console)

if __name__ == "__main__":
    main()