import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _connection_pool = None

    @classmethod
    def initialize(cls):
        cls._connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )

    @classmethod
    @contextmanager
    def get_cursor(cls):
        conn = cls._connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cls._connection_pool.putconn(conn)

# Initialize on import
DatabaseConnection.initialize()