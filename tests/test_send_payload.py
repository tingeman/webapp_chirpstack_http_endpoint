import requests
import json
from chirpstack_api import integration
from google.protobuf.json_format import Parse

# Define the base payload
base_payload = {
    "MessageType": "C",
    "rssi": "-83",
    "SensorNr": "3",
    "fPort": 8,
    "Payload": "C24:11:02:21:00:00000001010400013933T -83",
    "BoardStatus": "T",
    "SupplyID": "1",
    "FWversion": "04000139",
    "DeviceID": "99999999",
    "Timestamp": "2024-11-02T21:00:00Z"
}

# Define the URL of the Flask app
url = "http://localhost:8060/event?event=up"

# Send the payload as JSON
json_payload = base_payload.copy()
json_payload["encoding"] = "json"
payload_json = json.dumps(json_payload)
response_json = requests.post(url, data=payload_json, headers={"Content-Type": "application/json"})
print("JSON Payload")
print(f"Status Code: {response_json.status_code}")
print(f"Response Body: {response_json.text}")

# Send the payload as Protobuf
protobuf_payload = integration.UplinkEvent()
protobuf_payload_dict = base_payload.copy()
protobuf_payload_dict["encoding"] = "protobuf"
payload_json_for_protobuf = json.dumps(protobuf_payload_dict)
Parse(payload_json_for_protobuf, protobuf_payload)
protobuf_payload_bytes = protobuf_payload.SerializeToString()
response_protobuf = requests.post(url, data=protobuf_payload_bytes, headers={"Content-Type": "application/octet-stream"})
print("Protobuf Payload")
print(f"Status Code: {response_protobuf.status_code}")
print(f"Response Body: {response_protobuf.text}")
