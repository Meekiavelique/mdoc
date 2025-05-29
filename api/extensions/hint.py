from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import logging

logger = logging.getLogger(__name__)

class HintPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_hint_block = False
        hint_content = []
        hint_type = 'info'
        hint_title = ''
        counter = 0
        
        for line in lines:
            hint_match = re.match(r'^```hint\s*(\w+)?\s*(.*)?$', line.strip())
            if hint_match:
                in_hint_block = True
                hint_content = []
                hint_type = hint_match.group(1) or 'info'
                hint_title = hint_match.group(2) or ''
                continue
            elif in_hint_block and line.strip() == '```':
                in_hint_block = False
                
                try:
                    import markdown
                    content_text = '\n'.join(hint_content)
                    processed_content = markdown.markdown(
                        content_text, 
                        extensions=['fenced_code', 'codehilite'],
                        output_format='html5'
                    )
                except Exception as e:
                    logger.error(f"Error processing hint content: {e}")
                    processed_content = '<p>' + '\n'.join(hint_content) + '</p>'
                
                icon_map = {
                    'info': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 25 11 A 3 3 0 0 0 22 14 A 3 3 0 0 0 25 17 A 3 3 0 0 0 28 14 A 3 3 0 0 0 25 11 z M 21 21 L 21 23 L 22 23 L 23 23 L 23 36 L 22 36 L 21 36 L 21 38 L 22 38 L 23 38 L 27 38 L 28 38 L 29 38 L 29 36 L 28 36 L 27 36 L 27 21 L 26 21 L 22 21 L 21 21 z"></path></svg>',
                    'warning': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 23 15 L 23 26 L 27 26 L 27 15 L 23 15 z M 23 30 L 23 34 L 27 34 L 27 30 L 23 30 z"></path></svg>',
                    'error': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 32.990234 15.986328 A 1.0001 1.0001 0 0 0 32.292969 16.292969 L 25 23.585938 L 17.707031 16.292969 A 1.0001 1.0001 0 0 0 16.990234 15.990234 A 1.0001 1.0001 0 0 0 16.292969 17.707031 L 23.585938 25 L 16.292969 32.292969 A 1.0001 1.0001 0 1 0 17.707031 33.707031 L 25 26.414062 L 32.292969 33.707031 A 1.0001 1.0001 0 1 0 33.707031 32.292969 L 26.414062 25 L 33.707031 17.707031 A 1.0001 1.0001 0 0 0 32.990234 15.986328 z"></path></svg>',
                    'success': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 34.988281 14.988281 A 1.0001 1.0001 0 0 0 34.171875 15.439453 L 23.970703 30.476562 L 16.679688 23.710938 A 1.0001 1.0001 0 1 0 15.320312 25.177734 L 24.316406 33.525391 L 35.828125 16.560547 A 1.0001 1.0001 0 0 0 34.988281 14.988281 z"></path></svg>',
                    'tip': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 25 10 C 18.082031 10 12.398438 15.054688 11.458984 21.642578 A 1.0001 1.0001 0 1 0 13.4375 21.986328 C 14.261719 16.632813 19.203125 12 25 12 C 31.628906 12 37 17.371094 37 24 C 37 30.628906 31.628906 36 25 36 A 1.0001 1.0001 0 1 0 25 38 C 32.710938 38 39 31.710938 39 24 C 39 16.289063 32.710938 10 25 10 z"></path></svg>',
                    'note': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 6 4 L 6 46 L 44 46 L 44 14.59375 L 34.40625 4 L 6 4 z M 8 6 L 32 6 L 32 16 L 42 16 L 42 44 L 8 44 L 8 6 z M 34 7.4375 L 40.5625 14 L 34 14 L 34 7.4375 z M 12 22 L 12 24 L 38 24 L 38 22 L 12 22 z M 12 28 L 12 30 L 38 30 L 38 28 L 12 28 z M 12 34 L 12 36 L 30 36 L 30 34 L 12 34 z"></path></svg>'
                }
                
                valid_types = ['info', 'warning', 'error', 'success', 'tip', 'note']
                if hint_type not in valid_types:
                    hint_type = 'info'
                    logger.warning(f"Invalid hint type '{hint_match.group(1)}', defaulting to 'info'")
                
                icon = icon_map.get(hint_type, icon_map['info'])
                display_title = hint_title if hint_title else hint_type.title()
                
                import html
                display_title = html.escape(display_title)
                
                placeholder = f'''<div class="mdoc-hint mdoc-hint-{hint_type}" id="hint-{counter}">
    <div class="hint-header">
        <div class="hint-icon">{icon}</div>
        <h4 class="hint-title">{display_title}</h4>
    </div>
    <div class="hint-content">
        {processed_content}
    </div>
</div>'''
                
                new_lines.append(placeholder)
                counter += 1
                continue
            
            if in_hint_block:
                hint_content.append(line)
            else:
                new_lines.append(line)
                
        if in_hint_block:
            logger.warning("Unclosed hint block detected, closing automatically")
            try:
                import markdown
                content_text = '\n'.join(hint_content)
                processed_content = markdown.markdown(
                    content_text, 
                    extensions=['fenced_code', 'codehilite'],
                    output_format='html5'
                )
            except Exception as e:
                logger.error(f"Error processing unclosed hint content: {e}")
                processed_content = '<p>' + '\n'.join(hint_content) + '</p>'
            
            icon_map = {
                'info': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="20" height="20" viewBox="0 0 50 50"><path d="M 25 2 C 12.309295 2 2 12.309295 2 25 C 2 37.690705 12.309295 48 25 48 C 37.690705 48 48 37.690705 48 25 C 48 12.309295 37.690705 2 25 2 z M 25 4 C 36.609824 4 46 13.390176 46 25 C 46 36.609824 36.609824 46 25 46 C 13.390176 46 4 36.609824 4 25 C 4 13.390176 13.390176 4 25 4 z M 25 11 A 3 3 0 0 0 22 14 A 3 3 0 0 0 25 17 A 3 3 0 0 0 28 14 A 3 3 0 0 0 25 11 z M 21 21 L 21 23 L 22 23 L 23 23 L 23 36 L 22 36 L 21 36 L 21 38 L 22 38 L 23 38 L 27 38 L 28 38 L 29 38 L 29 36 L 28 36 L 27 36 L 27 21 L 26 21 L 22 21 L 21 21 z"></path></svg>'
            }
            
            icon = icon_map.get(hint_type, icon_map['info'])
            display_title = hint_title if hint_title else hint_type.title()
            
            import html
            display_title = html.escape(display_title)
            
            placeholder = f'''<div class="mdoc-hint mdoc-hint-{hint_type}" id="hint-{counter}">
    <div class="hint-header">
        <div class="hint-icon">{icon}</div>
        <h4 class="hint-title">{display_title}</h4>
    </div>
    <div class="hint-content">
        {processed_content}
    </div>
</div>'''
            
            new_lines.append(placeholder)
                
        return new_lines

class HintExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(HintPreprocessor(md), 'hint', 170)

def makeExtension(**kwargs):
    return HintExtension(**kwargs)