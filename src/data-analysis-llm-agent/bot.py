import logging
import os
import json
import openai  # Use synchronous OpenAI library for API calls

logging.info(f"User message")

model = "gpt-3.5-turbo-1106"
openai.api_key = os.getenv("OPENAI_API_KEY")


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
        # For function call, sometimes this can be empty
        if response_message.content:
            self.messages.append({"role": "assistant", "content": response_message.content})

        logging.info(f"User message: {message}")
        logging.info(f"Assistant response: {response_message.content}")

        return response_message

    def execute(self):
        # Make the synchronous API call
        completion = openai.ChatCompletion.create(
            model=model,
            messages=self.messages,
            tools=self.tools
        )
        print(completion)
        assistant_message = completion['choices'][0]['message']

        return assistant_message

    def call_function(self, tool_call):
        function_name = tool_call['function']['name']
        function_to_call = self.tool_functions[function_name]
        function_args = json.loads(tool_call['function']['arguments'])
        logging.info(f"Calling {function_name} with {function_args}")
        function_response = function_to_call(**function_args)

        return {
            "tool_call_id": tool_call['id'],
            "role": "tool",
            "name": function_name,
            "content": function_response,
        }

    def call_functions(self, tool_calls):
        # Sequentially call each function (no need for asyncio.gather)
        function_responses = []
        for tool_call in tool_calls:
            response = self.call_function(tool_call)
            function_responses.append(response)

        # Convert all function responses to strings and add to messages
        responses_in_str = [{**item, "content": str(item["content"])} for item in function_responses]

        # Log each tool call object separately
        for res in function_responses:
            logging.info(f"Tool Call: {res}")

        self.messages.extend(responses_in_str)

        response_message = self.execute()
        return response_message, function_responses
