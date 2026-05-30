import logging
import redis
from flask import Flask
from flask_wtf import CSRFProtect
from waitress import serve

from flask_session import Session

# Инициализируем расширения глобально, но БЕЗ привязки к конкретному app
csrf = CSRFProtect()


if __name__ == "__main__":
    app = Flask(__name__)
    app.secret_key = "супер_секретный_ключ_который_никто_не_должен_знать"
    # 2. Связываем расширения с созданным приложением
    csrf.init_app(app)

    # 3. Глушим лишние логи (как ты делал для Waitress/Werkzeug)
    app.logger.disabled = True
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    log = logging.getLogger("werkzeug")
    # log.disabled = True

    # app.config["WTF_CSRF_ENABLED"] = False

    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = redis.Redis(host="localhost", port=6379)
    # Запускаем расширение сессий
    Session(app)

    # 4. Регистрируем роуты (импортируем их внутри функции, чтобы избежать циклов!)
    from routes import bp

    app.register_blueprint(bp)

    # logging.getLogger('waitress').setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", port=8080, debug=True)
