import os
import shutil
from collections.abc import Iterable
from os import PathLike
from typing import Any

from farlog import getLogger

logger = getLogger("funutil")

__all__ = [
    "delete_file",
    "exist_and_create",
    "exists",
    "exists_dir",
    "exists_file",
    "info",
    "join_path",
    "list_file",
    "makedirs",
    "merge_file",
    "meta",
    "path_join",
    "path_parse",
    "removedirs",
    "rename",
    "split_file",
]

_Path = str | PathLike[str]


def info(msg: str) -> None:
    """记录路径操作信息。

    Args:
        msg: 日志消息。
    """
    logger.info(msg)


def rename(src: _Path, dst: _Path) -> None:
    """重命名存在的文件或目录。

    Args:
        src: 原路径。
        dst: 目标路径。
    """
    if os.path.exists(src):
        return os.rename(src, dst)
    else:
        logger.error(f"{src} not exist!")
        return


def removedirs(name: str | PathLike[str]) -> None:
    """递归删除目录及其内容。

    Args:
        name: 要删除的目录路径。
    """
    shutil.rmtree(name)


def path_parse(path: _Path | None) -> str | None:
    """展开用户目录并把相对路径转换为绝对路径。

    Args:
        path: 待解析路径。

    Returns:
        解析后的路径；输入为 ``None`` 时仍返回 ``None``。
    """
    if path is None:
        return path
    # ~处理
    path = os.path.expanduser(path)
    if not path.startswith("/"):
        return os.path.join(os.getcwd(), path)
    return path


def path_join(parent_path: _Path, child_path: _Path) -> str:
    """连接父路径和子路径。

    Args:
        parent_path: 父路径。
        child_path: 子路径。

    Returns:
        连接后的路径。
    """
    return os.path.join(path_parse(parent_path), child_path)


def join_path(child_path: _Path, parent_path: _Path | None = None) -> str:
    """按旧参数顺序连接子路径和父路径。

    Args:
        child_path: 子路径。
        parent_path: 父路径。

    Returns:
        连接后的路径。
    """
    return path_join(parent_path or os.getcwd(), child_path)


def delete_file(file_path: _Path) -> None:
    """删除存在的文件。

    Args:
        file_path: 文件路径。
    """
    if exists_file(file_path):
        info("file exist and delete")
        os.remove(file_path)


def exists_dir(file_dir: _Path, mkdir: bool = False) -> bool:
    """检查目录是否存在，并可在缺失时创建。

    Args:
        file_dir: 目录路径。
        mkdir: 缺失时是否创建目录。

    Returns:
        检查时目录是否已存在。
    """
    return exists(file_dir=file_dir, mkdir=mkdir, mode="path")


def exists_file(file_path: _Path, mkdir: bool = False) -> bool:
    """检查文件是否存在，并可创建缺失的父目录。

    Args:
        file_path: 文件路径。
        mkdir: 父目录缺失时是否创建。

    Returns:
        检查时文件是否已存在。
    """
    return exists(file_path=file_path, mkdir=mkdir, mode="file")


def exists(
    file_path: _Path | None = None,
    file_dir: _Path | None = None,
    file_name: _Path | None = None,
    mode: str = "file",
    mkdir: bool = False,
) -> bool:
    """
    文件或者目录是否存在，不存在是否需要新建
    :param file_path: 文件路径
    :param file_dir:  文件目录
    :param file_name: 文件名称
    :param mode:  file-文件，path-目录
    :param mkdir: 目录不存在是否需要新建
    :return: 是否存在
    """

    file_path = path_parse(file_path)
    file_dir = path_parse(file_dir)

    if mode == "file":
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)
        elif file_dir is not None and file_name is not None:
            file_path = os.path.join(file_dir, file_name)
        else:
            logger.warning("file_path or file_dir&file_name is needed")
            return False

        if os.path.exists(file_dir) and os.path.isdir(file_dir):
            return os.path.exists(file_path) and os.path.isfile(file_path)
        elif not os.path.exists(file_dir) and mkdir:
            makedirs(file_dir)
        return False

    elif mode == "path":
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)
        elif file_dir is None:
            logger.warning("file_path or file_dir is needed")
            return False

        if os.path.exists(file_dir) and os.path.isdir(file_dir):
            return True
        elif mkdir:
            makedirs(file_dir)
        return False

    return False


