import logging
import os
import json
from langchain_groq import ChatGroq
import asyncio

logging.info(f"User message")

# Initialize the synchronous ChatGroq client
client = ChatGroq(
    model="llama3-groq-70b-8192-tool-use-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Function to call the ChatGroq client in a separate thread
async def chat_with_groq(user_message):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
        messages=[{"role": "user", "content": user_message}]
    ))
    return response.choices[0].message.content

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
        self.messages.append({"role": "user", "content": f"""{message}"""})
        response_message = self.execute()
        # for function call sometimes this can be empty
        if response_message.content:
            self.messages.append({"role": "assistant", "content": response_message.content})

        logging.info(f"User message: {message}")
        logging.info(f"Assistant response: {response_message.content}")

        return response_message

    def execute(self):
        # Invoke the ChatGroq model
        completion = client.invoke("\n".join(
            f"{msg['role']}: {msg['content']}" for msg in self.messages
        ))
        
        print(completion)  # Log or print the response for debugging
        assistant_message = {
            "role": "assistant",
            "content": completion  # Adjust according to the format of the response
        }

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
        # Make function calls in sequence
        function_responses = [self.call_function(tool_call) for tool_call in tool_calls]

        # Extend conversation with all function responses
        responses_in_str = [{**item, "content": str(item["content"])} for item in function_responses]

        # Log each tool call object separately
        for res in function_responses:
            logging.info(f"Tool Call: {res}")

        self.messages.extend(responses_in_str)

        response_message = self.execute()
        return response_message, function_responses
