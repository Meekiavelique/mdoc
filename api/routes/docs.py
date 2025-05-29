from flask import Blueprint, render_template, abort, request, Response, jsonify, redirect
from markupsafe import Markup
import urllib.parse
import os
import hashlib
import logging
from api.utils.markdown import convert_markdown_to_html, remove_first_h1, extract_title_from_markdown, extract_description_from_markdown
from api.utils.github_utils import get_file_at_commit, get_template_history, get_document_contributors, get_document_author, is_recently_updated
from api.utils.sanitization import sanitize_filename, is_safe_path
from api.utils.documents import get_all_documents, get_documents_by_category, get_subdocuments, get_first_subdocument, get_sibling_navigation
from api.utils.analytics import analytics_db
from api.utils.sitemap_generator import generate_sitemap
from api.config import SITE_CONFIG, GITHUB_REPO

docs_bp = Blueprint('docs', __name__)
logger = logging.getLogger(__name__)

@docs_bp.route('/sitemap.xml')
def sitemap():
    try:
        sitemap_xml = generate_sitemap()
        response = Response(sitemap_xml, mimetype='application/xml')
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        logger.error(f"Error generating sitemap: {e}")
        abort(500)

@docs_bp.route('/api/docs')
def api_list_docs():
    try:
        documents = get_all_documents()
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

@docs_bp.route('/api/docs/<path:doc_name>')
def api_get_doc(doc_name):
    try:

        doc_name = urllib.parse.unquote(doc_name)
        doc_name = sanitize_filename(doc_name)

        logger.info(f"API request for document: {doc_name}")

        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')

        if '/' in doc_name:
            parts = doc_name.split('/')
            file_path = os.path.join(docs_dir, *parts)
        else:
            file_path = os.path.join(docs_dir, doc_name)

        md_path = f"{file_path}.md"

        if not is_safe_path(md_path, docs_dir):
            logger.warning(f"Unsafe path access attempted: {doc_name}")
            abort(404)

        if os.path.exists(md_path):
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                contributors = get_document_contributors(doc_name)
                view_count = analytics_db.get_view_count(doc_name)

                logger.info(f"Successfully retrieved document: {doc_name}, views: {view_count}")

                return jsonify({
                    'name': doc_name,
                    'title': extract_title_from_markdown(content),
                    'content': content,
                    'contributors': contributors,
                    'view_count': view_count
                })
            except Exception as e:
                logger.error(f"Error reading file {md_path}: {e}")
                return jsonify({'error': 'Failed to read document'}), 500
        else:
            logger.warning(f"Document not found: {md_path}")
            abort(404)

    except Exception as e:
        logger.error(f"Error in api_get_doc for {doc_name}: {e}")
        return jsonify({'error': str(e)}), 500

@docs_bp.route('/api/analytics/popular')
def api_popular_docs():
    try:
        popular = analytics_db.get_popular_documents(10)
        return jsonify(popular)
    except Exception as e:
        logger.error(f"Error getting popular docs: {e}")
        return jsonify([]), 500

@docs_bp.route('/')
def index():
    try:
        documents_by_category = get_documents_by_category()
        recently_updated = [doc for doc in get_all_documents() if doc.get('recently_updated')]
        popular_docs = analytics_db.get_popular_documents(5)

        return render_template('index.html', 
                             documents_by_category=documents_by_category,
                             recently_updated=recently_updated,
                             popular_docs=popular_docs)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', 
                             error_code="500", 
                             error_message=f"Internal Server Error: {str(e)}"), 500

