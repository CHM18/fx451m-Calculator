from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "build" / "flutter" / "images"
ASSETS_DIR = ROOT / "assets"
ICON_PATH = IMAGE_DIR / "icon.png"
FAVICON_PATH = IMAGE_DIR / "favicon.png"
ASSET_ICON_PATH = ASSETS_DIR / "icon.png"
ASSET_ICON_ANDROID_PATH = ASSETS_DIR / "icon_android.png"
ASSET_ICON_IOS_PATH = ASSETS_DIR / "icon_ios.png"
ASSET_ICON_WEB_PATH = ASSETS_DIR / "icon_web.png"
ASSET_ICON_WINDOWS_PATH = ASSETS_DIR / "icon_windows.png"
ASSET_FAVICON_PATH = ASSETS_DIR / "favicon.png"

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\BRUSHSCI.TTF"),
    Path(r"C:\Windows\Fonts\segoesc.ttf"),
    Path(r"C:\Windows\Fonts\seguisbi.ttf"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def lerp_color(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3))


def make_background(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (17, 18, 20, 255))
    pixels = image.load()
    top = (24, 24, 26)
    bottom = (32, 35, 38)
    center_x = size * 0.5
    center_y = size * 0.42
    max_radius = size * 0.82

    for y in range(size):
        vertical_t = y / max(1, size - 1)
        base = lerp_color(top, bottom, vertical_t)
        for x in range(size):
            dx = x - center_x
            dy = y - center_y
            radius_t = min(1.0, math.hypot(dx, dy) / max_radius)
            lift = 1.0 - radius_t
            pixels[x, y] = (
                min(255, int(base[0] + 16 * lift)),
                min(255, int(base[1] + 13 * lift)),
                min(255, int(base[2] + 10 * lift)),
                255,
            )

    vignette = Image.new("L", (size, size), 0)
    vignette_draw = ImageDraw.Draw(vignette)
    vignette_draw.ellipse(
        (-size * 0.15, -size * 0.05, size * 1.15, size * 1.25),
        fill=200,
    )
    vignette = ImageChops.invert(vignette).filter(ImageFilter.GaussianBlur(size // 7))
    image.putalpha(Image.new("L", (size, size), 255))
    shade = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shade.putalpha(vignette)
    return Image.alpha_composite(image, shade)


def draw_wave(draw: ImageDraw.ImageDraw, size: int, origin_y: float, amplitude: float, wavelength: float, phase: float, color: tuple[int, int, int, int], width: int, harmonic: float = 0.0) -> None:
    points: list[tuple[float, float]] = []
    for x in range(-size // 12, size + size // 12, 10):
        wave_y = origin_y + math.sin((x / wavelength) + phase) * amplitude
        if harmonic:
            wave_y += math.sin((x / (wavelength * 0.42)) + phase * 1.7) * amplitude * harmonic
        points.append((x, wave_y))
    draw.line(points, fill=color, width=width, joint="curve")


def add_scientific_background(base: Image.Image) -> Image.Image:
    size = base.size[0]
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    draw_wave(glow_draw, size, size * 0.31, size * 0.052, size * 0.112, 0.3, (132, 244, 194, 90), 16, harmonic=0.18)
    draw_wave(glow_draw, size, size * 0.43, size * 0.072, size * 0.16, 1.8, (80, 198, 255, 92), 14, harmonic=0.1)
    draw_wave(glow_draw, size, size * 0.57, size * 0.04, size * 0.11, 4.4, (201, 165, 108, 76), 10, harmonic=0.08)
    glow = glow.filter(ImageFilter.GaussianBlur(9))

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    draw_wave(overlay_draw, size, size * 0.31, size * 0.052, size * 0.112, 0.3, (170, 255, 220, 220), 5, harmonic=0.18)
    draw_wave(overlay_draw, size, size * 0.43, size * 0.072, size * 0.16, 1.8, (110, 214, 255, 210), 4, harmonic=0.1)
    draw_wave(overlay_draw, size, size * 0.57, size * 0.04, size * 0.11, 4.4, (219, 182, 126, 160), 3, harmonic=0.08)

    grid = Image.new("RGBA", base.size, (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    for y in (0.2, 0.4, 0.6):
        grid_draw.line(
            [(size * 0.12, size * y), (size * 0.9, size * y)],
            fill=(186, 198, 206, 30),
            width=2,
        )
    for x in (0.22, 0.4, 0.58, 0.76):
        grid_draw.line(
            [(size * x, size * 0.15), (size * x, size * 0.72)],
            fill=(186, 198, 206, 20),
            width=2,
        )

    scan = Image.new("RGBA", base.size, (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan)
    scan_y = size * 0.433
    scan_draw.line(
        [(size * 0.1, scan_y), (size * 0.92, scan_y)],
        fill=(154, 255, 212, 34),
        width=3,
    )

    composed = Image.alpha_composite(base, glow)
    composed = Image.alpha_composite(composed, grid)
    composed = Image.alpha_composite(composed, scan)
    return Image.alpha_composite(composed, overlay)


def render_script_glyph(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, fill: tuple[int, int, int, int], canvas_size: tuple[int, int], offset: tuple[int, int], shear: float = -0.18) -> Image.Image:
    temp = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp)
    temp_draw.text(offset, text, font=font, fill=fill)
    width, height = temp.size
    xshift = abs(shear) * height
    return temp.transform(
        (width, height),
        Image.Transform.AFFINE,
        (1, shear, -xshift * 0.35 if shear > 0 else xshift * 0.12, 0, 1, 0),
        Image.Resampling.BICUBIC,
    )


def add_fx_lettering(base: Image.Image) -> Image.Image:
    size = base.size[0]
    font_f = load_font(int(size * 0.62))
    font_x = load_font(int(size * 0.39))

    f_layer = render_script_glyph("f", font_f, (239, 243, 246, 255), base.size, (int(size * 0.11), int(size * 0.15)), shear=-0.1)
    x_layer = render_script_glyph("x", font_x, (239, 243, 246, 255), base.size, (int(size * 0.53), int(size * 0.48)), shear=-0.08)

    shadow = Image.new("RGBA", f_layer.size, (0, 0, 0, 0))
    shadow.alpha_composite(f_layer, (0, 0))
    shadow.alpha_composite(x_layer, (0, 0))
    shadow = shadow.filter(ImageFilter.GaussianBlur(13))
    shadow = ImageChops.offset(shadow, int(size * 0.008), int(size * 0.014))

    accent = Image.new("RGBA", f_layer.size, (0, 0, 0, 0))
    accent.alpha_composite(render_script_glyph("f", font_f, (161, 236, 213, 78), base.size, (int(size * 0.105), int(size * 0.145)), shear=-0.1))
    accent.alpha_composite(render_script_glyph("x", font_x, (196, 214, 224, 60), base.size, (int(size * 0.525), int(size * 0.475)), shear=-0.08))
    accent = accent.filter(ImageFilter.GaussianBlur(6))

    text_layer = Image.new("RGBA", f_layer.size, (0, 0, 0, 0))
    text_layer.alpha_composite(f_layer, (0, 0))
    text_layer.alpha_composite(x_layer, (0, 0))

    composed = Image.alpha_composite(base, shadow)
    composed = Image.alpha_composite(composed, accent)
    return Image.alpha_composite(composed, text_layer)


def add_border_and_glow(base: Image.Image) -> Image.Image:
    size = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    margin = int(size * 0.045)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=int(size * 0.18),
        outline=(155, 165, 170, 95),
        width=max(2, size // 96),
    )
    return Image.alpha_composite(base, overlay)


def render_icon(size: int) -> Image.Image:
    icon = make_background(size)
    icon = add_scientific_background(icon)
    icon = add_fx_lettering(icon)
    return add_border_and_glow(icon)


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    icon = render_icon(1024)
    icon.save(ICON_PATH)

    favicon = icon.resize((256, 256), Image.Resampling.LANCZOS)
    favicon.save(FAVICON_PATH)

    # Mirror the generated artwork into the root assets/ folder so Flet's
    # Android build pipeline picks up the custom icon instead of the default one.
    icon.save(ASSET_ICON_PATH)
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(ASSET_ICON_ANDROID_PATH)
    icon.resize((1024, 1024), Image.Resampling.LANCZOS).save(ASSET_ICON_IOS_PATH)
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(ASSET_ICON_WEB_PATH)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(ASSET_ICON_WINDOWS_PATH)
    favicon.save(ASSET_FAVICON_PATH)

    print(f"Wrote {ICON_PATH}")
    print(f"Wrote {FAVICON_PATH}")
    print(f"Wrote {ASSET_ICON_PATH}")
    print(f"Wrote {ASSET_ICON_ANDROID_PATH}")


if __name__ == "__main__":
    main()