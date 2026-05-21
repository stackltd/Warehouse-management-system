# import datetime
# import json
# import os
#
# import logging
#
# import transliterate
# from flask import Flask, request, render_template, redirect, g
# from jinja2 import exceptions
# from flask_wtf.file import FileField, FileRequired
# from werkzeug.utils import secure_filename
# from flask_wtf import FlaskForm
# # from waitress import serve
#
# from models import insert, exe, create_table
# from config import Bases
#
# base = Bases.baren.value
# bases = [member.value for member in Bases]
#
# app = Flask(__name__)
#
# app.logger.disabled = True
#
# log = logging.getLogger("werkzeug")
# log.disabled = True
#
# logger = logging.getLogger("логгер")
#
# path_to_log = f"./profiles/{base}/{base}.log"
# logging.basicConfig(
#     filename=path_to_log,
#     level=logging.INFO,
#     format="%(asctime)s - %(message)s",
#     datefmt="%d-%m-%Y %H:%M:%S %p",
# )
#
#
# class PhotoForm(FlaskForm):
#     photo = FileField(validators=[FileRequired()])
#
#
# class ManualForm(FlaskForm):
#     manual = FileField(validators=[FileRequired()])
#
#
# SORT_DIRECT = {True: "ASC", False: "DESC"}
#
#
# def initialize():
#     """Инициализация при запуске приложения и при смене базы"""
#     global fields, fields_params, fields_order, statuses, path_to_log, base, logger,\
#         res, fields_order_out, command, param_is_sorted, summ_some_fields,\
#         format_cut, sel_record, new_added, result, sort_asc, command_2, category, url_for_redirect_from_photo
#     print(f"Таблица {base}")
#
#     category = ""
#     result = []
#     res = []
#     fields_order_out = []
#     command = ""
#     command_2 = ""
#     param_is_sorted = False
#     summ_some_fields = 0
#     sort_asc = True
#     format_cut = True
#     sel_record = 0
#     new_added = False
#
#     with open(f"profiles/{base}/fields.json", "r", encoding="utf-8") as file:
#         result_dict: dict = json.load(file)
#
#     fields, fields_params, fields_order, statuses, url_for_redirect_from_photo = [
#         result_dict.get(field, "")
#         for field in ("fields", "fields_params", "fields_order", "statuses", "url_for_redirect_from_photo")
#     ]
#
# def reconfigure_logging():
#     """
#     Переконфигурация логгера при смене базы
#     :return:
#     """
#     global path_to_log
#     path_to_log = f"./profiles/{base}/{base}.log"
#     logger = logging.getLogger()
#     # Очистка обработчиков
#     for handler in logger.handlers[:]:
#         logger.removeHandler(handler)
#     # Новый обработчик с нужным форматом
#     handler = logging.FileHandler(filename=path_to_log)
#     formatter = logging.Formatter(
#         fmt="%(asctime)s - %(message)s", datefmt="%d-%m-%Y %H:%M:%S %p"
#     )
#     handler.setFormatter(formatter)
#     handler.setLevel(logging.INFO)
#
#     logger.addHandler(handler)
#     logger.setLevel(logging.INFO)
#
#
# # Закрытие соединения с базой данных после завершения запроса
# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(g, "_database", None)
#     if db is not None:
#         # print("close_connection")
#         db.close()
#
#
# @app.route("/base_choose", methods=["POST"])
# def base_choose():
#     """
#     Функция смены базы
#     :return:
#     """
#     global base
#     base = request.form.get("base_name")
#     initialize()
#     reconfigure_logging()
#     return redirect("/")
#
#
# @app.route("/", methods=["GET", "POST"])
# def stock():
#
#     def str_corr(str_in, ind):
#         """
#         Коррекция полученных данных, для отображения их пользователю
#         :param str_in: текущая строка из полученного массива
#         :param ind: индекс для нумерации от 1 до N
#         :return:
#         """
#         string_correct = [val if val is not None else "" for val in str_in]
#         # округление полей, где нет дробной части
#         string_correct = [
#             int(val) if isinstance(val, float) and val % 1 == 0 else val
#             for val in string_correct
#         ]
#         # добавляем к полям R и C строку с множителем
#         string_correct = [
#             (
#                 " ".join((str(val), string_correct[14]))
#                 if ind in (11, 12) and val != ""
#                 else val
#             )
#             for ind, val in enumerate(string_correct)
#         ]
#         # выделяем цветом просроченные заказы
#         current_date = datetime.datetime.now().date()
#         data_from_db = string_correct[18]
#         color_date = "black"
#         if data_from_db:
#             try:
#                 order_date = datetime.datetime.strptime(data_from_db, "%d.%m.%y").date()
#                 delta = (current_date - order_date).days
#                 color_date = (
#                     "red"
#                     if delta >= 0 and string_correct[29] in ["заказано", "со сроком"]
#                     else "black"
#                 )
#             except ValueError:
#                 color_date = "#b4c0e9"
#         string_correct.append(color_date)
#         string_correct.append(ind)
#         return string_correct
#
#     global res, fields_order_out, command, param_is_sorted, summ_some_fields, format_cut, sel_record, new_added, result
#
#     multidict = request.form
#     # формат вывода полей - полный/сокращённый
#     if multidict.get("format") is not None:
#         format_cut = not format_cut
#         if not format_cut:
#             fields_order_out = fields_order
#         else:
#             fields_order_out = []
#
#     if (
#         set(multidict.keys()).intersection(set(fields.keys()))
#         or multidict.get("вывести всё")
#         or multidict.get("заказы")
#     ):
#         result.clear()
#         sel_record = 0  # сброс режима изменения строки
#         param_is_sorted = False
#         fields_list = [f"'{x}'" for x in multidict]
#         fields_str = ", ".join(fields_list)
#         if multidict.get("вывести всё"):
#             command = """SELECT * FROM zip ORDER BY category"""
#             res = exe(query=command, base=base)
#         elif multidict.get("заказы"):
#             command = f"""SELECT * FROM zip WHERE status in ({', '.join([f"'{x}'" for x in statuses][:-1])}) ORDER BY history"""
#             res = exe(query=command, base=base)
#             # print(f"{res = }")
#         else:
#             command = f"""SELECT * FROM zip WHERE category IN ({fields_str}) ORDER BY category"""
#             res = exe(query=command, base=base)
#     elif not multidict:
#         res = exe(query=command, base=base)
#         result.clear()
#     # history
#     if res:
#         result.clear()
#         for ind, string in enumerate(res):
#             string_correct = str_corr(str_in=string, ind=ind + 1)
#             result.append(string_correct)
#
#         # помещаем вновь добавленную запись наверх и выделяем цветом до внесения первого изменения, или обновления
#         if new_added:
#             all_id = [x[0] for x in result]
#             # print("id_added", id_added, base, all_id)
#             if id_added not in all_id:
#                 rec_added = exe(
#                     f"""SELECT * FROM zip WHERE id = {id_added}""", base=base
#                 )[0]
#                 string_correct = str_corr(str_in=rec_added, ind=len(result) + 1)
#                 result_2 = [string_correct]
#             else:
#                 rec_added = [x for x in result if x[0] == id_added][0]
#                 result.remove(rec_added)
#                 result_2 = [rec_added]
#             result_2.extend(result)
#             result = result_2
#             sel_record = result[0][0]
#
#         # суммирование значений некоторых столбцов
#         summ_some_fields = {"summ": 0, "summ_sold": 0, "count_sold": 0}
#         for field in summ_some_fields:
#             summ_some_fields[field] = exe(
#                 f"""SELECT CAST(SUM({field}) AS INTEGER) FROM ({command})""", base=base
#             )[0][0]
#     categories = sorted(list(fields.keys()))
#     try:
#         return render_template(
#             "index.html",
#             categories=categories,
#             fields_params=fields_params,
#             fields_order=fields_order_out,
#             result=result,
#             summ_some_fields=summ_some_fields,
#             statuses=statuses,
#             sel_record=sel_record,
#             fields=fields,
#             message=["none", ""],
#             bases=bases,
#             base=base,
#         )
#     except exceptions.UndefinedError as ex:
#         # raise
#         print(f"{ex = }")
#         sel_record = 0
#         message = f"Ошибка в имени поля! Внесите в файле fields.py в fields поле {str(ex).split('attribute')[-1]}"
#         return render_template(
#             "index.html",
#             categories=categories,
#             fields_params=fields_params,
#             fields_order=fields_order_out,
#             result=result,
#             summ_some_fields=summ_some_fields,
#             statuses=statuses,
#             sel_record=sel_record,
#             fields=fields,
#             message=["inline-block", message],
#         )
#
#
# @app.route("/change/<id>", methods=["GET", "POST"])
# def change(id):
#     global command, param_is_sorted, command_2, sort_asc, sel_record, new_added, field_id_inverted
#     multidict = request.form
#     # внесение изменений
#     if len(multidict) == 1:
#         category, name = exe(
#             f"SELECT category, name FROM zip WHERE id = {id}", base=base
#         )[0]
#         if multidict.get("status"):
#             res = multidict.get("status")
#             value_old = exe(f"SELECT status FROM zip WHERE id = {id}", base=base)[0][0]
#             if isinstance(value_old, str):
#                 value_old = value_old.rstrip().lstrip()
#                 print(value_old)
#             exe(
#                 query=f"""UPDATE zip SET `status` = '{res}' WHERE id = {id}""",
#                 base=base,
#             )
#             logger.info(
#                 f"Для {category} {name} изменен статус с '{value_old}' на '{res}'"
#             )
#             if res == "принято":
#                 count_ordered = exe(
#                     query=f"""SELECT `count_ordered` FROM zip WHERE id = {id}""",
#                     base=base,
#                 )[0][0]
#                 count_old = exe(f"SELECT `count` FROM zip WHERE id = {id}", base=base)[
#                     0
#                 ][0]
#                 exe(
#                     query=f"""UPDATE zip SET `count_ordered` = 0 WHERE id = {id}""",
#                     base=base,
#                 )
#                 exe(
#                     query=f"""UPDATE zip SET `count` = `count` + {count_ordered} WHERE id = {id}""",
#                     base=base,
#                 )
#                 logger.info(
#                     f"{category} {name}: <i>count_ordered</i> '{count_ordered}' => '0'"
#                 )
#                 logger.info(
#                     f"{category} {name}: <i>count</i> '{count_old}' => '{count_old + count_ordered}'"
#                 )
#         else:
#             key_val = list(multidict.items())[0]
#             res = key_val[1]
#             field = key_val[0]
#             value_old = exe(f"SELECT `{field}` FROM zip WHERE id = {id}", base=base)[0][
#                 0
#             ]
#             if isinstance(value_old, str):
#                 value_old = value_old.rstrip().lstrip()
#             if res is not None:
#                 if (
#                     field
#                     in (
#                         "count",
#                         "price_market",
#                         "price_deliv",
#                         "count_ordered",
#                         "price_sale",
#                         "count_sold",
#                     )
#                     and not res
#                 ):
#                     res = 0
#                 query = f"""UPDATE zip SET `{field}` = ? WHERE id = {id}"""
#                 exe(query=query, param=res, base=base)
#             if not res:
#                 logger.info(f"Для {category} {name} поле <i>{field}</i> очищено")
#             if res:
#                 if field == "market":
#                     field = "расписка"
#                 elif field == "history":
#                     field = "дата"
#                 logger.info(
#                     f"{category} {name}: <i>{field}</i> '{value_old}' => '{res}'"
#                 )
#     # изменение R и C
#     elif len(multidict) == 2:
#         category, name = exe(
#             f"SELECT category, name FROM zip WHERE id = {id}", base=base
#         )[0]
#         data = list(multidict.items())
#         res_1 = data[0][1]
#         name_1 = data[0][0]
#         res_2 = data[1][1]
#         name_2 = data[1][0]
#         if res_1 is not None:
#             query = f"""UPDATE zip SET `{name_1}` = ? WHERE id = {id}"""
#             exe(query=query, param=res_1, base=base)
#         if res_2 is not None:
#             query = f"""UPDATE zip SET `{name_2}` = ? WHERE id = {id}"""
#             exe(query=query, param=res_2, base=base)
#         logger.info(f"{category} {name}: <i>{name_1}</i> на {res_1} {res_2}")
#     # реализация сортировки
#     elif id in (
#         "id",
#         "category",
#         "type",
#         "name",
#         "size",
#         "case",
#         "for",
#         "U",
#         "I",
#         "R",
#         "C",
#         "P",
#         "count",
#         "status",
#         "history",
#         "market",
#     ):
#         sel_record = 0  # сброс режима изменения строки
#         # other = ", U ASC, I ASC" if id in ("size", "case") else ""
#         if id in ("size", "case"):
#             other = ", U ASC, I ASC"
#         elif id == "U":
#             other = ", C ASC"
#         else:
#             other = ""
#
#         if not param_is_sorted:
#             command_2 = command
#             command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
#             sort_asc = not sort_asc
#             param_is_sorted = True
#         else:
#             command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
#             sort_asc = not sort_asc
#     elif id.isdigit():
#         new_added = False
#         # разрешаем изменение строки с номером id. sel_record передается через / в html
#         if sel_record == 0 or sel_record != int(id):
#             sel_record = int(id)
#         else:
#             sel_record = 0
#     return redirect("/")
#
#
# @app.route("/add/<id>", methods=["POST"])
# def add(id):
#     # from unidecode import unidecode
#     def load_file(f, field, rec_id, folder=""):
#         filename = f.filename
#         # print(filename)
#         latin = transliterate.translit(filename, 'ru', reversed=True)
#         # Или unidecode (без установки transliterate)
#         # latin = unidecode(filename)
#         name = secure_filename(latin)
#         f.save(os.path.join("static", "files", f"{folder}", name))
#         query = f"""UPDATE zip SET `{field}` = ? WHERE id = {rec_id}"""
#         exe(query=query, param=name, base=base)
#
#     global category, new_added, id_added
#
#     form_1 = PhotoForm()
#     form_2 = ManualForm()
#     if form_1.validate_on_submit():
#         load_file(f=form_1.photo.data, field="photo", rec_id=id)
#     elif form_2.validate_on_submit():
#         load_file(f=form_2.manual.data, field="manual", rec_id=id)
#
#     multidict = request.form
#     category = multidict.get("category")
#     if category:
#         multidict = dict(multidict)
#         multidict.update({"category": category})
#         # print(f"{multidict = }")
#         id_added = insert(names_dict=multidict, base=base)
#         # print("multidict", multidict, "base", base, "id_added = insert(names_dict=multidict)", id_added)
#         new_added = True
#     return redirect("/")
#
#
# @app.route("/report")
# def report():
#     # print("report", path_to_log)
#
#     def div_string(string_all, size_block):
#         """
#         Функция разделяет строки длиной более size_block на части
#         :param string_all:
#         :param size_block:
#         :return:
#         """
#         list_strings = []
#         numbers_block = len(string_all) // size_block
#         for numb in range(numbers_block):
#             start = numb * size_block
#             end = start + size_block
#             string = string_all[start:end]
#             list_strings.append(string)
#         else:
#             list_strings.append(string_all[end:])
#         return list_strings
#
#     with open(path_to_log, "r") as obj:
#         text = obj.read()
#     size_block = 135
#     text_list = []
#     # text = "\n".join(text.split("\n")[::-1])
#     for string in text.split("\n")[::-1]:
#         length = string.__len__()
#         if length > size_block:
#             string_divided = div_string(string_all=string, size_block=size_block)
#             text_list.extend(string_divided)
#         else:
#             text_list.append(string)
#     text = "\n".join(text_list)
#     return f"<pre style='font-size: 25; background-color: #ebeef2;'>{text}</pre>"
#
#
#
# @app.route("/static/files/<folder>/<name>")
# def redirect_from_photo(folder, name):
#     """Перенаправление с клика по photo, если в fields.json задан параметр url_for_redirect_from_photo"""
#     return redirect(f"{url_for_redirect_from_photo}/{folder}/{name}")
#
#
# if __name__ == "__main__":
#     create_table(base=base)
#     initialize()
#     app.config["WTF_CSRF_ENABLED"] = False
#     # logging.getLogger('waitress').setLevel(logging.ERROR)
#     # serve(app, host="0.0.0.0", port=8080)
#     app.run(host="0.0.0.0", port=8080, debug=True)


