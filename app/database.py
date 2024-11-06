import sqlite3
import logging
from config import settings

DB_FILE = settings.DB_FILE  # Path to the SQLite database file from config

# Initialize the SQLite database
def init_db() -> None:
    """
    Initializes the SQLite database by creating the messages table if it does not exist.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Create the messages table if it does not exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    dev_eui TEXT NOT NULL,
                    payload TEXT,
                    dev_addr TEXT,
                    received_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        logging.info("Database initialized.")
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {str(e)}")

# Store the message details in the SQLite database
def store_message(event_type: str, dev_eui: str, payload: str, dev_addr: str) -> None:
    """
    Stores the message details in the SQLite database.

    Args:
        event_type (str): The type of event (e.g., "uplink" or "join").
        dev_eui (str): The device EUI (unique identifier for the device).
        payload (str): The payload data (in hexadecimal format).
        dev_addr (str): The device address (specific to join events).
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Insert the message details into the messages table
            cursor.execute('''
                INSERT INTO messages (event_type, dev_eui, payload, dev_addr)
                VALUES (?, ?, ?, ?)
            ''', (event_type, dev_eui, payload, dev_addr))
        logging.info(f"Stored message of type '{event_type}' from device '{dev_eui}' in the database.")
    except sqlite3.Error as e:
        logging.error(f"Failed to store message in the database: {str(e)}")

def get_last_messages(n: int) -> list:
    """
    Retrieves the last 'n' messages from the SQLite database.

    Args:
        n (int): The number of messages to retrieve.

    Returns:
        list: A list of dictionaries containing the message details.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT event_type, dev_eui, payload, dev_addr, received_at
                FROM messages
                ORDER BY received_at DESC
                LIMIT ?
            ''', (n,))
            rows = cursor.fetchall()
            messages = [
                {
                    "event_type": row[0],
                    "dev_eui": row[1],
                    "payload": row[2],
                    "dev_addr": row[3],
                    "received_at": row[4]
                }
                for row in rows
            ]
        return messages
    except sqlite3.Error as e:
        logging.error(f"Failed to retrieve messages from the database: {str(e)}")
        return []
