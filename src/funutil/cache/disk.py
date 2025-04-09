import inspect
import os
from functools import wraps

from diskcache import Cache
from funutil.util.log import getLogger

logger = getLogger("funutil")

__all__ = ["DiskCache", "disk_cache"]


class DiskCache:
    def __init__(
        self,
        cache_key,
        cache_dir=".cache",
        is_cache="cache",
        expire=60 * 60 * 24,
        *args,
        **kwargs,
    ):
        self.cache_key = cache_key
        self.cache_dir = cache_dir
        self.is_cache = is_cache
        self.expire = expire
        self.cache = Cache(self.cache_dir)

        os.makedirs(self.cache_dir, exist_ok=True)
        ignore_file = f"{self.cache_dir}/.gitignore"
        if not os.path.exists(ignore_file):
            with open(ignore_file, "w") as f:
                f.write("*")

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i, (name, param) in enumerate(
                list(inspect.signature(func).parameters.items())
            ):
                if name in kwargs.keys():
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
    cache_key,
    cache_dir=".cache",
    is_cache="cache",
    expire=60 * 60 * 24,
    *args,
    **kwargs,
):
    return DiskCache(
        cache_key=cache_key,
        cache_dir=cache_dir,
        is_cache=is_cache,
        expire=expire,
        *args,
        **kwargs,
    )
