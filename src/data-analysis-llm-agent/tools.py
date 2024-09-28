import psycopg2
import sqlite3
import os
import plotly.graph_objs as go
import plotly.io as pio
from utils import convert_to_json, json_to_markdown_table

# function calling
# avialable tools
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
                        "description": "Complete and correct SQL query to fulfill user request.",
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
            "description": "Plot Bar or Line chart to visualize the result of SQL query. Supports multi-series for bar and line charts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {
                        "type": "string",
                        "description": "Plot type: bar, line, scatter, stacked_bar, clustered_bar, etc.",
                    },
                    "x_values": {
                        "type": "array",
                        "description": "List of x values for plotting.",
                        "items": {
                            "type": "string"
                        }
                    },
                    "y_values_list": {
                        "type": "array",
                        "description": "List of arrays, where each array is a set of y-axis values for plotting.",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        }
                    },
                    "y_labels": {
                        "type": "array",
                        "description": "List of labels for each y-axis series.",
                        "items": {
                            "type": "string"
                        }
                    },
                    "plot_title": {
                        "type": "string",
                        "description": "Descriptive title for the plot.",
                    },
                    "x_label": {
                        "type": "string",
                        "description": "Label for the x-axis.",
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Label for the y-axis.",
                    }
                },
                "required": ["plot_type", "x_values", "y_values_list", "plot_title", "x_label", "y_label"],
            },
        }
    }
]



async def run_postgres_query(sql_query, markdown=True):
    connection = None  # Initialize connection variable outside the try block
    try:
        # Establish the connection
        connection = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        print("Connected to the database!")

        # Create a cursor object
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(sql_query)

        # Fetch the column names
        column_names = [desc[0] for desc in cursor.description]

        # Fetch all rows
        result = cursor.fetchall()
        if markdown:
            # get result in json
            json_data = convert_to_json(result,column_names)
            markdown_data = json_to_markdown_table(json_data)

            return markdown_data

        return result, column_names
    except (Exception, psycopg2.Error) as error:
        print("Error while executing the query:", error)
        if markdown:
            return f"Error while executing the query: {error}"
        return [], []

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


async def run_sqlite_query(sql_query, markdown=True):
    connection = None
    try:
        # Establish the connection
        db_path = os.path.join(os.path.dirname(__file__), '../data/ai4i2020.db')
        print(db_path)
        connection = sqlite3.connect(db_path)

        # Create a cursor object
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(sql_query)

        # Fetch the column names
        column_names = [desc[0] for desc in cursor.description]

        # Fetch all rows
        result = cursor.fetchall()
        if markdown:
            # get result in json
            json_data = convert_to_json(result,column_names)
            markdown_data = json_to_markdown_table(json_data)
            return markdown_data

        return result, column_names
    except sqlite3.Error as error:
        print("Error while executing the query:", error)
        if markdown:
            return f"Error while executing the query: {error}"
        return [], []

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("SQLite connection is closed")

async def plot_chart(x_values, y_values_list, plot_title, x_label, y_labels, y_label="Y-Axis", plot_type='line', save_path="tmp/tmp.png"):
    """
    Generate a bar chart, line chart, or scatter plot based on input data using Plotly.
    Supports multi-series charts like stacked bar, clustered bar, etc.

    Parameters:
    x_values (array-like): Input values for the x-axis.
    y_values_list (array-like): List of arrays, where each array is a Y-axis series for the plot.
    plot_type (str, optional): Type of plot to generate ('bar', 'line', 'scatter', 'stacked_bar', 'clustered_bar', etc.). Default is 'line'.
    y_labels (array-like): List of labels for each Y-axis series.
    y_label (str, optional): General label for the Y-axis.
    save_path (str, optional): Path to save the plot image locally. If None, the plot image will not be saved locally.

    Returns:
    str: Data URI of the plot image.
    """
    # Validate input lengths
    for y_values in y_values_list:
        if len(x_values) != len(y_values):
            raise ValueError("Lengths of x_values and each y_values must be the same.")

    traces = []

    # Generate traces for each Y-series based on plot_type
    for i, y_values in enumerate(y_values_list):
        if plot_type == 'stacked_bar':
            trace = go.Bar(x=x_values, y=y_values, name=y_labels[i], marker=dict(line=dict(width=1)))
        elif plot_type == 'clustered_bar':
            trace = go.Bar(x=x_values, y=y_values, name=y_labels[i], marker=dict(line=dict(width=1)))
        elif plot_type == 'line':
            trace = go.Scatter(x=x_values, y=y_values, mode='lines+markers', name=y_labels[i],
                               marker=dict(size=8, line=dict(width=1)), line=dict(width=2))
        elif plot_type == 'scatter':
            trace = go.Scatter(x=x_values, y=y_values, mode='markers', name=y_labels[i], 
                               marker=dict(size=10, opacity=0.7, line=dict(width=1)))
        elif plot_type == 'pie':
            trace = go.Pie(labels=x_values, values=y_values, name=y_labels[i])
        # Add more types like stacked_area, etc., if needed
        traces.append(trace)

    # Layout settings for stacked and clustered bars
    if plot_type == 'stacked_bar':
        barmode = 'stack'
    elif plot_type == 'clustered_bar':
        barmode = 'group'
    else:
        barmode = None

    # Create layout for the plot
    layout = go.Layout(
        title=f'{plot_title} {plot_type.capitalize()} Chart',
        title_font=dict(size=20, family='Arial', color='#333'),
        xaxis=dict(title=x_label, titlefont=dict(size=18), tickfont=dict(size=14), gridcolor='#f0f0f0'),
        yaxis=dict(title=y_label, titlefont=dict(size=18), tickfont=dict(size=14), gridcolor='#f0f0f0'),
        margin=dict(l=60, r=60, t=80, b=60),
        plot_bgcolor='#f8f8f8',
        paper_bgcolor='#f8f8f8',
        barmode=barmode  # This controls stacking or grouping for bar charts
    )

    # Create figure and add traces to it
    fig = go.Figure(data=traces, layout=layout)

    return fig
