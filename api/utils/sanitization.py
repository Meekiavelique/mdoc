import re
import functools
import os
import logging

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=128)
def sanitize_filename(filename):
    if not filename:
        return ""
    
    filename = filename.replace('\x00', '')
    
    parts = filename.split('/')
    sanitized_parts = []
    
    for part in parts:
        if not part:
            continue
            
        sanitized = re.sub(r'[<>:"|?*\\]', '', part)
        
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        sanitized = sanitized.strip('. \t\n\r')
        
        if sanitized in ('', '.', '..'):
            continue
            
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
            
        if sanitized:
            sanitized_parts.append(sanitized)
    
    result = '/'.join(sanitized_parts)
    
    result = result.replace('..', '')
    
    if len(result) > 1000:
        result = result[:1000]
    
    logger.debug(f"Sanitized filename: '{filename}' -> '{result}'")
    return result

def is_safe_path(path, base_dir):
    try:
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(path)
        
        common_path = os.path.commonpath([abs_base, abs_path])
        is_safe = common_path == abs_base
        
        if not is_safe:
            logger.warning(f"Unsafe path detected: {path} (resolved to {abs_path}) is outside base {abs_base}")
        
        return is_safe
        
    except (ValueError, OSError) as e:
        logger.error(f"Error checking path safety for {path}: {e}")
        return False

def sanitize_url_path(url_path):
    if not url_path:
        return ""
    
    url_path = url_path.strip('/')
    
    components = url_path.split('/')
    sanitized_components = []
    
    for component in components:
        if not component:
            continue
            
        try:
            import urllib.parse
            component = urllib.parse.unquote(component)
        except Exception:
            pass
        
        sanitized = re.sub(r'[<>"|?*\\]', '', component)
        
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        sanitized = sanitized.strip()
        
        if sanitized and sanitized not in ('.', '..'):
            sanitized_components.append(sanitized)
    
    result = '/'.join(sanitized_components)
    logger.debug(f"Sanitized URL path: '{url_path}' -> '{result}'")
    return result

def validate_document_name(doc_name):
    if not doc_name:
        return False, "Document name cannot be empty"
    
    if len(doc_name) > 500:
        return False, "Document name too long"
    
    dangerous_patterns = [
        r'\.\./',
        r'\.\.',
        r'[<>:"|?*]',
        r'[\x00-\x1f\x7f-\x9f]',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, doc_name):
            return False, f"Document name contains invalid characters or patterns"
    
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    parts = doc_name.split('/')
    for part in parts:
        if part.upper() in reserved_names:
            return False, f"Document name contains reserved name: {part}"
    
    return True, "Valid document name"

def normalize_document_path(doc_path):
    if not doc_path:
        return ""
    
    doc_path = doc_path.strip('/')
    
    doc_path = doc_path.replace('\\', '/')
    
    doc_path = re.sub(r'/+', '/', doc_path)
    
    components = []
    for component in doc_path.split('/'):
        if component and component not in ('.', '..'):
            component = re.sub(r'\s+', '_', component.strip())
            components.append(component)
    
    result = '/'.join(components)
    logger.debug(f"Normalized document path: '{doc_path}' -> '{result}'")
    return result