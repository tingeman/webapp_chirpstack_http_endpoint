from flask import Flask

# Create a Flask app
app = Flask(__name__)

# Define a route to respond with "Hello, world!"
@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, world!", 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050)

# Run with Gunicorn using the command:
# gunicorn -b 0.0.0.0:8050 <your_filename>:app
