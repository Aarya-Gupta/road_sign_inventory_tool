# app/__init__.py
from flask import Flask
import config # Keep this import
import os
import logging # Add logging setup

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object(config)

    # Configure logging
    # You might want more sophisticated logging in production
    logging.basicConfig(level=logging.INFO if not app.debug else logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    app.logger.info("Flask app created")


    # Ensure instance folder exists (if needed for Flask sessions etc.)
    try:
        os.makedirs(app.instance_path)
        app.logger.info(f"Instance path created/ensured at {app.instance_path}")
    except OSError:
        pass # Already exists

    # --- Import and register the blueprint ---
    from . import routes # Import the routes module containing the blueprint 'bp'
    app.register_blueprint(routes.bp)
    app.logger.info("Registered 'main' blueprint")
    # You could also add a url_prefix here if needed: app.register_blueprint(routes.bp, url_prefix='/app')


    # A simple health check route (optional)
    @app.route('/health')
    def health():
        return "OK"

    return app