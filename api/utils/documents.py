import os
import functools
import logging
from api.utils.github_utils import is_recently_updated

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        documents = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        
        if not os.path.exists(docs_dir):
            logger.warning(f"Docs directory does not exist: {docs_dir}")
            os.makedirs(docs_dir, exist_ok=True)
            return []
        
        logger.info(f"Scanning documents in: {docs_dir}")
        
        def scan_directory(current_dir, parent_path=""):
            try:
                items = os.listdir(current_dir)
                logger.debug(f"Scanning directory: {current_dir}, found {len(items)} items")
            except PermissionError as e:
                logger.error(f"Permission denied accessing {current_dir}: {e}")
                return
            except Exception as e:
                logger.error(f"Error listing directory {current_dir}: {e}")
                return
            
            for item in items:
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(current_dir, item)
                
                try:
                    if os.path.isfile(item_path):
                        if item.endswith('.html') and item not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                            filename = item.replace('.html', '')
                            full_path = f"{parent_path}/{filename}" if parent_path else filename
                            
                            documents.append({
                                'filename': full_path,
                                'title': filename.replace('_', ' ').title(),
                                'category': parent_path.split('/')[0] if parent_path else 'Root',
                                'is_subdoc': bool(parent_path),
                                'parent': parent_path if parent_path else None,
                                'recently_updated': is_recently_updated(full_path),
                                'order': get_order_from_filename(filename),
                                'type': 'html'
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
                            except Exception as e:
                                logger.warning(f"Could not read title from {item_path}: {e}")
                            
                            documents.append({
                                'filename': full_path,
                                'title': title,
                                'category': parent_path.split('/')[0] if parent_path else 'Root',
                                'is_subdoc': bool(parent_path),
                                'parent': parent_path if parent_path else None,
                                'recently_updated': is_recently_updated(full_path),
                                'order': get_order_from_filename(filename),
                                'type': 'markdown'
                            })
                    
                    elif os.path.isdir(item_path):
                        new_parent = f"{parent_path}/{item}" if parent_path else item
                        scan_directory(item_path, new_parent)
                        
                except Exception as e:
                    logger.error(f"Error processing {item_path}: {e}")
                    continue
        
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
                    'category': folder_name.split('/')[0] if '/' in folder_name else 'Root',
                    'is_subdoc': False,
                    'parent': None,
                    'recently_updated': False,
                    'order': 999,
                    'is_virtual': True,
                    'type': 'virtual'
                })
        
        documents.sort(key=lambda x: (x['category'], x['order'], x['title']))
        
        logger.info(f"Found {len(documents)} documents total")
        logger.debug(f"Document breakdown: {len([d for d in documents if not d['is_subdoc']])} main docs, {len([d for d in documents if d['is_subdoc']])} subdocs")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return []

def get_order_from_filename(filename):
    try:
        parts = filename.split('_', 1)
        if len(parts) > 1 and parts[0].isdigit():
            return int(parts[0])
    except (ValueError, IndexError):
        pass
    
    return 999

def get_categories():
    try:
        documents = get_all_documents()
        categories = set()
        
        for doc in documents:
            if doc.get('category'):
                categories.add(doc['category'])
        
        result = sorted(list(categories))
        logger.debug(f"Found categories: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []

def get_documents_by_category():
    try:
        documents = get_all_documents()
        categorized = {}
        
        for doc in documents:
            category = doc.get('category', 'Root')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(doc)
        
        for category in categorized:
            categorized[category].sort(key=lambda x: (x['order'], x['title']))
        
        logger.debug(f"Categorized documents: {[(cat, len(docs)) for cat, docs in categorized.items()]}")
        return categorized
    except Exception as e:
        logger.error(f"Error grouping documents by category: {e}")
        return {}

def get_subdocuments(parent_path):
    try:
        documents = get_all_documents()
        subdocs = [doc for doc in documents if doc.get('parent') == parent_path]
        subdocs.sort(key=lambda x: (x['order'], x['title']))
        
        logger.debug(f"Found {len(subdocs)} subdocuments for parent: {parent_path}")
        return subdocs
    except Exception as e:
        logger.error(f"Error getting subdocuments for {parent_path}: {e}")
        return []

def get_first_subdocument(parent_path):
    try:
        subdocs = get_subdocuments(parent_path)
        if subdocs:
            first_subdoc = min(subdocs, key=lambda x: x['order'])
            logger.debug(f"First subdocument for {parent_path}: {first_subdoc['filename']}")
            return first_subdoc
        
        logger.debug(f"No subdocuments found for parent: {parent_path}")
        return None
    except Exception as e:
        logger.error(f"Error getting first subdocument for {parent_path}: {e}")
        return None

def get_sibling_navigation(doc_path):
    try:
        if '/' not in doc_path:
            logger.debug(f"No siblings for root-level document: {doc_path}")
            return None, None
        
        parent_path = '/'.join(doc_path.split('/')[:-1])
        subdocs = sorted(get_subdocuments(parent_path), key=lambda x: x['order'])
        
        if not subdocs:
            logger.debug(f"No subdocuments found for sibling navigation: {parent_path}")
            return None, None
        
        current_index = None
        for i, doc in enumerate(subdocs):
            if doc['filename'] == doc_path:
                current_index = i
                break
        
        if current_index is None:
            logger.warning(f"Current document not found in subdocs: {doc_path}")
            return None, None
        
        prev_doc = subdocs[current_index - 1] if current_index > 0 else None
        next_doc = subdocs[current_index + 1] if current_index < len(subdocs) - 1 else None
        
        logger.debug(f"Sibling navigation for {doc_path}: prev={prev_doc['filename'] if prev_doc else None}, next={next_doc['filename'] if next_doc else None}")
        return prev_doc, next_doc
        
    except Exception as e:
        logger.error(f"Error getting sibling navigation for {doc_path}: {e}")
        return None, None

def find_document_by_name(doc_name):
    try:
        documents = get_all_documents()
        for doc in documents:
            if doc['filename'] == doc_name:
                return doc
        
        logger.warning(f"Document not found: {doc_name}")
        return None
    except Exception as e:
        logger.error(f"Error finding document {doc_name}: {e}")
        return None

def get_document_stats():
    try:
        documents = get_all_documents()
        
        stats = {
            'total_documents': len(documents),
            'main_documents': len([d for d in documents if not d['is_subdoc']]),
            'subdocuments': len([d for d in documents if d['is_subdoc']]),
            'recently_updated': len([d for d in documents if d.get('recently_updated')]),
            'markdown_files': len([d for d in documents if d.get('type') == 'markdown']),
            'html_files': len([d for d in documents if d.get('type') == 'html']),
            'virtual_docs': len([d for d in documents if d.get('is_virtual')]),
            'categories': len(get_categories())
        }
        
        logger.info(f"Document statistics: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        return {}