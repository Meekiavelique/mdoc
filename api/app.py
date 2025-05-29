from flask import Flask
from api import routes
from api.utils.filters import register_filters
from api.utils.analytics import analytics_db
from api.utils.documents import get_all_documents
import os
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    register_filters(app)

    routes.register_blueprints(app)

    def init_with_retry():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Database initialization attempt {attempt + 1}")
                analytics_db.init_db()

                time.sleep(0.5)

                get_all_documents.cache_clear()
                docs = get_all_documents()
                logger.info(f"Successfully loaded {len(docs)} documents")

                doc_names = [doc['filename'] for doc in docs[:5]]
                logger.info(f"Sample documents: {doc_names}")
                break

            except Exception as e:
                logger.error(f"Initialization attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  
                else:
                    logger.error("Failed to initialize after all retries")

    init_thread = threading.Thread(target=init_with_retry)
    init_thread.daemon = True
    init_thread.start()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)