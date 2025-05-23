import os

GITHUB_REPO = "Meekiavelique/mdoc"
DOCS_DIR = os.path.join(os.path.dirname(__file__), 'templates', 'docs')

DATABASE_CONFIG = {
    'type': 'mysql',
    'host': 'YOURIP',
    'port': 3306,
    'database': 'mdoc_analytics',
    'username': 'mdoc_user',
    'password': 'your_strong_password'
}
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')

SITE_CONFIG = {
    'title': 'Mdoc',
    'description': 'Documentation System',
    'base_url': 'https://docs.meek-dev.com',
    'github_edit_base': f'https://github.com/{GITHUB_REPO}/edit/main/api/templates/docs'
}