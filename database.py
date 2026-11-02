import os
import mysql.connector
from urllib.parse import urlparse, unquote


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        url = urlparse(database_url)

        return mysql.connector.connect(
            host=url.hostname,
            port=url.port or 3306,
            user=unquote(url.username or ""),
            password=unquote(url.password or ""),
            database=url.path.lstrip("/")
        )

    
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="db_data_mahasiswa"
    )