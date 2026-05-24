import datetime
import json
import logging
import os

import transliterate
from werkzeug.utils import secure_filename

from models import ControlDatabase


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
    numbers_block = len(string_all) // size_block
    for numb in range(numbers_block):
        start = numb * size_block
        end = start + size_block
        string = string_all[start:end]
        list_strings.append(string)
    else:
        list_strings.append(string_all[end:])
    return list_strings


def load_file(f, field, rec_id, folder=""):
    filename = f.filename
    # print(filename)
    latin = transliterate.translit(filename, "ru", reversed=True)
    # Или unidecode (без установки transliterate)
    # latin = unidecode(filename)
    name = secure_filename(latin)
    f.save(os.path.join("static", "files", f"{folder}", name))
    query = f"""UPDATE zip SET `{field}` = ? WHERE id = {rec_id}"""
    return query, name


def get_fields(base):
    with open(f"profiles/{base}/fields.json", "r", encoding="utf-8") as file:
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
    from routes import Bases, app

    base: Bases = app.extensions.get("base")
    if base is None:
        app.extensions["base"], base = [Bases.baren] * 2
    app.extensions["storage"] = ControlDatabase(base.name)

    print(f"База {base.name}. Таблица {base.value}")

    base_is_changed = app.extensions.get("base_is_changed")
    fields_from_base = app.extensions.get("fields_from_base")

    if fields_from_base is None or base_is_changed:
        app.extensions["base_is_changed"] = False
        app.extensions["fields_from_base"] = get_fields(base.name)

    path_to_log = f"./profiles/{base.name}/{base.name}.log"
    app.extensions["path_to_log"] = path_to_log
    logging.basicConfig(
        filename=path_to_log,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S %p",
    )

    app.extensions["fields_order_out"] = []
    app.extensions["res"] = []
    app.extensions["command"] = ""
    app.extensions["command_2"] = ""
    app.extensions["param_is_sorted"] = False
    app.extensions["summ_some_fields"] = 0
    app.extensions["format_cut"] = True
    app.extensions["sel_record"] = 0
    app.extensions["new_added"] = False
    app.extensions["result"] = []
    app.extensions["sort_asc"] = True
