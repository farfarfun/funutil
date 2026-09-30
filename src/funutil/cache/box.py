"""兼容旧导入路径的内存缓存 API。"""

from farcache.box import (
    cache,
    fifo_cache,
    lfu_cache,
    lru_cache,
    rr_cache,
    ttl_cache,
    vttl_cache,
)

__all__ = [
    "cache",
    "fifo_cache",
    "lfu_cache",
    "lru_cache",
    "rr_cache",
    "ttl_cache",
    "vttl_cache",
]
