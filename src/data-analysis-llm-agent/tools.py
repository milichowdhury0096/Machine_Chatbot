import psycopg2
import sqlite3
import os
import plotly.graph_objs as go
import plotly.io as pio
from utils import convert_to_json, json_to_markdown_table

# function calling
# available tools
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "query_db",
            "description": "Fetch data from postgres database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "complete and correct sql query to fulfil user request.",
                    }
                },
                "required": ["sql_query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_chart",
            "description": "Plot Bar or Linechart to visualize the result of sql query",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {
                        "type": "string",
                        "description": "which plot type either bar or line or scatter",
                    },
                    "x_values": {
                        "type": "array",
                        "description": "list of x values for plotting",
                        "items": {
                            "type": "string"
                        }
                    },
                    "y_values": {
                        "type": "array",
                        "description": "list of y axis values for plotting",
                        "items": {
                            "type": "number"
                        }
                    },
                    "plot_title": {
                        "type": "string",
                        "description": "Descriptive Title for the plot",
                    },
                    "x_label": {
                        "type": "string",
                        "description": "Label for the x axis",
                    },
                    "y_label": {
                        "type": "string",
                        "description": "label for the y axis",
                    }
                },
                "required": ["plot_type","x_values","y_values","plot_title","x_label","y_label"],
            },
        }
    }
]

def run_postgres_query(sql_query, markdown=True):
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        print("Connected to the database!")

        cursor = connection.cursor()
        cursor.execute(sql_query)

        column_names = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()

        if markdown:
            json_data = convert_to_json(result, column_names)
            markdown_data = json_to_markdown_table(json_data)
            return markdown_data

        return result, column_names
    except (Exception, psycopg2.Error) as error:
        print("Error while executing the query:", error)
        if markdown:
            return f"Error while executing the query: {error}"
        return [], []
    finally:
        if connection:
            cursor.close()
            connection.close()

def run_sqlite_query(sql_query, markdown=True):
    connection = None
    try:
        db_path = os.path.join(os.path.dirname(__file__), '../data/movies.db')
        print(db_path)
        connection = sqlite3.connect(db_path)

        cursor = connection.cursor()
        cursor.execute(sql_query)

        column_names = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()

        if markdown:
            json_data = convert_to_json(result, column_names)
            markdown_data = json_to_markdown_table(json_data)
            return markdown_data

        return result, column_names
    except (Exception, sqlite3.Error) as error:
        print("Error while executing the query:", error)
        if markdown:
            return f"Error while executing the query: {error}"
        return [], []
   
