# funutil

`funutil` 是一个轻量的 Python 通用工具库，提供嵌套数据读取、缓存、计时和路径处理等常用能力。

## 安装

```bash
pip install funutil
```

## 最小示例

```python
from funutil import deep_get

data = {"users": [{"name": "farfarfun"}]}
print(deep_get(data, "users", 0, "name"))
```

## 重试装饰器

```python
from funutil.util.retrying import retry


@retry(retry_cnt=3, sleep_after_retry=1, retry_exceptions=(OSError,))
def call_remote(): ...
```

`retry_exceptions` 用于限定只重试指定类型的异常；重试次数耗尽后始终重新抛出原始
异常。`throw_error_after_retry` 参数已弃用且不再影响行为，显式传参会触发
`DeprecationWarning`，计划在下一个次版本中移除，请直接删除该参数。

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
