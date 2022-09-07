import functools


def cached(key):
    def factory(function):
        cache = {}

        @functools.wraps(function)
        def wrapper(*args):
            cache_key = key(*args)
            value = cache.get(cache_key, None)
            if value is None:
                value = cache[cache_key] = function(*args)
            return value

        return wrapper
    return factory
