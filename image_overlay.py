from flask import Flask, request, jsonify
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
app = Flask(__name__)

def process_image(image_stream, watermark_stream=None, story_id="", opacity=200, apply_watermark=True):
    try:
        image = Image.open(BytesIO(image_stream.read())).convert("RGBA")
        draw = ImageDraw.Draw(image)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]

        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 30)
                break
        else:
            font = ImageFont.load_default() 
            
        if story_id:
            text_position = (10, image.height - 50) 
            draw.text(text_position, story_id, fill=(255, 255, 255, 255), font=font)
        
        if apply_watermark and watermark_stream:
            watermark = Image.open(BytesIO(watermark_stream.read())).convert("RGBA")

            watermark_width = image.width // 3
            aspect_ratio = watermark.height / watermark.width
            watermark = watermark.resize((watermark_width, int(watermark_width * aspect_ratio)))

            opacity = int(opacity)
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: p * (opacity / 255))
            watermark.putalpha(alpha)

            pos = (image.width - watermark.width - 10, image.height - watermark.height - 10)
            image.paste(watermark, pos, watermark)

        output_buffer = BytesIO()
        image.convert("RGB").save(output_buffer, format="JPEG")
        output_buffer.seek(0)
        return base64.b64encode(output_buffer.getvalue()).decode('utf-8')
    
    except Exception as e:
        return str(e)

@app.route('/process-image', methods=['POST'])
def handle_image():
    if 'image' not in request.files:
        return jsonify({"error": "Image file is required"}), 400
    
    image_file = request.files['image']
    watermark_file = request.files.get('watermark', None)
    story_id = request.form.get('story_id', "")  # Default to empty string
    opacity = request.form.get('opacity', 128)
    apply_watermark = request.form.get('apply_watermark', 'true').lower() == 'true'

    try:
        result_b64 = process_image(image_file, watermark_file, story_id, opacity, apply_watermark)
        return jsonify({"processed_image": result_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=True)
