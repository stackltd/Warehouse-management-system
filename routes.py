import atexit
import json
import logging
import random

import redis
from flask import Flask, request, render_template, redirect, g, session, Blueprint
from flask.sessions import SecureCookieSessionInterface
from jinja2 import exceptions
from flask_wtf.csrf import CSRFProtect
from forms import ManualForm, PhotoForm

from models import ControlDatabase
from config import Bases, SORT_DIRECT, SIZE_BLOCK, FIELD_FOR_SORTING
from services import WarehouseService
from utils import str_corr, load_file, div_string, initialize

bases = [base_name for base_name in Bases]

# app = Flask(__name__)

logger = logging.getLogger("логгер")

bp = Blueprint("main", __name__)

db = ControlDatabase()
# Создаем экземпляр сервиса
warehouse_service = WarehouseService(db)

# Инициализируем подключение к Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)


def clear_redis_cache():
    print("⚠️ Сервер останавливается! Очищаю кэш Redis...")
    try:
        # Вариант А: Очистить ВООБЩЕ ВСЁ в текущей базе данных Redis
        # redis_client.flushdb()
        # Вариант Б: Если нужно удалить только определенные ключи (например, сессии)
        keys = redis_client.keys("session:*")
        if keys:
            redis_client.delete(*keys)
        print("✅ Кэш Redis успешно очищен.")
    except Exception as e:
        print(f"❌ Не удалось очистить Redis при закрытии: {e}")


# Регистрируем функцию в atexit
atexit.register(clear_redis_cache)


@bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@bp.before_request
def setup_user_session():
    if session.get("base") is None:
        initialize()


@bp.route("/select_base")
def select_base():
    """
    Функция смены базы
    :return:
    """
    base = request.args.get("base_name")
    try:
        warehouse_service.switch_base(base, bases)
    except ValueError:
        return render_template(
            template_name_or_list="index.html",
            message=["inline-block", "Ошибка выбора базы"],
        )

    return redirect("/")


@bp.route("/")
def stock():
    base = session["base"]

    (
        categories,
        fields_params,
        fields_order_out,
        result,
        summ_some_fields,
        statuses,
        sel_record,
        fields,
    ) = warehouse_service.get_fields_for_render(base)
    context = dict(
        template_name_or_list="index.html",
        categories=categories,
        fields_params=fields_params,
        fields_order=fields_order_out,
        result=result,
        summ_some_fields=summ_some_fields,
        statuses=statuses,
        sel_record=sel_record,
        fields=fields,
        bases=bases,
        base=base,
        message=["none", ""],
    )
    try:
        return render_template(**context)
    except exceptions.UndefinedError as ex:
        message = f"Ошибка в имени поля! Внесите в файле fields.py в fields поле {str(ex).split('attribute')[-1]}"
        context["sel_record"] = 0
        return render_template(template_name_or_list="index.html", message=message)


@bp.route("/sorting/<id>")
def sorting(id):
    """Сортировка столбца по параметру"""
    param_is_sorted = session.get("param_is_sorted")
    command = session.get("command")
    command_2 = session.get("command_2")
    sort_asc = session.get("sort_asc")

    if id in FIELD_FOR_SORTING:
        # сброс режима изменения строки
        session["sel_record"] = 0
        if id in ("size", "case"):
            other = ", U ASC, I ASC"
        elif id == "U":
            other = ", C ASC"
        else:
            other = ""

        if not param_is_sorted:
            command_2 = command
            command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
            sort_asc = not sort_asc
            session["param_is_sorted"] = True

        else:
            command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
            sort_asc = not sort_asc

    session["command"] = command
    session["command_2"] = command_2
    session["sort_asc"] = sort_asc

    return redirect("/")


@bp.route("/change_mode/<id>")
def change_mode(id):
    """Вход/выход в режим изменения строки"""

    if id.isdigit():
        sel_record = session.get("sel_record")
        session["new_added"] = False
        # разрешаем изменение строки с номером id. sel_record передается через / в html
        if sel_record == 0 or sel_record != int(id):
            sel_record = int(id)
        else:
            sel_record = 0
        session["sel_record"] = sel_record
    return redirect("/")