def exist_and_create(file_dir: _Path) -> None:
    """确保目录存在。

    Args:
        file_dir: 目录路径。
    """
    if os.path.exists(file_dir) and os.path.isdir(file_dir):
        return

    os.makedirs(file_dir)
    return


def _file_path(path: _Path) -> str:
    return os.path.dirname(path)


def _file_name(path: _Path) -> str:
    return os.path.basename(path)


def makedirs(name: _Path, mode: int = 0o777, exist_ok: bool = False) -> None:
    """递归创建目录。

    Args:
        name: 目录路径。
        mode: 新目录权限。
        exist_ok: 目录已存在时是否忽略错误。
    """
    os.makedirs(name, mode=mode, exist_ok=exist_ok)


def meta(
    file_dir: _Path, file_name: _Path | None = None, deep: int = 1
) -> dict[str, Any]:
    """
    返回文件的基本信息
    :param file_dir: 路径
    :param file_name: 文件名称
    :param deep: 深度
    :return:文件信息
    """
    return {
        "dir": file_dir,
        "name": file_name,
        "path": file_dir if file_name is None else os.path.join(file_dir, file_name),
        "isdir": file_name is None,
        "deep": deep,
    }


def list_file(file_dir: str | PathLike[str], deep: int = 1) -> list[str]:
    """
    返回这个目录下所有的文件，深度为deep
    :param file_dir: 路径
    :param deep:深度
    :return: 所有目录和文件
    """
    result = []
    if deep <= 0:
        return result
    for file_name in os.listdir(file_dir):
        tmp_path = os.path.join(file_dir, file_name)
        if os.path.isfile(tmp_path):
            result.append(tmp_path)
        elif os.path.isdir(tmp_path):
            result.extend(list_file(tmp_path, deep=deep - 1))
    return result


def merge_file(source_file: Iterable[_Path], target_file: _Path) -> None:
    """依次合并多个文本文件。

    Args:
        source_file: 源文件路径集合。
        target_file: 合并后的文件路径。
    """
    flag = 0  # 计数器

    info("开始。。。。。")

    with open(target_file, "w+") as write_file:
        for file_path in source_file:
            with open(file_path, "r") as f_source:
                write_file.writelines(f_source)
            write_file.write("\n")

    info("done " + str(flag) + "\t" + target_file)
    info("完成。。。。。")


def split_file(source_file: _Path, target_dir: _Path, max_line: int = 2000000) -> None:
    """按最大行数把文本文件拆分为多个 CSV 文件。

    Args:
        source_file: 源文件路径。
        target_dir: 输出目录前缀。
        max_line: 每个分卷的最大行数。
    """
    file_name = _file_name(source_file)
    flag = 0  # 计数器
    name = 1  # 文件名

    info("开始。。。。。")

    def get_filename() -> str:
        return str(target_dir) + file_name + "-split-" + str(name) + ".csv"

    write_file = open(get_filename(), "w+")  # noqa: SIM115 - 分卷时需要动态轮换句柄

    with open(source_file, "r") as f_source:
        for line in f_source:
            flag += 1

            write_file.write(line)

            if flag == max_line:
                info("done " + str(flag) + "\t" + get_filename())
                name += 1
                flag = 0

                write_file.close()
                write_file = open(get_filename(), "w+")  # noqa: SIM115 - 分卷时需要动态轮换句柄
    write_file.close()
    info("done " + str(flag) + "\t" + get_filename())
    info("完成。。。。。")
