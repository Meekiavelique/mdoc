from flask import Flask, render_template, abort, request, send_from_directory, Response
from markupsafe import Markup
import os
import sys
import re
from pathlib import Path
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
import bleach
from datetime import datetime
import functools

app = Flask(__name__)

ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'strong', 
                'em', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'br', 'span', 'img', 'div',
                'script', 'del']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'id', 'name', 'class'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'span': ['class', 'id'],
    'code': ['class'],
    'div': ['class', 'id'],
    'script': ['type', 'src'],
    'h1': ['id', 'class'],
    'h2': ['id', 'class'],
    'h3': ['id', 'class'],
    'h4': ['id', 'class'],
    'h5': ['id', 'class'],
    'h6': ['id', 'class'],
    'table': ['class'],
    'thead': ['class'],
    'tbody': ['class'],
    'tr': ['class'],
    'th': ['class', 'scope'],
    'td': ['class'],
    'ul': ['class'],
    'ol': ['class'],
    'li': ['class'],
    'p': ['class'],
    'pre': ['class'],
    'blockquote': ['class']
}

MARKDOWN_EXTENSIONS = [
    TableExtension(),
    FencedCodeExtension(),
    CodeHiliteExtension(linenums=False, css_class="codehilite", guess_lang=False),
    'toc',
    'md_in_html'
]

def sanitize_filename(filename):
    return re.sub(r'[^\w\-.]', '', filename)

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        templates = []
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        if os.path.exists(template_dir):
            for f in os.listdir(template_dir):
                if f.endswith('.html') and f not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                    templates.append(f.replace('.html', ''))
                elif f.endswith('.md'):
                    templates.append(f.replace('.md', ''))
        return sorted(templates)
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        return []

def process_math_expressions(md_content):
    math_placeholders = {}
    display_math_count = 0
    inline_math_count = 0

    display_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)

    def replace_display_math(match):
        nonlocal display_math_count
        placeholder = f'DISPLAY_MATH_PLACEHOLDER_{display_math_count}'
        math_placeholders[placeholder] = f'$${match.group(1)}$$'
        display_math_count += 1
        return placeholder

    md_content = display_pattern.sub(replace_display_math, md_content)

    inline_pattern = re.compile(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', re.DOTALL)

    def replace_inline_math(match):
        nonlocal inline_math_count
        placeholder = f'INLINE_MATH_PLACEHOLDER_{inline_math_count}'
        math_placeholders[placeholder] = f'${match.group(1)}$'
        inline_math_count += 1
        return placeholder

    md_content = inline_pattern.sub(replace_inline_math, md_content)

    return md_content, math_placeholders

def convert_markdown_to_html(md_content):
    md_content, math_placeholders = process_math_expressions(md_content)

    html_content = markdown.markdown(
        md_content,
        extensions=MARKDOWN_EXTENSIONS,
        output_format='html5'
    )

    for placeholder, math in math_placeholders.items():
        html_content = html_content.replace(placeholder, math)

    safe_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={'img': ['data', 'http', 'https']},
        strip=False
    )

    return safe_html

@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    response = send_from_directory(static_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=86400'  
    return response

@app.route('/<template_name>')
def serve_template(template_name):
    template_name = sanitize_filename(template_name)

    html_path = f"{template_name}.html"
    md_path = f"{template_name}.md"
    
    try:
        is_print = request.args.get('print') == '1'

        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        html_full_path = os.path.join(templates_dir, html_path)
        md_full_path = os.path.join(templates_dir, md_path)

        if os.path.exists(html_full_path):
            return render_template(html_path)
        elif os.path.exists(md_full_path):
            with open(md_full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            safe_html = convert_markdown_to_html(md_content)
            git_history = []  
            template = 'print.html' if is_print else 'markdown_base.html'

            response = render_template(
                template, 
                content=Markup(safe_html), 
                title=template_name.capitalize(),
                versions=git_history,
                is_print=is_print
            )

            if not is_print:
                response = Response(response)
                response.headers['Cache-Control'] = 'public, max-age=300'
            return response
        else:
            abort(404)
    except Exception as e:
        print(f"Error serving template {template_name}: {str(e)}")
        abort(500)

@app.route('/version/<template_name>/<commit_hash>')
def view_version(template_name, commit_hash):
    return serve_template(template_name)

@app.route('/')
def index():
    try:
        templates = get_all_documents()
        return render_template('index.html', templates=templates)
    except Exception as e:
        print(f"Error in index: {str(e)}")
        return render_template('error.html', error_code="500", error_message=f"Internal Server Error: {str(e)}"), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code="404", error_message="Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code="500", error_message="Internal Server Error"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code="403", error_message="Forbidden"), 403

@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', error_code="400", error_message="Bad Request"), 400

@app.errorhandler(Exception)
def handle_exception(e):
    code = getattr(e, 'code', 500)
    message = getattr(e, 'description', "Something went wrong")
    return render_template('error.html', error_code=code, error_message=message), code

@app.template_filter('now')
def _jinja2_filter_now(format_string="%Y-%m-%d"):
    return datetime.now().strftime(format_string)