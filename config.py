from enum import Enum


class Bases(Enum):
    baren = "baren"
    python = "python"
    pharmacy = "pharmacy"
    kroko = "kroko"
    test = "test"
    shaman = "shaman"


SORT_DIRECT = {True: "ASC", False: "DESC"}
SIZE_BLOCK = 135
