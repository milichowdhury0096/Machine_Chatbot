import chainlit as cl
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv("../.env")
from plotly.graph_objs import Figure

from utils import generate_sqlite_table_info_query, format_table_info
from tools import tools_schema, run_sqlite_query, plot_chart
from bot import ChatBot

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.addHandler(logging.FileHandler('chatbot.log'))

MAX_ITER = 5
schema_table_pairs = []

tool_run_sqlite_query = cl.step(type="tool", show_input="json", language="str")(run_sqlite_query)
tool_plot_chart = cl.step(type="tool", show_input="json", language="json")(plot_chart)
original_run_sqlite_query = tool_run_sqlite_query.__wrapped__
# cl.instrument_openai() 
# for automatic steps

@cl.on_chat_start
def on_chat_start():
    # build schema query
    table_info_query = generate_sqlite_table_info_query(schema_table_pairs)

    # execute query
    result, column_names = original_run_sqlite_query(table_info_query, markdown=False)

    # format result into string to be used in prompt
    table_info = '\n'.join([item[0] for item in result])

    system_message = f"""You are an expert in data analysis. You will provide valuable insights for business user based on their request...
    
    (Other details stay the same)

    Here are complete schema details with column details:
    {table_info}"""

    tool_functions = {
        "query_db": tool_run_sqlite_query,
        "plot_chart": tool_plot_chart
    }

    cl.user_session.set("bot", ChatBot(system_message, tools_schema, tool_functions))


@cl.on_message
def on_message(message: cl.Message):
    bot = cl.user_session.get("bot")

    # Create a new message for the bot's response
    msg = cl.Message(author="Assistant", content="")
    msg.send()  # Synchronously send the initial message

    # Step 1: Get the user request and the first response from the bot
    response_message = bot(message.content)
    msg.content = response_message.content or ""

    # Instead of updating, we just send the updated content directly
    if len(msg.content) > 0:
        cl.Message(author="Assistant", content=msg.content).send()

    # Step 2: Check tool_calls and handle them iteratively until MAX_ITER is reached
    cur_iter = 0
    tool_calls = response_message.tool_calls
    while cur_iter <= MAX_ITER:
        if tool_calls:
            bot.messages.append(response_message)
            response_message, function_responses = bot.call_functions(tool_calls)

            if response_message.content and len(response_message.content) > 0:
                # Send the updated response content as a new message
                cl.Message(author="Assistant", content=response_message.content).send()

            tool_calls = response_message.tool_calls

            # Display plotly chart if function response contains a plot
            function_responses_to_display = [res for res in function_responses if res['name'] in bot.exclude_functions]
            for function_res in function_responses_to_display:
                if isinstance(function_res["content"], Figure):
                    chart = cl.Plotly(name="chart", figure=function_res['content'], display="inline")
                    cl.Message(author="Assistant", content="", elements=[chart]).send()
        else:
            break
        cur_iter += 1
