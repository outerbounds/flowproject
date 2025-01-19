import os
from metaflow import conda

from .baseflow import BaseFlow, toml_parser

try:
    # apply dotenv file
    with open('.env') as f:
        for row in f:
            k, v = row.split('=')
            os.environ[k] = v.strip()
except:
    pass

def snowflake(f):
    return conda(python="3.11", packages={"snowflake-connector-python": "3.12.2"})(f)