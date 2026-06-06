import atexit
from flask import render_template, redirect, g, session, Blueprint, request, flash
from flask_login import login_required, logout_user

from webapp.models import ControlDatabase
from webapp.services import Service
from webapp.utils import initialize, clear_redis_cache
from webapp.config import Bases
from webapp.exceptions import Unauthorized

bp = Blueprint("main", __name__)

# Регистрируем функцию в atexit
atexit.register(clear_redis_cache)

# Создаем экземпляр контроллера бд
db = ControlDatabase()
# Создаем экземпляр сервиса
service = Service(db)


@bp.teardown_app_request
def close_connection(exception):
    """Соединение с базой только в момент обращения к ней в запросе."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@bp.before_request
def setup_user_session():
    """Инициализация контекста, логирования при запуске приложения"""

    if session.get("base") is None:
        initialize()


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Заход в систему. Контроль попыток перебора паролей с текущего IP"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        result = service.login(username, password)
        if isinstance(result, tuple):
            return result
        elif result:
            return redirect("/")
    flash("Неверный логин или пароль")
    return render_template("index.html")


@bp.route("/change_password", methods=["POST"])
def change_password():
    """Смена пароля"""
    args = [
        request.form.get(arg) for arg in ("curr_password", "password_1", "password_2")
    ]
    service.change_password(db, *args)
    return redirect("/")


@bp.route("/logout")
@login_required
def logout():
    """Выход из системы"""
    initialize()
    session["fields_from_base"] = "[]"
    logout_user()  # Удаление сессии из Redis и стирание куки
    return redirect("/login")


@bp.route("/select_base")
def select_base():
    """Смена базы"""
    try:
        service.switch_base()
    except ValueError:
        return render_template(
            template_name_or_list="index.html",
            message=["inline-block", "Ошибка выбора базы"],
        )
    return redirect("/")


@bp.route("/")
@login_required
def stock():
    """Рендеринг полей"""
    try:
        context = service.get_fields_for_render()
        return render_template(**context)
    except (ValueError, Unauthorized):
        return render_template(
            template_name_or_list="index.html",
            bases=session.get("available_bases", [base_name for base_name in Bases]),
            message=["inline-block", "Выберите базу"],
        )
    finally:
        session["message"] = ["none", ""]


@bp.route("/sorting/<id>")
def sorting(id):
    """Сортировка столбца по параметру"""
    service.sorting_by_field(id)
    return redirect("/")


@bp.route("/change_mode/<int:id>")
def change_mode(id):
    """Вход/выход в режим изменения строки"""
    service.change_mode(id)
    return redirect("/")


@bp.route("/change/<int:id>", methods=["POST"])
def change(id):
    """Изменение строки после вхождения в режим change_mode"""
    form = dict(request.form)
    service.change_field(id, multidict=form)
    return redirect("/")


@bp.route("/add_record/", methods=["POST"])
def add_record():
    """Добавление новой записи"""
    form = dict(request.form)
    service.add_new_record(multidict=form)
    return redirect("/")


@bp.route("/add_file/<int:id>", methods=["POST"])
def add_file(id):
    """Добавление файла"""
    service.upload_file(id)
    return redirect("/")


@bp.route("/report")
def report():
    """История изменений в базе"""
    text = service.report()
    html = f"<pre style='font-size: 25; background-color: #ebeef2;'>{text}</pre>"
    return html


@bp.route("/static/files/<folder>/<name>")
def redirect_from_photo(folder, name):
    """Перенаправление с клика по photo, если в fields.json задан параметр url_for_redirect_from_photo"""
    url_for_redirect_from_photo = session["url_for_redirect_from_photo"]
    return redirect(f"{url_for_redirect_from_photo}/{folder}/{name}")
