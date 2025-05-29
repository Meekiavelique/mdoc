import os
import functools
from api.utils.github_utils import is_recently_updated

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        documents = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            return []
        
        def scan_directory(current_dir, parent_path=""):
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                
                if os.path.isfile(item_path):
                    if item.endswith('.html') and item not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                        filename = item.replace('.html', '')
                        full_path = f"{parent_path}/{filename}" if parent_path else filename
                        documents.append({
                            'filename': full_path,
                            'title': filename.replace('_', ' ').title(),
                            'category': 'Root',
                            'is_subdoc': bool(parent_path),
                            'parent': parent_path if parent_path else None,
                            'recently_updated': is_recently_updated(full_path),
                            'order': get_order_from_filename(filename)
                        })
                    elif item.endswith('.md'):
                        filename = item.replace('.md', '')
                        full_path = f"{parent_path}/{filename}" if parent_path else filename
                        title = filename.replace('_', ' ').title()
                        
                        try:
                            with open(item_path, 'r', encoding='utf-8') as file:
                                first_line = file.readline().strip()
                                if first_line.startswith('# '):
                                    title = first_line[2:].strip()
                        except Exception:
                            pass
                        
                        documents.append({
                            'filename': full_path,
                            'title': title,
                            'category': 'Root',
                            'is_subdoc': bool(parent_path),
                            'parent': parent_path if parent_path else None,
                            'recently_updated': is_recently_updated(full_path),
                            'order': get_order_from_filename(filename)
                        })
                
                elif os.path.isdir(item_path):
                    new_parent = f"{parent_path}/{item}" if parent_path else item
                    scan_directory(item_path, new_parent)
        
        scan_directory(docs_dir)
     
        folder_names = set()
        for doc in documents:
            if doc['is_subdoc'] and doc['parent']:
                folder_names.add(doc['parent'])
        
        existing_parents = set(doc['filename'] for doc in documents if not doc['is_subdoc'])
        
        for folder_name in folder_names:
            if folder_name not in existing_parents:
                documents.append({
                    'filename': folder_name,
                    'title': folder_name.split('/')[-1].replace('_', ' ').title(),
                    'category': 'Root',
                    'is_subdoc': False,
                    'parent': None,
                    'recently_updated': False,
                    'order': 999,
                    'is_virtual': True
                })
        
        return sorted(documents, key=lambda x: (x['category'], x['title']))
        
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        return []

def get_order_from_filename(filename):
    parts = filename.split('_', 1)
    if len(parts) > 1 and parts[0].isdigit():
        return int(parts[0])
    return 999

def get_categories():
    documents = get_all_documents()
    categories = set()
    
    for doc in documents:
        if doc.get('category'):
            categories.add(doc['category'])
    
    return sorted(list(categories))

def get_documents_by_category():
    documents = get_all_documents()
    categorized = {}
    
    for doc in documents:
        category = doc.get('category', 'Root')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(doc)
    
    return categorized

def get_subdocuments(parent_path):
    documents = get_all_documents()
    return [doc for doc in documents if doc.get('parent') == parent_path]

def get_first_subdocument(parent_path):
    subdocs = get_subdocuments(parent_path)
    if subdocs:
        return min(subdocs, key=lambda x: x['order'])
    return None

def get_sibling_navigation(doc_path):
    if '/' not in doc_path:
        return None, None
    
    parent_path = '/'.join(doc_path.split('/')[:-1])
    subdocs = sorted(get_subdocuments(parent_path), key=lambda x: x['order'])
    
    current_index = None
    for i, doc in enumerate(subdocs):
        if doc['filename'] == doc_path:
            current_index = i
            break
    
    if current_index is None:
        return None, None
    
    prev_doc = subdocs[current_index - 1] if current_index > 0 else None
    next_doc = subdocs[current_index + 1] if current_index < len(subdocs) - 1 else None
    
    return prev_doc, next_doc