from aenum import Enum, NoAlias


class Bases(Enum):
    _settings_ = NoAlias  # <-- Запрещаем Python склеивать дубликаты!

    baren = "warehouse"
    python = "python"
    pharmacy = "warehouse"
    kroko = "kroko"
    test = "warehouse"
    shaman = "warehouse"


SORT_DIRECT = {True: "ASC", False: "DESC"}
SIZE_BLOCK = 135
