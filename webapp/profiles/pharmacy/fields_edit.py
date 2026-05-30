import json

with open("fields.json", encoding="utf-8") as obj:
    res = json.load(obj)


with open("fields.json", "w", encoding="utf-8") as obj:
    json.dump(res, obj, ensure_ascii=False, indent=4)
