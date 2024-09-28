import chainlit as cl
from dotenv import load_dotenv
import logging
from langchain.agents import initialize_agent, load_tools

# Load environment variables from .env file
load_dotenv("../.env")

from utils import generate_sqlite_table_info_query, format_table_info
from tools import tools_schema, run_sqlite_query
from bot import ChatBot

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.addHandler(logging.FileHandler('chatbot.log'))

MAX_ITER = 5
schema_table_pairs = []

tool_run_sqlite_query = cl.step(type="tool", show_input="json", language="str")(run_sqlite_query)
original_run_sqlite_query = tool_run_sqlite_query.__wrapped__

# Initialize the DALL·E agent
tools = load_tools(["dalle-image-generator"])
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Hi, I’m DataQube, your intelligent AI assistant. I can help you query data and generate insightful charts. How can I assist you today?").send()
    
    # Build schema query
    table_info_query = generate_sqlite_table_info_query(schema_table_pairs)

    # Execute query
    result, column_names = await original_run_sqlite_query(table_info_query, markdown=False)

    # Format result into string to be used in prompt
    table_info = '\n'.join([item[0] for item in result])

    system_message = f"""You are an expert in data analysis. You will provide valuable insights for business users based on their request.
    Before responding, you will make sure that the user asks pertains to data analysis on the provided schema; else decline.
    If the user requests some data, you will build an SQL query based on the user request for the SQLite DB from the provided schema/table details and call the query_db tool to fetch data from the database with the correct/relevant query that gives correct results.
    You have access to tools to execute database queries and get results. Once you have provided the data, you will reflect to see if you have provided the correct data or not. 
    You might discover some new insights while reflecting.
    
    Follow these Guidelines:
    - If you need certain inputs to proceed or are unsure about anything, you may ask questions but try to use your intelligence to understand user intentions.
    - In the response message, do not provide technical details like SQL, table, or column details; the response will be read by a business user, not a technical person.
    - Provide rich markdown responses; if it is table data, show it in markdown table format.
    - In case you get a database error, you will reflect and try to call the correct SQL query.
    - Limit top N queries to 5 and let the user know that you have limited results.
    - Limit the number of columns to 5-8; wisely choose top columns to query in SQL queries based on the user request.
    - When the user asks for all records, limit results to 10 and inform them that you are limiting records.
    - In SQL queries to fetch data, you must cast date and numeric columns into readable form (easy to read in string format).
    - Design robust SQL queries that take care of uppercase, lowercase, or some variations.
    - Pay careful attention to the schema and table details I have provided below. Only use columns and tables mentioned in the schema details.
    - Machine failure 1 is machine failure, and 0 means it is okay.
    - TWF is tool wear failure.
    - HDF is heat dissipation failure.
    - PWF is power failure.
    - OSF is overstrain failure.
    - RNF is random failures.
    Here are complete schema details with column details:
    {table_info}"""

    tool_functions = {
        "query_db": tool_run_sqlite_query,
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
    
    if len(msg.content) > 0:
        await msg.update()

    # Step 2: Check tool_calls - as long as there are tool calls and it doesn't cross MAX_ITER count, call iteratively
    cur_iter = 0
    tool_calls = response_message.tool_calls
    while cur_iter <= MAX_ITER:

        if tool_calls:
            bot.messages.append(response_message)  # Add tool call to messages before calling executing function calls
            response_message, function_responses = await bot.call_functions(tool_calls)

            # Response message is response after completing function calls and sending it back to the bot
            if response_message.content and len(response_message.content) > 0:
                await cl.Message(author="Assistant", content=response_message.content).send()

            # Reassign tool_calls from new response
            tool_calls = response_message.tool_calls

            # Handle DALL·E chart generation instead of Plotly
            function_responses_to_display = [res for res in function_responses if res['name'] in bot.exclude_functions]
            for function_res in function_responses_to_display:
                if isinstance(function_res["content"], str):
                    # Generate an image using DALL·E based on SQL output description
                    image_description = function_res["content"]
                    dalle_output = agent.run(f"Create the chart as mentioned using SQL output: {image_description}")
                    
                    # Send the generated image to the user
                    image = cl.Image(name="generated_image", image=dalle_output['image'], display="inline")
                    await cl.Message(author="Assistant", content="", elements=[image]).send()
        else:
            break
        cur_iter += 1
