import re
from pathlib import Path
import json

paths = ["./templates", "./static/js"]

with open("./static/locales/zh/text.json", "r") as r:
    dic = json.load(r)
    print(dic)


def get_first_key(val):
    for k, v in dic.items():
        if v == val:
            return k
    return None


def get_character():
    for path in paths:
        for file in Path(path).glob("*"):
            with open(file, "r") as f:
                content = f.read()
                for quote, text, _ in re.findall(
                    r"([`'\"])(.*?)(\1)",
                    f.read(),
                ):
                    if text in dic.values():
                        content = content.replace(text, get_first_key(text))
            for k, v in dic:
                content = content.replace(v, k)
            with open(file, "w") as f:
                f.write(content)
