import logging
import os
import json
from langchain_groq import ChatGroq
import chainlit as cl  # Import Chainlit for callback handling

# Set up logging
logging.basicConfig(level=logging.INFO)

# Log initial message
logging.info("Initializing chatbot...")
CHATGROQ_API_KEY= "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"
# Define the model and API key
model = "llama3-groq-70b-8192-tool-use-preview"
api_key = os.environ.get("CHATGROQ_API_KEY")  # Assuming the API key is stored in an environment variable

# Initialize the ChatGroq client with the API key
client = ChatGroq(
    model=model,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=api_key  # Pass the API key to the client
)

# Main chatbot class
class ChatBot:
    def __init__(self, system, tools, tool_functions):
        self.system = system
        self.tools = tools
        self.exclude_functions = ["plot_chart"]
        self.tool_functions = tool_functions
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": f"{message}"})
        response_message = self.execute()
        if response_message:
            self.messages.append({"role": "assistant", "content": response_message})

        logging.info(f"User message: {message}")
        logging.info(f"Assistant response: {response_message}")

        return response_message

    def execute(self):
        completion = client.invoke(self.messages)  # Use the ChatGroq client to get the response
        assistant_message = completion.content  # Access the content of the AIMessage directly
        return assistant_message

# Define the callback for handling chat messages
@cl.on_message
def handle_message(message):
    bot = ChatBot(system="You are a helpful assistant.", tools=[], tool_functions={})
    response = bot(message.content)
    cl.send_message(response)

# Optional: Define a callback for chat start if needed
@cl.on_chat_start
def on_chat_start():
    cl.send_message("Welcome to the chatbot! How can I assist you today?")

# Example usage (you can remove this section if you don't need it in your code)
if __name__ == "__main__":
    bot = ChatBot(system="You are a helpful assistant.", tools=[], tool_functions={})
    response = bot("What is the weather today?")
    print(response)
