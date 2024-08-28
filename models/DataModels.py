from dataclasses import dataclass
from datetime import date
from typing import Optional

from flask_login import UserMixin

from .util import unique, from_sql_results, exists, transact


class NotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@dataclass
class HasId:
    id: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, HasId):
            return self.id == other.id
        else:
            return NotImplemented

    def __ne__(self, other) -> bool:
        if isinstance(other, HasId):
            return self.id != other.id
        else:
            return NotImplemented

    @classmethod
    @unique
    def get_by_id(cls, id):
        return from_sql_results(
            cls, transact(f"SELECT * FROM {cls.__name__} WHERE id = %s", (id,))
        )

    def reload_status(self):
        new_self = self.__class__.get_by_id(self.id)
        if new_self:
            for key, val in new_self.__dict__.items():
                setattr(self, key, val)
        else:
            raise NotExistError

    def update_db(self):
        title, _ = transact(f"SELECT TOP 1 * FROM {self.__class__.__name__}")
        title.remove("id")
        transact(
            f"UPDATE {self.__class__.__name__} SET {','.join([f'{key}=%s' for key in title])} where id = %s",
            params=tuple(self.__dict__[key] for key in title) + (self.id,),
            have_return=False,
        )

    def insert_into_db(self):
        title, _ = transact(f"SELECT TOP 1 * FROM {self.__class__.__name__}")
        title.remove("id")
        transact(
            f"INSERT INTO {self.__class__.__name__}({','.join(title)}) VALUES({','.join(['%s'] * len(title))})",
            params=tuple(self.__dict__[key] for key in title),
            have_return=False,
        )


@dataclass(eq=False, order=False)
class HasTitle:
    title: str

    @classmethod
    def search_by_title(cls, keyword):
        return from_sql_results(
            cls,
            transact(
                f"SELECT * FROM {cls.__name__} WHERE title LIKE %s",
                ("%" + keyword + "%",),
            ),
        )


@dataclass(eq=False, order=False)
class HasContent:
    content: str

    @classmethod
    def search_by_content(cls, keyword):
        return from_sql_results(
            cls,
            transact(
                f"SELECT * FROM {cls.__name__} WHERE content LIKE %s",
                ("%" + keyword + "%",),
            ),
        )


@dataclass(eq=False, order=False)
class HasTimeStamp:
    create_at: date

    @classmethod
    def get_latest(cls, num):
        return from_sql_results(
            cls,
            transact(f"SELECT TOP {num} * FROM {cls.__name__} ORDER BY create_at DESC"),
        )


@dataclass(eq=False, order=False)
class HasAuthor:
    author_id: int


@dataclass(eq=False, order=False)
class HasContainer:
    contain_by: int


@dataclass(eq=False, order=False)
class HasHeat:
    heat: int

    @classmethod
    def get_hottest(cls, num):
        return from_sql_results(
            cls,
            transact(f"SELECT TOP {num} * FROM {cls.__name__} ORDER BY heat DESC"),
        )


@dataclass(eq=False, order=False)
class Usr(HasId, UserMixin):
    password_hash: bytes
    salt: bytes
    username: str
    email: str
    avatar: str = None
    birthday: Optional[date] = None
    sex: Optional[int] = None
    intro: Optional[str] = None
    is_administrator: bool = False

    @classmethod
    @unique
    def get_by_username(cls, username):
        return from_sql_results(
            cls, transact("SELECT * FROM usr WHERE username = %s", (username,))
        )

    @classmethod
    def search_by_username(cls, username):
        return from_sql_results(
            cls,
            transact(
                "SELECT * FROM usr WHERE username LIKE %s",
                ("%" + username + "%",),
            ),
        )

    @classmethod
    def exists_email(cls, email):
        return exists(cls, email=email)

    @classmethod
    def exists_username(cls, username):
        return exists(cls, username=username)


@dataclass(eq=False, order=False)
class Passage(HasId, HasTitle, HasContent, HasTimeStamp, HasAuthor, HasHeat):
    pass


@dataclass(eq=False, order=False)
class Comment(HasId, HasContent, HasTimeStamp, HasAuthor, HasContainer):
    pass


@dataclass(eq=False, order=False)
class Image(HasId, HasTimeStamp, HasContainer):
    img_name: str
    describe: str
    own_by: int
