import environs

from . import env_urls

env = environs.Env()


@env.parser_for("cache_url")
def cache_url_parser(value):
    return env_urls.cache_url(value)


@env.parser_for("session_redis_url")
def session_redis_url_parser(value):
    return env_urls.session_redis_url(value)
