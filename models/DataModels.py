from dataclasses import dataclass
from datetime import date
from typing import Optional, Literal

from itertools import count

from flask import abort
from flask_login import UserMixin

from .util import unique, from_sql_results, exists, transact, field_names
from collections import defaultdict

from uuid import UUID


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

    def _get_table_name(self, table):
        if isinstance(table, str):
            return table
        elif isinstance(table, type) and issubclass(table, ModelBase):
            return table.__name__
        else:
            raise ValueError("Argument Table with a invalid value")

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
                if self._offset:
                    query += f" OFFSET {self._offset} ROWS"
                    if self._fetch:
                        query += f" FETCH NEXT {self._fetch} ROWS ONLY"

        return query + ";"


@dataclass
class ModelBase:
    id: int

    @classmethod
    def sql_generator(cls):
        return SQLBuilder().table(cls.__name__)

    @classmethod
    def delete_by_id(cls, id):
        transact(
            cls.sql_generator().delete().where("id = %s").build(),
            params=(id,),
            have_return=False,
        )

    @classmethod
    @unique
    def get_by_id(cls, id):
        return from_sql_results(
            cls,
            transact(
                cls.sql_generator()
                .select()
                .col(*field_names(cls))
                .where("id = %s")
                .build(),
                params=(id,),
            ),
        )

    def reload_status(self):
        new_self = self.__class__.get_by_id(self.id)
        if new_self:
            for key, val in new_self.__dict__.items():
                setattr(self, key, val)
        else:
            abort(404)


class PageIter:
    def __init__(
        self, target_cls: ModelBase, gen: SQLBuilder, page_size, order_by, desc=True
    ):
        self.gen = gen
        self.condition = "1 = 1"
        self.page = 0
        self.page_size = page_size
        self.target_cls = target_cls
        self.order_by = order_by
        self.desc = desc

    def __iter__(self):
        return self

    def __next__(self):
        sql = (
            self.gen.offset(self.page_size * self.page)
            .fetch(self.page_size)
            .where(self.condition)
            .build()
        )
        res = from_sql_results(self.target_cls, transact(sql))
        if res:
            last = res[-1]
            self.condition = f"{self.order_by} {'<=' if self.desc else '>='} {getattr(last, self.order_by)} AND id > {getattr(last, 'id')}"
            self.page += 1
            return res
        else:
            raise StopIteration


@dataclass(eq=False, order=False)
class User(ModelBase, UserMixin):
    username: str
    is_administrator: bool
    avatar: Optional[str] = None
    birthday: Optional[date] = None
    intro: Optional[str] = None
    create_at: Optional[date] = None

    @classmethod
    def sql_generator(cls):
        pass

    @classmethod
    def update_intro(cls, intro, id):
        UserProfile.update_intro(intro, id)

    @classmethod
    def delete_by_id(cls, id):
        UserCredential.delete_by_id(id)

    @classmethod
    @unique
    def get_by_id(cls, id):
        cols = field_names(cls)
        cols.remove("id")
        cols.append("UserCredential.id as id")
        sql = (
            SQLBuilder()
            .table(UserCredential)
            .join(UserProfile, "UserCredential.id = UserProfile.id")
            .select()
            .col(*cols)
            .where(
                "UserCredential.id = %s",
            )
            .build()
        )
        return from_sql_results(
            cls,
            transact(sql, (id,)),
        )

    @classmethod
    def search_by_username(
        cls,
        username,
        topk=None,
        desc=True,
    ):
        cols = field_names(cls)
        cols.remove("id")
        cols.append("UserCredential.id as id")
        gen = (
            SQLBuilder()
            .table(UserCredential)
            .join(UserProfile, "UserCredential.id = UserProfile.id")
            .select()
            .col(*cols)
            .where("username LIKE %s")
            .order_by(create_at="DESC" if desc else "ASC")
        )
        if topk:
            gen = gen.fetch(topk)
        return from_sql_results(
            cls,
            transact(
                gen.build(),
                ("%" + username + "%",),
            ),
        )


