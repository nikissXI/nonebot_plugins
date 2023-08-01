import json
import random
import secrets
import uuid
from pathlib import Path

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


def load_queries():
    global QUERIES
    for path in queries_path.iterdir():
        if path.suffix != ".graphql":
            continue
        with open(path) as f:
            QUERIES[path.stem] = f.read()


load_queries()
