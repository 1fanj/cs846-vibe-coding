#!/usr/bin/env python3
from app.main import app
import json
import os

def to_yaml(obj, indent=0):
    out = ""
    ind = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out += f"{ind}{k}:\n{to_yaml(v, indent+1)}"
            else:
                out += f"{ind}{k}: {json.dumps(v)}\n"
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                out += f"{ind}-\n{to_yaml(item, indent+1)}"
            else:
                out += f"{ind}- {json.dumps(item)}\n"
    else:
        out += f"{ind}{json.dumps(obj)}\n"
    return out


def main():
    openapi = app.openapi()
    os.makedirs("docs", exist_ok=True)
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi, f, indent=2)
    with open("docs/openapi.yaml", "w") as f:
        f.write(to_yaml(openapi))
    print("Wrote docs/openapi.json and docs/openapi.yaml")


if __name__ == "__main__":
    main()
