from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

from flask import abort
from flask_login import UserMixin
from .util import (
    unique,
    from_sql_results,
    exists,
    transact,
    field_names,
    SQLBuilder,
    ModelBase,
    PageIter,
)


@dataclass(eq=False, order=False)
class User(ModelBase, UserMixin):
    username: str
    is_administrator: bool
    avatar: Optional[str] = None
    birthday: Optional[datetime] = None
    intro: Optional[str] = None
    create_at: Optional[datetime] = None

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
    birthday: Optional[datetime] = None
    intro: Optional[str] = None
    create_at: Optional[datetime] = None

    @classmethod
    def update_intro(cls, intro, id):
        transact(
            cls.sql_generator().update().col("intro").where("id = %s").build(),
            params=(intro, id),
            have_return=False,
        )


@dataclass(eq=False, order=False)
class Diary(ModelBase):
    content: str
    author_id: int
    create_at: Optional[datetime] = None

    @classmethod
    def retrieve_by_author_id(cls, author_id):
        return from_sql_results(
            cls,
            transact(
                cls.sql_generator().select().where("author_id=%s").build(),
                params=(author_id,),
            ),
        )


@dataclass(eq=False, order=False)
class Passage(ModelBase):
    is_draft: bool
    author_id: int
    content: str
    create_at: Optional[datetime] = None
    vote_up: int = 0

    @staticmethod
    def map_order(order: Literal["time", "vote_up"] = "time"):
        match order:
            case "time":
                return "create_at"
            case "vote_up":
                return "vote_up"
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
        order_by: Literal["time", "vote_up"] = "time",
        desc=True,
    ):

        order_by = cls.map_order(order_by)
        return PageIter(
            target_cls=Passage,
            gen=cls.sql_gen_select(is_draft=False),
            page_size=page_size,
            order_by=order_by,
            desc=desc,
        )

    @classmethod
    def retrieve_passages_by_author_id(
        cls,
        author_id,
        is_draft=False,
        order_by: Literal["time", "vote_up"] = "time",
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
        order_by: Literal["time", "vote_up"] = "time",
        desc=True,
    ):
        order_direction = "DESC" if desc else "ASC"
        gen = (
            cls.sql_gen_select(is_draft=is_draft)
            .order_by(**{cls.map_order(order_by): order_direction})
            .where("content LIKE %s")
        )
        if topk:
            gen = gen.offset(0).fetch(topk)
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
    def sql_gen_update_vote_up(cls):
        return cls.sql_generator().update().col("vote_up")


@dataclass(eq=False, order=False)
class Comment(ModelBase):
    content: str
    author_id: int
    contain_by: int
    create_at: datetime = None


@dataclass(eq=False, order=False)
class Image(ModelBase):
    uuid: str
    alt: str
    title: str
    contain_by: int
    create_at: datetime = None


@dataclass(eq=False, order=False)
class Avatar(ModelBase):
    uuid: str
    create_at: datetime = None
