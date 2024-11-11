import time
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from handlers import handle_event
from database import get_last_messages, clear_messages_from_db
from utils import clear_json_files

bp = Blueprint('endpoint', __name__)

@bp.route('/event', methods=['POST'])
def handle_event() -> tuple:
    """
    Handles incoming POST requests for different event types (uplink, join).
    Parses the request and routes it to the appropriate handler based on the event type.
    """
    logging.info(f"Received request with content type: {request.content_type}") # Log the content type of the request
    
    try:
        event_type = request.args.get('event')
        logging.debug(f"Received request for event type: {event_type}")

        body = request.data
        logging.debug(f"Received request body:\n{body}")
        if not body:
            return "Missing request body", 400

        if request.content_type not in {'application/json', 'application/octet-stream'}:
            return "Invalid Content-Type", 400

        is_json = request.content_type == 'application/json'

        return handle_event(event_type, body, is_json)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}", 500

@bp.route('/last-messages', methods=['GET'])
def last_messages() -> tuple:
    """
    Serves the last 'n' messages received in JSON format.
    """
    start_time = time.time()
    logging.info("Received request for last messages")
    try:
        n = request.args.get('n', default=5, type=int)
        if n <= 0:
            return "Invalid 'n' query parameter", 400

        messages = get_last_messages(n)
        output = jsonify(messages)
        logging.info(f"Returning last {n} messages")
        return output, 200
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}", 500
    finally:
        end_time = time.time()
        logging.info(f"Request handled in {end_time - start_time} seconds")

@bp.route('/health', methods=['GET'])
def health_check() -> tuple:
    """
    Simple health check endpoint.
    """
    return "OK", 200

@bp.route('/clear_messages', methods=['GET'])
def clear_messages_route():
    """
    Route to display a confirmation page and clear the database and JSON files upon user confirmation.
    """
    if 'confirm' in request.args and request.args.get('confirm') == 'yes':
        clear_messages_from_db()
        clear_json_files()  # Replace with the actual path to the JSON files
        return redirect(url_for('endpoint.index'))  # Redirect to the home page after clearing messages
    return render_template('clear_messages.html')

@bp.route('/', methods=['GET'])
def index() -> str:
    """
    Index route that serves the home page.
    """
    return render_template('index.html')

