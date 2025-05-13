# run.py
from app import create_app
import config

app = create_app()

if __name__ == '__main__':
    # Make sure the host is accessible if running in Docker or VM
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)
    