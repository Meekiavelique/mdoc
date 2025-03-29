import urllib.parse
from datetime import datetime

def register_filters(app):
    @app.template_filter('urlencode')
    def urlencode_filter(s):
        return urllib.parse.quote(s.encode('utf-8') if isinstance(s, str) else s)
        
    @app.template_filter('now')
    def _jinja2_filter_now(format_string="%Y-%m-%d"):
        return datetime.now().strftime(format_string)