@docs_bp.route('/<path:template_name>')
def serve_template(template_name):
    try:

        template_name = urllib.parse.unquote(template_name)
        template_name = sanitize_filename(template_name)

        logger.info(f"Serving template: {template_name}")

        is_print = request.args.get('print') == '1'
        is_version = False

        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')

        if '/' in template_name:
            parts = template_name.split('/')
            file_path = os.path.join(docs_dir, *parts)
        else:
            file_path = os.path.join(docs_dir, template_name)

        html_path = f"{file_path}.html"
        md_path = f"{file_path}.md"

        folder_path = os.path.join(docs_dir, template_name)
        if os.path.isdir(folder_path) and not os.path.exists(md_path) and not os.path.exists(html_path):
            first_subdoc = get_first_subdocument(template_name)
            if first_subdoc:
                return redirect(f"/{first_subdoc['filename']}")
            else:
                abort(404)

        try:
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16] if client_ip else None
            user_agent = request.headers.get('User-Agent', '')

            view_count = analytics_db.record_view(template_name, ip_hash, user_agent)
            logger.info(f"Recorded view for {template_name}: {view_count}")
        except Exception as e:
            logger.warning(f"Failed to record view for {template_name}: {e}")
            view_count = 0

        git_history = get_template_history(template_name)
        contributors = get_document_contributors(template_name)
        author = get_document_author(template_name)
        recently_updated = is_recently_updated(template_name)

        subdocuments = get_subdocuments(template_name)
        prev_doc, next_doc = get_sibling_navigation(template_name)

        if os.path.exists(html_path) and is_safe_path(html_path, docs_dir):
            return render_template(f"docs/{template_name}.html")

        elif os.path.exists(md_path) and is_safe_path(md_path, docs_dir):
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()

                title = extract_title_from_markdown(md_content) or template_name.split('/')[-1].replace('_', ' ').title()
                description = extract_description_from_markdown(md_content)

                safe_html = convert_markdown_to_html(md_content)
                safe_html = remove_first_h1(safe_html)

                template = 'print.html' if is_print else 'markdown_base.html'

                breadcrumbs = []
                if '/' in template_name:
                    parts = template_name.split('/')
                    for i, part in enumerate(parts):
                        path = '/'.join(parts[:i+1])
                        name = part.replace('_', ' ').title()
                        if i == len(parts) - 1:
                            breadcrumbs.append({'name': name, 'path': path, 'is_current': True})
                        else:
                            breadcrumbs.append({'name': name, 'path': path, 'is_current': False})

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
                    github_edit_url=f"{SITE_CONFIG['github_edit_base']}/{template_name}.md",
                    subdocuments=subdocuments,
                    prev_doc=prev_doc,
                    next_doc=next_doc,
                    breadcrumbs=breadcrumbs,
                    get_subdocuments=get_subdocuments
                )

                if not is_print:
                    response = Response(response)
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                return response

            except Exception as e:
                logger.error(f"Error processing markdown for {template_name}: {e}")
                abort(500)
        else:
            logger.warning(f"Template not found: {template_name}")
            abort(404)

    except Exception as e:
        logger.error(f"Error serving template {template_name}: {e}")
        abort(500)

@docs_bp.route('/version/<path:template_name>/<commit_hash>')
def view_version(template_name, commit_hash):
    try:
        template_name = urllib.parse.unquote(template_name)
        template_name = sanitize_filename(template_name)

        is_print = request.args.get('print') == '1'
        is_version = True

        md_content = get_file_at_commit(f"api/templates/docs/{template_name}.md", commit_hash)

        if not md_content:
            html_content = get_file_at_commit(f"api/templates/docs/{template_name}.html", commit_hash)
            if html_content:
                return html_content
            else:
                abort(404)

        title = extract_title_from_markdown(md_content) or template_name.split('/')[-1].replace('_', ' ').title()
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

        breadcrumbs = []
        if '/' in template_name:
            parts = template_name.split('/')
            for i, part in enumerate(parts):
                path = '/'.join(parts[:i+1])
                name = part.replace('_', ' ').title()
                breadcrumbs.append({'name': name, 'path': path})

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
            github_edit_url=f"{SITE_CONFIG['github_edit_base']}/{template_name}.md",
            breadcrumbs=breadcrumbs,
            get_subdocuments=get_subdocuments
        )
    except Exception as e:
        logger.error(f"Error viewing version {template_name} at {commit_hash}: {e}")
        abort(500)

@docs_bp.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code="404", error_message="Page Not Found"), 404

@docs_bp.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code="500", error_message="Internal Server Error"), 500