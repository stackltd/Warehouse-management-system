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
    from models import ControlDatabase

    ControlDatabase().create_table("baren", query_create_table)
