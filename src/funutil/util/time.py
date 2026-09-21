import time
from datetime import datetime, timedelta

from funutil.util.log import getLogger

logger = getLogger("funutil")


_DAY_SECOND = 24 * 60 * 60
_HOUR_SECOND = 60 * 60
_TEN_MINUTE_SECOND = 10 * 60
_MINUTE_SECOND = 60


class WorkTime:
    """判断给定本地时间是否接近指定周期的结束位置。"""

    @staticmethod
    def time_to_end(
        time_str: str | float | None = None,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        circle_time: int = _DAY_SECOND,
        threshold_time: int = 60,
    ) -> bool:
        """判断时间是否落在周期结束前的阈值内。

        Args:
            time_str: 本地时间字符串或 Unix 时间戳；省略时使用当前时间。
            format_str: 字符串时间格式。
            circle_time: 周期秒数。
            threshold_time: 周期结束前的阈值秒数。

        Returns:
            时间处于周期结束阈值内时返回 ``True``。
        """
        if time_str is None:
            unix = int(time.time())
        elif isinstance(time_str, (int, float)):
            unix = int(time_str)
        else:
            unix = int(time.mktime(time.strptime(time_str, format_str)))

        logger.debug(f"本地时间为 :{unix}")

        second_mod = unix % circle_time
        if second_mod > circle_time - threshold_time:
            logger.debug("time to end")
            return True
        return False

    def time_to_day_end(self, *args, **kwargs) -> bool:
        """判断时间是否接近一天结束。"""
        return self.time_to_end(
            *args, circle_time=_DAY_SECOND, threshold_time=60, **kwargs
        )

    def time_to_hour_end(self, *args, **kwargs) -> bool:
        """判断时间是否接近一小时结束。"""
        return self.time_to_end(
            *args, circle_time=_HOUR_SECOND, threshold_time=60, **kwargs
        )

    def time_to_ten_minute_end(self, *args, **kwargs) -> bool:
        """判断时间是否接近十分钟周期结束。"""
        return self.time_to_end(
            *args, circle_time=_TEN_MINUTE_SECOND, threshold_time=30, **kwargs
        )

    def time_to_minute_end(self, *args, **kwargs) -> bool:
        """判断时间是否接近一分钟结束。"""
        return self.time_to_end(
            *args, circle_time=_MINUTE_SECOND, threshold_time=10, **kwargs
        )

    def test(self) -> None:
        """执行各周期判断的基本调用检查。"""
        time_str = "2021-01-01 10:32:32"
        self.time_to_day_end(time_str=time_str)
        self.time_to_hour_end(time_str=time_str)
        self.time_to_ten_minute_end(time_str=time_str)

        self.time_to_day_end()
        self.time_to_hour_end()
        self.time_to_ten_minute_end()

        unix = int(time.time())
        self.time_to_day_end(unix)
        self.time_to_hour_end(unix)
        self.time_to_ten_minute_end(unix)


def now2unix() -> int:
    """
    当前时间戳
    :return:
    """
    return int(time.mktime(time.localtime()))


def now2time(time_type: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    当前时间
    :return:
    """
    return time.strftime(time_type, time.localtime())


def time2unix(time_str: str, time_type: str = "%Y-%m-%d %H:%M:%S") -> int:
    """
    > str2unix('2013-10-10 23:40:00')

    '2013-10-10 23:40:00'
    :param time_str:
    :param time_type: '%Y-%m-%d %H:%M:%S'
    :return:
    """
    return int(time.mktime(time.strptime(time_str, time_type)))


def unix2time(time_stamp: float, time_type: str = "%Y-%m-%d %H:%M:%S") -> str:
    """把 Unix 时间戳格式化为本地时间字符串。

    Args:
        time_stamp: Unix 时间戳。
        time_type: 输出格式。

    Returns:
        格式化后的本地时间字符串。
    """
    return time.strftime(time_type, time.localtime(time_stamp))


def month_first_datetime(months: int) -> datetime:
    """返回相对当前月份偏移后的首日零点。"""
    today = datetime.today()  # noqa: DTZ002 - 该 API 明确返回本地朴素时间
    months = today.month + months - 1
    years = -int((months % 12 - months) / 12)
    months = months % 12 + 1

    return datetime(  # noqa: DTZ001 - 保持既有本地朴素时间返回类型
        today.year + years, months, 1
    )


def month_during(months: int) -> tuple[int, datetime, datetime]:
    """返回相对月份的偏移值、首日和末日。"""
    first = month_first_datetime(months)
    last = month_first_datetime(months + 1) - timedelta(seconds=1)
    return months, first, last


def week_during(weeks: int) -> tuple[datetime, datetime]:
    """返回相对周的开始和结束本地时间。"""
    today = datetime.today()  # noqa: DTZ002 - 该 API 明确返回本地朴素时间
    first = today + timedelta(weeks=weeks) - timedelta(days=today.weekday())
    first = datetime(  # noqa: DTZ001 - 保持既有本地朴素时间返回类型
        first.year, first.month, first.day
    )
    last = first + timedelta(weeks=1) - timedelta(seconds=1)
    return first, last


def day_during(days: int) -> tuple[datetime, datetime]:
    """返回相对日期的开始和结束本地时间。"""
    today = datetime.today()  # noqa: DTZ002 - 该 API 明确返回本地朴素时间
    first = today + timedelta(days=days)
    first = datetime(  # noqa: DTZ001 - 保持既有本地朴素时间返回类型
        first.year, first.month, first.day
    )
    last = first + timedelta(days=1) - timedelta(seconds=1)
    return first, last
