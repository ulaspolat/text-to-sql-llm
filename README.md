```markdown
# Ethereum Transaction SQL Assistant

This project is an Ethereum transaction SQL assistant built using LangChain and integrates with the Etherscan API to retrieve transaction data. It allows users to ask questions about Ethereum transactions, which are converted into SQL queries to fetch answers from a MySQL database.

![System Flow Diagram](diagram.png)

## Features

- Connect to a MySQL database and fetch Ethereum transaction data.
- Use natural language to generate SQL queries based on user questions.
- Get instant answers about Ethereum transactions through a chat interface.

## Requirements

To run this project, you'll need to have the following software and libraries installed:

- Python 3.8 or higher
- MySQL Server
- Required Python packages (listed below)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Set up a Conda virtual environment**: Create a new Conda environment with the required Python version:
   ```bash
   conda create -n eth-sql-assistant python=3.8
   conda activate eth-sql-assistant
   ```

3. **Install required libraries**: Make sure to install the necessary Python packages listed in `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```

4. **Fill the .env file with your API keys**.

## Usage

1. **Run the Streamlit application**: In your terminal, execute the following command to start the app:
   ```bash
   streamlit run app.py
   ```

2. **Connect to the MySQL Database**: Enter your database connection details in the sidebar of the application.

3. **Ask Questions**: Once connected, type your questions about Ethereum transactions into the chat interface. The application will generate SQL queries and return answers based on your database.

If you encounter issues connecting to the database, double-check your database credentials and ensure the MySQL server is running (Services → MySQL80, make sure it's running).

## Acknowledgments

- [LangChain Documentation](https://docs.langchain.com) for providing the framework used in this project.
- [Etherscan API](https://etherscan.io/apis) for transaction data.
- The tutorial by Alejandro AO on YouTube for guidance on implementing certain parts of the project: [YouTube Tutorial](https://www.youtube.com/watch?v=YqqRkuizNN4&ab_channel=AlejandroAO-Software%26Ai).
```
