from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import urllib.parse

class IframePreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_iframe_block = False
        iframe_config = {}
        counter = 0
        
        for line in lines:
            if line.strip() == '```iframe':
                in_iframe_block = True
                iframe_config = {}
                continue
            elif in_iframe_block and line.strip() == '```':
                in_iframe_block = False
                
                placeholder = self._create_iframe_embed(iframe_config, counter)
                new_lines.append(placeholder)
                counter += 1
                continue
            elif in_iframe_block:
                self._parse_config_line(line, iframe_config)
                continue
            
            iframe_match = re.match(r'^!\[iframe\]\(([^)]+)\)(?:\{([^}]+)\})?', line.strip())
            if iframe_match:
                url = iframe_match.group(1)
                options = iframe_match.group(2) or ""
                
                config = {'url': url}
                if options:
                    for option in options.split(','):
                        if '=' in option:
                            key, value = option.strip().split('=', 1)
                            config[key] = value
                        else:
                            config[option.strip()] = True
                
                placeholder = self._create_iframe_embed(config, counter)
                new_lines.append(placeholder)
                counter += 1
                continue
            
            new_lines.append(line)
                
        return new_lines
    
    def _parse_config_line(self, line, config):
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
        elif line:
            config[line] = True
    
    def _create_iframe_embed(self, config, counter):
        url = config.get('url', '')
        width = config.get('width', '100%')
        height = config.get('height', '400')
        title = config.get('title', 'Embedded Content')
        
        if not url:
            return f'<div class="iframe-error">Error: No URL provided</div>'
        
        iframe_id = f"iframe-{counter}"
        
        sandbox_attrs = []
        if 'allow-scripts' in config:
            sandbox_attrs.append('allow-scripts')
        if 'allow-forms' in config:
            sandbox_attrs.append('allow-forms')
        if 'allow-same-origin' in config:
            sandbox_attrs.append('allow-same-origin')
        if 'allow-popups' in config:
            sandbox_attrs.append('allow-popups')
        
        sandbox = f'sandbox="{" ".join(sandbox_attrs)}"' if sandbox_attrs else ''
        
        allow_attrs = []
        if 'fullscreen' in config:
            allow_attrs.append('fullscreen')
        if 'camera' in config:
            allow_attrs.append('camera')
        if 'microphone' in config:
            allow_attrs.append('microphone')
        if 'geolocation' in config:
            allow_attrs.append('geolocation')
        
        allow = f'allow="{"; ".join(allow_attrs)}"' if allow_attrs else ''
        
        return f'''
<div class="mdoc-iframe" id="{iframe_id}">
    <div class="component-header">
        <span>{title}</span>
        <a href="{url}" target="_blank" class="iframe-external-link">↗</a>
    </div>
    <div class="component-body">
        <iframe src="{url}" 
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                {sandbox}
                {allow}
                loading="lazy">
        </iframe>
    </div>
</div>
'''

class IframeExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(IframePreprocessor(md), 'iframe', 171)

def makeExtension(**kwargs):
    return IframeExtension(**kwargs)