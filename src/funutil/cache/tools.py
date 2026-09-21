from collections.abc import Callable
from typing import Any

from cachetools import FIFOCache, LFUCache, LRUCache, RRCache, TTLCache, cached

__all__ = ["cache", "fifo_cache", "lfu_cache", "lru_cache", "rr_cache", "ttl_cache"]

_Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]


def cache(func: Callable[..., Any], /) -> Callable[..., Any]:
    """使用默认大小的 LRU 缓存装饰函数。

    Args:
        func: 要缓存结果的函数。

    Returns:
        带缓存能力的函数。
    """
    return cached(LRUCache(maxsize=100)).__call__(func)


def ttl_cache(maxsize: int = 1000) -> _Decorator:
    """创建固定 60 秒有效期的缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(TTLCache(maxsize=maxsize, ttl=60)).__call__(func)


def lru_cache(maxsize: int = 1000) -> _Decorator:
    """创建最近最少使用缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(LRUCache(maxsize=maxsize)).__call__(func)


def lfu_cache(maxsize: int = 1000) -> _Decorator:
    """创建最不经常使用缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(LFUCache(maxsize=maxsize)).__call__(func)


def fifo_cache(maxsize: int = 1000) -> _Decorator:
    """创建先进先出缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(FIFOCache(maxsize=maxsize)).__call__(func)


def rr_cache(maxsize: int = 1000) -> _Decorator:
    """创建随机替换缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(RRCache(maxsize=maxsize)).__call__(func)
