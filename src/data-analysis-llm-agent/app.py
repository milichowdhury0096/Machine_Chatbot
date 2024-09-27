import chainlit as cl
from dotenv import load_dotenv
import logging
from plotly.graph_objs import Figure
from utils import generate_sqlite_table_info_query, format_table_info
from tools import tools_schema, run_sqlite_query, plot_chart
from bot import ChatBot

# Load environment variables from .env file
load_dotenv("../.env")

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('chatbot.log'))

MAX_ITER = 5
schema_table_pairs = []

# Define tools with limits
tool_run_sqlite_query = cl.step(type="tool", show_input="json", language="str")(run_sqlite_query)
tool_plot_chart = cl.step(type="tool", show_input="json", language="json")(plot_chart)
original_run_sqlite_query = tool_run_sqlite_query.__wrapped__

# Function to limit rows and columns in SQL queries
def limit_query_results(query):
    return f"{query} LIMIT 100"  # Limit to 100 rows

def limit_columns(query):
    # Modify query to select only top 10 columns (adjust according to your dataset)
    return query.replace("SELECT *", "SELECT column1, column2, column3, column4, column5, column6, column7, column8, column9, column10")

# cl.instrument_openai() 
# for automatic steps

@cl.on_chat_start
async def on_chat_start():
    # Build schema query
    table_info_query = generate_sqlite_table_info_query(schema_table_pairs)

    # Execute query with row and column limits
    table_info_query_limited = limit_columns(table_info_query)
    result, column_names = await original_run_sqlite_query(limit_query_results(table_info_query_limited), markdown=False)

    # Format result into string to be used in the prompt
    table_info = '\n'.join([item[0] for item in result])

    system_message = f"""You are an expert in data analysis. You will provide valuable insights for the business user based on their request.
    Before responding, you will ensure that the user asks data analysis-related queries based on the provided schema, else you will decline the request.
    
    If the user requests data, you will build SQL queries based on the user request for the SQLite DB from the provided schema/table details, and call query_db tools to fetch data with the correct/relevant query.
    You have access to tools to execute database queries and plot results.

    Reflection:
    - Reflect to check if you provided correct data.
    - Always limit query results to 100 rows and 10 columns.
    - For graph generation, you can use between 100 to 500 rows depending on the graph type.

    {table_info}"""

    # Tool functions
    tool_functions = {
        "query_db": tool_run_sqlite_query,
        "plot_chart": tool_plot_chart
    }

    cl.user_session.set("bot", ChatBot(system_message, tools_schema, tool_functions))


@cl.on_message
async def on_message(message: cl.Message):
    bot = cl.user_session.get("bot")

    msg = cl.Message(author="Assistant", content="")
    await msg.send()

    # Step 1: User request and first response from the bot
    response_message = await bot(message.content)
    msg.content = response_message.content or ""

    # Pending message to be sent
    if len(msg.content) > 0:
        await msg.update()

    # Step 2: Check tool_calls, as long as there are tool calls and it doesn't cross MAX_ITER, call iteratively
    cur_iter = 0
    tool_calls = response_message.tool_calls
    while cur_iter <= MAX_ITER:

        if tool_calls:
            bot.messages.append(response_message)  # Add tool call to messages before executing function calls
            response_message, function_responses = await bot.call_functions(tool_calls)

            # Response message after completing function calls
            if response_message.content and len(response_message.content) > 0:
                await cl.Message(author="Assistant", content=response_message.content).send()

            # Reassign tool_calls from new response
            tool_calls = response_message.tool_calls

            # Some responses, like charts, should be displayed explicitly
            function_responses_to_display = [res for res in function_responses if res['name'] in bot.exclude_functions]
            for function_res in function_responses_to_display:
                # Plot chart with variable row limits (100-500 rows)
                if isinstance(function_res["content"], Figure):
                    chart = cl.Plotly(name="chart", figure=function_res['content'], display="inline")
                    await cl.Message(author="Assistant", content="", elements=[chart]).send()
        else:
            break
        cur_iter += 1
