from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import urllib.parse

class VideoPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_video_block = False
        video_config = {}
        counter = 0
        
        for line in lines:
            if line.strip() == '```video':
                in_video_block = True
                video_config = {}
                continue
            elif in_video_block and line.strip() == '```':
                in_video_block = False
                
                placeholder = self._create_video_embed(video_config, counter)
                new_lines.append(placeholder)
                counter += 1
                continue
            elif in_video_block:
                self._parse_config_line(line, video_config)
                continue
            
            video_url_match = re.match(r'^!\[video\]\(([^)]+)\)(?:\{([^}]+)\})?', line.strip())
            if video_url_match:
                url = video_url_match.group(1)
                options = video_url_match.group(2) or ""
                
                config = {'url': url}
                if options:
                    for option in options.split(','):
                        if '=' in option:
                            key, value = option.strip().split('=', 1)
                            config[key] = value
                        else:
                            config[option.strip()] = True
                
                placeholder = self._create_video_embed(config, counter)
                new_lines.append(placeholder)
                counter += 1
                continue
            
            new_lines.append(line)
                
        return new_lines
    
    def _parse_config_line(self, line, config):
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
        elif line:
            config[line] = True
    
    def _create_video_embed(self, config, counter):
        url = config.get('url', '')
        width = config.get('width', '100%')
        height = config.get('height', '400')
        autoplay = 'autoplay' in config
        muted = 'muted' in config or autoplay
        loop = 'loop' in config
        controls = 'controls' not in config or config.get('controls', 'true').lower() == 'true'
        
        if not url:
            return f'<div class="video-error">Error: No video URL provided</div>'
        
        video_id = f"video-{counter}"
        
        if 'youtube.com/watch' in url or 'youtu.be/' in url:
            return self._create_youtube_embed(url, config, video_id)
        elif 'vimeo.com' in url:
            return self._create_vimeo_embed(url, config, video_id)
        elif 'twitch.tv' in url:
            return self._create_twitch_embed(url, config, video_id)
        else:
            return self._create_direct_video_embed(url, config, video_id)
    
    def _create_youtube_embed(self, url, config, video_id):
        video_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)', url)
        if not video_match:
            return '<div class="video-error">Error: Invalid YouTube URL</div>'
        
        video_id_yt = video_match.group(1)
        width = config.get('width', '100%')
        height = config.get('height', '400')
        autoplay = '&autoplay=1' if 'autoplay' in config else ''
        muted = '&mute=1' if 'muted' in config or 'autoplay' in config else ''
        loop = '&loop=1' if 'loop' in config else ''
        controls = '&controls=0' if config.get('controls', 'true').lower() == 'false' else ''
        start = f"&start={config['start']}" if 'start' in config else ''
        
        embed_url = f"https://www.youtube.com/embed/{video_id_yt}?{autoplay}{muted}{loop}{controls}{start}"
        
        return f'''
<div class="mdoc-video" id="{video_id}">
    <div class="component-header">
        <span>YouTube Video</span>
        <a href="{url}" target="_blank" class="video-external-link">↗</a>
    </div>
    <div class="component-body">
        <iframe src="{embed_url}" 
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                allowfullscreen 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
        </iframe>
    </div>
</div>
'''
    
    def _create_vimeo_embed(self, url, config, video_id):
        video_match = re.search(r'vimeo\.com/(\d+)', url)
        if not video_match:
            return '<div class="video-error">Error: Invalid Vimeo URL</div>'
        
        video_id_vimeo = video_match.group(1)
        width = config.get('width', '100%')
        height = config.get('height', '400')
        autoplay = '&autoplay=1' if 'autoplay' in config else ''
        muted = '&muted=1' if 'muted' in config or 'autoplay' in config else ''
        loop = '&loop=1' if 'loop' in config else ''
        
        embed_url = f"https://player.vimeo.com/video/{video_id_vimeo}?{autoplay}{muted}{loop}"
        
        return f'''
<div class="mdoc-video" id="{video_id}">
    <div class="component-header">
        <span>Vimeo Video</span>
        <a href="{url}" target="_blank" class="video-external-link">↗</a>
    </div>
    <div class="component-body">
        <iframe src="{embed_url}" 
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                allowfullscreen>
        </iframe>
    </div>
</div>
'''
    
    def _create_twitch_embed(self, url, config, video_id):
        if '/videos/' in url:
            video_match = re.search(r'twitch\.tv/videos/(\d+)', url)
            if video_match:
                video_id_twitch = video_match.group(1)
                embed_url = f"https://player.twitch.tv/?video={video_id_twitch}&parent={config.get('domain', 'localhost')}"
            else:
                return '<div class="video-error">Error: Invalid Twitch video URL</div>'
        else:
            channel_match = re.search(r'twitch\.tv/([a-zA-Z0-9_]+)', url)
            if channel_match:
                channel = channel_match.group(1)
                embed_url = f"https://player.twitch.tv/?channel={channel}&parent={config.get('domain', 'localhost')}"
            else:
                return '<div class="video-error">Error: Invalid Twitch channel URL</div>'
        
        width = config.get('width', '100%')
        height = config.get('height', '400')
        
        return f'''
<div class="mdoc-video" id="{video_id}">
    <div class="component-header">
        <span>Twitch Stream</span>
        <a href="{url}" target="_blank" class="video-external-link">↗</a>
    </div>
    <div class="component-body">
        <iframe src="{embed_url}" 
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                allowfullscreen>
        </iframe>
    </div>
</div>
'''
    
    def _create_direct_video_embed(self, url, config, video_id):
        width = config.get('width', '100%')
        height = config.get('height', '400')
        autoplay = 'autoplay' if 'autoplay' in config else ''
        muted = 'muted' if 'muted' in config or 'autoplay' in config else ''
        loop = 'loop' if 'loop' in config else ''
        controls = '' if config.get('controls', 'true').lower() == 'false' else 'controls'
        poster = f'poster="{config["poster"]}"' if 'poster' in config else ''
        
        return f'''
<div class="mdoc-video" id="{video_id}">
    <div class="component-header">
        <span>Video</span>
        <a href="{url}" target="_blank" class="video-external-link">↗</a>
    </div>
    <div class="component-body">
        <video width="{width}" 
               height="{height}" 
               {controls} 
               {autoplay} 
               {muted} 
               {loop} 
               {poster}>
            <source src="{url}" type="video/mp4">
            <source src="{url}" type="video/webm">
            <source src="{url}" type="video/ogg">
            Your browser does not support the video tag.
        </video>
    </div>
</div>
'''

class VideoExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(VideoPreprocessor(md), 'video', 172)

def makeExtension(**kwargs):
    return VideoExtension(**kwargs)