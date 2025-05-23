import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from api.config import DISCORD_WEBHOOK_URL, SITE_CONFIG

def generate_doc_preview_image(title, description, author):
    width, height = 800, 400
    bg_color = (47, 49, 54)
    text_color = (255, 255, 255)
    accent_color = (88, 101, 242)
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        desc_font = ImageFont.truetype("arial.ttf", 24)
        author_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
    
    y_offset = 50
    
    if len(title) > 35:
        title = title[:35] + "..."
    draw.text((50, y_offset), title, fill=text_color, font=title_font)
    
    y_offset += 100
    
    if description:
        if len(description) > 80:
            description = description[:80] + "..."
        draw.text((50, y_offset), description, fill=(185, 187, 190), font=desc_font)
        y_offset += 60
    
    draw.text((50, height - 80), f"By {author}", fill=(114, 118, 125), font=author_font)
    
    draw.text((width - 200, height - 40), "mdoc", fill=accent_color, font=author_font)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def send_discord_notification(doc_name, title, description, author, doc_url):
    if not DISCORD_WEBHOOK_URL:
        return False
    
    try:
        preview_image = generate_doc_preview_image(title, description, author)
        
        embed = {
            "title": title,
            "description": description[:100] + "..." if len(description) > 100 else description,
            "url": doc_url,
            "color": 5814783,
            "fields": [
                {
                    "name": "Author",
                    "value": author,
                    "inline": True
                },
                {
                    "name": "Document",
                    "value": doc_name,
                    "inline": True
                }
            ],
            "image": {
                "url": f"data:image/png;base64,{preview_image}"
            },
            "footer": {
                "text": "Mdoc Documentation System"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        return response.status_code == 204
        
    except Exception as e:
        print(f"Discord notification error: {e}")
        return False