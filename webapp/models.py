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
        try:
            cursor = conn.cursor()
            cursor.execute(query, param)

            result = cursor.fetchall()
            return result
        except OperationalError:
            return []


from flask_login import UserMixin


# класс пользователя для БД
class User(UserMixin):
    def __init__(
        self, user_id, username, password_hash, role, fullname="", available_bases=""
    ):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.fullname = fullname
        self.available_bases = available_bases

    @classmethod
    def get_user(cls, query, param):
        with sqlite3.connect(f"./databases/db.sqlite3.db") as obj:
            conn = obj
            cursor = conn.cursor()
            user_get_field = cursor.execute(query, param).fetchall()
            if not user_get_field:
                return []
        user = User(*user_get_field[0])
        return user


if __name__ == "__main__":
    from config import Bases

    """            query = "SELECT * FROM 'user' WHERE 'username' = ?"
            param = (username,)"""
    base = "db.sqlite3"
    table = ""
    asd = ControlDatabase(debug=True)
    res = asd.select(
        base=base,
        query="SELECT * FROM user WHERE username = ?",
        # table=table,
        # fields="coeff",
        param=("admin",),
        # where="username = ?",
    )

    # res = User.get_user_by(db=ControlDatabase(debug=True), field="id", value=1)
    print(res)
    for i in res:
        print(i)

    # query_create_table = """CREATE TABLE IF NOT EXISTS user (
    #                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                                     username TEXT UNIQUE,
    #                                     password_hash TEXT,
    #                                     role TEXT,
    #                                     fullname TEXT,
    #                                     available_bases TEXT);
    #                                   """
    # ControlDatabase().create_table("db.sqlite3", query_create_table)
