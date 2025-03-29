from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import base64

class P5jsPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_p5js_block = False
        p5js_code = []
        sketch_count = 0
        
        for line in lines:
            if line.strip() == '```p5js':
                in_p5js_block = True
                p5js_code = []
                continue
            elif in_p5js_block and line.strip() == '```':
                in_p5js_block = False
                
                sketch_content = '\n'.join(p5js_code)
                safe_code = base64.b64encode(sketch_content.encode('utf-8')).decode('ascii')
                
                placeholder = (
                    f'<div class="mdoc-p5js-sketch" id="p5js-container-{sketch_count}" '
                    f'data-sketch-code="{safe_code}"></div>'
                )
                new_lines.append(placeholder)
                sketch_count += 1
                continue
            
            if in_p5js_block:
                p5js_code.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

class P5jsExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(P5jsPreprocessor(md), 'p5js', 173)

def makeExtension(**kwargs):
    return P5jsExtension(**kwargs)