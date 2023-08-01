import json
import random
import re
import secrets
import uuid
from pathlib import Path

import execjs

CONST_NAMESPACE = uuid.UUID("12345678123456781234567812345678")

QUERIES = {}
GQL_URL = "https://poe.com/api/gql_POST"
GQL_RECV_URL = "https://poe.com/api/receive_POST"
HOME_URL = "https://poe.com"
SETTING_URL = "https://poe.com/api/settings"

queries_path = Path(__file__).resolve().parent / "poe_graphql"


def generate_data(query_name, variables) -> str:
    if query_name == "recv":
        data = [
            {
                "category": "poe/bot_response_speed",
                "data": variables,
            }
        ]
        if random.random() > 0.9:
            data.append(
                {
                    "category": "poe/statsd_event",
                    "data": {
                        "key": "poe.speed.web_vitals.INP",
                        "value": random.randint(100, 125),
                        "category": "time",
                        "path": "/[handle]",
                        "extra_data": {},
                    },
                }
            )
    else:
        data = {
            "query": QUERIES[query_name],
            "queryName": query_name,
            "variables": variables,
        }
    return json.dumps(data, separators=(",", ":"))


def generate_nonce(length: int = 16):
    return secrets.token_hex(length // 2)


def extract_formkey(html, script):
    script_regex = r"<script>(.+?)</script>"
    vars_regex = r'window\._([a-zA-Z0-9]{10})="([a-zA-Z0-9]{10})"'
    key, value = re.findall(vars_regex, script)[0]

    script_text = """
      let QuickJS = undefined, process = undefined;
      let window = {
        document: {a:1},
        navigator: {
          userAgent: "a"
        }
      };
    """
    script_text += f"window._{key} = '{value}';"
    script_text += "".join(re.findall(script_regex, html))

    function_regex = r"(window\.[a-zA-Z0-9]{17})=function"
    function_text = re.search(function_regex, script_text).group(1)
    exec_script = f"{function_text}()"

    context = execjs.compile(script_text)
    formkey = context.eval(exec_script)
    return formkey


def load_queries():
    global QUERIES
    for path in queries_path.iterdir():
        if path.suffix != ".graphql":
            continue
        with open(path) as f:
            QUERIES[path.stem] = f.read()


load_queries()
