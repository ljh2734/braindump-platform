import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def generate_captcha_text(length=4):
    """生成随机验证码文本"""
    chars = string.ascii_uppercase + string.digits  # A-Z, 0-9
    return ''.join(random.choices(chars, k=length))

def generate_captcha_image(text):
    """根据文本生成验证码图片"""
    width, height = 120, 50
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill='gray', width=1)

    # 添加噪点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill='black')

    # 绘制验证码文本（可加载字体，这里用默认）
    try:
        # 加载系统字体（如 arial.ttf），若无则用默认
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()

    text_width = draw.textlength(text, font=font)
    x = (width - text_width) / 2
    y = (height - 36) / 2
    draw.text((x, y), text, fill='black', font=font)

    # 转为字节流
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io