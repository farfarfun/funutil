import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from .log import getLogger

logger = getLogger("funutil")

__all__ = ["Retry", "retry"]


class Retry:
    """在函数失败时按指定次数重试。

    Args:
        retry_cnt: 最大调用次数，必须大于零。
        sleep_after_retry: 每次失败后的等待秒数。
        throw_error_after_retry: 已弃用的兼容参数；耗尽次数后始终抛出原异常。
        retry_exceptions: 可重试的异常类型，默认为常见 I/O 异常。
    """

    def __init__(
        self,
        retry_cnt: int = 3,
        sleep_after_retry: float = 0,
        throw_error_after_retry: bool = True,
        retry_exceptions: tuple[type[Exception], ...] = (OSError,),
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if retry_cnt < 1:
            raise ValueError("retry_cnt 必须大于零")
        self.retry_cnt = retry_cnt
        self.sleep_after_retry = sleep_after_retry
        self.throw_error_after_retry = throw_error_after_retry
        self.retry_exceptions = retry_exceptions

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for step in range(self.retry_cnt):
                try:
                    return func(*args, **kwargs)
                except self.retry_exceptions as e:
                    logger.error(
                        f"Exception while retrying {step + 1}/{self.retry_cnt}: {e}"
                    )
                    if self.sleep_after_retry > 0 and step < self.retry_cnt - 1:
                        time.sleep(self.sleep_after_retry)
                    if step == self.retry_cnt - 1:
                        raise
            raise RuntimeError("重试循环未执行")

        return wrapper


def retry(
    retry_cnt: int = 3,
    sleep_after_retry: float = 0,
    throw_error_after_retry: bool = True,
    retry_exceptions: tuple[type[Exception], ...] = (OSError,),
    *args: Any,
    **kwargs: Any,
) -> Retry:
    """创建重试装饰器。

    Args:
        retry_cnt: 最大调用次数，必须大于零。
        sleep_after_retry: 每次失败后的等待秒数。
        throw_error_after_retry: 已弃用的兼容参数；耗尽次数后始终抛出原异常。
        retry_exceptions: 可重试的异常类型，默认为常见 I/O 异常。
        *args: 为兼容旧调用保留的扩展位置参数。
        **kwargs: 为兼容旧调用保留的扩展关键字参数。

    Returns:
        可用于装饰函数的重试对象。
    """
    return Retry(
        retry_cnt,
        sleep_after_retry,
        throw_error_after_retry,
        retry_exceptions,
        *args,
        **kwargs,
    )
