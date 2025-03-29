from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import base64

class GeoGebraPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_geogebra_block = False
        config_lines = []
        counter = 0
        
        for line in lines:
            if line.strip() == '```geogebra':
                in_geogebra_block = True
                config_lines = []
                continue
            elif in_geogebra_block and line.strip() == '```':
                in_geogebra_block = False
                
                config_str = '\n'.join(config_lines)
                safe_config = base64.b64encode(config_str.encode('utf-8')).decode('ascii')
                
                placeholder = (
                    f'<div class="mdoc-geogebra" id="geogebra-container-{counter}" '
                    f'data-geogebra-config="{safe_config}"></div>'
                )
                new_lines.append(placeholder)
                counter += 1
                continue
            
            if in_geogebra_block:
                config_lines.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

class GeoGebraExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(GeoGebraPreprocessor(md), 'geogebra', 174)

def makeExtension(**kwargs):
    return GeoGebraExtension(**kwargs)