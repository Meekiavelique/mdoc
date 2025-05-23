import os
from datetime import datetime
from api.config import SITE_CONFIG
from api.utils.documents import get_all_documents
from api.utils.github_utils import get_template_history

def generate_sitemap():
    base_url = SITE_CONFIG['base_url']
    documents = get_all_documents()
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    sitemap_xml += f'  <url>\n'
    sitemap_xml += f'    <loc>{base_url}/</loc>\n'
    sitemap_xml += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
    sitemap_xml += f'    <changefreq>daily</changefreq>\n'
    sitemap_xml += f'    <priority>1.0</priority>\n'
    sitemap_xml += f'  </url>\n'
    
    for doc in documents:
        history = get_template_history(doc['filename'])
        last_modified = datetime.now().strftime("%Y-%m-%d")
        
        if history:
            last_modified = datetime.strptime(history[0]["date"], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d")
        
        sitemap_xml += f'  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/{doc["filename"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{last_modified}</lastmod>\n'
        sitemap_xml += f'    <changefreq>weekly</changefreq>\n'
        sitemap_xml += f'    <priority>0.8</priority>\n'
        sitemap_xml += f'  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    return sitemap_xml