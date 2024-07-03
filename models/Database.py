from dbutils.pooled_db import PooledDB
import pymssql
import tomllib


class ConnectionPool:
    def __init__(self, db_host, db_user, db_pw, db_name):
        self.pool = PooledDB(
            creator=pymssql,
            mincached=2,
            maxcached=10,
            host=db_host,
            user=db_user,
            password=db_pw,
            database=db_name,
            charset="utf8",
        )

    def __call__(self, transact, params=None, have_return=True):
        connection = self.pool.connection()
        cursor = connection.cursor()
        res = None
        try:
            connection.begin()
            if params:
                cursor.execute(transact, params)
            else:
                cursor.execute(transact)
            if have_return:
                title = [item[0] for item in cursor.description]
                res = (title, cursor.fetchall())
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
        return res


config = tomllib.load(open("../config.toml", "rb"))

DB_SERVER = config["database"]["server"]
DB_USER = config["database"]["user"]
DB_PASSWORD = config["database"]["password"]
DB_NAME = config["database"]["name"]

transact = ConnectionPool(
    db_host=DB_SERVER, db_user=DB_USER, db_pw=DB_PASSWORD, db_name=DB_NAME
)
