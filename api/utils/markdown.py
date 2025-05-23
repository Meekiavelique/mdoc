import markdown
import re
import bleach
from api.extensions.glsl import GlslExtension
from api.extensions.desmos import DesmosExtension
from api.extensions.mermaid import MermaidExtension
from api.extensions.geogebra import GeoGebraExtension
from api.extensions.p5js import P5jsExtension
from api.utils.cross_reference import process_cross_references
from api.utils.table_of_contents import generate_table_of_contents, add_ids_to_headings
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'strong', 
                'em', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'br', 'span', 'img', 'div',
                'del', 'canvas', 'select', 'option', 'label', 'input', 'button']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'id', 'name', 'class', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    **dict.fromkeys(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'ul', 'ol', 'li', 'pre', 'blockquote', 'code', 'table', 'thead', 'tbody', 'tr', 'td'], ['class', 'id']),
    'th': ['class', 'scope'],
    'div': ['class', 'id', 'data-fragment-shader', 'data-simple-display', 'data-no-ui', 'data-width', 'data-height', 'data-graph-config', 'data-diagram', 'data-geogebra-config', 'data-sketch-code'],
    'canvas': ['width', 'height', 'class', 'id'],
    'select': ['class', 'id'],
    'option': ['value', 'selected'],
    'input': ['type', 'min', 'max', 'step', 'value', 'class', 'id'],
    'button': ['class', 'id', 'type']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'tel', 'ftp', '#']

MARKDOWN_EXTENSIONS = [
    TableExtension(),
    FencedCodeExtension(),
    CodeHiliteExtension(linenums=False, css_class="codehilite", guess_lang=False),
    GlslExtension(),
    DesmosExtension(),
    MermaidExtension(),
    GeoGebraExtension(),
    P5jsExtension(),
    'toc',
    'md_in_html'
]

def extract_title_from_markdown(md_content):
    if not md_content:
        return None

    lines = md_content.strip().split('\n')
    if lines and lines[0].startswith('# '):
        return lines[0][2:].strip()
    return None

def extract_description_from_markdown(md_content):
    if not md_content:
        return ""
    
    lines = md_content.strip().split('\n')
    description = ""
    
    for line in lines[1:]:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('```'):
            description = line[:200]
            break
    
    return description

def convert_markdown_to_html(md_content):
    try:
        md_content = process_cross_references(md_content)
        
        html_content = markdown.markdown(
            md_content,
            extensions=MARKDOWN_EXTENSIONS,
            output_format='html5'
        )
        
        html_content = add_ids_to_headings(html_content)
        
        def enhance_external_link(match):
            href = match.group(1)
            rest_of_tag = match.group(2)
            content = match.group(3)
            
            if href.startswith(('http://', 'https://')):
                if 'target=' not in rest_of_tag:
                    rest_of_tag += ' target="_blank"'
                if 'rel=' not in rest_of_tag:
                    rest_of_tag += ' rel="noopener noreferrer"'
                if 'class=' not in rest_of_tag:
                    rest_of_tag += ' class="external-link-button"'
            
            return f'<a href="{href}"{rest_of_tag}>{content}</a>'
        
        link_pattern = r'<a href="([^"]*)"([^>]*)>(.*?)</a>'
        html_content = re.sub(link_pattern, enhance_external_link, html_content, flags=re.DOTALL)
        
        safe_html = bleach.clean(
            html_content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=False,
            strip_comments=False
        )
        
        return safe_html

    except Exception as e:
        print(f"Error converting Markdown to HTML: {str(e)}")
        return f"<p>Error processing content: {str(e)}</p>"

def remove_first_h1(html_content):
    h1_pattern = re.compile(r'<h1[^>]*>.*?</h1>', re.DOTALL)
    match = h1_pattern.search(html_content)
    if match:
        return html_content.replace(match.group(0), '', 1)
    return html_content