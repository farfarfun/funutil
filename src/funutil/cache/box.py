from collections.abc import Callable
from typing import Any

from cachebox import FIFOCache, LFUCache, LRUCache, RRCache, TTLCache, VTTLCache, cached

__all__ = [
    "cache",
    "fifo_cache",
    "lfu_cache",
    "lru_cache",
    "rr_cache",
    "ttl_cache",
    "vttl_cache",
]


_Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]


def cache(func: Callable[..., Any], /) -> Callable[..., Any]:
    """使用默认大小的 LRU 缓存装饰函数。

    Args:
        func: 要缓存结果的函数。

    Returns:
        带缓存能力的函数。
    """
    return cached(LRUCache(maxsize=1000)).__call__(func)


def vttl_cache(maxsize: int = 1000) -> _Decorator:
    """创建支持逐项过期时间的缓存装饰器。

    Args:
        maxsize: 最大缓存项数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(VTTLCache(maxsize=maxsize, ttl=60)).__call__(func)


def ttl_cache(maxsize: int = 1000, ttl: float = 60) -> _Decorator:
    """创建统一过期时间的缓存装饰器。

    Args:
        maxsize: 最大缓存项数。
        ttl: 缓存有效秒数。

    Returns:
        函数装饰器。
    """
    return lambda func: cached(TTLCache(maxsize=maxsize, global_ttl=ttl)).__call__(func)


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
