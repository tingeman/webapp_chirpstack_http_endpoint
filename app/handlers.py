from chirpstack_api import integration
from google.protobuf.message import DecodeError
from google.protobuf.json_format import MessageToJson

from utils import unmarshal, save_protobuf_as_json
from database import store_json_message

# Handle uplink events
def handle_uplink_event(body, is_json):
    """
    Handles uplink events by unmarshaling the incoming data, saving it as JSON, 
    and storing it in the SQLite database.

    Args:
        body (bytes): The request body containing the event data.
        is_json (bool): Flag indicating if the data is in JSON format.

    Returns:
        tuple: A response message and HTTP status code.
    """
    try:
        # Unmarshal the incoming data into an UplinkEvent protobuf message
        print('Creating uplink event...')
        uplink_event = integration.UplinkEvent()
        print('Unmarshalling uplink event...')
        up = unmarshal(body, uplink_event, is_json)
        print(f"Uplink received from: {up.device_info.dev_eui} with payload: {up.data.hex()}")
        print(f'\nUplink event: {up}')

        # Save the protobuf message as JSON to a file
        save_protobuf_as_json(up, "uplink")
        
        # Store the message details in the SQLite database
        
        # Convert the protobuf message to JSON format
        json_data = MessageToJson(up)
        store_json_message("uplink", json_data)
        
        return "Uplink event processed", 200
    except DecodeError as e:
        return f"Failed to parse uplink event: {str(e)}", 400

# Handle join events
def handle_join_event(body, is_json):
    """
    Handles join events by unmarshaling the incoming data, saving it as JSON, 
    and storing it in the SQLite database.

    Args:
        body (bytes): The request body containing the event data.
        is_json (bool): Flag indicating if the data is in JSON format.

    Returns:
        tuple: A response message and HTTP status code.
    """
    try:
        # Unmarshal the incoming data into a JoinEvent protobuf message
        join = unmarshal(body, integration.JoinEvent(), is_json)
        print(f"Device: {join.device_info.dev_eui} joined with DevAddr: {join.dev_addr}")
        # Save the protobuf message as JSON to a file
        save_protobuf_as_json(join, "join")
        # Store the message details in the SQLite database

        # Convert the protobuf message to JSON format
        json_data = MessageToJson(up)
        store_json_message("uplink", json_data)
        
        return "Join event processed", 200
    except DecodeError as e:
        return f"Failed to parse join event: {str(e)}", 400