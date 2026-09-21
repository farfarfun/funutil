from typing import Any


def deep_get(data: dict[str, Any] | list[Any] | None, *keys: str | int) -> Any | None:
    """按键或下标逐层读取嵌套数据，路径不存在时返回 ``None``。

    Args:
        data: 待读取的字典或列表。
        *keys: 字典键或列表下标组成的路径。

    Returns:
        路径对应的值；路径无效时返回 ``None``。
    """
    if data is None:
        return None
    for key in keys:
        is_list_index = (
            isinstance(key, int)
            and isinstance(data, list)
            and -len(data) <= key < len(data)
        )
        is_dict_key = isinstance(key, str) and isinstance(data, dict) and key in data
        if not (is_list_index or is_dict_key):
            return None
        data = data[key]
    return data


def find_get(data: dict[str, Any] | None, *keys: str) -> Any | None:
    """返回字典中第一个匹配候选键的值。

    Args:
        data: 待读取的字典。
        *keys: 按优先级排列的候选键。

    Returns:
        第一个匹配键的值；没有匹配时返回 ``None``。
    """
    if not data:
        return None
    for key in keys:
        if key in data:
            return data[key]
    return None
