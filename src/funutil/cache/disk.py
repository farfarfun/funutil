import inspect
import os
from collections.abc import Callable
from functools import wraps
from hashlib import md5
from typing import Any

from diskcache import Cache

from funutil.util.log import getLogger

logger = getLogger("funutil")

__all__ = ["DiskCache", "disk_cache"]


class DiskCache:
    """使用 diskcache 保存函数结果的装饰器。

    Args:
        cache_key: 用作缓存键的函数参数名。
        cache_dir: 缓存目录；省略时按被装饰函数生成。
        is_cache: 控制是否缓存的函数参数名。
        expire: 缓存有效秒数。
    """

    def __init__(
        self,
        cache_key: str,
        cache_dir: str | None = None,
        is_cache: str = "cache",
        expire: float = 60 * 60 * 24,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.cache_key = cache_key
        self.cache_dir = cache_dir
        self.is_cache = is_cache
        self.expire = expire
        self.cache: Cache | None = None

    def init_cache(self, func: Callable[..., Any]) -> Cache:
        """初始化并返回底层磁盘缓存。

        Args:
            func: 被缓存的函数。

        Returns:
            已初始化的 diskcache 缓存。
        """
        if self.cache is not None:
            return self.cache
        uid = md5(func.__code__.co_filename.encode("utf-8")).hexdigest()
        if self.cache_dir is None:
            self.cache_dir = os.path.join(".disk_cache", f"{uid}-{func.__name__}")
        logger.success(
            f"init func {func.__name__} success. with cache_dir: {self.cache_dir}"
        )
        self.cache = Cache(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        ignore_file = f"{self.cache_dir}/.gitignore"
        if not os.path.exists(ignore_file):
            with open(ignore_file, "w") as f:
                f.write("*")
        return self.cache

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self.init_cache(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            for i, (name, param) in enumerate(
                list(inspect.signature(func).parameters.items())
            ):
                if name in kwargs:
                    continue
                kwargs[name] = args[i] if i < len(args) else param.default

            cache_key = kwargs.get(self.cache_key, "")
            is_cache = kwargs.get(self.is_cache, True) and cache_key is not None

            if not is_cache:
                return func(**kwargs)

            # 检查缓存中是否存在该键
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(
                    f"Cache hit for function '{func.__name__}' with key: {cache_key}"
                )
                return cached_result

            # 如果没有缓存，执行函数并缓存结果
            result = func(**kwargs)
            self.cache.set(cache_key, result, expire=self.expire)
            logger.debug(
                f"Cache data for function '{func.__name__}' with key: {cache_key}"
            )
            return result

        return wrapper


def disk_cache(
    cache_key: str,
    cache_dir: str | None = None,
    is_cache: str = "cache",
    expire: float = 60 * 60 * 24,
    *args: Any,
    **kwargs: Any,
) -> DiskCache:
    """创建磁盘缓存装饰器。

    Args:
        cache_key: 用作缓存键的函数参数名。
        cache_dir: 缓存目录。
        is_cache: 控制是否缓存的函数参数名。
        expire: 缓存有效秒数。
        *args: 为兼容旧调用保留的扩展位置参数。
        **kwargs: 为兼容旧调用保留的扩展关键字参数。

    Returns:
        可用于装饰函数的缓存对象。
    """
    return DiskCache(cache_key, cache_dir, is_cache, expire, *args, **kwargs)
