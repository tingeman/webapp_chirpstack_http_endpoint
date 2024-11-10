import datetime
import loggings
from google.protobuf.json_format import Parse, MessageToJson
from google.protobuf.message import DecodeError
from pathlib import Path
from config import settings

OUTPUT_DIR = Path(settings.JSON_OUTPUT_DIR)  # Path to the JSON output directory from config

# Create the output directory if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Unmarshal the incoming data into a protobuf message
def unmarshal(body: bytes, payload, is_json: bool):
    """
    Unmarshals the incoming data into a protobuf message.

    Args:
        body (bytes): The request body containing the event data.
        payload (protobuf message): The protobuf message to populate.
        is_json (bool): Flag indicating if the data is in JSON format.

    Returns:
        protobuf message: The populated protobuf message.

    Raises:
        DecodeError: If there is an error during unmarshaling.
    """
    try:
        if is_json:
            # Parse the JSON data into the protobuf message
            return Parse(body, payload)
        # Parse the binary data into the protobuf message
        payload.ParseFromString(body)
        return payload
    except (ValueError, DecodeError) as e:
        raise DecodeError(f"Error unmarshaling data: {str(e)}")

# Save a protobuf message as a JSON file
def save_protobuf_as_json(protobuf_message, event_type: str) -> None:
    """
    Saves a protobuf message as a JSON file.

    Args:
        protobuf_message (protobuf message): The protobuf message to save.
        event_type (str): The type of event (e.g., "uplink" or "join").
    """
    try:
        # Convert the protobuf message to JSON format
        json_data = MessageToJson(protobuf_message)
        # Generate a filename based on the event type and current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{event_type}_{timestamp}.json"
        # Write the JSON data to the file
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'w') as json_file:
            json_file.write(json_data)
        logging.info(f"Saved protobuf message as JSON to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save protobuf message as JSON: {str(e)}")

def clear_json_files() -> None:
    """
    Removes all JSON files from the data directory.
    """
    try:
        for file_path in OUTPUT_DIR.glob('*.json'):
            file_path.unlink()
            logging.info(f"Removed file: {file_path}")
        logging.info(f"All JSON files cleared from {OUTPUT_DIR}.")
    except Exception as e:
        logging.error(f"Failed to clear JSON files: {str(e)}")
