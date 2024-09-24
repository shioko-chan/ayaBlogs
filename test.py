# 假设这些是你已有的模块或功能
import copy
from typing import List, Any
from collections import defaultdict


# 模拟的模型类
class ModelBase:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class SQLBuilder:
    __slots__ = (
        "_where",
        "_having",
        "_value",
        "_query_type",
        "_col",
        "_join",
        "_table",
        "_group_by",
        "_order_by",
        "_offset",
        "_fetch",
    )

    def __init__(self):
        self._where = []
        self._having = []
        self._value = []
        self._col = None
        self._join = defaultdict(list)
        self._query_type = None
        self._table = None
        self._group_by = None
        self._order_by = None
        self._offset = None
        self._fetch = None

    def __add__(self, other):
        if not isinstance(other, SQLBuilder):
            raise ValueError("Unsupported Type")

        res = SQLBuilder()
        for k in other.__slots__:
            v = getattr(other, k)
            if not v:
                setattr(res, k, getattr(self, k))
            elif isinstance(v, list):
                setattr(res, k, getattr(self, k) + v)
            else:
                nv = getattr(self, k)
                setattr(res, k, nv if nv else v)
        return res

    def __iadd__(self, other):
        if not isinstance(other, SQLBuilder):
            raise ValueError("Unsupported Type")

        for k in other.__slots__:
            v = getattr(other, k)
            if not v:
                continue
            if isinstance(v, list):
                getattr(self, k).extend(v)
            elif not getattr(self, k):
                setattr(self, k, v)
        return self

    def _get_table_name(self, table):
        if isinstance(table, str):
            return table
        elif isinstance(table, type) and issubclass(table, ModelBase):
            return table.__name__
        else:
            raise ValueError("Argument Table with a invalid value")

    def value(self, *val):
        self._value.extend(list(val))
        return self

    def insert(self):
        self._query_type = "INSERT"
        return self

    def delete(self):
        self._query_type = "DELETE"
        return self

    def update(self):
        self._query_type = "UPDATE"
        return self

    def select(self):
        self._query_type = "SELECT"
        return self

    def col(self, *columns):
        self._col = list(columns)
        return self

    def table(self, table):
        self._table = self._get_table_name(table)
        return self

    def join(self, table, *condition):
        self._join[self._get_table_name(table)].extend(list(condition))
        return self

    def where(self, *condition):
        self._where.extend(list(condition))
        return self

    def group_by(self, *columns):
        self._group_by = ", ".join(columns)
        return self

    def having(self, *condition):
        self._having.extend(list(condition))
        return self

    def order_by(self, **columns_order):
        self._order_by = (
            f"{', '.join(f'{col} {order}' for col, order in columns_order.items())}"
        )
        return self

    def offset(self, offset):
        self._offset = offset
        return self

    def fetch(self, fetch_size):
        self._fetch = fetch_size
        return self

    def copy(self):
        return copy.deepcopy(self)

    def build(self) -> str:
        if self._query_type not in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
            raise ValueError("Unsupported query type")

        if not self._table:
            raise ValueError("Table Name NOT Specified")

        def add_where():
            if self._where:
                return f" WHERE {' AND '.join(self._where)}"
            return ""

        if self._query_type == "DELETE":
            query = f"DELETE FROM {self._table}" + add_where()

        elif not self._col:
            raise ValueError("Columns NOT Specified")

        elif self._query_type == "INSERT":
            query = f"INSERT INTO {self._table}({', '.join(self._col)}) VALUES({', '.join(self._value + ['%s'] * (len(self._col) - len(self._value)))})"

        elif self._query_type == "UPDATE":
            query = (
                f"UPDATE {self._table} SET {', '.join([f'{col}={val}' for col, val in zip(self._col, self._value + ['%s'] * (len(self._col) - len(self._value)))])}"
                + add_where()
            )

        elif self._query_type == "SELECT":
            query = (
                f"SELECT {', '.join(self._col)} FROM {self._table}"
                + "".join(
                    f" INNER JOIN {k} ON {' AND '.join(v)}"
                    for k, v in self._join.items()
                )
                + add_where()
            )
            if self._group_by:
                query += f" GROUP BY {self._group_by}"
                if self._having:
                    query += f" HAVING {' AND '.join(self._having)}"
            if self._order_by:
                query += f" ORDER BY {self._order_by}"
                if self._offset is not None:
                    query += f" OFFSET {self._offset} ROWS"
                    if self._fetch:
                        query += f" FETCH NEXT {self._fetch} ROWS ONLY"

        return query + ";"


results = [
    ModelBase(id=i, name=f"Item {i}") for i in range(1, 21)  # 生成 20 个模拟记录
]


# 模拟的数据库操作
def transact(sql, args):
    print(f"Executing SQL: {sql}")
    offset = int(sql.split("OFFSET ")[1].split(" ")[0])
    limit = int(sql.split("NEXT ")[1].split(" ")[0])
    return results[offset : offset + limit]


class PageIter:
    def __init__(
        self, target_cls: ModelBase, gen: SQLBuilder, page_size, order_by, desc=True
    ):
        self.gen = gen
        self.condition = "1 = 1"
        self.page = 0
        self.page_size = page_size
        self.target_cls = target_cls
        self.desc = desc
        self.order_by = order_by
        order_direction = "DESC" if desc else "ASC"
        self.gen = self.gen.order_by(**{order_by: order_direction, "id": "ASC"})
        self.args = ()

    def __iter__(self):
        return self

    def __next__(self):
        sql = (
            self.gen.copy()
            .offset(self.page_size * self.page)
            .fetch(self.page_size)
            .where(self.condition)
            .build()
        )
        res = transact(sql, self.args)
        if res:
            last = res[-1]
            self.condition = f"{self.order_by} {'<=' if self.desc else '>='} %s AND id > {getattr(last, 'id')}"
            getattr(last, self.order_by)
            self.page += 1
            return res
        else:
            raise StopIteration


# 测试 PageIter
def test_page_iter():
    # 初始化 SQLBuilder
    sql_builder = SQLBuilder().table("foo").select().col("*")

    # 创建 PageIter 实例
    paginator = PageIter(
        target_cls=ModelBase, gen=sql_builder, page_size=5, order_by="name", desc=True
    )

    # 迭代结果
    for page in paginator:
        print(f"Page results: {[item.name for item in page]}")


# 运行测试
if __name__ == "__main__":
    test_page_iter()
    builder = SQLBuilder().select().table("foo").col("*")
    s1 = builder.col("123").where("1=1").build()
    s2 = builder.where("1=0").build()
    print(s1, s2)
