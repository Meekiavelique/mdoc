import os
import functools

@functools.lru_cache(maxsize=128)
def get_all_documents():
    try:
        templates = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'docs')
        
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            
        for f in os.listdir(docs_dir):
            if f.endswith('.html') and f not in ['index.html', 'markdown_base.html', 'error.html', 'print.html']:
                filename = f.replace('.html', '')
                templates.append({
                    'filename': filename, 
                    'title': filename.capitalize()
                })
            elif f.endswith('.md'):
                filename = f.replace('.md', '')
                title = filename.capitalize()
                try:
                    with open(os.path.join(docs_dir, f), 'r', encoding='utf-8') as file:
                        first_line = file.readline().strip()
                        if first_line.startswith('# '):
                            title = first_line[2:].strip()
                except Exception:
                    pass
                templates.append({
                    'filename': filename, 
                    'title': title
                })
        return sorted(templates, key=lambda x: x['title'])
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        return []