# Conversational AI with Data Vizualization Tools

## 📚 Overview

This repository contains a conversational AI chatbot built using **Chainlit** and **Chatgroq's: llama3-groq-70b-8192-tool-use-preview** model. The chatbot provides data analysis insights by leveraging a predefined schema and incorporates function calling to utilize various tools effectively. It also includes error handling with automatic retries for database operations.

## 🔧 Features

- **Tool Access**:
  - **Database Query**: Execute and retrieve data from a database.
  - **Plot Chart**: Generate visualizations to facilitate data interpretation.

## 🏗️ Architecture

The application is structured into the following components:

- **`app.py`**: Main application file that initializes the Chainlit framework and orchestrates chatbot logic.
- **`bot.py`**: Contains the logic for processing user messages and generating responses via the OpenAI API.
- **`utils.py`**: Utility functions for database introspection and data format conversions.
- **`tools.py`**: Functions for executing database queries and generating plots.

## 🚀 How It Works

The chatbot operates through a simple interaction loop:

1. **User Interaction**: The user sends a message to the chatbot.
2. **Processing**: The chatbot analyzes the message and may invoke tool calls to fetch data or generate plots.
3. **Response Construction**: Tool results, including outputs and any error messages, are integrated into the conversation. These responses are sent back to the language model for refinement.
4. **Execution Loop**: An execution loop runs for a defined number of iterations (`MAX_ITER`) if the response includes additional tool calls.
5. **Final Response**: The chatbot delivers the response to the user, including any generated plots or tables.

## 📝 Conclusion

This chatbot application combines Chainlit and llama3-groq-70b-8192-tool-use-preview model to deliver insightful data analysis based on user queries. Its architecture supports efficient function calling and robust error handling, ensuring accurate and responsive interactions.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.

## 🤝 Contributing

Contributions are welcome! Please submit a pull request or open an issue for discussion.

## 📧 Contact

For questions or inquiries, please reach out at [mili.chowdhury_ds24sp@praxistech.school].
