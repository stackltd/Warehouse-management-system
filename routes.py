import logging

from flask import Flask, request, render_template, redirect, g
from jinja2 import exceptions
from flask_wtf.csrf import CSRFProtect
from forms import ManualForm, PhotoForm

from models import ControlDatabase
from config import Bases, SORT_DIRECT, SIZE_BLOCK
from utils import str_corr, load_file, div_string, initialize

bases = [member.name for member in Bases]

app = Flask(__name__)
csrf = CSRFProtect(app)

app.logger.disabled = True

log = logging.getLogger("werkzeug")
log.disabled = True

logger = logging.getLogger("логгер")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/select_base")
def select_base():
    """
    Функция смены базы
    :return:
    """

    app.extensions["base_is_changed"] = True
    base_name = request.args.get("base_name")
    base = Bases[base_name]
    app.extensions["base"] = base
    # print("base, base.name, base.value", base, base.name, base.value)
    path_to_log = f"./profiles/{base.name}/{base.name}.log"
    app.extensions["path_to_log"] = path_to_log

    initialize()

    # смена логгера для новой базы
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
    return redirect("/")


@app.route("/")
def stock():
    base: Bases = app.extensions["base"]
    storage: ControlDatabase = app.extensions["storage"]
    table = base.value

    res = app.extensions.get("res")
    command = app.extensions.get("command")
    summ_some_fields = app.extensions.get("summ_some_fields")
    fields_order_out = app.extensions.get("fields_order_out")
    format_cut = app.extensions.get("format_cut")
    sel_record = app.extensions.get("sel_record")
    new_added = app.extensions.get("new_added")
    result = app.extensions.get("result")
    id_added = app.extensions.get("id_added")

    fields, fields_params, fields_order, statuses, url_for_redirect_from_photo = (
        app.extensions["fields_from_base"]
    )
    app.extensions["url_for_redirect_from_photo"] = url_for_redirect_from_photo

    multidict = request.args
    # формат вывода полей - полный/сокращённый
    if multidict.get("format") is not None:
        format_cut = not format_cut
        if not format_cut:
            fields_order_out = fields_order
        else:
            fields_order_out = []
        app.extensions["fields_order_out"] = fields_order_out
        app.extensions["format_cut"] = format_cut

    if (
        set(multidict.keys()).intersection(set(fields.keys()))
        or multidict.get("вывести всё")
        or multidict.get("заказы")
    ):
        result.clear()
        sel_record = 0  # сброс режима изменения строки
        app.extensions["param_is_sorted"] = False

        fields_list = [f"'{x}'" for x in multidict]
        fields_str = ", ".join(fields_list)
        if multidict.get("вывести всё"):
            command = f"""SELECT * FROM {table} ORDER BY category"""
        elif multidict.get("заказы"):
            command = f"""SELECT * FROM {table} WHERE status in ({', '.join([f"'{x}'" for x in statuses][:-1])}) ORDER BY history"""
        else:
            command = f"""SELECT * FROM {table} WHERE category IN ({fields_str}) ORDER BY category"""
        res = storage.exe(query=command)

    elif not multidict:
        result.clear()
        res = storage.exe(query=command)
    # history
    if res:
        result.clear()
        for ind, string in enumerate(res):
            string_correct = str_corr(str_in=string, ind=ind + 1)
            result.append(string_correct)

        # помещаем вновь добавленную запись наверх и выделяем цветом до внесения первого изменения, или обновления
        if new_added:
            all_id = [x[0] for x in result]
            if id_added not in all_id:
                rec_added = storage.exe(
                    f"""SELECT * FROM {table} WHERE id = {id_added}""",
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
            summ_some_fields[field] = storage.exe(
                f"""SELECT CAST(SUM({field}) AS INTEGER) FROM ({command})""",
            )[0][0]
        app.extensions["summ_some_fields"] = summ_some_fields

    categories = sorted(list(fields.keys()))

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
        base=base.name,
        message=["none", ""],
    )
    try:
        return render_template(**context)
    except exceptions.UndefinedError as ex:
        # raise
        print(f"{ex = }")
        sel_record = 0
        message = f"Ошибка в имени поля! Внесите в файле fields.py в fields поле {str(ex).split('attribute')[-1]}"
        context["sel_record"] = 0
        context["message"] = ["inline-block", message]
        return render_template(**context)
    finally:
        app.extensions["res"] = res
        app.extensions["command"] = command
        app.extensions["sel_record"] = sel_record
        app.extensions["result"] = result


