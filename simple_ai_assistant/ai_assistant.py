import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# INITIALIZATION

# load config from .env file
load_dotenv()

# Create a clien that communicates with Ollama
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

console = Console()

# Send a question to the AI model
def ask_to_model(client, message):
    return client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

def chat_loop():
    while True:
        user_prompt = input("\n> ")

        if user_prompt:
            with console.status("..."):
                model_response = ask_to_model(client, user_prompt)

        if model_response:
            console.print(Panel(
                Markdown(model_response.choices[0].message.content),
                title=os.getenv("MODEL"),
                border_style="cyan"
            ))

if __name__ == "__main__":
    chat_loop()