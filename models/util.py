def unique(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res[0] if res else None

    return wrapper


def from_sql_results(cls, results):
    title, content = results
    return [cls(**dict(zip(title, item))) for item in content]