import json

import logging

from flask import Flask, request, render_template, redirect, g, session
from jinja2 import exceptions
from flask_wtf.csrf import CSRFProtect
from waitress import serve

from forms import ManualForm, PhotoForm
from models import insert, exe, create_table
from config import Bases
from utils import str_corr, load_file, reconfigure_logging, div_string, get_fields

base = Bases.baren.value

print(f"Таблица {base}")

bases = [member.value for member in Bases]

app = Flask(__name__)
csrf = CSRFProtect(app)

app.logger.disabled = True

log = logging.getLogger("werkzeug")
log.disabled = True

logger = logging.getLogger("логгер")

path_to_log = f"./profiles/{base}/{base}.log"
logging.basicConfig(
    filename=path_to_log,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S %p",
)


SORT_DIRECT = {True: "ASC", False: "DESC"}
SIZE_BLOCK = 135


def initialize():
    """Инициализация при запуске приложения и при смене базы"""
    global res, fields_order_out, command, param_is_sorted, summ_some_fields, format_cut, sel_record, new_added, result, sort_asc, command_2

    print(app.extensions.get("base"))

    result = []
    res = []
    fields_order_out = []
    command = ""
    command_2 = ""
    param_is_sorted = False
    summ_some_fields = 0
    sort_asc = True
    format_cut = True
    sel_record = 0
    new_added = False


