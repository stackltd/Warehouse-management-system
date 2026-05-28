import json
import sqlite3
import logging
from pprint import pprint
from sqlite3 import OperationalError
from typing import Callable
from config import Bases

from flask import g

logger = logging.getLogger("логгер.models")


class ControlDatabase:

    def __init__(self, base):
        self.base = base

    def __str__(self):
        return f"{self.base}"

    def _get_db(self):
        """
        Создание соединения с базой данных для текущего контекста приложения, создание дескриптора базы данных,
         которое можно использовать во всех методах
        """
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(f"databases/{self.base}.db")
        return db

    def create_table(self, table):
        # print("create_table(base)", base)
        with sqlite3.connect(f"databases/{self.base}.db") as conn:
            cursor = conn.cursor()
            query_create_table = f"""CREATE TABLE IF NOT EXISTS {table} (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                    category TEXT,
                                    type TEXT,
                                    name TEXT,
                                    describe TEXT,
                                    size REAL,
                                    `case` TEXT,
                                    for TEXT,
                                    U REAL,
                                    I REAL,
                                    P REAL,
                                    R REAL,
                                    C REAL,
                                    L REAL,
                                    coeff TEXT,
                                    `count` INT DEFAULT 0,
                                    photo TEXT,
                                    manual TEXT,
                                    history TEXT,
                                    market TEXT,
                                    url_order TEXT,
                                    price_market REAL DEFAULT 0,
                                    price_deliv REAL DEFAULT 0,
                                    count_ordered REAL DEFAULT 0,
                                    price_in REAL GENERATED ALWAYS AS (price_market + price_deliv),
                                    summ REAL GENERATED ALWAYS AS (price_in * `count`),
                                    price_sale REAL DEFAULT 0,
                                    count_sold INT DEFAULT 0,
                                    summ_sold REAL GENERATED ALWAYS AS (price_sale * count_sold),
                                    status TEXT);
                                  """
            cursor.execute(query_create_table)
            conn.commit()

    def insert(self, table, names_dict):
        keys = ", ".join([f'"{name}"' for name in names_dict])
        values = ", ".join([f"{names_dict[name]}" for name in names_dict])
        # используем параметризованные запросы
        params = values.split(", ")
        ques_marks = ", ".join(["?" for _ in range(len(params))])
        conn = self._get_db()
        cursor = conn.cursor()
        query = f"""INSERT INTO {table} ({keys}) VALUES ({ques_marks});"""
        logger.info(f"Добавлена позиция {values}")
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid

    def update(self, query="", param=None):
        conn = self._get_db()
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
        query="",
        table="",
        fields="*",
        param=(),
        where="1",
        order_by="1",
        debug=False,
    ):
        if debug:
            with sqlite3.connect(f"./databases/{self.base}.db") as obj:
                conn = obj
        else:
            conn = self._get_db()
        if not query:
            query = f"SELECT {fields} FROM {table} WHERE {where} ORDER BY {order_by}"
        # print(query)
        try:
            cursor = conn.cursor()
            cursor.execute(query, param)

            result = cursor.fetchall()
            return result
        except OperationalError as ex:
            return []

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)


if __name__ == "__main__":
    from config import Bases

    base = "baren"
    asd = ControlDatabase(base)
    res = asd.select(
        table=Bases[base],
        fields="id, `count`, name",
        param=(20, 15),
        where="`id` <= ? AND `count` <= ?",
        order_by="`count` ASC",
        debug=True,
    )
    # for i in res:
    #     print(i)
    print(asd.to_json())
    print(asd.from_json(asd.to_json()))
