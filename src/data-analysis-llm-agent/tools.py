import psycopg2
import sqlite3
import os
import plotly.graph_objs as go
import plotly.io as pio
from utils import convert_to_json, json_to_markdown_table

# Function schema for available tools
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
                        "description": "Complete and correct SQL query to fulfill user request."
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
            "description": "Plot Bar or Linechart to visualize the result of SQL query",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {
                        "type": "string",
                        "description": "Plot type: bar, line, scatter, etc."
                    },
                    "x_values": {
                        "type": "array",
                        "description": "List of x-values for plotting",
                        "items": {
                            "type": "string"
                        }
                    },
                    "y_values": {
                        "type": "array",
                        "description": "List of y-axis values for plotting",
                        "items": {
                            "type": "number"
                        }
                    },
                    "plot_title": {
                        "type": "string",
                        "description": "Descriptive title for the plot"
                    },
                    "x_label": {
                        "type": "string",
                        "description": "Label for the x-axis"
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Label for the y-axis"
                    }
                },
                "required": ["plot_type", "x_values", "y_values", "plot_title", "x_label", "y_label"],
            },
        }
    }
]

# Function to query PostgreSQL database
async def run_postgres_query(sql_query, markdown=True):
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
            print("PostgreSQL connection is closed")


# Function to query SQLite database
async def run_sqlite_query(sql_query, markdown=True):
    connection = None
    try:
        db_path = os.path.join(os.path.dirname(__file__), '../data/ai4i2020.db')
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
    except sqlite3.Error as error:
        print("Error while executing the query:", error)
        if markdown:
            return f"Error while executing the query: {error}"
        return [], []
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("SQLite connection is closed")


# Function to plot various types of charts
async def plot_chart(x_values, y_values, plot_title, x_label, y_label, plot_type='line', y2_values=None, save_path="tmp/tmp.png"):
    """
    Generate various types of charts based on input data using Plotly.

    Parameters:
    x_values (array-like): Input values for the x-axis.
    y_values (array-like): Input values for the y-axis.
    plot_type (str, optional): Type of plot to generate (e.g., 'bar', 'line', 'scatter', 'pie', 'gauge', etc.). Default is 'line'.
    y2_values (array-like, optional): Optional second y-axis values for combo charts.
    save_path (str, optional): Path to save the plot image locally. If None, the plot image will not be saved locally.

    Returns:
    str: Data URI of the plot image or the plot itself.
    """
    # Validate input lengths
    if len(x_values) != len(y_values):
        raise ValueError("Lengths of x_values and y_values must be the same.")

    # Define plotly trace based on plot_type
    if plot_type == 'bar':
        trace = go.Bar(x=x_values, y=y_values, marker=dict(color='#24C8BF', line=dict(width=1)))
    elif plot_type == 'scatter':
        trace = go.Scatter(x=x_values, y=y_values, mode='markers', marker=dict(color='#df84ff', size=10, opacity=0.7, line=dict(width=1)))
    elif plot_type == 'line':
        trace = go.Scatter(x=x_values, y=y_values, mode='lines+markers', marker=dict(color='#ff9900', size=8, line=dict(width=1)), line=dict(width=2, color='#ff9900'))
    elif plot_type == 'area':
        trace = go.Scatter(x=x_values, y=y_values, fill='tozeroy', mode='none', fillcolor='rgba(0,100,80,0.2)')
    elif plot_type == 'pie':
        trace = go.Pie(labels=x_values, values=y_values, hole=0)
    elif plot_type == 'donut':
        trace = go.Pie(labels=x_values, values=y_values, hole=0.4)
    elif plot_type == 'stacked_bar':
        trace = go.Bar(x=x_values, y=y_values, marker=dict(color='#24C8BF', line=dict(width=1)), name=plot_title)
    elif plot_type == 'stacked_area':
        trace = go.Scatter(x=x_values, y=y_values, mode='lines', fill='tonexty', stackgroup='one')
    elif plot_type == 'gauge':
        trace = go.Indicator(mode="gauge+number", value=y_values[0], gauge={'axis': {'range': [None, max(y_values)]}})
    elif plot_type == 'bubble':
        trace = go.Scatter(x=x_values, y=y_values, mode='markers', marker=dict(size=[v*10 for v in y_values]))
    elif plot_type == 'combo':
        if y2_values is None or len(x_values) != len(y2_values):
            raise ValueError("For combo charts, provide y2_values of the same length as x_values.")
        trace = go.Scatter(x=x_values, y=y2_values, mode='lines', name='Line Data', line=dict(width=2, color='#ff9900'))
        trace2 = go.Bar(x=x_values, y=y_values, name='Bar Data', marker=dict(color='#24C8BF', line=dict(width=1)))

    # Create layout for the plot
    layout = go.Layout(
        title=f'{plot_title} {plot_type.capitalize()} Chart',
        title_font=dict(size=20, family='Arial', color='#333'),
        xaxis=dict(title=x_label, titlefont=dict(size=18), tickfont=dict(size=14), gridcolor='#f0f0f0'),
        yaxis=dict(title=y_label, titlefont=dict(size=18), tickfont=dict(size=14), gridcolor='#f0f0f0'),
        margin=dict(l=60, r=60, t=80, b=60),
        plot_bgcolor='#f8f8f8',
        paper_bgcolor='#f8f8f8',
        barmode='stack' if 'stacked' in plot_type else None  # Set barmode to stacked if the chart is stacked
    )

    # Handle combo chart with two traces
    if plot_type == 'combo':
        fig = go.Figure(data=[trace2, trace], layout=layout)
    else:
        fig = go.Figure(data=[trace], layout=layout)

    # Save or return the figure
    if save_path:
        pio.write_image(fig, save_path)
        return save_path

    return fig
