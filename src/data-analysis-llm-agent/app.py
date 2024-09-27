import logging
import os
import json

from langchain_groq import ChatGroq

# Set up logging
logging.basicConfig(level=logging.INFO)

# Log initial message
logging.info("Initializing chatbot...")

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
        if response_message.content:
            self.messages.append({"role": "assistant", "content": response_message.content})

        logging.info(f"User message: {message}")
        logging.info(f"Assistant response: {response_message.content}")

        return response_message

    def execute(self):
        completion = client.invoke(self.messages)  # Use the ChatGroq client to get the response
        assistant_message = completion.content  # Access the content of the AIMessage directly
        return assistant_message
        
    def call_function(self, tool_call):
        function_name = tool_call.function.name
        function_to_call = self.tool_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        logging.info(f"Calling {function_name} with {function_args}")
        function_response = function_to_call(**function_args)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response,
        }

    def call_functions(self, tool_calls):
        function_responses = [self.call_function(tool_call) for tool_call in tool_calls]
        responses_in_str = [{**item, "content": str(item["content"])} for item in function_responses]
        for res in function_responses:
            logging.info(f"Tool Call: {res}")
        self.messages.extend(responses_in_str)
        response_message = self.execute()
        return response_message, function_responses
