import chainlit as cl
from dotenv import load_dotenv
import logging
from plotly.graph_objs import Figure
from utils import generate_sqlite_table_info_query, format_table_info
from tools import tools_schema, sync_run_sqlite_query, plot_chart  # Use the synchronous version
from bot import ChatBot

# Load environment variables from .env file
load_dotenv("../.env")

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('chatbot.log'))

MAX_ITER = 5
schema_table_pairs = []

tool_run_sqlite_query = sync_run_sqlite_query  # Ensure this is a synchronous function
tool_plot_chart = plot_chart

@cl.on_chat_start
def on_chat_start():
    table_info_query = generate_sqlite_table_info_query(schema_table_pairs)
    result, column_names = tool_run_sqlite_query(table_info_query, markdown=False)
    table_info = '\n'.join([item[0] for item in result])

    system_message = f"""You are an expert in data analysis... (rest of your system message)."""

    tool_functions = {
        "query_db": tool_run_sqlite_query,
        "plot_chart": tool_plot_chart
    }

    bot = ChatBot(system_message, tools_schema, tool_functions)
    cl.user_session.set("bot", bot)

@cl.on_message
def on_message(message: cl.Message):
    bot = cl.user_session.get("bot")

    if bot is None:
        logging.error("Bot not initialized.")
        return

    msg = cl.Message(author="Assistant", content="")
    msg.send()  # No await needed since it's synchronous

    # Step 1: Handle user request and bot response
    response_message = bot(message.content)
    msg.content = response_message.content or ""

    if len(msg.content) > 0:
        msg.update()

    # Step 2: Check tool_calls and iterate
    cur_iter = 0
    tool_calls = response_message.tool_calls
    while cur_iter <= MAX_ITER:
        if tool_calls:
            bot.messages.append(response_message)
            response_message, function_responses = bot.call_functions(tool_calls)

            if response_message.content and len(response_message.content) > 0:
                cl.Message(author="Assistant", content=response_message.content).send()

            tool_calls = response_message.tool_calls

            function_responses_to_display = [res for res in function_responses if res['name'] in bot.exclude_functions]
            for function_res in function_responses_to_display:
                if isinstance(function_res["content"], Figure):
                    chart = cl.Plotly(name="chart", figure=function_res['content'], display="inline")
                    cl.Message(author="Assistant", content="", elements=[chart]).send()
        else:
            break
        cur_iter += 1
