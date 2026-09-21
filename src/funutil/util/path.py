import os
from collections.abc import Iterable
from os import PathLike
from typing import Any

from funutil.path.core import (
    delete_file,
    exist_and_create,
    exists,
    exists_dir,
    exists_file,
    info,
    join_path,
    makedirs,
    path_join,
    path_parse,
    rename,
)

__all__ = [
    "LocalPath",
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
    "rename",
    "split_file",
]

_Path = str | PathLike[str]


def _file_name(path: _Path) -> str:
    return os.path.basename(path)


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


def list_file(file_dir: _Path, deep: int = 1) -> list[dict[str, Any]]:
    """
    返回这个目录下所有的目录和文件，深度为deep
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
            result.append(meta(file_dir=file_dir, file_name=file_name, deep=deep))
        elif os.path.isdir(tmp_path):
            result.append(meta(file_dir=tmp_path, deep=deep))
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


class LocalPath:
    """保存本地文件路径并提供基本文件操作。

    Args:
        file_dir: 文件所在目录。
        file_name: 文件名。
        file_path: 完整文件路径，优先于目录和文件名。
    """

    def __init__(
        self,
        file_dir: _Path | None = None,
        file_name: _Path | None = None,
        file_path: _Path | None = None,
    ) -> None:
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)

        if file_dir is not None and file_name is not None:
            file_path = os.path.join(file_dir, file_name)

        self.file_dir = file_dir
        self.file_name = file_name
        self.file_path = file_path

    def make_dirs(self) -> None:
        """创建保存的目录路径。"""
        os.makedirs(self.file_dir)

    def exist(self) -> bool:
        """返回保存的文件路径是否存在。"""
        return os.path.exists(self.file_path)

    def list_file(self, deep: int = 1) -> list[dict[str, Any]]:
        """返回目录下指定深度内的文件和目录元数据。"""
        result = []
        if deep <= 0:
            return result
        for file in os.listdir(self.file_dir):
            tmp_path = os.path.join(self.file_dir, file)
            if os.path.isfile(tmp_path):
                result.append(self.to_json(file, deep=deep))
            elif os.path.isdir(tmp_path):
                result.append(self.to_json(deep=deep))
                result.extend(LocalPath(file_dir=tmp_path).list_file(deep=deep - 1))

        return result

    def meta(self) -> dict[str, Any]:
        """返回当前路径的元数据。"""
        return self.to_json(self.file_name)

    def to_json(self, file_name: _Path | None = None, deep: int = 1) -> dict[str, Any]:
        """把路径信息转换为字典。

        Args:
            file_name: 相对于保存目录的文件名。
            deep: 当前遍历深度。

        Returns:
            路径元数据字典。
        """
        return {
            "dir": self.file_dir,
            "name": file_name,
            "path": self.file_dir
            if file_name is None
            else os.path.join(self.file_dir, file_name),
            "isdir": file_name is None,
            "deep": deep,
        }
