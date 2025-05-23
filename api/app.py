from flask import Flask
from api import routes
from api.utils.filters import register_filters
from api.utils.analytics import analytics_db
from api.utils.documents import get_all_documents
import os

def create_app():
    app = Flask(__name__)
    
    register_filters(app)
    
    routes.register_blueprints(app)
    
    analytics_db.init_db()
    
    get_all_documents.cache_clear()
    docs = get_all_documents()
    print(f"Found {len(docs)} documents: {[d['filename'] for d in docs]}")
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)