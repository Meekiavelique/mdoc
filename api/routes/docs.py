from flask import Blueprint, render_template, abort, request, Response
from markupsafe import Markup
import urllib.parse
import os
from api.utils.markdown import convert_markdown_to_html, remove_first_h1, extract_title_from_markdown
from api.utils.github import get_file_at_commit, get_template_history
from api.utils.sanitization import sanitize_filename
from api.utils.documents import get_all_documents

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/')
def index():
    try:
        templates = get_all_documents()
        return render_template('index.html', templates=templates)
    except Exception as e:
        print(f"Error in index: {str(e)}")
        return render_template('error.html', error_code="500", error_message=f"Internal Server Error: {str(e)}"), 500

@docs_bp.route('/<path:template_name>')
def serve_template(template_name):
    template_name = urllib.parse.unquote(template_name)
    template_name = sanitize_filename(template_name)

    html_path = f"{template_name}.html"
    md_path = f"{template_name}.md"
    
    try:
        is_print = request.args.get('print') == '1'
        is_version = False

        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        
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

@docs_bp.route('/version/<path:template_name>/<commit_hash>')
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

@docs_bp.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code="404", error_message="Page Not Found"), 404

@docs_bp.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code="500", error_message="Internal Server Error"), 500