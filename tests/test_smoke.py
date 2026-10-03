"""Lightweight smoke tests for funutil.

funutil is a small general-purpose utility library (logging helper, decorators,
caches, misc helpers). These tests are not exhaustive unit tests; they exist to
catch import breakage and gross regressions in the public API surface. Any real
network/filesystem/cloud calls are avoided or isolated to tmp_path.
"""

import ast
import importlib.metadata
import subprocess
import sys

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


def test_deep_get_list_indices_and_boundaries():
    from funutil import deep_get

    data = {"users": [{"name": "first"}, {"name": "last"}]}
    assert deep_get(data, "users", 0, "name") == "first"
    assert deep_get(data, "users", -1, "name") == "last"
    assert deep_get(data, "users", 2) is None
    assert deep_get(data, "users", -3) is None


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


def test_importing_log_module_has_no_filesystem_side_effect(tmp_path):
    subprocess.run(
        [sys.executable, "-c", "import funutil.util.log"], cwd=tmp_path, check=True
    )
    assert list(tmp_path.iterdir()) == []


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


def test_run_timer_context_manager_does_not_swallow_errors():
    from funutil import RunTimer

    with pytest.raises(ValueError, match="boom"), RunTimer(dump_file=None):
        raise ValueError("boom")


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
            raise OSError("transient failure")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 3


def test_retry_raises_after_exhausting_attempts():
    from funutil.util.retrying import retry

    @retry(retry_cnt=2, sleep_after_retry=0, throw_error_after_retry=True)
    def always_fails():
        raise OSError("permanent failure")

    with pytest.raises(OSError, match="permanent failure"):
        always_fails()


def test_retry_only_catches_configured_exceptions():
    from funutil.util.retrying import retry

    attempts = {"n": 0}

    @retry(retry_cnt=3, retry_exceptions=(OSError,))
    def invalid_input():
        attempts["n"] += 1
        raise ValueError("invalid input")

    with pytest.raises(ValueError, match="invalid input"):
        invalid_input()
    assert attempts["n"] == 1


def test_retry_never_swallows_last_error():
    from funutil.util.retrying import retry

    @retry(retry_cnt=2, throw_error_after_retry=False)
    def unavailable():
        raise OSError("unavailable")

    with pytest.raises(OSError, match="unavailable"):
        unavailable()


def test_retry_warns_when_deprecated_param_passed_explicitly():
    from funutil.util.retrying import retry

    with pytest.warns(DeprecationWarning, match="throw_error_after_retry"):
        retry(retry_cnt=1, throw_error_after_retry=False)

    with pytest.warns(DeprecationWarning, match="throw_error_after_retry"):
        retry(retry_cnt=1, throw_error_after_retry=True)


def test_retry_omitting_deprecated_param_does_not_warn():
    import warnings

    from funutil.util.retrying import retry

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        retry(retry_cnt=1)


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
    from funutil.cache import ttl_cache

    calls = []

    @ttl_cache(maxsize=10, ttl=60)
    def add(a, b):
        calls.append((a, b))
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert len(calls) == 1


@pytest.mark.parametrize(
    "decorator_name",
    ["cache", "fifo_cache", "lfu_cache", "lru_cache", "rr_cache", "ttl_cache", "vttl_cache"],
)
def test_public_memory_cache_decorators_cache_results(decorator_name):
    import funutil.cache as cache_module

    calls = []
    decorator = getattr(cache_module, decorator_name)

    def value(key):
        calls.append(key)
        return key

    cached_value = decorator(value) if decorator_name == "cache" else decorator(maxsize=2)(value)
    assert cached_value("key") == cached_value("key") == "key"
    assert calls == ["key"]


def test_legacy_cachetools_module_forwards_to_farcache():
    from funutil.cache.tools import lru_cache

    assert lru_cache.__module__ == "farcache.box"


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


