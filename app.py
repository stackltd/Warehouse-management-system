import logging

from waitress import serve

from routes import app
from utils import initialize

if __name__ == "__main__":
    initialize()
    app.secret_key = "супер_секретный_ключ_который_никто_не_должен_знать"
    # app.config["WTF_CSRF_ENABLED"] = False
    # logging.getLogger('waitress').setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", port=8080, debug=True)
