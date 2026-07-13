from src.normalizers.normalizer import normalize_json
from src.sql_builder.query_builder import build_ddl
from src.models.users import users
from src.database.clickhouse import get_client

import requests


r = requests.get("https://jsonplaceholder.typicode.com/users").json()
rows = normalize_json(r,users)

users_ddl = build_ddl(users)

client = get_client()
client.command(users_ddl)
client.insert(table="users", data=rows)