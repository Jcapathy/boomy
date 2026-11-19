"""Draws Boomy's icons from the mark's geometry (`app/src/components/mascot.tsx`): the app
icon source (src-tauri/icons/app-icon.png, which `tauri icon` turns into every size), About's
renditions of it (src/features/about/) and the tray's per-state images (src-tauri/icons/tray/). Run from app/:

    uv run --with pillow python scripts/draw-icons.py

The tray images are brand cyan on transparent: Windows shows them as they are, on light
taskbars and dark, and macOS, which uses them as template images, reads only their alpha.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ICONS = Path(__file__).resolve().parent.parent / "src-tauri" / "icons"
CYAN = (58, 232, 255, 255)
INK = (18, 18, 18, 255)
CLEAR = (0, 0, 0, 0)
SUPERSAMPLE = 8

# The mark in its 120 viewBox, as mascot.tsx draws it.
BODY = (58, 66, 40)  # cx, cy, r
SPARKS = ((94, 26, 7), (109, 42, 4.5), (80, 10, 4.5))
EYES = (45, 71)
EYE_Y = 64


def canvas(px: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (px * SUPERSAMPLE, px * SUPERSAMPLE), CLEAR)
    return image, ImageDraw.Draw(image)


def circle(draw: ImageDraw.ImageDraw, k: float, cx: float, cy: float, r: float, fill):
    draw.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), fill=fill)


def mark(draw: ImageDraw.ImageDraw, k: float, ox: float, oy: float, s: float, fill):
    """The body and sparks, at offset (ox, oy) and scale s within the 120 box."""
    cx, cy, r = BODY
    circle(draw, k, ox + cx * s, oy + cy * s, r * s, fill)
    for sx, sy, sr in SPARKS:
        circle(draw, k, ox + sx * s, oy + sy * s, sr * s, fill)


def eyes(draw: ImageDraw.ImageDraw, k: float, state: str, fill, ox=0.0, oy=0.0, s=1.0):
    """One state's eyes, as mascot.tsx draws them, thickened to read at tray size."""

    def at(x: float, y: float) -> tuple[float, float]:
        return (ox + x * s) * k, (oy + y * s) * k

    for ex in EYES:
        if state in ("idle", "listening", "thinking"):
            r = {"idle": 7.5, "listening": 10.5, "thinking": 6.5}[state]
            dx, dy = (5, -6) if state == "thinking" else (0, 0)
            circle(draw, k, ox + (ex + dx) * s, oy + (EYE_Y + dy) * s, r * s, fill)
        elif state == "speaking":
            (x0, y0), (x1, y1) = at(ex - 7, EYE_Y - 9.5), at(ex + 7, EYE_Y + 9.5)
            draw.ellipse((x0, y0, x1, y1), fill=fill)
        elif state in ("waking", "working"):
            # Closed lids while waking; half-open, busy eyes while an agent works.
            h = 3 if state == "waking" else 5.5
            (x0, y0), (x1, y1) = at(ex - 8.5, EYE_Y - h), at(ex + 8.5, EYE_Y + h)
            draw.rounded_rectangle((x0, y0, x1, y1), radius=h * s * k, fill=fill)
        elif state == "failed":
            d, w = 5.5, int(5 * s * k)
            draw.line((*at(ex - d, EYE_Y - d), *at(ex + d, EYE_Y + d)), fill=fill, width=w)
            draw.line((*at(ex + d, EYE_Y - d), *at(ex - d, EYE_Y + d)), fill=fill, width=w)


def finish(image: Image.Image, px: int, path: Path) -> None:
    image.resize((px, px), Image.Resampling.LANCZOS).save(path)
    print(f"wrote {path.relative_to(ICONS.parent.parent)}")


def app_icon() -> None:
    px = 1024
    image, draw = canvas(px)
    k = px * SUPERSAMPLE / 120
    draw.rounded_rectangle((0, 0, 120 * k, 120 * k), radius=26 * k, fill=INK)
    # The logo tile's inset (app-logo.tsx): the mark at 72%, centred.
    mark(draw, k, 16.8, 16.8, 0.72, CYAN)
    eyes(draw, k, "idle", INK, 16.8, 16.8, 0.72)
    finish(image, px, ICONS / "app-icon.png")


def client_logo() -> None:
    """The logo other services show for Boomy as a signed-in client (OAuth `logo_uri`):
    the mark in ink on cyan, full bleed, so a service's own round crop keeps it whole."""
    px = 512
    image, draw = canvas(px)
    k = px * SUPERSAMPLE / 120
    draw.rectangle((0, 0, 120 * k, 120 * k), fill=CYAN)
    mark(draw, k, 16.8, 16.8, 0.72, INK)
    eyes(draw, k, "idle", CYAN, 16.8, 16.8, 0.72)
    out = ICONS.parent.parent.parent / ".github" / "assets" / "logo.png"
    image.resize((px, px), Image.Resampling.LANCZOS).save(out)
    print("wrote .github/assets/logo.png")


def about_icons() -> None:
    """Settings, About: the app icon at 64 pt, 2x, for both themes."""
    about = ICONS.parent.parent / "src" / "features" / "about"
    icon = Image.open(ICONS / "app-icon.png").resize((128, 128), Image.Resampling.LANCZOS)
    for theme in ("light", "dark"):
        icon.save(about / f"app-icon-{theme}@2x.png")
        print(f"wrote src/features/about/app-icon-{theme}@2x.png")


def tray_icons() -> None:
    px = 36
    for state in ("idle", "waking", "listening", "thinking", "speaking", "working", "failed"):
        image, draw = canvas(px)
        k = px * SUPERSAMPLE / 120
        # Fill the tray's square: the mark spans about 8 to 114, so a little larger.
        mark(draw, k, -4, -1, 1.08, CYAN)
        eyes(draw, k, state, CLEAR, -4, -1, 1.08)
        finish(image, px, ICONS / "tray" / f"{state}.png")


if __name__ == "__main__":
    app_icon()
    about_icons()
    client_logo()
    tray_icons()