@bp.route("/change/<id>", methods=["POST"])
def change(id):
    """Изменение строки после вхождения в режим change_mode"""
    base = session["base"]
    # db = ControlDatabase(base)
    table = Bases[base]

    multidict = dict(request.form)
    multidict.pop("csrf_token")
    # внесение изменений
    if len(multidict) == 1:
        category, name = db.select(
            base=base,
            query=f"SELECT category, name FROM {table} WHERE id = {id}",
        )[0]
        if multidict.get("status"):
            status = multidict.get("status")
            statuses = session["fields_from_base"][3]
            if status not in statuses:
                redirect("/")
            value_old = db.select(
                base=base, query=f"SELECT status FROM {table} WHERE id = {id}"
            )[0][0]
            if isinstance(value_old, str):
                value_old = value_old.rstrip().lstrip()
                print(value_old)
            db.update(
                base=base,
                query=f"""UPDATE {table} SET `status` = '{status}' WHERE id = {id}""",
            )
            logger.info(
                f"Для {category} {name} изменен статус с '{value_old}' на '{status}'"
            )
            if status == "принято":
                count_ordered = db.select(
                    base=base,
                    query=f"""SELECT `count_ordered` FROM {table} WHERE id = {id}""",
                )[0][0]
                count_old = db.select(
                    base=base, query=f"SELECT `count` FROM {table} WHERE id = {id}"
                )[0][0]
                db.update(
                    base=base,
                    query=f"""UPDATE {table} SET `count_ordered` = 0 WHERE id = {id}""",
                )
                db.update(
                    base=base,
                    query=f"""UPDATE {table} SET `count` = `count` + {count_ordered} WHERE id = {id}""",
                )
                logger.info(
                    f"{category} {name}: <i>count_ordered</i> '{count_ordered}' => '0'"
                )
                logger.info(
                    f"{category} {name}: <i>count</i> '{count_old}' => '{count_old + count_ordered}'"
                )
        else:
            key_val = list(multidict.items())[0]
            res = key_val[1]
            field = key_val[0]
            value_old = db.select(
                base=base, query=f"SELECT `{field}` FROM {table} WHERE id = {id}"
            )[0][0]
            if isinstance(value_old, str):
                value_old = value_old.rstrip().lstrip()
            if res is not None:
                if (
                    field
                    in (
                        "count",
                        "price_market",
                        "price_deliv",
                        "count_ordered",
                        "price_sale",
                        "count_sold",
                    )
                    and not res
                ):
                    res = 0
                query = f"""UPDATE {table} SET `{field}` = ? WHERE id = {id}"""
                db.update(base=base, query=query, param=res)
            if not res:
                logger.info(f"Для {category} {name} поле <i>{field}</i> очищено")
            if res:
                if field == "market":
                    field = "расписка"
                elif field == "history":
                    field = "дата"
                # print("logger")
                logger.info(
                    f"{category} {name}: <i>{field}</i> '{value_old}' => '{res}'"
                )
    # изменение R и C
    elif len(multidict) == 2:
        category, name = db.select(
            base=base, query=f"SELECT category, name FROM {table} WHERE id = {id}"
        )[0]
        data = list(multidict.items())
        res_1 = data[0][1]
        name_1 = data[0][0]
        res_2 = data[1][1]
        name_2 = data[1][0]
        if res_1 is not None:
            query = f"""UPDATE {table} SET `{name_1}` = ? WHERE id = {id}"""
            db.update(base=base, query=query, param=res_1)
        if res_2 is not None:
            query = f"""UPDATE {table} SET `{name_2}` = ? WHERE id = {id}"""
            db.update(base=base, query=query, param=res_2)
        logger.info(f"{category} {name}: <i>{name_1}</i> на {res_1} {res_2}")

    return redirect("/")


@bp.route("/add/<id>", methods=["POST"])
def add(id):
    base = session["base"]
    # db = ControlDatabase(base)
    table = Bases[base]

    form_1 = PhotoForm()
    form_2 = ManualForm()
    if form_1.validate_on_submit():
        query, name = load_file(table, f=form_1.photo.data, field="photo", rec_id=id)
        db.update(base=base, query=query, param=name)
    elif form_2.validate_on_submit():
        query, name = load_file(table, f=form_2.manual.data, field="manual", rec_id=id)
        db.update(base=base, query=query, param=name)

    multidict = dict(request.form)
    multidict.pop("csrf_token")
    category = multidict.get("category")

    if category:
        multidict = dict(multidict)
        multidict.update({"category": category})
        session["id_added"] = db.insert(base=base, names_dict=multidict)
        session["new_added"] = True
    return redirect("/")


@bp.route("/report")
def report():
    path_to_log = session["path_to_log"]

    with open(path_to_log, "r") as obj:
        text = obj.read()
    text_list = []
    for string in text.split("\n")[::-1]:
        length = string.__len__()
        if length > SIZE_BLOCK:
            string_divided = div_string(string_all=string, size_block=SIZE_BLOCK)
            text_list.extend(string_divided)
        else:
            text_list.append(string)
    text = "\n".join(text_list)
    return f"<pre style='font-size: 25; background-color: #ebeef2;'>{text}</pre>"


@bp.route("/static/files/<folder>/<name>")
def redirect_from_photo(folder, name):
    """Перенаправление с клика по photo, если в fields.json задан параметр url_for_redirect_from_photo"""
    url_for_redirect_from_photo = session["url_for_redirect_from_photo"]
    return redirect(f"{url_for_redirect_from_photo}/{folder}/{name}")
