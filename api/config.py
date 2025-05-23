import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_REPO = "Meekiavelique/mdoc"
DOCS_DIR = os.path.join(os.path.dirname(__file__), 'templates', 'docs')

DATABASE_CONFIG = {
    'type': os.getenv('DB_TYPE', 'sqlite'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'mdoc_analytics'),
    'username': os.getenv('DB_USER', 'mdoc_user'),
    'password': os.getenv('DB_PASSWORD', ''),
    'path': os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'data', 'analytics.db'))
}

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

SITE_CONFIG = {
    'title': os.getenv('SITE_TITLE', 'Mdoc'),
    'description': os.getenv('SITE_DESCRIPTION', 'Documentation System'),
    'base_url': os.getenv('SITE_BASE_URL', 'https://docs.meek-dev.com'),
    'github_edit_base': f'https://github.com/{GITHUB_REPO}/edit/main/api/templates/docs'
}