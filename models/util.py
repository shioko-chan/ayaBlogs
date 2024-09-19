from flask import current_app
from typing import Callable, Optional, TypeVar, List
from dataclasses import fields, is_dataclass


def transact(transact: str, params=None, have_return=True):
    pool = current_app.extensions["pool"]
    return pool(transact, params, have_return)


T = TypeVar("T")


def unique(func: Callable[..., Optional[List[T]]]) -> Callable[..., Optional[T]]:
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res[0] if res else None

    return wrapper


def from_sql_results(cls, results):
    title, content = results
    return [cls(**dict(zip(title, item))) for item in content]


def exists(cls, use_and_operator=True, **kwargs):
    op = "AND" if use_and_operator else "OR"
    _, val = transact(
        f"SELECT 1 WHERE EXISTS(SELECT 1 FROM {cls.__name__} WHERE {f' {op} '.join([f'{key} = %s' for key in kwargs.keys()])})",
        tuple(kwargs.values()),
    )
    return bool(val)


def get_config(key, default=None):
    return current_app.config.get(key, default)


def get_extension(key, default=None):
    return current_app.extensions.get(key, default)


def field_names(cls):
    if is_dataclass(cls):
        return [field.name for field in fields(cls)]
    else:
        raise ValueError("Not a dataclass")
