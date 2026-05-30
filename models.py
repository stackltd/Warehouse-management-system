import sqlite3
import logging
from sqlite3 import OperationalError

from flask import g

logger = logging.getLogger("логгер.models")


class ControlDatabase:

    def __init__(self, debug=False):
        self.debug = debug

    def _get_db(self, base):
        """
        Создание соединения с базой данных для текущего контекста приложения, создание дескриптора базы данных,
         которое можно использовать во всех методах
        """
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(f"databases/{base}.db")

        return db

    def _get_conn(self, base):
        if self.debug:
            with sqlite3.connect(f"./databases/{base}.db") as obj:
                conn = obj
        else:
            conn = self._get_db(base)
        return conn

    @staticmethod
    def create_table(base, query_create_table):
        with sqlite3.connect(f"databases/{base}.db") as conn:
            cursor = conn.cursor()
            cursor.execute(query_create_table)
            conn.commit()

    def insert(self, base, names_dict):
        conn = self._get_conn(base)
        table = Bases[base]
        keys = ", ".join([f'"{name}"' for name in names_dict])
        values = ", ".join([f"{names_dict[name]}" for name in names_dict])
        # используем параметризованные запросы
        params = values.split(", ")
        ques_marks = ", ".join(["?" for _ in range(len(params))])
        cursor = conn.cursor()
        query = f"""INSERT INTO {table} ({keys}) VALUES ({ques_marks});"""
        logger.info(f"Добавлена позиция {values}")
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid

    def update(self, base, query="", param=None):
        conn = self._get_conn(base)
        try:
            cursor = conn.cursor()
            if param is not None:
                list_params = []
                list_params.append(param)
                cursor.execute(query, list_params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        except OperationalError:
            return []

    def select(
        self,
        base,
        query="",
        table="",
        fields="*",
        param=(),
        where="1",
        order_by="1",
    ):
        conn = self._get_conn(base)
        if not query and table:
            query = f"SELECT {fields} FROM {table} WHERE {where} ORDER BY {order_by}"
        # print(query)
        try:
            cursor = conn.cursor()
            cursor.execute(query, param)

            result = cursor.fetchall()
            return result
        except OperationalError:
            return []


if __name__ == "__main__":
    from config import Bases

    base = "baren"
    asd = ControlDatabase(debug=True)
    res = asd.select(
        base=base,
        table="warehouse",
        # fields="coeff",
        # where="coeff LIKE 'μF'",
    )
    for i in res:
        print(i)
