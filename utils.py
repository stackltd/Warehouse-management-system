import datetime
import json
import logging
import os

import transliterate
from werkzeug.utils import secure_filename

from models import exe


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


def load_file(base, f, field, rec_id, folder=""):
    filename = f.filename
    # print(filename)
    latin = transliterate.translit(filename, "ru", reversed=True)
    # Или unidecode (без установки transliterate)
    # latin = unidecode(filename)
    name = secure_filename(latin)
    f.save(os.path.join("static", "files", f"{folder}", name))
    query = f"""UPDATE zip SET `{field}` = ? WHERE id = {rec_id}"""
    exe(query=query, param=name, base=base)


def reconfigure_logging(path_to_log):
    """
    Переконфигурация логгера при смене базы
    :return:
    """
    logger = logging.getLogger()
    # Очистка обработчиков
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # Новый обработчик с нужным форматом
    handler = logging.FileHandler(filename=path_to_log)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(message)s", datefmt="%d-%m-%Y %H:%M:%S %p"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


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