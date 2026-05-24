import sqlite3
import logging
from sqlite3 import OperationalError
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

    def create_table(self):
        # print("create_table(base)", base)
        with sqlite3.connect(f"databases/{self.base}.db") as conn:
            cursor = conn.cursor()
            query_create_table = """CREATE TABLE IF NOT EXISTS zip (
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

    def insert(self, names_dict):
        keys = ", ".join([f'"{name}"' for name in names_dict])
        values = ", ".join([f"{names_dict[name]}" for name in names_dict])
        # используем параметризованные запросы
        params = values.split(", ")
        ques_marks = ", ".join(["?" for _ in range(len(params))])
        conn = self._get_db()
        cursor = conn.cursor()
        query = f"""INSERT INTO zip ({keys}) VALUES ({ques_marks});"""
        logger.info(f"Добавлена позиция {values}")
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid

    def exe(self, query="", param=None):
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
