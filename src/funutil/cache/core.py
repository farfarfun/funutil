"""兼容旧导入路径的 pickle 缓存 API。"""

from farcache import cache, lru_cache
from farcache.core import PickleCache, cached_property, pkl_cache

__all__ = ["PickleCache", "cache", "cached_property", "lru_cache", "pkl_cache"]
