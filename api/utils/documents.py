import os
import functools
from api.utils.github_utils import is_recently_updated

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        templates = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            return []
            
        for f in os.listdir(docs_dir):
            file_path = os.path.join(docs_dir, f)
            
            if os.path.isfile(file_path):
                if f.endswith('.html') and f not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                    filename = f.replace('.html', '')
                    templates.append({
                        'filename': filename, 
                        'title': filename.replace('_', ' ').title(),
                        'category': None,
                        'recently_updated': is_recently_updated(filename)
                    })
                elif f.endswith('.md'):
                    filename = f.replace('.md', '')
                    title = filename.replace('_', ' ').title()
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            first_line = file.readline().strip()
                            if first_line.startswith('# '):
                                title = first_line[2:].strip()
                    except Exception:
                        pass
                    
                    templates.append({
                        'filename': filename, 
                        'title': title,
                        'category': None,
                        'recently_updated': is_recently_updated(filename)
                    })
        
        return sorted(templates, key=lambda x: x['title'])
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        return []

def get_categories():
    documents = get_all_documents()
    categories = set()
    
    for doc in documents:
        if doc.get('category'):
            categories.add(doc['category'])
    
    return sorted(list(categories))

def get_documents_by_category():
    documents = get_all_documents()
    categorized = {'Root': documents}
    return categorized