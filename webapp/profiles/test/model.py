query_create_table = """CREATE TABLE IF NOT EXISTS warehouse (
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

if __name__ == "__main__":
    if __name__ == "__main__":
        from werkzeug.security import generate_password_hash, check_password_hash

        # 1. Берем пароль в явном виде (например, из request.form)
        plain_password = "123"

        # 2. Генерируем хэш
        password_hash = generate_password_hash(plain_password)

        # Смотрим, что получилось
        print("Оригинальный пароль:", plain_password)
        print("Хэш для базы данных:", password_hash)
        # Выведет что-то вроде: scrypt:32768:8:1$uYx8N...$efc09...
        is_valid = check_password_hash(password_hash, plain_password)
        print(is_valid)
