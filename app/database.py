import sqlite3
import logging
import json
from config import settings

DB_FILE = settings.DB_FILE  # Path to the SQLite database file from config

# Initialize the SQLite database
def init_db() -> None:
    """
    Initializes the SQLite database by creating the messages table if it does not exist.
    """
    try:
        logging.info("Initializing database...")
        if check_table_exists('messages'):
            logging.info("Table 'messages' exists")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Create the messages table if it does not exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    received_at DATETIME DEFAULT (datetime('now', 'utc'))
                )
            ''')
        logging.info("Database initialized.")
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {str(e)}")

# Store the message details in the SQLite database
def store_json_message(event_type: str,  payload: str) -> None:
    """
    Stores the message details in the SQLite database.

    Args:
        event_type (str): The type of event (e.g., "uplink" or "join").
        payload (str): The payload data (in hexadecimal format).
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Insert the message details into the messages table
            cursor.execute('''
                INSERT INTO messages (event_type, payload)
                VALUES (?, ?)
            ''', (event_type, payload))
        logging.info(f"Stored message of type '{event_type}' in the database.")
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
                SELECT event_type, payload, received_at
                FROM messages
                ORDER BY received_at DESC
                LIMIT ?
            ''', (n,))
            rows = cursor.fetchall()
            messages = [
                {
                    "event_type": row[0],
                    "payload": json.loads(row[1]),  # Parse payload as JSON
                    "received_at": row[2]
                }
                for row in rows
            ]
        logging.info(f"Retrieved last {n} messages from the database.")
        return messages
    except sqlite3.Error as e:
        logging.error(f"Failed to retrieve messages from the database: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse payload as JSON: {str(e)}")
        return []
    finally:
        logging.info("Leaving get_last_messages function.")


def check_table_exists(table_name: str) -> bool:
    """
    Checks if a table exists in the SQLite database.

    Args:
        table_name (str): The name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name=?
            ''', (table_name,))
            result = cursor.fetchone()
            return result is not None
    except sqlite3.Error as e:
        logging.error(f"Failed to check if table exists: {str(e)}")
        return False

def clear_messages_from_db() -> None:
    """
    Clears all messages from the SQLite database.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages')
            conn.commit()
        logging.info("All messages cleared from the database.")
    except sqlite3.Error as e:
        logging.error(f"Failed to clear messages from the database: {str(e)}")
