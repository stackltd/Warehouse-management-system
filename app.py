import logging

import redis
from waitress import serve

from flask_session import Session

from routes import app

# from utils import initialize

if __name__ == "__main__":
    # initialize()
    app.secret_key = "супер_секретный_ключ_который_никто_не_должен_знать"
    # app.config["WTF_CSRF_ENABLED"] = False
    # logging.getLogger('waitress').setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=8080)
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = redis.Redis(host="localhost", port=6379)
    # Запускаем расширение сессий
    Session(app)
    app.run(host="0.0.0.0", port=8080, debug=True)
