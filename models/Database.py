from dbutils.pooled_db import PooledDB
import pymssql


class ConnectionPool:
    def __init__(self, app):
        print(
            app.config["DB_SERVER"],
            app.config["DB_USER"],
            app.config["DB_PASSWORD"],
            app.config["DB_NAME"],
        )
        self.pool = PooledDB(
            creator=pymssql,
            mincached=2,
            maxcached=10,
            host=app.config["DB_SERVER"],
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            database=app.config["DB_NAME"],
            charset="utf8",
        )
        app.extensions["pool"] = self

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
            print(transact)
            raise e
        finally:
            cursor.close()
            connection.close()
        return res
