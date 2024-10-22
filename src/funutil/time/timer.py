import json
import time
from functools import wraps


class CacheDump:

    def __init__(self, elapsed=10, file_path="dump.json"):
        """
        :param elapsed: time to dump the cache
        """
        self.dump_data = {}
        self.file_path = file_path
        self.elapsed = elapsed
        self.last_dump_time = time.time()

    def add(self, key, value):
        self.dump_data[key] = value
        self.dump()

    def dump(self):
        if time.time() - self.last_dump_time < self.elapsed:
            return

        with open(self.file_path, 'w', encoding='utf-8') as out_data:
            out_data.write(json.dumps(self.dump_data, indent=4, sort_keys=True))
        self.last_dump_time = time.time()


class RunTimer:
    cache_dump = CacheDump(elapsed=3)

    def __init__(self, time_func=time.perf_counter, dump=False):
        self.counter = 0
        self.elapsed = 0
        self.dump = dump
        self.time_func = time_func
        self.time_snapshot = None

    def start(self):
        self.time_snapshot = time.time()

    def stop(self):
        self.elapsed += time.time() - self.time_snapshot
        self.time_snapshot = None
        self.counter += 1

    def __str__(self):
        return f'{self.counter}, {self.elapsed / self.counter}s'

    @property
    def running(self) -> bool:
        return self.time_snapshot is not None

    def wrap(self, func, *args, **kwargs):
        self.start()
        res = func(*args, **kwargs)
        self.stop()
        if self.dump:
            key = f"{func.__code__.co_flags}-{func.__name__}"
            value = {
                'counter': self.counter,
                'elapsed': self.elapsed,
                "average": self.elapsed / self.counter,
            }
            self.cache_dump.add(key, value)
        return res

    def __call__(self, func=None, *args, **kwargs):
        if func is not None:
            @wraps(func)
            def wrapper(*args2, **kwargs2):
                self.wrap(func, args2, kwargs2)

            return wrapper

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return True
