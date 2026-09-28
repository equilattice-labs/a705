"""Generate Orbinza's deterministic identity and product visual assets.

The scenes are intentionally app-like: dark market surfaces, compact terminal
labels and cyan/amber/magenta state colors. They are generated locally so the
website can reproduce the same assets without a remote image dependency.
Run from ``website`` with ``python scripts/generate-assets.py``.
"""
from __future__ import annotations

import hashlib
import shutil
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = "#090d14"
SURFACE = "#101925"
SURFACE_2 = "#152235"
CYAN = "#28d7e8"
CYAN_DARK = "#126b80"
AMBER = "#f4b84a"
MAGENTA = "#f05bbb"
TEXT = "#eef6ff"
MUTED = "#8294ab"
GRID = "#203247"


def font_path(kind: str) -> str:
    options = {
        "sans": ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "bold": ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "mono": ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    }
    for candidate in options[kind]:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("Install Arial/Consolas or DejaVu fonts before regenerating assets.")


class Scene:
    def __init__(self, w: int, h: int, title: str, description: str, bg: str = BG):
        self.w, self.h, self.scale = w, h, 2
        self.im = Image.new("RGB", (w * self.scale, h * self.scale), bg)
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
            f'<rect width="{w}" height="{h}" fill="{bg}"/>',
        ]

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1, radius=0):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        s = self.scale
        self.draw.rounded_rectangle((x*s, y*s, (x+w)*s, (y+h)*s), radius=radius*s, fill=None if fill == "none" else fill, outline=None if stroke == "none" else stroke, width=max(1, round(sw*s)))

    def circle(self, cx, cy, radius, fill="none", stroke="none", sw=1):
        self.svg.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        s = self.scale
        self.draw.ellipse(((cx-radius)*s, (cy-radius)*s, (cx+radius)*s, (cy+radius)*s), fill=None if fill == "none" else fill, outline=None if stroke == "none" else stroke, width=max(1, round(sw*s)))

    def line(self, points, color=CYAN, sw=2):
        pairs = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        self.svg.append(f'<polyline points="{pairs}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')
        pts = [(round(x*self.scale), round(y*self.scale)) for x, y in points]
        self.draw.line(pts, fill=color, width=max(1, round(sw*self.scale)), joint="curve")

    def text(self, x, y, content, size=24, color=TEXT, kind="sans", align="left"):
        family = "Consolas, monospace" if kind == "mono" else "Arial, Helvetica, sans-serif"
        anchor = {"left": "start", "center": "middle", "right": "end"}[align]
        weight = 700 if kind == "bold" else 400
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(content)}</text>')
        font = ImageFont.truetype(font_path(kind), round(size*self.scale))
        self.draw.text((round(x*self.scale), round(y*self.scale)), content, fill=color, font=font, anchor={"left": "ls", "center": "ms", "right": "rs"}[align])

    def grid(self, x, y, w, h, step=50, color=GRID):
        for offset in range(0, int(w)+1, step):
            self.line([(x+offset, y), (x+offset, y+h)], color, 1)
        for offset in range(0, int(h)+1, step):
            self.line([(x, y+offset), (x+w, y+offset)], color, 1)

    def mark(self, cx, cy, size, background=None):
        """Signal-orbit mark: two orbital rings and a stepped price pulse."""
        if background:
            self.circle(cx, cy, size*.53, background)
        self.circle(cx, cy, size*.43, "none", CYAN, max(2, size*.022))
        self.circle(cx, cy, size*.27, "none", AMBER, max(2, size*.018))
        pulse = [(-.31, .07), (-.18, .07), (-.08, -.13), (.02, .14), (.12, -.06), (.21, .01), (.31, .01)]
        self.line([(cx+px*size, cy+py*size) for px, py in pulse], MAGENTA, max(2, size*.035))
        self.circle(cx+size*.12, cy-size*.06, size*.035, AMBER)
        self.circle(cx-size*.08, cy+size*.14, size*.027, CYAN)

    def save(self, path: Path, vector=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        if vector:
            path.with_suffix(".svg").write_text("\n".join(self.svg + ["</svg>"]) + "\n", encoding="utf-8")
        if path.suffix == ".svg":
            return
        raster = self.im.resize((self.w, self.h), Image.Resampling.LANCZOS)
        if path.suffix == ".webp":
            raster.save(path, quality=94, method=6)
        elif path.suffix == ".jpg":
            raster.save(path, quality=95, subsampling=0, optimize=True)
        else:
            raster.save(path, optimize=True)


def terminal_header(s: Scene, label: str, right: str = "SOLANA / PREVIEW"):
    s.text(64, 57, "ORBINZA", 22, CYAN, "bold")
    s.text(64, 84, label, 13, MUTED, "mono")
    s.text(s.w-64, 57, right, 13, AMBER, "mono", "right")
    s.line([(64, 111), (s.w-64, 111)], GRID, 1)


def hero():
    s = Scene(2000, 1119, "Orbinza market terminal", "Orbinza Solana market terminal visual with signal, scenario and journal surfaces.")
    s.grid(72, 150, 1856, 850, 80)
    terminal_header(s, "MARKETS / SIGNAL DESK", "OBZA / SOLANA")
    s.text(92, 260, "Orbit the", 88, TEXT, "bold")
    s.text(92, 355, "signal.", 88, CYAN, "bold")
    s.text(92, 438, "Own the scenario.", 44, AMBER, "bold")
    s.text(94, 493, "Watchlists, payoff paths and a local thesis.", 23, MUTED)
    s.rect(92, 566, 520, 238, SURFACE, GRID, 1, 8)
    s.text(124, 609, "OBZA / MARKET UNIT", 15, MUTED, "mono")
    s.text(124, 681, "$1.00", 57, TEXT, "bold")
    s.text(453, 681, "+5.8%", 25, CYAN, "mono", "right")
    s.line([(124, 724), (552, 724)], GRID, 1)
    s.text(124, 764, "MODEL QUOTE / 30D EPOCH", 13, MUTED, "mono")
    s.mark(1542, 477, 610, SURFACE_2)
    s.circle(1542, 477, 345, "none", CYAN_DARK, 2)
    s.rect(1010, 682, 725, 254, BG, GRID, 1, 8)
    s.text(1040, 726, "SCENARIO PATH / USER PRICED", 14, CYAN, "mono")
    points = [(1045, 861), (1120, 828), (1194, 842), (1277, 783), (1360, 808), (1442, 751), (1523, 779), (1603, 712), (1694, 732)]
    s.line(points, CYAN, 5)
    s.line([(1045, 875), (1694, 875)], GRID, 1)
    s.circle(1603, 712, 7, AMBER)
    s.text(1040, 909, "REFERENCE  $1.00", 13, MUTED, "mono")
    s.text(1695, 909, "NO LIVE FEED", 13, MAGENTA, "mono", "right")
    return s


def token():
    s = Scene(1800, 1209, "Orbinza OBZA market card", "OBZA signal-orbit mark on a Solana market terminal grid.")
    s.grid(86, 112, 1628, 1005, 80)
    terminal_header(s, "ASSET / OBZA", "SOLANA / CONTEXT")
    s.text(118, 233, "OBZA", 26, CYAN, "bold")
    s.text(118, 270, "Orbinza market unit", 20, MUTED)
    s.text(118, 418, "SIGNAL", 15, MUTED, "mono")
    s.text(118, 478, "+5.8%", 52, CYAN, "bold")
    s.text(118, 514, "model move / illustrative", 15, MUTED, "mono")
    s.mark(892, 525, 505, SURFACE_2)
    s.circle(892, 525, 296, "none", CYAN_DARK, 2)
    s.rect(118, 825, 1564, 155, SURFACE, GRID, 1, 8)
    s.text(150, 872, "INCOME", 15, AMBER, "mono")
    s.text(150, 928, "$0.95", 37, TEXT, "bold")
    s.text(600, 872, "UPSIDE", 15, MAGENTA, "mono")
    s.text(600, 928, "$0.05", 37, TEXT, "bold")
    s.text(1050, 872, "EPOCH", 15, MUTED, "mono")
    s.text(1050, 928, "30D", 37, TEXT, "bold")
    s.text(1650, 872, "PREVIEW", 15, CYAN, "mono", "right")
    s.text(1650, 928, "NO CA", 37, MAGENTA, "bold", "right")
    s.circle(1636, 260, 11, AMBER)
    s.text(1664, 267, "USER ASSUMPTION", 14, MUTED, "mono")
    return s


def stack():
    s = Scene(1200, 1200, "Orbinza signal stack", "Three terminal surfaces for observe, model and journal.", BG)
    terminal_header(s, "WORKFLOW / THREE SURFACES")
    s.text(82, 205, "From signal", 53, TEXT, "bold")
    s.text(82, 266, "to scenario.", 53, CYAN, "bold")
    rows = [(370, "01", "OBSERVE", "Read the market surface.", CYAN), (555, "02", "MODEL", "Move the price slider.", AMBER), (740, "03", "JOURNAL", "Keep the reason local.", MAGENTA)]
    for y, number, title, body, color in rows:
        s.rect(82, y, 1036, 140, SURFACE, GRID, 1, 8)
        s.circle(144, y+70, 28, BG, color, 2)
        s.text(144, y+77, number, 15, color, "mono", "center")
        s.text(205, y+62, title, 29, color, "bold")
        s.text(205, y+99, body, 18, MUTED)
        s.text(1047, y+79, "ACTIVE", 13, color, "mono", "right")
        if y < 740:
            s.line([(1046, y+150), (1046, y+175)], color, 2)
            s.line([(1038, y+166), (1046, y+175), (1054, y+166)], color, 2)
    s.rect(82, 1004, 1036, 75, BG, GRID, 1, 6)
    s.text(112, 1050, "SOLANA / LOCAL PREVIEW / NO EXECUTION", 14, MUTED, "mono")
    s.text(1086, 1050, "OBZA", 14, CYAN, "mono", "right")
    return s


def network():
    s = Scene(1200, 1200, "Orbinza Solana workflow", "A compact market workflow from watchlist to payoff model and local journal.")
    terminal_header(s, "SOLANA / WORKFLOW", "OBZA / PREVIEW")
    s.text(82, 196, "Scan. Model.", 54, TEXT, "bold")
    s.text(82, 255, "Keep the proof.", 54, CYAN, "bold")
    s.text(84, 302, "A working surface for user-priced crypto scenarios.", 18, MUTED)
    nodes = [(380, "01", "WATCHLIST", "Observe the signal", CYAN), (574, "02", "PAYOFF", "Set the boundary", AMBER), (768, "03", "JOURNAL", "Export your view", MAGENTA)]
    for y, number, title, body, color in nodes:
        s.rect(82, y, 1036, 138, SURFACE, GRID, 1, 8)
        s.circle(144, y+69, 29, BG, color, 2)
        s.text(144, y+76, number, 15, color, "mono", "center")
        s.text(205, y+59, title, 28, color, "bold")
        s.text(205, y+97, body, 18, TEXT)
        s.text(1049, y+77, "OPEN", 13, color, "mono", "right")
        if y < 768:
            s.line([(1048, y+147), (1048, y+174)], GRID, 2)
            s.line([(1039, y+165), (1048, y+174), (1057, y+165)], GRID, 2)
    s.text(84, 1056, "SCENARIOS ARE ASSUMPTIONS, NOT PREDICTIONS.", 14, MUTED, "mono")
    s.mark(1017, 207, 142, SURFACE_2)
    return s


def og_image():
    s = Scene(1200, 630, "Orbinza Solana market terminal", "Orbinza market terminal preview for Solana.")
    s.grid(42, 110, 1116, 464, 56)
    terminal_header(s, "MARKETS / OG CARD", "SOLANA / OBZA")
    s.text(64, 244, "ORBIT THE SIGNAL.", 58, TEXT, "bold")
    s.text(64, 312, "OWN THE SCENARIO.", 52, CYAN, "bold")
    s.text(66, 363, "Signals / payoff paths / local journal", 21, MUTED)
    s.rect(64, 416, 682, 104, SURFACE, GRID, 1, 7)
    s.text(90, 455, "OBZA", 17, CYAN, "bold")
    s.text(90, 490, "USER-PRICED / NO LIVE QUOTE", 14, MUTED, "mono")
    s.text(698, 487, "+5.8%", 25, AMBER, "mono", "right")
    s.mark(1011, 321, 260, SURFACE_2)
    s.text(66, 580, "ORBINZA / SOLANA MARKET APP PREVIEW", 14, MUTED, "mono")
    return s


def identity_assets(public: Path):
    icon = Scene(64, 64, "Orbinza icon", "Signal-orbit mark.", BG)
    icon.mark(32, 32, 48, SURFACE_2)
    icon.save(public / "icon.svg", vector=True)
    apple = Scene(180, 180, "Orbinza app icon", "Signal-orbit mark.", BG)
    apple.mark(90, 90, 138, SURFACE_2)
    apple.save(public / "apple-icon.png")


def generate():
    script = Path(__file__).resolve()
    website = script.parents[1]
    public = website / "public"
    public.mkdir(exist_ok=True)
    identity_assets(public)
    for name, scene in [("hero", hero()), ("token", token()), ("stack", stack()), ("network", network()), ("og-image", og_image())]:
        scene.save(public / f"{name}.webp" if name != "og-image" else public / "og-image.jpg", vector=True)

    mirror = website / "a705"
    if mirror.is_dir():
        (mirror / "public").mkdir(exist_ok=True)
        (mirror / "scripts").mkdir(exist_ok=True)
        for name in ["icon.svg", "apple-icon.png", "hero.webp", "hero.svg", "token.webp", "token.svg", "stack.webp", "stack.svg", "network.webp", "network.svg", "og-image.jpg", "og-image.svg"]:
            shutil.copy2(public / name, mirror / "public" / name)
        destination = mirror / "scripts" / script.name
        if destination.resolve() != script:
            shutil.copy2(script, destination)

    print("Orbinza terminal assets regenerated.")
    for path in sorted(public.iterdir()):
        if path.suffix in [".jpg", ".png", ".webp"]:
            with Image.open(path) as im:
                print(f"{path.relative_to(website.parent)}: {im.width}x{im.height} {im.mode} {path.stat().st_size:,} bytes")
    if mirror.is_dir():
        for name in ["icon.svg", "apple-icon.png", "hero.webp", "hero.svg", "token.webp", "token.svg", "stack.webp", "stack.svg", "network.webp", "network.svg", "og-image.jpg", "og-image.svg"]:
            assert hashlib.sha256((public / name).read_bytes()).digest() == hashlib.sha256((mirror / "public" / name).read_bytes()).digest(), name
        print("Mirror verification: public assets are byte-identical.")


if __name__ == "__main__":
    generate()
