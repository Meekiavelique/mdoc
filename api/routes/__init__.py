from api.routes.docs import docs_bp
from api.routes.static import static_bp

def register_blueprints(app):
    app.register_blueprint(docs_bp)
    app.register_blueprint(static_bp)