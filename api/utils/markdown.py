import markdown
import re
import bleach
from api.extensions.glsl import GlslExtension
from api.extensions.desmos import DesmosExtension
from api.extensions.mermaid import MermaidExtension
from api.extensions.geogebra import GeoGebraExtension
from api.extensions.p5js import P5jsExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'strong', 
                'em', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'br', 'span', 'img', 'div',
                'script', 'del', 'canvas', 'select', 'option', 'label', 'input', 'button']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'id', 'name', 'class', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    **dict.fromkeys(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'ul', 'ol', 'li', 'pre', 'blockquote', 'code', 'table', 'thead', 'tbody', 'tr', 'td'], ['class', 'id']),
    'script': ['type', 'src'],
    'th': ['class', 'scope'],
    'div': ['class', 'id', 'data-fragment-shader', 'data-simple-display', 'data-no-ui', 'data-width', 'data-height', 'data-graph-config', 'data-diagram', 'data-geogebra-config', 'data-sketch-code', 'style'],
    'canvas': ['width', 'height', 'class', 'id'],
    'select': ['class', 'id'],
    'option': ['value', 'selected'],
    'input': ['type', 'min', 'max', 'step', 'value', 'class', 'id'],
    'button': ['class', 'id', 'type']
}

ALLOWED_PROTOCOLS = {
    'a': ['http', 'https', 'mailto', 'tel'],
    'img': ['data', 'http', 'https']
}

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

def convert_markdown_to_html(md_content):
    html_content = markdown.markdown(
        md_content,
        extensions=MARKDOWN_EXTENSIONS,
        output_format='html5'
    )

    html_content = re.sub(
        r'<a\s+href="(https?://[^"]+)"([^>]*)>([^<]+)</a>',
        r'<a href="\1" class="external-link-button" target="_blank" rel="noopener noreferrer"\2>\3</a>',
        html_content
    )

    custom_attributes = ALLOWED_ATTRIBUTES.copy()

    if 'a' not in custom_attributes:
        custom_attributes['a'] = ['href', 'title', 'class', 'id', 'target', 'rel']
    elif 'href' not in custom_attributes['a']:
        custom_attributes['a'].append('href')

    if 'div' in custom_attributes:
        for attr in ['data-fragment-shader', 'data-simple-display', 'data-no-ui', 'data-width', 'data-height', 
                    'data-graph-config', 'data-diagram', 'data-geogebra-config', 'data-sketch-code']:
            if attr not in custom_attributes['div']:
                custom_attributes['div'].append(attr)

    safe_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=custom_attributes,
        protocols=ALLOWED_PROTOCOLS,
        strip=False,
        strip_comments=False
    )

    return safe_html

def remove_first_h1(html_content):
    h1_pattern = re.compile(r'<h1[^>]*>.*?</h1>', re.DOTALL)
    match = h1_pattern.search(html_content)
    if match:
        return html_content.replace(match.group(0), '', 1)
    return html_content