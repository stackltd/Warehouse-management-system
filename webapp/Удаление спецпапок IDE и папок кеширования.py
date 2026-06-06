import os
import shutil

curr_dir = os.path.abspath("")


def recurs(curr_dir, delete):
    """
    Функция удаляет спецпапки IDE и папки кеширования python
    """
    os.chdir(curr_dir)
    folders = [x for x in os.listdir(curr_dir) if os.path.isdir(x)]
    if folders:
        # print(folders)
        for name in folders:
            try:
                if (
                    name.startswith(".")
                    or name.startswith("_")
                    or name.startswith("__")
                ):
                    os.chdir(curr_dir)
                    print(os.getcwd(), name)
                    if delete:
                        shutil.rmtree(name)
                else:
                    new_dir = os.path.join(curr_dir, name)
                    recurs(new_dir, delete)
            except FileNotFoundError as ex:
                print(ex)
            except PermissionError as ex:
                print(ex, os.getcwd(), name)


recurs(curr_dir=curr_dir, delete=True)
