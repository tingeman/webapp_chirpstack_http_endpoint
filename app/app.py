from flask import Flask
import logging
from config import run_server_settings
from database import init_db, close_db
from routes import bp

app = Flask(__name__)

# Close the database connection after each request
app.teardown_appcontext(close_db)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize the database
logging.info("Initializing database...")
init_db()

# Register the blueprint
app.register_blueprint(bp)

if __name__ == '__main__':
    # Run the Flask app on host and port defined in settings
    app.run(host=run_server_settings.HOST, port=run_server_settings.PORT)
