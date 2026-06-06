import datetime
import json
import logging
import os
from logging.handlers import RotatingFileHandler

import redis
import transliterate
from flask import session
from werkzeug.utils import secure_filename

from webapp.config import Bases
from webapp.models import logger

waitress_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
waitress_handler = RotatingFileHandler(
    "logs/waitress.log", maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
waitress_handler.setFormatter(waitress_formatter)
waitress_logger = logging.getLogger("waitress")  # Создаем изолированный логгер
waitress_logger.setLevel(logging.DEBUG)
waitress_logger.addHandler(waitress_handler)
waitress_logger.debug("start")


def str_corr(str_in, ind):
    """
    Коррекция полученных данных, для отображения их пользователю
    :param str_in: текущая строка из полученного массива
    :param ind: индекс для нумерации от 1 до N
    :return:
    """
    string_correct = [val if val is not None else "" for val in str_in]
    # округление полей, где нет дробной части
    string_correct = [
        int(val) if isinstance(val, float) and val % 1 == 0 else val
        for val in string_correct
    ]
    # добавляем к полям R и C строку с множителем
    string_correct = [
        (
            " ".join((str(val), string_correct[14]))
            if ind in (11, 12) and val != ""
            else val
        )
        for ind, val in enumerate(string_correct)
    ]
    # выделяем цветом просроченные заказы
    current_date = datetime.datetime.now().date()
    data_from_db = string_correct[18]
    color_date = "black"
    if data_from_db:
        try:
            order_date = datetime.datetime.strptime(data_from_db, "%d.%m.%y").date()
            delta = (current_date - order_date).days
            color_date = (
                "red"
                if delta >= 0 and string_correct[29] in ["заказано", "со сроком"]
                else "black"
            )
        except ValueError:
            color_date = "#b4c0e9"
    string_correct.append(color_date)
    string_correct.append(ind)
    return string_correct


def div_string(string_all, size_block):
    """
    Функция разделяет строки длиной более size_block на части
    :param string_all:
    :param size_block:
    :return:
    """
    list_strings = []
    end = 0
    numbers_block = len(string_all) // size_block
    for numb in range(numbers_block):
        start = numb * size_block
        end = start + size_block
        string = string_all[start:end]
        list_strings.append(string)
    else:
        list_strings.append(string_all[end:])
    return list_strings


def load_file(table, f, field, rec_id, folder=""):
    filename = f.filename
    latin = transliterate.translit(filename, "ru", reversed=True)
    name = secure_filename(latin)
    f.save(os.path.join("webapp", "static", "files", f"{folder}", name))
    query = f"""UPDATE {table} SET `{field}` = ? WHERE id = {rec_id}"""
    return query, name


def get_fields(base):
    with open(f"./webapp/profiles/{base}/fields.json", "r", encoding="utf-8") as file:
        result_dict: dict = json.load(file)

    result = [
        result_dict.get(field, "")
        for field in (
            "fields",
            "fields_params",
            "fields_order",
            "statuses",
            "url_for_redirect_from_photo",
        )
    ]
    return result


def initialize():
    """Инициализация при запуске приложения/смене базы"""

    logger.debug("initialize")
    base = session.get("base")
    if base is None:
        return

    session["base"] = base
    print(f"База {base}, таблица {Bases[base]}")

    base_is_changed = session.get("base_is_changed")
    fields_from_base = session.get("fields_from_base")

    if fields_from_base is None or base_is_changed:
        session["base_is_changed"] = False
        session["fields_from_base"] = json.dumps(get_fields(base))

    path_to_log = f"./webapp/profiles/{base}/{base}.log"
    session["path_to_log"] = path_to_log
    logging.basicConfig(
        filename=path_to_log,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S %p",
        encoding="utf-8",
    )

    session["fields_order_out"] = []
    session["res"] = []
    session["command"] = ""
    session["command_2"] = ""
    session["param_is_sorted"] = False
    session["summ_some_fields"] = 0
    session["format_cut"] = True
    session["sel_record"] = 0
    session["new_added"] = False
    session["result"] = []
    session["sort_asc"] = True


def clear_redis_cache():
    waitress_logger.debug("clear_redis_cache")

    """Сброс данных в redis"""
    # Инициализируем подключение к Redis
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    print("Сервер останавливается! Очистка кэша Redis...")
    try:
        keys = redis_client.keys("session:*")
        if keys:
            redis_client.delete(*keys)
        print("Кэш Redis успешно очищен.")
    except Exception as e:
        print(f"Не удалось очистить Redis при закрытии: {e}")
