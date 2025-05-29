import re
import functools
import os

@functools.lru_cache(maxsize=32)
def sanitize_filename(filename):

    if not filename:
        return ""
    

    parts = filename.split('/')
    sanitized_parts = []
    
    for part in parts:

        sanitized = re.sub(r'[<>:"|?*\\]', '', part)
        sanitized = sanitized.strip('. ')
        if sanitized:  
            sanitized_parts.append(sanitized)
    

    result = '/'.join(sanitized_parts)

    result = result.replace('..', '')
    
    return result

def is_safe_path(path, base_dir):

    try:
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, path))
        return abs_path.startswith(abs_base)
    except:
        return False