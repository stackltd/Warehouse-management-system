import json
import logging

from flask import session, request

from config import Bases
from models import ControlDatabase
from utils import str_corr, initialize


class WarehouseService:
    def __init__(self, db: ControlDatabase):
        self.db = db

    def switch_base(self, base: str, bases):
        """Сервисный метод смены базы данных"""
        if base not in bases:
            raise ValueError("Неверное имя базы данных")

        session["base_is_changed"] = True
        session["base"] = base
        path_to_log = f"./profiles/{base}/{base}.log"
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

    def get_fields_for_render(self, base) -> tuple:
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

        return (
            categories,
            fields_params,
            fields_order_out,
            result,
            summ_some_fields,
            statuses,
            sel_record,
            fields,
        )
