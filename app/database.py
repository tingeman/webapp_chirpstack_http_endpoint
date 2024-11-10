import sqlite3
from flask import g
import logging
import json
import time
from config import settings


DB_FILE = settings.DB_FILE  # Path to the SQLite database file from config

# Function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_FILE)
        # No need to implement a retry mechanism here
        # as the connect command is not affected by a locked database
    return g.db

# Function to close the database connection after each request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        # No need to implement a retry mechanism here
        # as the close command is not affected by a locked database


class RetryDBOperation:
    def __init__(self, retries=5, delay=0.1):
        """
        Context manager for retrying database operations.

        Args:
            retries (int): Number of retries.
            delay (float): Delay between retries in seconds.
        """
        self.retries = retries
        self.delay = delay

    def __enter__(self):
        # Nothing to initialize on entering the context
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Handle exceptions, specifically "database is locked" errors
        if exc_type is sqlite3.OperationalError and "locked" in str(exc_value).lower():
            for attempt in range(self.retries):
                logging.warning(f"Database is locked, retrying {attempt + 1}/{self.retries}...")
                time.sleep(self.delay)
                # Suppress the exception and allow the retry
                return True
        # If retries are exhausted or it's not a locking error, propagate the exception
        return False


# Initialize the SQLite database
def init_db() -> None:
    """
    Initializes the SQLite database by creating the messages table if it does not exist.
    """
    try:
        logging.info("Initializing database...")
        db = get_db()  # Use get_db() to get the connection
        with RetryDBOperation():
            cursor = db.cursor()
            # Create the messages table if it does not exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    received_at DATETIME DEFAULT (datetime('now', 'utc'))
                )
            ''')
        with RetryDBOperation():
            db.commit()
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
        db = get_db()  # Use get_db() to get the connection
        with RetryDBOperation():
            cursor = db.cursor()
            # Insert the message details into the messages table
            cursor.execute('''
                INSERT INTO messages (event_type, payload)
                VALUES (?, ?)
            ''', (event_type, payload))
        with RetryDBOperation():
            db.commit()
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
        db = get_db()  # Use get_db() to get the connection
        with RetryDBOperation():
            cursor = db.cursor()
            cursor.execute('''
                SELECT event_type, payload, received_at
                FROM messages
                ORDER BY received_at DESC
                LIMIT ?
            ''', (n,))
        with RetryDBOperation():
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
        db = get_db()  # Use get_db() to get the connection
        with RetryDBOperation():
            cursor = db.cursor()
            cursor.execute('''
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name=?
            ''', (table_name,))
        with RetryDBOperation():
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
        db = get_db()  # Use get_db() to get the connection
        with RetryDBOperation():
            cursor = db.cursor()
            cursor.execute('DELETE FROM messages')
        with RetryDBOperation():
            db.commit()
        logging.info("All messages cleared from the database.")
    except sqlite3.Error as e:
        logging.error(f"Failed to clear messages from the database: {str(e)}")