@dataclass(eq=False, order=False)
class UserCredential(ModelBase, UserMixin):
    password_hash: bytes
    salt: bytes
    username: str
    email: str
    is_administrator: bool = False

    @classmethod
    @unique
    def get_by_username(cls, username):
        sql = (
            cls.sql_generator()
            .select()
            .col(*field_names(cls))
            .where("username = %s")
            .build()
        )
        return from_sql_results(cls, transact(sql, (username,)))

    @classmethod
    def exists_email(cls, email):
        return exists(cls, email=email)

    @classmethod
    def exists_username(cls, username):
        return exists(cls, username=username)

    @classmethod
    def insert_new(cls, pw_hash, salt, username, email):
        transact(
            cls.sql_generator()
            .insert()
            .col("password_hash", "salt", "username", "email")
            .build(),
            params=(pw_hash, salt, username, email),
            have_return=False,
        )


@dataclass(eq=False, order=False)
class UserProfile(ModelBase, UserMixin):
    avatar: Optional[str] = None
    birthday: Optional[date] = None
    intro: Optional[str] = None
    create_at: Optional[date] = None

    @classmethod
    def update_intro(cls, intro, id):
        transact(
            cls.sql_generator().update().col("intro").where("id = %s").build(),
            params=(intro, id),
            have_return=False,
        )


@dataclass(eq=False, order=False)
class Passage(ModelBase):
    is_draft: bool
    author_id: int
    content: str
    create_at: Optional[date] = None
    heat: int = 0

    @staticmethod
    def map_order(order: Literal["time", "heat"] = "time"):
        match order:
            case "time":
                return "create_at"
            case "heat":
                return "heat"
            case _:
                raise ValueError("Unsupported order name")

    @classmethod
    def sql_gen_select(cls, is_draft=False):
        return (
            cls.sql_generator()
            .select()
            .col("*")
            .where(f"is_draft = {1 if is_draft else 0 }")
        )

    @classmethod
    def retrieve_passages_paged(
        cls,
        page_size,
        is_draft=False,
        order_by: Literal["time", "heat"] = "time",
        desc=True,
    ):

        order_by = cls.map_order(order_by)
        order_direction = "DESC" if desc else "ASC"
        gen = cls.sql_gen_select(is_draft=is_draft).order_by(
            **{order_by: order_direction, "id": "ASC"}
        )
        return PageIter(
            target_cls=Passage,
            gen=gen,
            page_size=page_size,
            order_by=order_by,
            desc=desc,
        )

    @classmethod
    def retrieve_passages_by_author_id(
        cls,
        author_id,
        is_draft=False,
        order_by: Literal["time", "heat"] = "time",
        desc=True,
    ):
        order_direction = "DESC" if desc else "ASC"
        sql = (
            cls.sql_gen_select(is_draft=is_draft)
            .order_by(**{cls.map_order(order_by): order_direction})
            .where("author_id = %s")
            .build()
        )
        return from_sql_results(
            cls,
            transact(
                sql,
                (author_id,),
            ),
        )

    @classmethod
    def search_by_content(
        cls,
        content,
        topk=None,
        is_draft=False,
        order_by: Literal["time", "heat"] = "time",
        desc=True,
    ):
        order_direction = "DESC" if desc else "ASC"
        gen = (
            cls.sql_gen_select(is_draft=is_draft)
            .order_by(**{cls.map_order(order_by): order_direction})
            .where("content LIKE %s")
        )
        if topk:
            gen = gen.fetch(topk)
        sql = gen.build()
        return from_sql_results(
            cls,
            transact(
                sql,
                params=(content,),
            ),
        )

    @classmethod
    def sql_gen_insert(cls):
        return cls.sql_generator().insert().col("is_draft", "author_id", "content")

    @classmethod
    def sql_gen_update_content(cls):
        return cls.sql_generator().update().col("content")

    @classmethod
    def sql_gen_update_heat(cls):
        return cls.sql_generator().update().col("heat")


@dataclass(eq=False, order=False)
class Comment(ModelBase):
    content: str
    author_id: int
    contain_by: int
    create_at: date = None


@dataclass(eq=False, order=False)
class Image(ModelBase):
    uuid: str
    alt: str
    title: str
    contain_by: int
    create_at: date = None


@dataclass(eq=False, order=False)
class Avatar(ModelBase):
    uuid: str
    create_at: date = None
