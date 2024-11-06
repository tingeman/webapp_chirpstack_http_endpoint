from flask import Blueprint, request, jsonify
import logging
from .validation import validate_event_type
from .handlers import handle_uplink_event, handle_join_event
from .database import get_last_messages
from .utils import unmarshal, save_protobuf_as_json

bp = Blueprint('endpoint', __name__)

@bp.route('/event', methods=['POST'])
def handle_event() -> tuple:
    """
    Handles incoming POST requests for different event types (uplink, join).
    Parses the request and routes it to the appropriate handler based on the event type.
    """
    try:
        event_type = request.args.get('event')
        if not event_type or not validate_event_type(event_type):
            return "Invalid or missing 'event' query parameter", 400

        body = request.data
        if not body:
            return "Missing request body", 400

        if request.content_type not in {'application/json', 'application/octet-stream'}:
            return "Invalid Content-Type", 400
        is_json = request.content_type == 'application/json'

        if event_type == "up":
            return handle_uplink_event(body, is_json)
        elif event_type == "join":
            return handle_join_event(body, is_json)
        else:
            return f"Handler for event '{event_type}' is not implemented", 400

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}", 500

@bp.route('/last-messages', methods=['GET'])
def last_messages() -> tuple:
    """
    Serves the last 'n' messages received in JSON format.
    """
    try:
        n = request.args.get('n', default=5, type=int)
        if n <= 0:
            return "Invalid 'n' query parameter", 400

        messages = get_last_messages(n)
        return jsonify(messages), 200
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}", 500
