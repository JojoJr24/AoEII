from flask import Flask
from flask_cors import CORS
from db import init_db
from utils import setup_logging
from dotenv import load_dotenv
from routes.api import api_bp
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
setup_logging(app)

# Register the API Blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Initialize the database
with app.app_context():
    init_db()
    app.logger.info("Database initialized.")


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5001)
