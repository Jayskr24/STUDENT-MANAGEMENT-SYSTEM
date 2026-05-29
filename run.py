import os
from web.app import app
from core.database import init_db

if __name__ == "__main__":
    init_db()
    # Get port assigned by the cloud host, or default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)