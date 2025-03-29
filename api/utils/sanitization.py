import re
import functools

@functools.lru_cache(maxsize=32)
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)