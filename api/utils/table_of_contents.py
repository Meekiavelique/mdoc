import re

def generate_table_of_contents(html_content):
    heading_pattern = r'<h([1-6])(?:\s+id="([^"]*)")?[^>]*>(.*?)</h[1-6]>'
    headings = re.findall(heading_pattern, html_content, re.DOTALL)
    
    if not headings:
        return ""
    
    toc_html = '<div class="table-of-contents">\n'
    toc_html += '<h3>Table of Contents</h3>\n<ul>\n'
    
    for level, heading_id, text in headings:
        level = int(level)
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        
        if not heading_id:
            heading_id = re.sub(r'[^\w\s-]', '', clean_text.lower())
            heading_id = re.sub(r'[-\s]+', '-', heading_id).strip('-')
        
        toc_html += f'<li class="toc-level-{level}"><a href="#{heading_id}">{clean_text}</a></li>\n'
    
    toc_html += '</ul>\n</div>\n'
    return toc_html

def add_ids_to_headings(html_content):
    def add_id(match):
        tag = match.group(1)
        level = match.group(2)
        attrs = match.group(3) or ""
        text = match.group(4)
        
        if 'id=' not in attrs:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            heading_id = re.sub(r'[^\w\s-]', '', clean_text.lower())
            heading_id = re.sub(r'[-\s]+', '-', heading_id).strip('-')
            attrs += f' id="{heading_id}"'
        
        return f'<{tag}{level}{attrs}>{text}</{tag}{level}>'
    
    pattern = r'<(h)([1-6])([^>]*)>(.*?)</h[1-6]>'
    return re.sub(pattern, add_id, html_content, flags=re.DOTALL)