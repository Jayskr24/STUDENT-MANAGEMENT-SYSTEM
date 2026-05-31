import sys
import os

# Root folder ko path mein add karo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web.app import app
from core.database import init_db

if __name__ == "__main__":
    init_db()  # Database initialize karo
    app.run(debug=True, host="0.0.0.0", port=5000)