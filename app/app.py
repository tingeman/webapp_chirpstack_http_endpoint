from flask import Flask
import logging
from config import run_server_settings
from .database import init_db
from .routes import bp

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Register the blueprint
app.register_blueprint(bp)

if __name__ == '__main__':
    # Initialize the database
    init_db()
    # Run the Flask app on host and port defined in settings
    app.run(host=run_server_settings.HOST, port=run_server_settings.PORT)
