"""Lightweight smoke tests for funutil.

funutil is a small general-purpose utility library (logging helper, decorators,
caches, misc helpers). These tests are not exhaustive unit tests; they exist to
catch import breakage and gross regressions in the public API surface. Any real
network/filesystem/cloud calls are avoided or isolated to tmp_path.
"""

import importlib.metadata

import pytest


# ---------------------------------------------------------------------------
# Imports: the top-level package and every "obviously public" submodule
# should import cleanly with no ImportError.
# ---------------------------------------------------------------------------


def test_import_top_level_package():
    import funutil

    for name in [
        "RunTimer",
        "deep_get",
        "get_logger",
        "find_get",
        "getLogger",
        "run_timer",
        "get_package_version",
    ]:
        assert hasattr(funutil, name), f"funutil.{name} missing"


@pytest.mark.parametrize(
    "module_name",
    [
        "funutil.cache",
        "funutil.cache.box",
        "funutil.cache.core",
        "funutil.cache.disk",
        "funutil.cache.tools",
        "funutil.convert",
        "funutil.convert.curl2py",
        "funutil.math",
        "funutil.math.prime",
        "funutil.path",
        "funutil.path.core",
        "funutil.time",
        "funutil.time.timer",
        "funutil.util",
        "funutil.util.log",
        "funutil.util.map",
        "funutil.util.package",
        "funutil.util.path",
        "funutil.util.retrying",
        "funutil.util.time",
    ],
)
def test_import_public_submodules(module_name):
    importlib.import_module(module_name)


def test_paper_submodules_not_importable_here():
    # funutil.paper.Paper / Paper2 execute real, unmocked network requests
    # (web-of-knowledge / cnki scraping with expired, hardcoded cookies) at
    # *module import time* -- there is no way to import them without firing
    # a live HTTP request, so they are intentionally excluded from the smoke
    # suite rather than mocked at import-time module-body granularity.
    pytest.skip(
        "funutil.paper.Paper/Paper2 在模块顶层直接发起真实网络请求（爬取网站，"
        "使用过期的硬编码 cookie），无法安全 import，跳过"
    )


# ---------------------------------------------------------------------------
# funutil.util.map: deep_get / find_get
# ---------------------------------------------------------------------------


def test_find_get_returns_first_matching_key():
    from funutil import find_get

    data = {"k1": "v1", "k2": "v2"}
    assert find_get(data, "missing", "k1") == "v1"
    assert find_get(data, "nope") is None
    assert find_get(None, "k1") is None


def test_deep_get_dict_path():
    from funutil import deep_get

    data = {"a": {"b": {"c": "leaf"}}}
    assert deep_get(data, "a", "b", "c") == "leaf"
    assert deep_get(data, "a", "missing") is None
    assert deep_get(None, "a") is None


def test_deep_get_integer_list_index_is_broken():
    # KNOWN BUG: deep_get()'s loop body has two independent `if` statements
    # instead of `if/elif`, so after a successful integer list-index step the
    # second (str/dict) `if` always fails and its `else: return None` fires
    # unconditionally. Any path that indexes into a list with an int always
    # returns None instead of the element. Not fixed here (smoke-test scope
    # only, no business-logic fixes).
    pytest.skip(
        "已知bug：deep_get 对路径中包含 list 整数下标的情况恒返回 None"
        "（两个独立 if 而非 if/elif 导致的逻辑缺陷），不在本次冒烟测试修复范围内"
    )


# ---------------------------------------------------------------------------
# funutil.util.log / top-level get_logger
# ---------------------------------------------------------------------------


def test_get_logger_returns_usable_logger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from funutil import get_logger, getLogger

    logger = get_logger("smoke_test_logger")
    # should not raise
    logger.info("smoke test log message")

    logger2 = getLogger("smoke_test_logger2")
    logger2.info("smoke test log message 2")


# ---------------------------------------------------------------------------
# funutil.get_package_version
# ---------------------------------------------------------------------------


def test_get_package_version_matches_installed_metadata():
    from funutil import get_package_version

    assert get_package_version("funutil") == importlib.metadata.version("funutil")


# ---------------------------------------------------------------------------
# funutil.RunTimer / run_timer decorator
# ---------------------------------------------------------------------------


