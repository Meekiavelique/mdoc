from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import base64

class MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_mermaid_block = False
        mermaid_lines = []
        counter = 0
        simple_display = False
        
        for line in lines:
            if line.strip() == '```mermaid simple':
                in_mermaid_block = True
                mermaid_lines = []
                simple_display = True
                continue
            elif line.strip() == '```mermaid':
                in_mermaid_block = True
                mermaid_lines = []
                simple_display = False
                continue
            elif in_mermaid_block and line.strip() == '```':
                in_mermaid_block = False
                
                diagram_definition = '\n'.join(mermaid_lines)
                safe_diagram = base64.b64encode(diagram_definition.encode('utf-8')).decode('ascii')
                
                if simple_display:
                    placeholder = (
                        f'<div class="mdoc-mermaid" id="mermaid-diagram-{counter}" '
                        f'data-diagram="{safe_diagram}" data-simple-display="true"></div>'
                    )
                else:
                    placeholder = (
                        f'<div class="mdoc-mermaid" id="mermaid-diagram-{counter}" '
                        f'data-diagram="{safe_diagram}"></div>'
                    )
                new_lines.append(placeholder)
                counter += 1
                continue
            
            if in_mermaid_block:
                mermaid_lines.append(line)
            else:
                new_lines.append(line)
                
        return new_lines

class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MermaidPreprocessor(md), 'mermaid', 176)

def makeExtension(**kwargs):
    return MermaidExtension(**kwargs)