import requests
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch API key from environment variables
api_key = os.getenv("ETHERSCAN_API_KEY")
address = '0x974CaA59e49682CdA0AD2bbe82983419A2ECC400'
url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={api_key}"

# Fetch transactions from Etherscan API
response = requests.get(url)
data = response.json()

# Fetch current ETH to USD price from Etherscan
eth_usd_url = f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={api_key}"
eth_usd_response = requests.get(eth_usd_url)
eth_usd_data = eth_usd_response.json()

eth_to_usd = float(eth_usd_data["result"]["ethusd"])

# Define the time range
now = datetime.now()
forty_eight_hours_ago = now - timedelta(hours=48)

# MySQL connection details
db_config = {
    "user": "root",
    "password": "admin",
    "host": "localhost",
    "database": "transactions_db"
}

def delete_old_records(cursor):
    delete_query = """
    DELETE FROM transactions WHERE Time < %s
    """
    cursor.execute(delete_query, (forty_eight_hours_ago.strftime('%Y-%m-%d %H:%M:%S'),))
    print("Old records deleted.")

def insert_transaction(cursor, transaction):
    # First check if the transaction already exists
    check_query = "SELECT COUNT(*) FROM transactions WHERE Transaction_Hash = %s"
    cursor.execute(check_query, (transaction["hash"],))
    exists = cursor.fetchone()[0]
    
    if exists:
        # If the transaction already exists, do not insert it
        return

    # Convert ETH values to USD
    amount_eth = int(transaction["value"]) / 10**18
    txn_fee_eth = int(transaction["gasUsed"]) * int(transaction["gasPrice"]) / 10**18
    amount_usd = amount_eth * eth_to_usd
    txn_fee_usd = txn_fee_eth * eth_to_usd

    # Insert the transaction if it doesn't exist
    insert_query = """
    INSERT INTO transactions (Transaction_Hash, Block_No, Time, `From`, `To`, Amount, Txn_Fee, Amount_USD, Txn_Fee_USD) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        transaction["hash"],
        transaction["blockNumber"],
        datetime.fromtimestamp(int(transaction["timeStamp"])).strftime('%Y-%m-%d %H:%M:%S'),
        transaction["from"],
        transaction["to"],
        amount_eth,
        txn_fee_eth,
        amount_usd,
        txn_fee_usd
    ))

def main():
    if data["status"] == "1":  # Check if the API response is OK
        transactions = data["result"]
        recent_transactions = [
            tx for tx in transactions 
            if datetime.fromtimestamp(int(tx["timeStamp"])) >= forty_eight_hours_ago
        ]

        if not recent_transactions:
            print("No new transactions in the last 48 hours.")
            return
        
        try:
            # Connect to MySQL database
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            
            # Delete old records
            delete_old_records(cursor)
            
            # Insert new transactions
            for transaction in recent_transactions:
                insert_transaction(cursor, transaction)
            
            # Commit the transactions to the database
            connection.commit()
            print(f"Inserted {len(recent_transactions)} new transactions into the database.")
        
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        
        finally:
            cursor.close()
            connection.close()

    else:
        print("Failed to fetch transactions from Etherscan API")

if __name__ == "__main__":
    main()