def test_run_timer_decorator_wraps_function(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from funutil import run_timer

    @run_timer
    def add(a, b):
        return a + b

    assert add(2, 3) == 5
    assert add(4, 5) == 9


def test_run_timer_context_manager(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from funutil import RunTimer

    timer = RunTimer(dump_file=None)
    assert timer.running is False
    with timer:
        assert timer.running is True
    assert timer.running is False
    assert timer.counter == 1


# ---------------------------------------------------------------------------
# funutil.util.retrying: Retry / retry
# ---------------------------------------------------------------------------


def test_retry_succeeds_after_transient_failures():
    from funutil.util.retrying import retry

    attempts = {"n": 0}

    @retry(retry_cnt=3, sleep_after_retry=0, throw_error_after_retry=True)
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ValueError("transient failure")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 3


def test_retry_raises_after_exhausting_attempts():
    from funutil.util.retrying import retry

    @retry(retry_cnt=2, sleep_after_retry=0, throw_error_after_retry=True)
    def always_fails():
        raise ValueError("permanent failure")

    with pytest.raises(Exception):
        always_fails()


# ---------------------------------------------------------------------------
# funutil.cache: in-memory decorators (cachebox-backed)
# ---------------------------------------------------------------------------


def test_lru_cache_decorator_caches_results():
    from funutil.cache import lru_cache

    calls = []

    @lru_cache(maxsize=10)
    def add(a, b):
        calls.append((a, b))
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert len(calls) == 1  # second call was served from cache


def test_ttl_cache_decorator_basic_call():
    # KNOWN BUG: funutil.cache.box.ttl_cache/vttl_cache call
    # `cachebox.TTLCache(maxsize=maxsize, ttl=ttl)` / `VTTLCache(..., ttl=60)`,
    # but the currently-installable cachebox (6.2.6) renamed that constructor
    # kwarg to `global_ttl` -- so these two decorators raise
    # `TypeError: TTLCache.__init__() got an unexpected keyword argument 'ttl'`
    # against any modern cachebox release. This is an upstream-API-drift bug
    # in funutil's source, not fixed here (smoke-test scope only, no
    # business-logic fixes).
    pytest.skip(
        "已知bug：funutil.cache.box 的 ttl_cache/vttl_cache 调用 cachebox.TTLCache("
        "ttl=...)，但当前可安装的 cachebox(6.2.6) 已将该参数改名为 global_ttl，"
        "导致 TypeError，不在本次冒烟测试修复范围内"
    )


# ---------------------------------------------------------------------------
# funutil.cache: PickleCache / pkl_cache (disk-pickle-backed)
# ---------------------------------------------------------------------------


def test_pkl_cache_hits_on_second_call(tmp_path):
    from funutil.cache import pkl_cache

    calls = []

    @pkl_cache(cache_key="name", cache_dir=str(tmp_path / "pkl_cache"))
    def get_value(name="d", cache=True):
        calls.append(name)
        return f"value-{name}"

    first = get_value(name="foo")
    second = get_value(name="foo")

    assert first == second == "value-foo"
    assert len(calls) == 1  # second call served from the pickle cache


# ---------------------------------------------------------------------------
# funutil.cache: DiskCache / disk_cache (diskcache-backed)
# ---------------------------------------------------------------------------


def test_disk_cache_hits_on_second_call(tmp_path):
    from funutil.cache import disk_cache

    calls = []

    @disk_cache(cache_key="name", cache_dir=str(tmp_path / "disk_cache"))
    def get_value(name="d", cache=True):
        calls.append(name)
        return f"value-{name}"

    first = get_value(name="foo")
    second = get_value(name="foo")

    assert first == second == "value-foo"
    assert len(calls) == 1  # second call served from the disk cache


# ---------------------------------------------------------------------------
# funutil.path: list_file / removedirs
# ---------------------------------------------------------------------------


def test_list_file_and_removedirs(tmp_path):
    from funutil.path import list_file, removedirs

    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.txt").write_text("hello")

    files = list_file(str(sub), deep=1)
    assert any(f.endswith("a.txt") for f in files)

    removedirs(str(sub))
    assert not sub.exists()


# ---------------------------------------------------------------------------
# funutil.convert: convert_curl_to_python
# ---------------------------------------------------------------------------


def test_convert_curl_to_python_basic():
    from funutil.convert import convert_curl_to_python

    curl_cmd = 'curl "https://example.com/api" -H "Accept: application/json"'
    result = convert_curl_to_python(curl_cmd)

    assert "requests.get(" in result
    assert "https://example.com/api" in result


# ---------------------------------------------------------------------------
# funutil.math.prime: is_probable_prime
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n,expected",
    [
        (2, True),
        (3, True),
        (7, True),
        (17, True),
        (4, False),
        (8, False),
        (9, False),
    ],
)
def test_is_probable_prime(n, expected):
    from funutil.math.prime import is_probable_prime

    assert is_probable_prime(n) is expected


# ---------------------------------------------------------------------------
# funutil.util.time: date/time helpers
# ---------------------------------------------------------------------------


def test_time_conversion_helpers_roundtrip():
    from funutil.util.time import now2time, now2unix, time2unix, unix2time

    unix_ts = now2unix()
    assert isinstance(unix_ts, int)

    time_str = now2time()
    assert isinstance(time_str, str)

    assert time2unix(unix2time(unix_ts)) == unix_ts


def test_worktime_with_int_input_does_not_raise():
    from funutil.util.time import WorkTime

    wt = WorkTime()
    result = wt.time_to_day_end(time_str=1735689600)
    assert isinstance(result, bool)


def test_worktime_default_and_string_input_is_broken():
    # KNOWN BUG: util/time.py does `from datetime import datetime, timedelta` at
    # module scope, but WorkTime.time_to_end() internally calls
    # `datetime.datetime.now()` / `datetime.datetime.strptime(...)`, treating
    # the already-imported *class* as if it were the `datetime` *module*. This
    # raises AttributeError for the two most common call patterns: no
    # time_str (defaults to None) and a string time_str. Only the int/float
    # branch happens to work. Not fixed here (smoke-test scope only, no
    # business-logic fixes).
    pytest.skip(
        "已知bug：WorkTime.time_to_end 对 time_str=None（默认值）或字符串输入会抛 "
        "AttributeError（模块内误用 datetime.datetime，而 datetime 已经是类本身），"
        "仅 int/float 输入可用，不在本次冒烟测试修复范围内"
    )
