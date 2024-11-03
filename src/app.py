from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from a .env file
load_dotenv()

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    """Initialize a connection to a MySQL database with error handling."""
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    try:
        # Attempt to connect to the database using SQLAlchemy URI
        return SQLDatabase.from_uri(db_uri)
    except SQLAlchemyError as e:
        # Display an error message in Streamlit if the connection fails
        st.error(f"Failed to connect to the database: {str(e)}")
        return None

def get_sql_chain(db):
    """ Create a chain of runnables to generate SQL queries based on user questions. """
    template = """
    You are a SQL expert specializing in blockchain data analysis, particularly Ethereum transactions. The user will ask questions about a dataset containing Ethereum transactions for Stake.com.
    If a user asks a question about Stake.com, you can assume that the address is 0x974CaA59e49682CdA0AD2bbe82983419A2ECC400.
    Your task is to generate precise SQL queries based on the table schema provided below.

    <SCHEMA>{schema}</SCHEMA>
    
    <Conversation History>
    {chat_history}

    Write only the SQL query and nothing else. Do not include any explanatory text, comments, or backticks.

    Example Questions and Corresponding SQL Queries:
    1. Question: What is the total transaction fee paid in Ethereum?
    SQL Query: SELECT SUM(Txn_Fee) FROM transactions;

    2. Question: Which block contains the most transactions?
    SQL Query: SELECT Block_No, COUNT(*) AS transaction_count FROM transactions GROUP BY Block_No ORDER BY transaction_count DESC LIMIT 1;

    3. Question: What is the average transaction fee in USD?
    SQL Query: SELECT AVG(Txn_Fee_USD) FROM transactions;

    4. Question: Which address sent the highest value of Ethereum in a single transaction?
    SQL Query: SELECT `From`, MAX(Amount) FROM transactions;

    5. Question: How many transactions above $100 USD occurred in the last 2 hours?
    SQL Query: SELECT COUNT(*) FROM transactions WHERE Amount_USD > 100 AND Time >= NOW() - INTERVAL 2 HOUR;

    Your turn:

    Question: {question}
    SQL Query:
    """
    
    # Create a prompt template for SQL query generation
    prompt = ChatPromptTemplate.from_template(template)
    
    # Load a language model with specific settings
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0)

    # Retrieve database schema to guide SQL query generation
    def get_schema(_):
        return db.get_table_info()
    
    # Define the runnable chain for query generation
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )
    
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    # Obtain the SQL chain for query generation
    sql_chain = get_sql_chain(db)
    
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about Ethereum transactions.

    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}"""
    
    # Create a prompt template for generating responses
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize language model for generating responses
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0)

    # Define the runnable chain for response generation
    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response=lambda vars: db.run(vars["query"]),
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Invoke the chain with the user's query and recent chat history
    return chain.invoke({
        "question": user_query,
        "chat_history": chat_history[-2:],
    })
    
# Initialize chat history in Streamlit session state if not already present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]

# Configure Streamlit app settings
st.set_page_config(page_title="Chat with MySQL", page_icon=":speech_balloon:", layout="wide")

# Sidebar for Settings
with st.sidebar:
    st.title("Settings")
    st.write("This is a simple chat application using MySQL. Connect to the database and start chatting.")
    
    # User input fields for database connection parameters
    st.text_input("Host", value="localhost", key="Host")
    st.text_input("Port", value="3306", key="Port")
    st.text_input("User", value="root", key="User")
    st.text_input("Password", type="password", value="admin", key="Password")
    st.text_input("Database", value="transactions_db", key="Database")
    
    # Button to connect to the database
    if st.button("Connect"):
        with st.spinner("Connecting to database..."):
            db = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Port"],
                st.session_state["Database"]
            )
            st.session_state.db = db
            st.success("Connected to database!")
    
    # Button to reset chat history
    if st.button("Reset Chat"):
        st.session_state.chat_history = [
            AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
        ]
    
# Main Interface
st.title("Chat with MySQL about Ethereum Transactions")
st.write("Ask questions about your Ethereum transactions, and I'll generate SQL queries to get the answers.")

# Display conversation history in the chat interface
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

# Capture user input from chat box
user_query = st.chat_input("Type a message...")

# Check if the database connection exists
if "db" not in st.session_state or st.session_state.db is None:
    st.warning("Please connect to the database to start.")
else:
    if user_query is not None and user_query.strip() != "":
        # Append user message to chat history
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.chat_message("Human"):
            st.markdown(user_query)

        with st.chat_message("AI"):
            with st.spinner("Thinking..."):
                # Ensure database connection exists before querying
                response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
                st.markdown(response)

        # Append AI response to chat history
        st.session_state.chat_history.append(AIMessage(content=response))
