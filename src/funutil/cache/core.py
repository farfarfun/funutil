import hashlib
import inspect
import os
import pickle
from collections.abc import Callable
from functools import cache, cached_property, lru_cache, wraps
from typing import Any

from farlog import getLogger

logger = getLogger("funutil")

__all__ = ["PickleCache", "cache", "cached_property", "lru_cache", "pkl_cache"]


class PickleCache:
    """使用 pickle 文件保存函数结果的装饰器。

    Args:
        cache_key: 用作缓存键的函数参数名。
        cache_dir: 缓存文件目录。
        is_cache: 控制是否缓存的函数参数名。
        printf: 是否以信息级别记录缓存事件。
    """

    def __init__(
        self,
        cache_key: str,
        cache_dir: str = ".cache",
        is_cache: str = "cache",
        printf: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.cache_key = cache_key
        self.cache_dir = cache_dir
        self.is_cache = is_cache

        self.printf = printf

    def log(self, msg: str) -> None:
        """记录缓存事件。

        Args:
            msg: 日志消息。
        """
        if self.printf:
            logger.info(msg)
        else:
            logger.debug(msg)

    def get_cache_file(self, key: Any) -> str:
        """返回缓存键对应的文件路径。

        Args:
            key: 缓存键。

        Returns:
            pickle 缓存文件路径。
        """
        key = str(key)
        # 使用 MD5 值作为缓存文件名
        return os.path.join(
            self.cache_dir, hashlib.md5(key.encode()).hexdigest() + ".pkl"
        )

    @staticmethod
    def load_cache(cache_file: str) -> Any | None:
        """读取缓存文件，文件不存在或内容无效时返回 ``None``。

        Args:
            cache_file: pickle 缓存文件路径。

        Returns:
            已缓存的数据；无法读取时返回 ``None``。
        """
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.PickleError):
            return None

    def save_cache(self, cache_file: str, data: Any) -> None:
        """把数据写入缓存文件。

        Args:
            cache_file: pickle 缓存文件路径。
            data: 要缓存的数据。
        """
        os.makedirs(self.cache_dir, exist_ok=True)
        ignore_file = f"{self.cache_dir}/.gitignore"
        if not os.path.exists(ignore_file):
            with open(ignore_file, "w") as f:
                f.write("*")

        with open(cache_file, "wb") as f:
            pickle.dump(data, f)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i, (name, param) in enumerate(
                list(inspect.signature(func).parameters.items())
            ):
                if name in kwargs:
                    continue
                kwargs[name] = args[i] if i < len(args) else param.default

            is_cache = kwargs.get(self.is_cache, True)
            cache_key = kwargs.get(
                self.cache_key, ""
            )  # 假设输入参数中有一个名为 '${cache_key}' 的字段
            is_cache = is_cache and cache_key is not None
            cache_file = (
                self.get_cache_file(cache_key) if is_cache else None
            )  # 将 SQL 语句作为缓存的键

            if is_cache:
                # 检查缓存中是否存在该键
                cached_result = self.load_cache(cache_file)
                if cached_result is not None:
                    self.log(
                        f"Cache hit for function '{func.__name__}' with key: {cache_key}"
                    )
                    return cached_result

            # 如果没有缓存，执行函数并缓存结果
            result = func(**kwargs)
            if is_cache:
                self.save_cache(cache_file, result)
                self.log(
                    f"Cache data for function '{func.__name__}' with key: {cache_key}"
                )
            return result

        return wrapper


def pkl_cache(
    cache_key: str,
    cache_dir: str = ".cache",
    is_cache: str = "cache",
    printf: bool = False,
    *args: Any,
    **kwargs: Any,
) -> PickleCache:
    """创建 pickle 文件缓存装饰器。

    Args:
        cache_key: 用作缓存键的函数参数名。
        cache_dir: 缓存文件目录。
        is_cache: 控制是否缓存的函数参数名。
        printf: 是否以信息级别记录缓存事件。
        *args: 为兼容旧调用保留的扩展位置参数。
        **kwargs: 为兼容旧调用保留的扩展关键字参数。

    Returns:
        可用于装饰函数的缓存对象。
    """
    return PickleCache(cache_key, cache_dir, is_cache, printf, *args, **kwargs)
