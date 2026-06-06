import json
import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import session, request
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from webapp.config import Bases, FIELD_FOR_SORTING, SORT_DIRECT, SIZE_BLOCK
from webapp.forms import PhotoForm, ManualForm
from webapp.models import ControlDatabase, User
from webapp.utils import str_corr, initialize, load_file, div_string
from webapp.exceptions import Unauthorized

logger = logging.getLogger("логгер")
logging.raiseExceptions = False

bases = [base_name for base_name in Bases]

r = redis.Redis(host="localhost", port=6379, db=0)

TIME_BLOCK = 60

#  НОВЫЙ ЛОГГЕР ДЛЯ АУТЕНТИФИКАЦИИ (только для входов и лимитеров)
auth_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
auth_handler = RotatingFileHandler(
    "logs/auth_attempts.log", maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
auth_handler.setFormatter(auth_formatter)

auth_logger = logging.getLogger("auth_events")  # Создаем изолированный логгер
auth_logger.setLevel(logging.INFO)
auth_logger.addHandler(auth_handler)
# отключаем передачу логов "наверх" в корневой логгер, чтобы логи входа не дублировались в консоли или других файлах
auth_logger.propagate = False

auth_log = logging.getLogger("auth_events")


class Service:
    def __init__(self, db: ControlDatabase):
        self.db = db

    def switch_base(self):
        """Сервисный метод смены базы данных"""
        base = request.args.get("base_name")
        if base not in bases:
            raise ValueError("Неверное имя базы данных")

        session["base_is_changed"] = True
        session["base"] = base
        path_to_log = f"./webapp/profiles/{base}/{base}.log"
        session["path_to_log"] = path_to_log

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

    def get_fields_for_render(self) -> dict:
        base = session.get("base")
        if base is None:
            raise ValueError("Не выбрана база")

        available_bases = current_user.available_bases or ""
        if available_bases and current_user.role != "admin":
            session["available_bases"] = available_bases.split()
        if current_user.role == "admin":
            session["available_bases"] = bases
        if current_user.role != "admin" and base not in available_bases:
            raise Unauthorized

        table = Bases[base]

        res = session.get("res")
        command = session.get("command")
        summ_some_fields = session.get("summ_some_fields")
        fields_order_out = session.get("fields_order_out")
        format_cut = session.get("format_cut")
        sel_record = session.get("sel_record")
        new_added = session.get("new_added")
        result = session.get("result")
        id_added = session.get("id_added")

        fields_from_base = session["fields_from_base"]
        fields, fields_params, fields_order, statuses, url_for_redirect_from_photo = (
            json.loads(fields_from_base)
        )
        session["url_for_redirect_from_photo"] = url_for_redirect_from_photo
        session["statuses"] = statuses

        multidict = request.args
        # формат вывода полей - полный/сокращённый
        if multidict.get("format") is not None:
            format_cut = not format_cut
            if not format_cut:
                fields_order_out = fields_order
            else:
                fields_order_out = []
            session["fields_order_out"] = fields_order_out
            session["format_cut"] = format_cut

        if (
            set(multidict.keys()).intersection(set(fields.keys()))
            or multidict.get("вывести всё")
            or multidict.get("заказы")
        ):
            result.clear()
            sel_record = 0  # сброс режима изменения строки
            session["param_is_sorted"] = False

            fields_list = [f"'{x}'" for x in multidict]
            fields_str = ", ".join(fields_list)
            if multidict.get("вывести всё"):
                command = f"""SELECT * FROM {table} ORDER BY category"""
            elif multidict.get("заказы"):
                command = f"""SELECT * FROM {table} WHERE status in ({', '.join([f"'{x}'" for x in statuses][:-1])}) ORDER BY history"""

            else:
                command = f"""SELECT * FROM {table} WHERE category IN ({fields_str}) ORDER BY category"""
            res = self.db.select(base=base, query=command)

        elif not multidict:
            result.clear()
            res = self.db.select(base=base, query=command)
        if res:
            result.clear()
            for ind, string in enumerate(res):
                string_correct = str_corr(str_in=string, ind=ind + 1)
                result.append(string_correct)

            # помещаем вновь добавленную запись наверх и выделяем цветом до внесения первого изменения, или обновления
            if new_added:
                all_id = [x[0] for x in result]
                if id_added not in all_id:
                    rec_added = self.db.select(
                        base=base,
                        query=f"""SELECT * FROM {table} WHERE id = {id_added}""",
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
                query = f"""SELECT CAST(SUM({field}) AS INTEGER) FROM ({command})"""
                summ_some_fields[field] = self.db.select(
                    base=base,
                    query=query,
                )[
                    0
                ][0]
            session["summ_some_fields"] = summ_some_fields

        categories = sorted(list(fields.keys()))

        session["res"] = res
        session["command"] = command
        session["sel_record"] = sel_record
        session["result"] = result

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
            bases=session.get("available_bases", bases),
            base=base,
            message=session.get("message", ["none", ""]),
        )

        return context

    @staticmethod
    def sorting_by_field(id):
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

    @staticmethod
    def change_mode(id):
        """Вход/выход в режим изменения строки"""
        sel_record = session.get("sel_record")
        session["new_added"] = False
        # разрешаем изменение строки с номером id. sel_record передается через / в html
        if sel_record == 0 or sel_record != int(id):
            sel_record = int(id)
        else:
            sel_record = 0
        session["sel_record"] = sel_record

    def change_field(self, id, multidict):
        base = session["base"]
        table = Bases[base]
        multidict.pop("csrf_token")
        # изменение R и C
        if multidict.keys() & {"R", "C"}:
            category, name = self.db.select(
                base=base, query=f"SELECT category, name FROM {table} WHERE id = {id}"
            )[0]
            data = list(multidict.items())
            res_1 = data[0][1]
            name_1 = data[0][0]
            res_2 = data[1][1]
            name_2 = data[1][0]
            if res_1 is not None:
                query = f"""UPDATE {table} SET `{name_1}` = ? WHERE id = {id}"""
                self.db.update(base=base, query=query, param=res_1)
            if res_2 is not None:
                query = f"""UPDATE {table} SET `{name_2}` = ? WHERE id = {id}"""
                self.db.update(base=base, query=query, param=res_2)
            logger.info(f"{category} {name}: <i>{name_1}</i> на {res_1} {res_2}")

        else:
            category, name = self.db.select(
                base=base,
                query=f"SELECT category, name FROM {table} WHERE id = {id}",
            )[0]
            if multidict.get("status"):
                status = multidict.get("status")
                statuses = session["statuses"]
                if status not in statuses:
                    return
                value_old = self.db.select(
                    base=base, query=f"SELECT status FROM {table} WHERE id = {id}"
                )[0][0]
                if isinstance(value_old, str):
                    value_old = value_old.rstrip().lstrip()
                self.db.update(
                    base=base,
                    query=f"""UPDATE {table} SET `status` = '{status}' WHERE id = {id}""",
                )
                logger.info(
                    f"Для {category} {name} изменен статус с '{value_old}' на '{status}'"
                )
                if status == "принято":
                    count_ordered = self.db.select(
                        base=base,
                        query=f"""SELECT `count_ordered` FROM {table} WHERE id = {id}""",
                    )[0][0]
                    count_old = self.db.select(
                        base=base, query=f"SELECT `count` FROM {table} WHERE id = {id}"
                    )[0][0]
                    self.db.update(
                        base=base,
                        query=f"""UPDATE {table} SET `count_ordered` = 0 WHERE id = {id}""",
                    )
                    self.db.update(
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
                value_old = self.db.select(
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
                    self.db.update(base=base, query=query, param=res)
                if not res:
                    logger.info(f"Для {category} {name} поле <i>{field}</i> очищено")
                if res:
                    if field == "market":
                        field = "расписка"
                    elif field == "history":
                        field = "дата"
                    logger.info(
                        f"{category} {name}: <i>{field}</i> '{value_old}' => '{res}'"
                    )

    def add_new_record(self, multidict):
        multidict.pop("csrf_token")
        base = session.get("base")
        if base is None:
            return
        category = multidict.get("category")

        if category:
            multidict = dict(multidict)
            multidict.update({"category": category})
            session["id_added"] = self.db.insert(base=base, names_dict=multidict)
            session["new_added"] = True

    def upload_file(self, id):
        base = session["base"]
        table = Bases[base]

        form_1 = PhotoForm()
        form_2 = ManualForm()
        if form_1.validate_on_submit():
            query, name = load_file(
                table, f=form_1.photo.data, field="photo", rec_id=id
            )
            self.db.update(base=base, query=query, param=name)
        elif form_2.validate_on_submit():
            query, name = load_file(
                table, f=form_2.manual.data, field="manual", rec_id=id
            )
            self.db.update(base=base, query=query, param=name)

    @staticmethod
    def report():
        path_to_log = session.get("path_to_log")
        if path_to_log is None:
            return "Нет данных"

        with open(path_to_log, "r") as obj:
            text = obj.read()
        text_list = []
        for string in text.split("\n")[::-1]:
            length = string.__len__()
            if all(
                map(
                    lambda x: x not in string,
                    (
                        "The CSRF session token is missing",
                        "The CSRF token has expired",
                        "The CSRF token is missing",
                        "Task queue depth",
                    ),
                )
            ):
                if length > SIZE_BLOCK:
                    string_divided = div_string(
                        string_all=string, size_block=SIZE_BLOCK
                    )
                    text_list.extend(string_divided)
                else:
                    text_list.append(string)
        text = "\n".join(text_list)
        return text

    @staticmethod
    def login(username, password):
        # Получаем IP-адрес клиента для уникальной идентификации
        user_ip = request.remote_addr
        # Ключи для Redis
        count_key = f"login_count:{user_ip}"
        lock_key = f"login_lock:{user_ip}"

        # Проверяем, есть ли в Redis флаг жесткой блокировки для этого IP
        if r.exists(lock_key):
            auth_log.warning(
                f"Попытка входа с IP {user_ip} (логин: {username}) после блокировки"
            )
            return (
                f"Слишком много попыток входа. Этот IP заблокирован на {TIME_BLOCK} секунд.",
                429,
            )

        # Если ключа не было, увеличиваем счетчик запросов в Redis
        current_requests = r.incr(count_key)
        # Если это первый запрос в серии, задаем ему время жизни (например, окно в 1 минуту)
        if current_requests == 1:
            r.expire(count_key, 60)

        # Если запросов стало больше 5
        if current_requests > 5:
            # Создаем ключ блокировки на определенное время
            r.setex(lock_key, TIME_BLOCK, "blocked")
            # Сбрасываем основной счетчик, чтобы после разблокировки начать заново
            r.delete(count_key)
            auth_log.warning(
                f"БЛОКИРОВКА | Превышен лимит попыток для IP:  {user_ip} (логин: {username})"
            )
            return (
                f"Слишком много попыток входа. Вы заблокированы на {TIME_BLOCK} секунд.",
                429,
            )

        user = User.get_user(
            query="SELECT * FROM user WHERE username = ?", param=(username,)
        )
        if user and check_password_hash(user.password_hash, password):
            # Flask-Login генерирует сессию, связывает её с Redis и прописывает куку в браузер
            login_user(user, remember=True)
            auth_log.info(
                f"УСПЕХ | Пользователь {username} успешно вошел в систему. IP: {user_ip}"
            )
            # Успешный вход — очищаем кэш попыток в Redis для этого IP
            r.delete(count_key)
            return True
        auth_log.warning(
            f"ОТКАЗ | Неверный пароль для пользователя: {username} | IP: {user_ip}"
        )

    @staticmethod
    def change_password(db, curr_password, password_1, password_2):
        if check_password_hash(current_user.password_hash, curr_password):
            if password_1 == password_2:
                password_hash = generate_password_hash(password_1)
                query = f"""UPDATE user SET password_hash = ? WHERE id = {current_user.id}"""
                db.update(base="main_base", query=query, param=password_hash)
                message = "Пароль бы успешно сменен"
            else:
                message = "Ошибка. Неверно введен подтверждающий пароль"
        else:
            message = "Ошибка. Неверно введен пароль"
        session["message"] = ["inline-block", message]
