import re
from pathlib import Path
import json

paths = ["./templates", "./static/js"]

with open("./static/locales/zh/text.json", "r") as r:
    dic = json.load(r)
    print(dic)


def get_character():
    for path in paths:
        for file in Path(path).glob("*"):
            with open(file, "r") as f:
                content = f.read()
            for k, v in dic:
                content = content.replace(v, k)
            with open(file, "w") as f:
                f.write(content)
