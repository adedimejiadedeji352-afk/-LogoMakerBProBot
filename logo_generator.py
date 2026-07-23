import io
import math
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 800, 800

COLOR_SCHEMES = {
    "Ocean Blue": {"bg": (13, 27, 42), "primary": (27, 94, 148), "accent": (255, 255, 255)},
    "Sunset Orange": {"bg": (255, 247, 235), "primary": (255, 111, 60), "accent": (44, 44, 44)},
    "Forest Green": {"bg": (240, 245, 240), "primary": (34, 87, 62), "accent": (255, 255, 255)},
    "Bold Black": {"bg": (255, 255, 255), "primary": (20, 20, 20), "accent": (255, 200, 0)},
    "Purple Tech": {"bg": (18, 15, 30), "primary": (124, 77, 255), "accent": (255, 255, 255)},
}

SHAPES = ["circle", "square", "hexagon", "badge"]


def _get_font(size):
    font_paths = [
        "fonts/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_hexagon(draw, center, radius, fill):
    cx, cy = center
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        points.append((x, y))
    draw.polygon(points, fill=fill)


def generate_logo(text: str, scheme_name: str, shape: str) -> bytes:
    scheme = COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["Ocean Blue"])
    bg_color = scheme["bg"]
    primary_color = scheme["primary"]
    accent_color = scheme["accent"]

    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    center = (WIDTH // 2, HEIGHT // 2 - 60)
    radius = 220

    if shape == "circle":
        draw.ellipse(
            [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
            fill=primary_color,
        )
    elif shape == "square":
        draw.rounded_rectangle(
            [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
            radius=40,
            fill=primary_color,
        )
    elif shape == "hexagon":
        _draw_hexagon(draw, center, radius, primary_color)
    elif shape == "badge":
        draw.ellipse(
            [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
            fill=primary_color,
        )
        draw.ellipse(
            [
                center[0] - radius + 20,
                center[1] - radius + 20,
                center[0] + radius - 20,
                center[1] + radius - 20,
            ],
            outline=accent_color,
            width=6,
        )

    initials = "".join([w[0].upper() for w in text.split()][:2]) or text[:2].upper()
    initials_font = _get_font(140)
    bbox = draw.textbbox((0, 0), initials, font=initials_font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (center[0] - text_w / 2, center[1] - text_h / 2 - bbox[1]),
        initials,
        font=initials_font,
        fill=accent_color,
    )

    name_font = _get_font(64)
    bbox2 = draw.textbbox((0, 0), text, font=name_font)
    name_w = bbox2[2] - bbox2[0]
    draw.text(
        (WIDTH / 2 - name_w / 2, center[1] + radius + 40),
        text,
        font=name_font,
        fill=primary_color if bg_color != primary_color else accent_color,
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
