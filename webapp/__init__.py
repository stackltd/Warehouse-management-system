import logging
import redis
from flask import Flask
from flask_session import Session
from flask_wtf import CSRFProtect

from routes import bp

secret_key = "супер_секретный_ключ_который_никто_не_должен_знать"

# Инициализируем csrf глобально, без привязки к конкретному app
csrf = CSRFProtect()

def create_app():


    app = Flask(__name__)
    app.secret_key = secret_key
    # Связываем csrf с созданным приложением
    csrf.init_app(app)

    # Глушим лишние логи
    app.logger.disabled = True
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    # log = logging.getLogger("werkzeug")
    # log.disabled = True

    # app.config["WTF_CSRF_ENABLED"] = False

    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = redis.Redis(host="localhost", port=6379)
    # Запуск расширение сессий
    Session(app)
    app.register_blueprint(bp)

    return app
