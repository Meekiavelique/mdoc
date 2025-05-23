from flask import Blueprint, render_template, abort, request, Response, jsonify
from markupsafe import Markup
import urllib.parse
import os
import hashlib
from api.utils.markdown import convert_markdown_to_html, remove_first_h1, extract_title_from_markdown, extract_description_from_markdown
from api.utils.github_utils import get_file_at_commit, get_template_history, get_document_contributors, get_document_author, is_recently_updated
from api.utils.sanitization import sanitize_filename
from api.utils.documents import get_all_documents, get_documents_by_category
from api.utils.analytics import analytics_db
from api.utils.sitemap_generator import generate_sitemap
from api.config import SITE_CONFIG, GITHUB_REPO

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/sitemap.xml')
def sitemap():
    sitemap_xml = generate_sitemap()
    response = Response(sitemap_xml, mimetype='application/xml')
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@docs_bp.route('/api/docs')
def api_list_docs():
    documents = get_all_documents()
    return jsonify(documents)

@docs_bp.route('/api/docs/<path:doc_name>')
def api_get_doc(doc_name):
    doc_name = sanitize_filename(doc_name)
    
    try:
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        md_path = os.path.join(docs_dir, f"{doc_name}.md")
        
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'name': doc_name,
                'title': extract_title_from_markdown(content),
                'content': content,
                'contributors': get_document_contributors(doc_name),
                'view_count': analytics_db.get_view_count(doc_name)
            })
        else:
            abort(404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@docs_bp.route('/api/analytics/popular')
def api_popular_docs():
    popular = analytics_db.get_popular_documents(10)
    return jsonify(popular)

@docs_bp.route('/')
def index():
    try:
        documents_by_category = get_documents_by_category()
        recently_updated = [doc for doc in get_all_documents() if doc.get('recently_updated')]
        popular_docs = analytics_db.get_popular_documents(5)
        
        print(f"DEBUG - documents_by_category: {documents_by_category}")
        print(f"DEBUG - recently_updated: {recently_updated}")
        print(f"DEBUG - popular_docs: {popular_docs}")
        
        return render_template('index.html', 
                             documents_by_category=documents_by_category,
                             recently_updated=recently_updated,
                             popular_docs=popular_docs)
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
        contributors = get_document_contributors(template_name)
        author = get_document_author(template_name)
        view_count = analytics_db.get_view_count(template_name)
        recently_updated = is_recently_updated(template_name)
        
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16] if client_ip else None
        user_agent = request.headers.get('User-Agent', '')
        
        analytics_db.record_view(template_name, ip_hash, user_agent)

        if os.path.exists(html_full_path):
            return render_template(f"docs/{html_path}")
        elif os.path.exists(md_full_path):
            with open(md_full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
            title = extract_title_from_markdown(md_content) or template_name.capitalize()
            description = extract_description_from_markdown(md_content)
            
            safe_html = convert_markdown_to_html(md_content)
            safe_html = remove_first_h1(safe_html)
            
            template = 'print.html' if is_print else 'markdown_base.html'

            response = render_template(
                template, 
                content=Markup(safe_html), 
                title=title,
                description=description,
                doc_name=template_name,
                versions=git_history,
                contributors=contributors,
                author=author,
                view_count=view_count,
                recently_updated=recently_updated,
                is_print=is_print,
                is_version=is_version,
                github_repo=GITHUB_REPO,
                github_edit_url=f"{SITE_CONFIG['github_edit_base']}/{template_name}.md"
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
        description = extract_description_from_markdown(md_content)
        
        safe_html = convert_markdown_to_html(md_content)
        safe_html = remove_first_h1(safe_html)
        
        git_history = get_template_history(template_name)
        contributors = get_document_contributors(template_name)
        author = get_document_author(template_name)
        view_count = analytics_db.get_view_count(template_name)
        
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
            description=description,
            version_info=version_info,
            doc_name=template_name,
            versions=git_history,
            contributors=contributors,
            author=author,
            view_count=view_count,
            is_print=is_print,
            is_version=is_version,
            current_hash=commit_hash,
            github_repo=GITHUB_REPO,
            github_edit_url=f"{SITE_CONFIG['github_edit_base']}/{template_name}.md"
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