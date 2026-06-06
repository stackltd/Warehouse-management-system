import logging
from logging.handlers import RotatingFileHandler

from flask_login import LoginManager
from waitress import serve

from webapp import create_app
from webapp.models import User

app = create_app()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = (
    "main.login"  # Куда редиректить, если пользователь не залогинен
)


@login_manager.user_loader
def load_user(user_id):
    """Извлечение объекта пользователя по его ID. Вызывается при каждом запросе"""
    user = User.get_user(query="SELECT * FROM user WHERE id = ?", param=(user_id,))
    return user


if __name__ == "__main__":
    logging.getLogger("waitress").setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=88)
    app.run(host="0.0.0.0", port=88, debug=True)