@app.route("/sorting/<id>")
def sorting(id):
    """Сортировка столбца по параметру"""
    param_is_sorted = app.extensions.get("param_is_sorted")
    command = app.extensions.get("command")
    command_2 = app.extensions.get("command_2")
    sort_asc = app.extensions.get("sort_asc")

    if id in (
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
        app.extensions["sel_record"] = 0
        # сброс режима изменения строки
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
            app.extensions["param_is_sorted"] = True

        else:
            command = f"""SELECT * FROM ({command_2}) ORDER BY `{id}` {SORT_DIRECT[sort_asc]}{other}"""
            sort_asc = not sort_asc

    app.extensions["command"] = command
    app.extensions["command_2"] = command_2
    app.extensions["sort_asc"] = sort_asc

    return redirect("/")


@app.route("/change/<id>", methods=["GET", "POST"])
def change(id):
    """Изменение строки после вхождения в режим изменения"""
    storage: ControlDatabase = app.extensions["storage"]
    base: Bases = app.extensions["base"]
    table = base.value

    # вход в режим изменения строки
    if id.isdigit() and request.method == "GET":
        sel_record = app.extensions.get("sel_record")
        app.extensions["new_added"] = False
        # разрешаем изменение строки с номером id. sel_record передается через / в html
        if sel_record == 0 or sel_record != int(id):
            sel_record = int(id)
        else:
            sel_record = 0
        app.extensions["sel_record"] = sel_record

    elif request.method == "POST":
        multidict = dict(request.form)
        multidict.pop("csrf_token")
        # внесение изменений
        if len(multidict) == 1:
            category, name = storage.exe(
                f"SELECT category, name FROM {table} WHERE id = {id}",
            )[0]
            if multidict.get("status"):
                res = multidict.get("status")
                value_old = storage.exe(f"SELECT status FROM {table} WHERE id = {id}")[
                    0
                ][0]
                if isinstance(value_old, str):
                    value_old = value_old.rstrip().lstrip()
                    print(value_old)
                storage.exe(
                    query=f"""UPDATE {table} SET `status` = '{res}' WHERE id = {id}"""
                )
                logger.info(
                    f"Для {category} {name} изменен статус с '{value_old}' на '{res}'"
                )
                if res == "принято":
                    count_ordered = storage.exe(
                        query=f"""SELECT `count_ordered` FROM {table} WHERE id = {id}""",
                    )[0][0]
                    count_old = storage.exe(
                        f"SELECT `count` FROM {table} WHERE id = {id}"
                    )[0][0]
                    storage.exe(
                        query=f"""UPDATE {table} SET `count_ordered` = 0 WHERE id = {id}""",
                    )
                    storage.exe(
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
                value_old = storage.exe(
                    f"SELECT `{field}` FROM {table} WHERE id = {id}"
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
                    storage.exe(query=query, param=res)
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
            category, name = storage.exe(
                f"SELECT category, name FROM {table} WHERE id = {id}"
            )[0]
            data = list(multidict.items())
            res_1 = data[0][1]
            name_1 = data[0][0]
            res_2 = data[1][1]
            name_2 = data[1][0]
            if res_1 is not None:
                query = f"""UPDATE {table} SET `{name_1}` = ? WHERE id = {id}"""
                storage.exe(query=query, param=res_1)
            if res_2 is not None:
                query = f"""UPDATE {table} SET `{name_2}` = ? WHERE id = {id}"""
                storage.exe(query=query, param=res_2)
            logger.info(f"{category} {name}: <i>{name_1}</i> на {res_1} {res_2}")
    return redirect("/")


@app.route("/add/<id>", methods=["POST"])
def add(id):
    storage: ControlDatabase = app.extensions["storage"]
    base: Bases = app.extensions["base"]
    table = base.value

    form_1 = PhotoForm()
    form_2 = ManualForm()
    if form_1.validate_on_submit():
        query, name = load_file(table, f=form_1.photo.data, field="photo", rec_id=id)
        storage.exe(query=query, param=name)
    elif form_2.validate_on_submit():
        query, name = load_file(table, f=form_2.manual.data, field="manual", rec_id=id)
        storage.exe(query=query, param=name)

    multidict = dict(request.form)
    multidict.pop("csrf_token")
    category = multidict.get("category")

    if category:
        multidict = dict(multidict)
        multidict.update({"category": category})
        app.extensions["id_added"] = storage.insert(names_dict=multidict)
        app.extensions["new_added"] = True
    return redirect("/")


@app.route("/report")
def report():
    print("report")
    path_to_log = app.extensions["path_to_log"]

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


@app.route("/static/files/<folder>/<name>")
def redirect_from_photo(folder, name):
    """Перенаправление с клика по photo, если в fields.json задан параметр url_for_redirect_from_photo"""
    url_for_redirect_from_photo = app.extensions["url_for_redirect_from_photo"]
    return redirect(f"{url_for_redirect_from_photo}/{folder}/{name}")
