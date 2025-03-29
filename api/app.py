from flask import Flask, render_template, abort, request, send_from_directory, Response
from markupsafe import Markup
import os
import sys
import re
import urllib.parse
from pathlib import Path
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
import bleach
from datetime import datetime
import functools
import requests

app = Flask(__name__)

ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'strong', 
                'em', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'br', 'span', 'img', 'div',
                'script', 'del']

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'id', 'name', 'class', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    **dict.fromkeys(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'ul', 'ol', 'li', 'pre', 'blockquote', 'code', 'table', 'thead', 'tbody', 'tr', 'td'], ['class', 'id']),
    'script': ['type', 'src'],
    'th': ['class', 'scope']
}

MARKDOWN_EXTENSIONS = [
    TableExtension(),
    FencedCodeExtension(),
    CodeHiliteExtension(linenums=False, css_class="codehilite", guess_lang=False),
    'toc',
    'md_in_html'
]

@app.template_filter('urlencode')
def urlencode_filter(s):
    return urllib.parse.quote(s.encode('utf-8') if isinstance(s, str) else s)

@functools.lru_cache(maxsize=32)
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@functools.lru_cache(maxsize=32)
def get_github_file_history(file_path, repo="Meekiavelique/mdoc"):
    api_url = f"https://api.github.com/repos/{repo}/commits"
    params = {"path": file_path}
    
    headers = {}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        
        commits = response.json()
        history = []
        
        for commit in commits:
            commit_data = {
                "hash": commit["sha"],
                "short_hash": commit["sha"][:7],
                "author": commit["commit"]["author"]["name"],
                "date": datetime.strptime(
                    commit["commit"]["author"]["date"], 
                    "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%Y-%m-%d %H:%M"),
                "message": commit["commit"]["message"].split("\n")[0],
                "url": commit["html_url"]
            }
            history.append(commit_data)
            
        return history
    except Exception as e:
        print(f"Error fetching GitHub history: {str(e)}")
        return []

def get_file_at_commit(file_path, commit_hash, repo="Meekiavelique/mdoc"):
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    params = {"ref": commit_hash}
    
    headers = {"Accept": "application/vnd.github.v3.raw"}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching file at commit: {str(e)}")
        return None

@functools.lru_cache(maxsize=32)
def get_template_history(template_name):
    md_history = get_github_file_history(f"api/templates/docs/{template_name}.md")
    html_history = get_github_file_history(f"api/templates/docs/{template_name}.html")
    
    combined_history = md_history + html_history
    return sorted(
        combined_history, 
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"), 
        reverse=True
    )

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        templates = []
        docs_dir = os.path.join(os.path.dirname(__file__), 'templates', 'docs')
        
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            
        for f in os.listdir(docs_dir):
            if f.endswith('.html') and f not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                filename = f.replace('.html', '')
                templates.append({
                    'filename': filename, 
                    'title': filename.capitalize()
                })
            elif f.endswith('.md'):
                filename = f.replace('.md', '')
                title = filename.capitalize()
                try:
                    with open(os.path.join(docs_dir, f), 'r', encoding='utf-8') as file:
                        first_line = file.readline().strip()
                        if first_line.startswith('# '):
                            title = first_line[2:].strip()
                except Exception:
                    pass
                templates.append({
                    'filename': filename, 
                    'title': title
                })
        return sorted(templates, key=lambda x: x['title'])
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        return []

def extract_title_from_markdown(md_content):
    if not md_content:
        return None
    
    lines = md_content.strip().split('\n')
    if lines and lines[0].startswith('# '):
        return lines[0][2:].strip()
    return None

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
        protocols={
            'a': ['http', 'https', 'mailto', 'tel'],
            'img': ['data', 'http', 'https']
        },
        strip=False
    )

    return safe_html

def remove_first_h1(html_content):
    h1_pattern = re.compile(r'<h1[^>]*>.*?</h1>', re.DOTALL)
    match = h1_pattern.search(html_content)
    if match:
        return html_content.replace(match.group(0), '', 1)
    return html_content

@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    response = send_from_directory(static_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=86400'  
    return response

@app.route('/<path:template_name>')
def serve_template(template_name):
    template_name = urllib.parse.unquote(template_name)
    template_name = sanitize_filename(template_name)

    html_path = f"{template_name}.html"
    md_path = f"{template_name}.md"
    
    try:
        is_print = request.args.get('print') == '1'
        is_version = False

        docs_dir = os.path.join(os.path.dirname(__file__), 'templates', 'docs')
        
        html_full_path = os.path.join(docs_dir, html_path)
        md_full_path = os.path.join(docs_dir, md_path)

        git_history = get_template_history(template_name)

        if os.path.exists(html_full_path):
            return render_template(f"docs/{html_path}")
        elif os.path.exists(md_full_path):
            with open(md_full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
            title = extract_title_from_markdown(md_content) or template_name.capitalize()
            
            safe_html = convert_markdown_to_html(md_content)
            
            safe_html = remove_first_h1(safe_html)
            
            template = 'print.html' if is_print else 'markdown_base.html'

            response = render_template(
                template, 
                content=Markup(safe_html), 
                title=title,
                doc_name=template_name,
                versions=git_history,
                is_print=is_print,
                is_version=is_version
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

@app.route('/version/<path:template_name>/<commit_hash>')
def view_version(template_name, commit_hash):
    template_name = urllib.parse.unquote(template_name)
    template_name = sanitize_filename(template_name)
    
    try:
        is_print = request.args.get('print') == '1'
        is_version = True
        
        md_content = get_file_at_commit(f"api/templates/docs/{template_name}.md", commit_hash)
        
        if not md_content:
            html_content = get_file_at_commit(f"api/templates/docs/{template_name}.html", commit_hash)
            if html_content:
                return html_content
            else:
                abort(404)
        
        title = extract_title_from_markdown(md_content) or template_name.capitalize()
        
        safe_html = convert_markdown_to_html(md_content)
        
        safe_html = remove_first_h1(safe_html)
        
        git_history = get_template_history(template_name)
        
        template = 'print.html' if is_print else 'markdown_base.html'
        
        current_version = None
        for version in git_history:
            if version['hash'] == commit_hash:
                current_version = version
                break
        
        version_info = f"Version: {current_version['short_hash'] if current_version else commit_hash[:7]}"
        
        return render_template(
            template, 
            content=Markup(safe_html), 
            title=title,
            version_info=version_info,
            doc_name=template_name,
            versions=git_history,
            is_print=is_print,
            is_version=is_version,
            current_hash=commit_hash
        )
    except Exception as e:
        print(f"Error viewing version {template_name} at {commit_hash}: {str(e)}")
        abort(500)

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