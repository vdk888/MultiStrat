import os
import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Configure application
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)

# Import routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolios')
def portfolios():
    return render_template('portfolios.html')

@app.route('/assets')
def assets():
    return render_template('assets.html')

@app.route('/strategies')
def strategies():
    return render_template('strategies.html')

@app.route('/optimization')
def optimization():
    return render_template('optimization.html')

@app.route('/performance')
def performance():
    return render_template('performance.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# Create database tables
with app.app_context():
    from app.database.models import Asset, AssetClass, Strategy, Portfolio
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created.")

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)