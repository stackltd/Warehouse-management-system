import os.path
import sqlite3
import logging
from pprint import pprint

from prettytable import from_db_cursor

from sqlite3 import OperationalError

from config import Bases

from flask import g

# print(f"{base=}")
logger = logging.getLogger("логгер.models")

base = Bases.baren.value


# Создание соединения с базой данных для текущего контекста приложения, создание дескриптора базы данных,
# которое можно использовать во всех методах
def get_db(base):
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(f"./databases/{base}.db")
    return db


def create_table(base):
    # print("create_table(base)", base)
    with sqlite3.connect(f"./databases/{base}.db") as conn:
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


def insert(names_dict, base=base, test=False):
    keys = ", ".join([f'"{name}"' for name in names_dict])
    values = ", ".join([f"{names_dict[name]}" for name in names_dict])
    # используем параметризованные запросы
    params = values.split(", ")
    ques_marks = ", ".join(["?" for _ in range(len(params))])
    if test:
        with sqlite3.connect(f"./databases/{base}.db") as obj:
            conn = obj
    else:
        conn = get_db(base)
    cursor = conn.cursor()
    query = f"""INSERT INTO zip ({keys}) VALUES ({ques_marks});"""
    logger.info(f"Добавлена позиция {values}")
    cursor.execute(query, params)
    conn.commit()
    return cursor.lastrowid


def select(fields="*", _from="zip", where="1", order_by="1"):
    conn = get_db(base)
    cursor = conn.cursor()
    query = f"SELECT {fields} FROM {_from} zip WHERE {where} ORDER BY {order_by}"
    result = cursor.execute(query).fetchall()
    return result


