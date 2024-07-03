from Database import transact
from dataclasses import dataclass
from datetime import date
from util import unique, from_sql_results
from flask_login import UserMixin
from Database import transact
from dataclasses import dataclass
from typing import Optional
from datetime import date
from models import unique
from util import from_sql_results


class NotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@dataclass
class BaseData:
    id: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BaseData):
            return self.id == other.id
        else:
            return NotImplemented

    def __ne__(self, other) -> bool:
        if isinstance(other, BaseData):
            return self.id != other.id
        else:
            return NotImplemented

    @classmethod
    @unique
    def get_by_id(cls, id):
        return from_sql_results(
            cls, transact(f"SELECT * FROM {cls.__name__} WHERE id = %s", (id,))
        )

    @classmethod
    def reload_status(cls, self):
        if not isinstance(self, cls):
            raise NotImplementedError
        new_self = cls.get_by_id(self.id)
        if new_self:
            for key, val in new_self.__dict__.items():
                setattr(self, key, val)
        else:
            raise NotExistError


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
    def search_by_content(cls, keyword):
        return from_sql_results(
            cls,
            transact(
                f"SELECT * FROM {cls.__name__} WHERE content LIKE %s",
                ("%" + keyword + "%",),
            ),
        )


@dataclass(eq=False, order=False)
class HasAuthor:
    author_id: int


@dataclass(eq=False, order=False)
class HasContainer:
    contain_by: int


@dataclass(eq=False, order=False)
class User(BaseData, UserMixin):
    password_hash: bytes
    salt: bytes
    username: str
    email: str
    birthday: Optional[date] = None
    sex: Optional[int] = None
    intro: Optional[str] = None
    is_administrator: bool = False
    is_valid: bool = True

    @property
    def is_administrator(self):
        try:
            User.reload_status(self)
        except NotExistError:
            self.is_valid = False
        return self.is_valid and self.is_administrator

    @property
    def is_active(self):
        return self.is_valid

    @classmethod
    @unique
    def get_by_id(cls, id):
        return from_sql_results(cls, transact("SELECT * FROM usr WHERE id = %s", (id,)))

    @classmethod
    @unique
    def get_by_username(cls, username):
        return from_sql_results(
            cls, transact("SELECT * FROM usr WHERE username = %s", (username,))
        )


@dataclass(eq=False, order=False)
class Passage(BaseData, HasTitle, HasContent, HasTimeStamp, HasAuthor):
    pass


@dataclass(eq=False, order=False)
class Announcement(BaseData, HasTitle, HasContent, HasTimeStamp, HasAuthor):
    pass


@dataclass(eq=False, order=False)
class Comment(BaseData, HasContent, HasTimeStamp, HasAuthor, HasContainer):
    pass


@dataclass(eq=False, order=False)
class Vote(BaseData, HasContent, HasTimeStamp, HasAuthor):
    pass


@dataclass(eq=False, order=False)
class OptionItem(BaseData, HasContent, HasContainer):
    vote_cnt: int


@dataclass(eq=False, order=False)
class Poll(BaseData, HasTimeStamp):
    poller_id: int
    option_item_id: int


@dataclass(eq=False, order=False)
class Image(BaseData, HasTimeStamp, HasContainer):
    img_name: str
    describe: str
    own_by: int


print(Passage.search_by_content("2"))
