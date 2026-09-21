"""Lightweight smoke tests for funutil.

funutil is a small general-purpose utility library (logging helper, decorators,
caches, misc helpers). These tests are not exhaustive unit tests; they exist to
catch import breakage and gross regressions in the public API surface. Any real
network/filesystem/cloud calls are avoided or isolated to tmp_path.
"""

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
            raise ValueError("transient failure")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 3


def test_retry_raises_after_exhausting_attempts():
    from funutil.util.retrying import retry

    @retry(retry_cnt=2, sleep_after_retry=0, throw_error_after_retry=True)
    def always_fails():
        raise ValueError("permanent failure")

    with pytest.raises(ValueError, match="permanent failure"):
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
    from funutil.cache import ttl_cache

    calls = []

    @ttl_cache(maxsize=10, ttl=60)
    def add(a, b):
        calls.append((a, b))
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3
    assert len(calls) == 1


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
