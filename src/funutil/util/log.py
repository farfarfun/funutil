"""兼容旧导入路径的日志接口。"""

from farlog import get_logger, getLogger

__all__ = ["getLogger", "get_logger"]
