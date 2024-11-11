from chirpstack_api import integration
from google.protobuf.message import DecodeError
from google.protobuf.json_format import MessageToJson
from utils import unmarshal, save_json_to_file
from database import store_json_message
import logging

event_dict = {
    "up": integration.UplinkEvent,
    "join": integration.JoinEvent,
    "ack": integration.AckEvent,
    "txack": integration.TxAckEvent,
    "log": integration.LogEvent,
    "status": integration.StatusEvent,
    "location": integration.LocationEvent,
    "integration": integration.IntegrationEvent,
}


# Handle uplink events
def handle_event(event_type, body, is_json):
    """
    Handles events by unmarshaling the incoming data, saving it as JSON, 
    and storing it in the SQLite database.

    Args:
        event_type (str): The type of event (uplink or join or ?).
        body (bytes): The request body containing the event data.
        is_json (bool): Flag indicating if the data is in JSON format.

    Returns:
        tuple: A response message and HTTP status code.
    """
    try:
        # Unmarshal the incoming data into an Event protobuf message
        try:
            event = event_dict[event_type]()
        except KeyError:
            logging.error(f"Unsupported event type: {event_type}")
            return f"Unsupported event type: {event_type}", 400
        
        message = unmarshal(body, event, is_json)

        try:
            logging.info(f"Message received from: {message.device_info.dev_eui}")
        except AttributeError:
            logging.info("Message received")
        
        # Convert the protobuf message to JSON format
        json_data = MessageToJson(message)

        # Save the protobuf message as JSON to a file
        save_json_to_file(event_type, message)
        
        # Store the message details in the SQLite database
        store_json_message(event_type, json_data)
        
        return f"{event_type} event processed", 200
    except DecodeError as e:
        return f"Failed to parse {event_type} event: {str(e)}", 400
