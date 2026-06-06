from werkzeug.security import generate_password_hash

from models import ControlDatabase
from profiles.test.model import query_create_table

query_create_table_user = """CREATE TABLE IF NOT EXISTS user (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    username TEXT UNIQUE,
                                    password_hash TEXT,
                                    role TEXT,
                                    fullname TEXT,
                                    available_bases TEXT);
                                  """

db = ControlDatabase(debug=True)

db.create_base("main_base", query_create_table=query_create_table_user)

db.create_base(base="test", query_create_table=query_create_table)

password_hash = generate_password_hash("admin")
db.insert("main_base", {"username": "admin", "password_hash": password_hash, "role": "admin"}, table="user")

res = db.select(
        base="main_base",
        query="SELECT * FROM user",
    )
print(res)