# Закрытие соединения с базой данных после завершения запроса
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/base_choose", methods=["POST"])
def base_choose():
    """
    Функция смены базы
    :return:
    """

    session["base_is_changed"] = True
    base = request.form.get("base_name")
    app.extensions["base"] = base
    session["base"] = base
    print(f"Смена таблицы на {base}")

    session["base_is_changed"] = True
    path_to_log = f"./profiles/{base}/{base}.log"
    session["path_to_log"] = path_to_log

    initialize()
    reconfigure_logging(path_to_log)
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
def stock():
    base = session.get("base", Bases.baren.value)

    base_is_changed = session.get("base_is_changed")
    fields_from_base = session.get("fields_from_base")

    if fields_from_base is None or base_is_changed:
        session["base_is_changed"] = False
        session["fields_from_base"] = json.dumps(get_fields(base))


    fields, fields_params, fields_order, statuses, url_for_redirect_from_photo = json.loads(session["fields_from_base"])
    session["url_for_redirect_from_photo"] = url_for_redirect_from_photo

    global res, fields_order_out, command, param_is_sorted, summ_some_fields, format_cut, sel_record, new_added, result

    multidict = request.form
    # формат вывода полей - полный/сокращённый
    if multidict.get("format") is not None:
        format_cut = not format_cut
        if not format_cut:
            fields_order_out = fields_order
        else:
            fields_order_out = []

    if (
        set(multidict.keys()).intersection(set(fields.keys()))
        or multidict.get("вывести всё")
        or multidict.get("заказы")
    ):
        result.clear()
        sel_record = 0  # сброс режима изменения строки
        param_is_sorted = False
        fields_list = [f"'{x}'" for x in multidict]
        fields_str = ", ".join(fields_list)
        if multidict.get("вывести всё"):
            command = """SELECT * FROM zip ORDER BY category"""
            res = exe(query=command, base=base)
        elif multidict.get("заказы"):
            command = f"""SELECT * FROM zip WHERE status in ({', '.join([f"'{x}'" for x in statuses][:-1])}) ORDER BY history"""
            res = exe(query=command, base=base)
            # print(f"{res = }")
        else:
            command = f"""SELECT * FROM zip WHERE category IN ({fields_str}) ORDER BY category"""
            res = exe(query=command, base=base)
    elif not multidict:
        res = exe(query=command, base=base)
        result.clear()
    # history
    if res:
        result.clear()
        for ind, string in enumerate(res):
            string_correct = str_corr(str_in=string, ind=ind + 1)
            result.append(string_correct)

        # помещаем вновь добавленную запись наверх и выделяем цветом до внесения первого изменения, или обновления
        if new_added:
            all_id = [x[0] for x in result]
            # print("id_added", id_added, base, all_id)
            if id_added not in all_id:
                rec_added = exe(
                    f"""SELECT * FROM zip WHERE id = {id_added}""", base=base
                )[0]
                string_correct = str_corr(str_in=rec_added, ind=len(result) + 1)
                result_2 = [string_correct]
            else:
                rec_added = [x for x in result if x[0] == id_added][0]
                result.remove(rec_added)
                result_2 = [rec_added]
            result_2.extend(result)
            result = result_2
            sel_record = result[0][0]

        # суммирование значений некоторых столбцов
        summ_some_fields = {"summ": 0, "summ_sold": 0, "count_sold": 0}
        for field in summ_some_fields:
            summ_some_fields[field] = exe(
                f"""SELECT CAST(SUM({field}) AS INTEGER) FROM ({command})""", base=base
            )[0][0]
    categories = sorted(list(fields.keys()))
    try:
        return render_template(
            "index.html",
            categories=categories,
            fields_params=fields_params,
            fields_order=fields_order_out,
            result=result,
            summ_some_fields=summ_some_fields,
            statuses=statuses,
            sel_record=sel_record,
            fields=fields,
            message=["none", ""],
            bases=bases,
            base=base,
        )
    except exceptions.UndefinedError as ex:
        # raise
        print(f"{ex = }")
        sel_record = 0
        message = f"Ошибка в имени поля! Внесите в файле fields.py в fields поле {str(ex).split('attribute')[-1]}"
        return render_template(
            "index.html",
            categories=categories,
            fields_params=fields_params,
            fields_order=fields_order_out,
            result=result,
            summ_some_fields=summ_some_fields,
            statuses=statuses,
            sel_record=sel_record,
            fields=fields,
            message=["inline-block", message],
        )


