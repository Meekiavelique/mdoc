from flask import Flask
from api import routes
from api.utils.filters import register_filters
import os

def create_app():
    app = Flask(__name__)
    
    register_filters(app)
    
    routes.register_blueprints(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)