def test_legacy_util_path_keeps_metadata_results(tmp_path, monkeypatch):
    from funutil.util.path import join_path, list_file

    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("hello")

    assert join_path("a.txt") == str(tmp_path / "a.txt")
    assert list_file(tmp_path) == [
        {
            "dir": tmp_path,
            "name": "a.txt",
            "path": str(tmp_path / "a.txt"),
            "isdir": False,
            "deep": 1,
        }
    ]


def test_merge_and_split_files(tmp_path):
    from funutil.path.core import merge_file, split_file

    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    merged = tmp_path / "merged.txt"
    first.write_text("a\nb\n")
    second.write_text("c\n")

    merge_file([first, second], merged)
    assert merged.read_text() == "a\nb\n\nc\n\n"

    split_file(merged, str(tmp_path) + "/", max_line=2)
    assert (tmp_path / "merged.txt-split-1.csv").read_text() == "a\nb\n"
    assert (tmp_path / "merged.txt-split-2.csv").read_text() == "\nc\n"


# ---------------------------------------------------------------------------
# funutil.convert: convert_curl_to_python
# ---------------------------------------------------------------------------


def test_convert_curl_to_python_basic():
    from funutil.convert import convert_curl_to_python

    curl_cmd = 'curl "https://example.com/api" -H "Accept: application/json"'
    result = convert_curl_to_python(curl_cmd)

    assert "requests.get(" in result
    assert "https://example.com/api" in result


def test_convert_curl_to_python_escapes_quotes_in_literals():
    """data/url 中的引号与反斜杠必须被转义为合法 Python 字面量，不能破坏生成代码。"""
    from funutil.convert import convert_curl_to_python

    curl_cmd = (
        'curl "https://example.com/api" -X POST '
        '-d "name=O\'Brien \\"hi\\"" '
        '-H "Content-Type: application/json"'
    )
    result = convert_curl_to_python(curl_cmd)

    # 生成的代码必须是合法 Python，能被编译（即便不执行）
    compile(result, "<generated>", "exec")
    # data 字面量经 repr() 转义后能还原出原始值，而不是被引号截断/破坏语法
    data_line = next(line for line in result.splitlines() if "data=" in line)
    data_literal = data_line.strip().removeprefix("data=").rstrip(",")
    assert ast.literal_eval(data_literal) == 'name=O\'Brien "hi"'


def test_convert_curl_to_python_rejects_unknown_method():
    """`-X` 指定的方法必须落在白名单内，否则不能拼进可执行代码字符串。"""
    from funutil.convert import convert_curl_to_python

    curl_cmd = 'curl "https://example.com" -X "get); import os; os.system(\'x\'); ("'
    with pytest.raises(ValueError, match="不支持的 HTTP 方法"):
        convert_curl_to_python(curl_cmd)


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
        (1, False),
        (0, False),
        (-1, False),
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


def test_worktime_default_string_and_cycle_boundary():
    from funutil.util.time import WorkTime

    wt = WorkTime()
    assert isinstance(wt.time_to_day_end(), bool)
    assert isinstance(wt.time_to_day_end("2025-01-01 00:00:00"), bool)
    assert wt.time_to_end(55, circle_time=60, threshold_time=10) is True
    assert wt.time_to_end(50, circle_time=60, threshold_time=10) is False


def test_date_ranges_have_inclusive_boundaries():
    from datetime import timedelta

    from funutil.util.time import day_during, month_during, week_during

    day_first, day_last = day_during(0)
    week_first, week_last = week_during(0)
    offset, month_first, month_last = month_during(0)

    assert day_last - day_first == timedelta(days=1, seconds=-1)
    assert week_last - week_first == timedelta(weeks=1, seconds=-1)
    assert month_last + timedelta(seconds=1) > month_first
    assert offset == 0


def test_repeating_timer_runs_until_cancelled():
    from threading import Event

    from funutil.time import RepeatingTimer

    called = Event()
    timer = RepeatingTimer(0.01, called.set)
    timer.start()
    try:
        assert called.wait(1)
    finally:
        timer.cancel()
        timer.join(timeout=1)
    assert not timer.is_alive()
