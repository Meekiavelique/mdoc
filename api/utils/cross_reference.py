import re
from api.utils.documents import get_all_documents

def process_cross_references(content):
    documents = get_all_documents()
    doc_titles = {doc['filename']: doc['title'] for doc in documents}
    
    def replace_reference(match):
        ref_text = match.group(1)
        
        if ref_text in doc_titles:
            return f'<a href="/{ref_text}" class="cross-reference">{doc_titles[ref_text]}</a>'
        
        for filename, title in doc_titles.items():
            if title.lower() == ref_text.lower():
                return f'<a href="/{filename}" class="cross-reference">{title}</a>'
        
        return f'<span class="broken-reference">[[{ref_text}]]</span>'
    
    pattern = r'\[\[([^\]]+)\]\]'
    return re.sub(pattern, replace_reference, content)