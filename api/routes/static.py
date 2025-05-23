from flask import Blueprint, send_from_directory, abort
import os

static_bp = Blueprint('static', __name__)

@static_bp.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    response = send_from_directory(static_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=86400'  
    return response

@static_bp.route('/favicon.ico')
def favicon():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    try:
        return send_from_directory(static_dir, 'favicon.ico')
    except:
        abort(404)