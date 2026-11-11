import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


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

def chat_loop(client, model, console):
    
    chat_history = []
    while True:
        try:
            user_prompt = input("\n> ")
        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!")

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
    chat_loop(client, model, Console())


if __name__ == "__main__":
    main()