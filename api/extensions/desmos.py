
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import json
import base64

class DesmosPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_desmos_block = False
        desmos_config = []
        counter = 0
        
        for line in lines:
            if line.strip() == '```desmos':
                in_desmos_block = True
                desmos_config = []
                continue
            elif in_desmos_block and line.strip() == '```':
                in_desmos_block = False
                
                config_json = '\n'.join(desmos_config)
                safe_config = base64.b64encode(config_json.encode('utf-8')).decode('ascii')
                
                placeholder = (
                    f'<div class="mdoc-desmos-graph" id="desmos-container-{counter}" '
                    f'data-graph-config="{safe_config}"></div>'
                )
                new_lines.append(placeholder)
                counter += 1
                continue
            
            if in_desmos_block:
                desmos_config.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

class DesmosExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(DesmosPreprocessor(md), 'desmos', 175)

def makeExtension(**kwargs):
    return DesmosExtension(**kwargs)