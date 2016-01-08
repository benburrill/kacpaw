KA_DOMAIN = "https://www.khanacademy.org"

# An exception that indicates that something will be implemented in the future
todo = NotImplementedError("Not yet implemented")


def kaurl(*location):
    """Forms a url on KA"""
    return "/".join((KA_DOMAIN,) + location)

def raiser(exception):
    """Returns a function that raises an exception"""
    def do_raise(*args, **kwargs):
        raise exception
    return do_raise

def get_dict_path(base, path):
    path = list(path)
    level = path.pop(0)

    if path:
        return get_dict_path(base[level], path)
    return base[level]

def update_dict_path(base, path, value, default=dict):
    path = list(path)
    level = path.pop(0)

    if path: # we need to go at least one level deeper
        base.setdefault(level, default())
        update_dict_path(base[level], path, value, default)
    else: # level is the level we are trying to set
        base[level] = value
    return base # return base, now updated, for convenience

def method(cls, name):
    def decorator(func):
        func.__name__ = name
        func.__qualname__ = ".".join([cls.__qualname__, func.__name__])
        return func
    return decorator