@app.route("/change/<id>", methods=["GET", "POST"])
def change(id):
    base = session["base"]

    global command, param_is_sorted, command_2, sort_asc, sel_record, new_added, field_id_inverted
    multidict = dict(request.form)
    # удаляем csrf_token из multidict
    if multidict:
        multidict.pop("csrf_token")
    # внесение изменений
    if len(multidict) == 1:
        category, name = exe(
            f"SELECT category, name FROM zip WHERE id = {id}", base=base
        )[0]
        if multidict.get("status"):
            res = multidict.get("status")
            value_old = exe(f"SELECT status FROM zip WHERE id = {id}", base=base)[0][0]
            if isinstance(value_old, str):
                value_old = value_old.rstrip().lstrip()
                print(value_old)
            exe(
                query=f"""UPDATE zip SET `status` = '{res}' WHERE id = {id}""",
                base=base,
            )
            logger.info(
                f"Для {category} {name} изменен статус с '{value_old}' на '{res}'"
            )
            if res == "принято":
                count_ordered = exe(
                    query=f"""SELECT `count_ordered` FROM zip WHERE id = {id}""",
                    base=base,
                )[0][0]
                count_old = exe(f"SELECT `count` FROM zip WHERE id = {id}", base=base)[
                    0
                ][0]
                exe(
                    query=f"""UPDATE zip SET `count_ordered` = 0 WHERE id = {id}""",
                    base=base,
                )
                exe(
                    query=f"""UPDATE zip SET `count` = `count` + {count_ordered} WHERE id = {id}""",
                    base=base,
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
            value_old = exe(f"SELECT `{field}` FROM zip WHERE id = {id}", base=base)[0][
                0
            ]
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
                query = f"""UPDATE zip SET `{field}` = ? WHERE id = {id}"""
                exe(query=query, param=res, base=base)
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
        category, name = exe(
            f"SELECT category, name FROM zip WHERE id = {id}", base=base
        )[0]
        data = list(multidict.items())
        res_1 = data[0][1]
        name_1 = data[0][0]
        res_2 = data[1][1]
        name_2 = data[1][0]
        if res_1 is not None:
            query = f"""UPDATE zip SET `{name_1}` = ? WHERE id = {id}"""
            exe(query=query, param=res_1, base=base)
        if res_2 is not None:
            query = f"""UPDATE zip SET `{name_2}` = ? WHERE id = {id}"""
            exe(query=query, param=res_2, base=base)
        logger.info(f"{category} {name}: <i>{name_1}</i> на {res_1} {res_2}")
    # реализация сортировки
    elif id in (
        "id",
        "category",
        "type",
        "name",
        "size",
        "case",
        "for",
        "U",
        "I",
        "R",
        "C",
        "P",
        "count",
        "status",
        "history",
        "market",
    ):
        sel_record = 0  # сброс режима изменения строки
        # other = ", U ASC, I ASC" if id in ("size", "case") else ""
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
            param_is_sorted = True
        else:
            command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
            sort_asc = not sort_asc
    elif id.isdigit():
        new_added = False
        # разрешаем изменение строки с номером id. sel_record передается через / в html
        if sel_record == 0 or sel_record != int(id):
            sel_record = int(id)
        else:
            sel_record = 0
    return redirect("/")


@app.route("/add/<id>", methods=["POST"])
def add(id):
    base = session["base"]

    global new_added, id_added

    form_1 = PhotoForm()
    form_2 = ManualForm()
    if form_1.validate_on_submit():
        load_file(base, f=form_1.photo.data, field="photo", rec_id=id)
    elif form_2.validate_on_submit():
        load_file(base, f=form_2.manual.data, field="manual", rec_id=id)

    multidict = dict(request.form)
    multidict.pop("csrf_token")
    category = multidict.get("category")

    if category:
        multidict = dict(multidict)
        multidict.update({"category": category})
        # print(f"{multidict = }")
        id_added = insert(names_dict=multidict, base=base)
        # print("multidict", multidict, "base", base, "id_added = insert(names_dict=multidict)", id_added)
        new_added = True
    return redirect("/")


@app.route("/report")
def report():
    path_to_log = session["path_to_log"]

    with open(path_to_log, "r") as obj:
        text = obj.read()
    text_list = []
    # text = "\n".join(text.split("\n")[::-1])
    for string in text.split("\n")[::-1]:
        length = string.__len__()
        if length > SIZE_BLOCK:
            string_divided = div_string(string_all=string, size_block=SIZE_BLOCK)
            text_list.extend(string_divided)
        else:
            text_list.append(string)
    text = "\n".join(text_list)
    return f"<pre style='font-size: 25; background-color: #ebeef2;'>{text}</pre>"


@app.route("/static/files/<folder>/<name>")
def redirect_from_photo(folder, name):
    """Перенаправление с клика по photo, если в fields.json задан параметр url_for_redirect_from_photo"""
    url_for_redirect_from_photo = session["url_for_redirect_from_photo"]
    return redirect(f"{url_for_redirect_from_photo}/{folder}/{name}")


if __name__ == "__main__":
    # create_table(base=base)
    initialize()
    app.secret_key = "супер_секретный_ключ_который_никто_не_должен_знать"  # ключ для шифрования сессии
    # app.config["WTF_CSRF_ENABLED"] = False
    # logging.getLogger('waitress').setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", port=8080, debug=True)
