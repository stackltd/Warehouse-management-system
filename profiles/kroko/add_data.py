import json

if __name__ == "__main__":

    with open("fields.json", "r", encoding="utf-8") as file:
        result = json.load(file)

    fields: dict = result["fields"]

    for i in range(1923, 2009):
        fields.update({i: {}})
    result["fields"] = fields

    with open("fields.json", "w", encoding="utf-8") as obj:
        json.dump(result, obj, indent=4, ensure_ascii=False)
