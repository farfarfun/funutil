import json
import time
from collections.abc import Callable
from functools import wraps
from threading import Timer
from types import TracebackType
from typing import Any


class CacheDump:
    """按时间间隔把计时统计写入 JSON 文件。

    Args:
        elapsed: 两次写入之间的最小秒数。
    """

    def __init__(self, elapsed: float = 10) -> None:
        """初始化统计缓存。

        Args:
            elapsed: 两次写入之间的最小秒数。
        """
        self.dump_data: dict[str, Any] = {}
        self.elapsed = elapsed
        self.last_dump_time = time.time()

    def add(self, key: str, value: Any, dump_file: str | None = None) -> None:
        """添加统计项并在满足间隔时写入文件。

        Args:
            key: 统计项名称。
            value: 统计数据。
            dump_file: JSON 输出路径；省略时不写文件。
        """
        self.dump_data[key] = value
        self.dump(dump_file)

    def dump(self, dump_file: str | None = None) -> None:
        """在满足间隔时把当前统计写入文件。

        Args:
            dump_file: JSON 输出路径；省略时不写文件。
        """
        if dump_file is None:
            return
        if time.time() - self.last_dump_time < self.elapsed:
            return
        dump_data = {
            "data": self.dump_data,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(dump_file, "w", encoding="utf-8") as out_data:
            out_data.write(json.dumps(dump_data, indent=4, sort_keys=True))
        self.last_dump_time = time.time()


class RunTimer:
    """统计函数或代码块的调用次数和运行时间。

    Args:
        time_func: 提供单调时间值的函数。
        dump_file: 统计输出文件；传入 ``None`` 时不写文件。
    """

    cache_dump = CacheDump(elapsed=3)

    def __init__(
        self,
        time_func: Callable[[], float] = time.perf_counter,
        dump_file: str | None = "runtime.log",
    ) -> None:
        self.counter = 0
        self.elapsed = 0
        self.dump_file = dump_file
        self.time_func = time_func
        self.time_snapshot: float | None = None

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.start()
            try:
                res = func(*args, **kwargs)
            finally:
                self.stop()
            if self.dump_file is not None:
                key = f"{func.__code__.co_flags}-{func.__name__}"
                value = {
                    "counter": self.counter,
                    "elapsed": self.elapsed,
                    "average": self.elapsed / self.counter,
                }
                self.cache_dump.add(key, value, dump_file=self.dump_file)
            return res

        return wrapper

    def start(self) -> None:
        """开始一次计时。"""
        self.time_snapshot = self.time_func()

    def stop(self) -> None:
        """结束当前计时并累加统计。"""
        if self.time_snapshot is None:
            raise RuntimeError("计时尚未开始")
        self.elapsed += self.time_func() - self.time_snapshot
        self.time_snapshot = None
        self.counter += 1

    def __str__(self) -> str:
        average = self.elapsed / self.counter if self.counter else 0.0
        return f"{self.counter}, {average}s"

    @property
    def running(self) -> bool:
        """返回计时器当前是否正在计时。"""
        return self.time_snapshot is not None

    def __enter__(self) -> "RunTimer":  # noqa: PYI034 - 支持 Python 3.10
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.stop()
        return False


class RepeatingTimer(Timer):
    """按固定间隔重复调用目标函数，直至计时器结束。"""

    def run(self) -> None:
        """重复执行目标函数，直至收到结束信号。"""
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def run_timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """使用默认计时器装饰函数。

    Args:
        func: 要统计运行时间的函数。

    Returns:
        带计时统计的函数。
    """
    return RunTimer().__call__(func)
