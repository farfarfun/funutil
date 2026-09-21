from importlib.metadata import version


def get_package_version(package: str) -> str:
    """返回已安装 Python 包的版本。

    Args:
        package: 分发包名称。

    Returns:
        包版本字符串。
    """
    return version(package)
