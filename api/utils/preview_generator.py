import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import hashlib

def generate_doc_preview(title, description="", author=""):
    width, height = 1200, 630
    bg_color = (255, 255, 255)
    text_color = (51, 51, 51)
    accent_color = (3, 102, 214)
    secondary_color = (127, 140, 141)
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 64)
        desc_font = ImageFont.truetype("arial.ttf", 32)
        author_font = ImageFont.truetype("arial.ttf", 24)
        brand_font = ImageFont.truetype("arial.ttf", 48)
    except:
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
    
    draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
    
    draw.rectangle([(60, 60), (width - 60, height - 60)], outline=(221, 221, 221), width=2)
    
    y_offset = 120
    
    title_lines = []
    if len(title) > 35:
        words = title.split()
        line1 = []
        line2 = []
        for word in words:
            if len(' '.join(line1 + [word])) <= 35:
                line1.append(word)
            else:
                line2.append(word)
        title_lines = [' '.join(line1), ' '.join(line2)]
    else:
        title_lines = [title]
    
    for line in title_lines:
        draw.text((100, y_offset), line, fill=text_color, font=title_font)
        y_offset += 80
    
    y_offset += 30
    
    if description:
        desc_lines = []
        if len(description) > 70:
            words = description.split()
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) <= 70:
                    current_line.append(word)
                else:
                    desc_lines.append(' '.join(current_line))
                    current_line = [word]
                    if len(desc_lines) >= 2:
                        break
            if current_line and len(desc_lines) < 2:
                desc_lines.append(' '.join(current_line))
        else:
            desc_lines = [description]
        
        for line in desc_lines:
            draw.text((100, y_offset), line, fill=secondary_color, font=desc_font)
            y_offset += 45
    
    draw.rectangle([(60, height - 120), (width - 60, height - 60)], fill=(248, 249, 250))
    
    if author:
        draw.text((100, height - 105), f"By {author}", fill=secondary_color, font=author_font)
    
    draw.text((width - 200, height - 105), "mdoc", fill=accent_color, font=brand_font)
    
    return img

def save_preview_image(title, description="", author="", doc_name=""):
    img = generate_doc_preview(title, description, author)
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'previews')
    os.makedirs(static_dir, exist_ok=True)
    
    filename = f"{doc_name}.png" if doc_name else f"{hashlib.md5(title.encode()).hexdigest()}.png"
    filepath = os.path.join(static_dir, filename)
    
    img.save(filepath, 'PNG', quality=95)
    
    return f"/static/previews/{filename}"