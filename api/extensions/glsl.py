from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import base64

class GlslPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_glsl_block = False
        glsl_code = []
        canvas_count = 0
        simple_display = False
        no_ui = False
        width = None
        height = None
        
        for line in lines:

            if line.strip() == '```glsl simple' or re.match(r'```glsl\s+simple\s*.*', line.strip()):
                in_glsl_block = True
                glsl_code = []
                simple_display = True
                no_ui = False
                

                match = re.match(r'```glsl\s+simple\s+(\d+)x(\d+)', line.strip())
                if match:
                    width, height = match.groups()
                continue
            elif line.strip() == '```glsl noui' or re.match(r'```glsl\s+noui\s*.*', line.strip()):
                in_glsl_block = True
                glsl_code = []
                simple_display = False
                no_ui = True
                

                match = re.match(r'```glsl\s+noui\s+(\d+)x(\d+)', line.strip())
                if match:
                    width, height = match.groups()
                continue
            elif line.strip() == '```glsl':
                in_glsl_block = True
                glsl_code = []
                simple_display = False
                no_ui = False
                continue
            elif in_glsl_block and line.strip() == '```':
                in_glsl_block = False
                

                if glsl_code is None:
                    glsl_code = []
                    
                shader_content = '\n'.join(glsl_code)
                safe_code = base64.b64encode(shader_content.encode('utf-8')).decode('ascii')
                
                if simple_display:
                    placeholder = (
                        f'<div class="mdoc-glsl-canvas" id="glsl-container-{canvas_count}" '
                        f'data-fragment-shader="{safe_code}" data-simple-display="true"'
                    )
                    if width and height:
                        placeholder += f' data-width="{width}" data-height="{height}"'
                    placeholder += '></div>'
                elif no_ui:
                    placeholder = (
                        f'<div class="mdoc-glsl-canvas" id="glsl-container-{canvas_count}" '
                        f'data-fragment-shader="{safe_code}" data-no-ui="true"'
                    )
                    if width and height:
                        placeholder += f' data-width="{width}" data-height="{height}"'
                    placeholder += '></div>'
                else:
                    placeholder = (
                        f'<div class="mdoc-glsl-canvas" id="glsl-container-{canvas_count}" '
                        f'data-fragment-shader="{safe_code}"></div>'
                    )
                new_lines.append(placeholder)
                canvas_count += 1
                
                width = None
                height = None
                continue
            
            if in_glsl_block:
                glsl_code.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

class GlslExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(GlslPreprocessor(md), 'glsl', 175)

def makeExtension(**kwargs):
    return GlslExtension(**kwargs)