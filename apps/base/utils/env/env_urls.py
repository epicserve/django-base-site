import os
from typing import Any, Dict
from urllib.parse import ParseResult, parse_qs, urlparse

CACHE_URL_DEFAULT_KEY = "CACHE_URL"

# TODO: switch to using lru_cache if you can figure out how to make it work with mypy
_url_parse_cache: Dict[str, ParseResult] = {}
_get_params_cache: Dict[str, Dict[str, str]] = {}


def get_params(url_str: str) -> Dict[str, str]:

    if url_str in _get_params_cache:
        return _get_params_cache[url_str]

    url: ParseResult = parse_url(url_str)

    # flatten params
    rtn = {key: val[0] for key, val in parse_qs(url.query).items()}
    _get_params_cache[url_str] = rtn
    return rtn


def parse_url(url_str: str) -> ParseResult:

    if url_str in _url_parse_cache:
        return _url_parse_cache[url_str]

    rtn = urlparse(url_str)
    _url_parse_cache[url_str] = rtn
    return rtn


def get_db(url_path: str) -> int:
    db = url_path[1:] or "0"
    return int(db)


def cache_url(env_url: str = "") -> Dict[str, Any]:

    if not env_url:
        env_url = os.environ.get(env_url, CACHE_URL_DEFAULT_KEY)

    url = parse_url(env_url)
    params = get_params(env_url)

    rtn = {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": f"{url.hostname}:{url.port}",
        "OPTIONS": {
            "DB": get_db(url.path),
            "PASSWORD": url.password,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": params.get("max_connections", 50),
                "timeout": params.get("timeout", 20),
            },
        },
    }

    return rtn


def session_redis_url(env_url: str = "") -> Dict[str, Any]:
    if not env_url:
        env_url = os.environ.get(env_url, CACHE_URL_DEFAULT_KEY)

    url = parse_url(env_url)
    params = get_params(env_url)

    rtn = {
        "host": url.hostname,
        "port": url.port,
        "db": get_db(url.path),
        "password": url.password,
        "socket_timeout": params.get("timeout", 20),
    }

    return rtn