def exe(query="", pragma=False, param=None, test=False, base=base):
    # print(f"{query = }")
    if test:
        with sqlite3.connect(f"./databases/{base}.db") as obj:
            conn = obj
    else:
        conn = get_db(base)
    try:
        cursor = conn.cursor()
        # print(f"{param = }")
        if pragma:
            query = """pragma table_info(zip)"""
            res = cursor.execute(query).fetchall()
            return {v[1]: i for i, v in enumerate(res)}
        else:
            if param is not None:
                list_params = []
                list_params.append(param)
                # print(f"{list_params = }", f"{param = }")
                cursor.execute(query, list_params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
    except OperationalError:
        return []


query = """SELECT * FROM zip"""
# query = """SELECT * FROM zip WHERE category = 'Аккумулятор' ORDER BY `size` ASC, 'U'"""
# query = """DELETE FROM zip WHERE `zip`.`id` = 40"""
# query = """pragma table_info(zip)"""
# query=f"""SELECT `count_ordered` FROM zip WHERE id = 71"""
# query = """SELECT SUM(summ_sold) FROM zip"""
# query = """SELECT * FROM (SELECT * FROM zip) order by category"""
# query = """SELECT category, name FROM zip WHERE id == 18"""
# query = """UPDATE zip SET size = "CSB" WHERE id=3"""
# query = """UPDATE zip SET `count` = 111 WHERE id=143"""
# query = """pragma table_info(zip)"""
# query = """DROP TABLE zip"""
# query = """SELECT price FROM zip"""
# query = """UPDATE zip SET history=datetime('now') || ' установка Яну' WHERE id=1"""

if __name__ == "__main__":
    # create_table(base="kroko")
    if test_1 := True:
        res = exe(query=query, pragma=False, test=True, base="pharmacy")
        print(*res, sep="\n")
        # a  = []
        # for i in res:
        #     a.append(i[1])
        # print(a)
        # for i in res:
        #     a.append(i[1])
        # a.sort()
        # a = set(a)
        # print(list(a))
        # print(i[1])
        # categ = ['антимикроб', 'миорелаксант', 'абсорбент', 'муколитик', 'поливитамин', 'пробиотик', 'жаропониж', 'ранозаживл',
        #          'гл-кор-стероид', 'антисептик', 'гастро', 'хондропро', 'кардио', 'антиаллерген', 'антивир', 'спазмолитик', 'ноотроп',
        #          'цервикалг', 'гипотенз', 'антитромб', 'седативное', 'нпвп']

        categories = [
            "антисептик",
            "нпвп",
            "миорелаксант",
            "хондропрот",
            "гипотенз",
            "поливитамин",
            "поливитамин",
            "муколитик",
            "поливитамин",
            "антисептик",
            "пробиотик",
            "седативное",
            "антимикроб",
            "кардио",
            "антивир",
            "спазмолитик",
            "муколитик",
            "нпвп",
            "нпвп",
            "ранозаживл",
            "муколитик",
            "антиаллерген",
            "спазмолитик",
            "абсорбент",
            "антисептик",
            "гипотенз",
            "цервикалг",
            "гл-кор-стероид",
            "седативное",
            "муколитик",
            "ранозаживл",
            "спазмолитик",
            "жаропониж",
            "антитромб",
            "кардио",
            "гастро",
            "ноотроп",
            "нпвп",
        ]
        # categories.sort()
        # print(sorted(list(set(categories))))

        # for i, name in enumerate(categories):
        #     # print(i + 1, name)
        #     exe(query=f"""UPDATE zip SET category = "{name}" WHERE id={i + 1}""", pragma=False, test=True, base="pharmacy")
    if test_2 := False:
        a = "Delta"
        b = 16
        c = "HR 12-7.2"
        exe(query=f"""UPDATE zip SET size = "{a}" WHERE id={b}""", test=True)
        exe(query=f"""UPDATE zip SET name = "{c}" WHERE id={b}""", test=True)
        exe(query=f"""UPDATE zip SET type = "Pb-acid" WHERE id={b}""", test=True)

    # exe(query="""UPDATE zip SET photo = "LG_LED.png" WHERE id=17""")

    # exe(query="""UPDATE zip SET photo = "LG_LED.png" WHERE id=17""")

    # for i in range(135, 141):
    #     exe(query=f"""DELETE FROM zip WHERE `zip`.`id` = {i}""")

    # print(os.path.abspath


# import sqlite3
# import logging
# from sqlite3 import OperationalError
# from flask import g
# logger = logging.getLogger("логгер.models")
#
# # base = Bases.baren.value
#
# class ControlDatabase:
#
#     # Создание соединения с базой данных для текущего контекста приложения, создание дескриптора базы данных,
#     # которое можно использовать во всех методах
#     @staticmethod
#     def _get_db(base):
#         db = getattr(g, "_database", None)
#         if db is None:
#             db = g._database = sqlite3.connect(f"databases/{base}.db")
#         return db
#
#
#     def create_table(base):
#         # print("create_table(base)", base)
#         with sqlite3.connect(f"databases/{base}.db") as conn:
#             cursor = conn.cursor()
#             query_create_table = """CREATE TABLE IF NOT EXISTS zip (
#                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                                     category TEXT,
#                                     type TEXT,
#                                     name TEXT,
#                                     describe TEXT,
#                                     size REAL,
#                                     `case` TEXT,
#                                     for TEXT,
#                                     U REAL,
#                                     I REAL,
#                                     P REAL,
#                                     R REAL,
#                                     C REAL,
#                                     L REAL,
#                                     coeff TEXT,
#                                     `count` INT DEFAULT 0,
#                                     photo TEXT,
#                                     manual TEXT,
#                                     history TEXT,
#                                     market TEXT,
#                                     url_order TEXT,
#                                     price_market REAL DEFAULT 0,
#                                     price_deliv REAL DEFAULT 0,
#                                     count_ordered REAL DEFAULT 0,
#                                     price_in REAL GENERATED ALWAYS AS (price_market + price_deliv),
#                                     summ REAL GENERATED ALWAYS AS (price_in * `count`),
#                                     price_sale REAL DEFAULT 0,
#                                     count_sold INT DEFAULT 0,
#                                     summ_sold REAL GENERATED ALWAYS AS (price_sale * count_sold),
#                                     status TEXT);
#                                   """
#             cursor.execute(query_create_table)
#             conn.commit()
#
#
#     def insert(self, names_dict, base):
#         keys = ", ".join([f'"{name}"' for name in names_dict])
#         values = ", ".join([f"{names_dict[name]}" for name in names_dict])
#         # используем параметризованные запросы
#         params = values.split(", ")
#         ques_marks = ", ".join(["?" for _ in range(len(params))])
#         conn = self._get_db(base)
#         cursor = conn.cursor()
#         query = f"""INSERT INTO zip ({keys}) VALUES ({ques_marks});"""
#         logger.info(f"Добавлена позиция {values}")
#         cursor.execute(query, params)
#         conn.commit()
#         return cursor.lastrowid
#
#
#
#     def exe(self, query="", param=None, base=None):
#         conn = self._get_db(base)
#         try:
#             cursor = conn.cursor()
#             if param is not None:
#                 list_params = []
#                 list_params.append(param)
#                 cursor.execute(query, list_params)
#             else:
#                 cursor.execute(query)
#             conn.commit()
#             return cursor.fetchall()
#         except OperationalError:
#             return []
