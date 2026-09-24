"""Rebuild Lumquira assets from original, deterministic vector scenes.

Run: python scripts/generate-assets.py (requires Pillow).
SVG and raster exports share geometry, copy and colors. No remote assets or APIs
are used. Website public assets and this script are mirrored to a705 when present.
"""
from __future__ import annotations

import hashlib
import math
import shutil
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAPER = "#090b0f"
GREEN = "#b7f36b"
CORAL = "#ff756d"
BLUE = "#19232d"
INK = "#f2f4f7"
MUTED = "#84909d"
LINE = "#29313b"
WHITE = "#11151b"
PALE = "#161c23"


def font_path(kind):
    options = {
        "sans": ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "bold": ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "serif": ["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
        "mono": ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
    }
    for candidate in options[kind]:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("Install Arial/Georgia/Consolas or DejaVu fonts before regenerating assets.")


class Scene:
    def __init__(self, w, h, title, description, bg=PAPER):
        self.w, self.h, self.scale = w, h, 2
        self.im = Image.new("RGB", (w * self.scale, h * self.scale), bg)
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
                    f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
                    f'<rect width="{w}" height="{h}" fill="{bg}"/>']

    def box(self, x, y, w, h, fill, radius=0, stroke=None, sw=1):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
        s = self.scale
        self.draw.rounded_rectangle((x*s, y*s, (x+w)*s, (y+h)*s), radius=radius*s, fill=fill, outline=stroke, width=max(1, round(sw*s)))

    def circle(self, x, y, r, fill=None, stroke=None, sw=1):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
        s = self.scale
        self.draw.ellipse(((x-r)*s, (y-r)*s, (x+r)*s, (y+r)*s), fill=fill, outline=stroke, width=max(1, round(sw*s)))

    def line(self, points, color=GREEN, sw=2):
        pairs = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
        self.svg.append(f'<polyline points="{pairs}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')
        pts = [(round(x*self.scale), round(y*self.scale)) for x, y in points]
        self.draw.line(pts, fill=color, width=max(1, round(sw*self.scale)), joint="curve")
        for x, y in points:
            r = sw/2
            self.draw.ellipse(((x-r)*self.scale, (y-r)*self.scale, (x+r)*self.scale, (y+r)*self.scale), fill=color)

    def text(self, x, y, content, size=24, color=GREEN, kind="sans", align="left"):
        family = {"sans": "Arial, Helvetica, sans-serif", "bold": "Arial, Helvetica, sans-serif", "serif": "Georgia, serif", "mono": "Consolas, monospace"}[kind]
        anchor = {"left": "start", "center": "middle", "right": "end"}[align]
        weight = 700 if kind == "bold" else 400
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(content)}</text>')
        font = ImageFont.truetype(font_path(kind), round(size*self.scale))
        self.draw.text((round(x*self.scale), round(y*self.scale)), content, fill=color, font=font, anchor={"left": "ls", "center": "ms", "right": "rs"}[align])

    def mark(self, cx, cy, size, color=GREEN, accent=CORAL, background=None):
        if background:
            self.box(cx-size*.59, cy-size*.59, size*1.18, size*1.18, background, size*.24)
        self.circle(cx, cy, size*.39, None, color, size*.045)
        pulse = [(-.25,.015),(-.13,.015),(-.055,-.13),(.035,.17),(.12,-.04),(.19,.015),(.25,.015)]
        self.line([(cx+px*size, cy+py*size) for px, py in pulse], accent, size*.045)

    def grid(self, x, y, w, h, step=50, color=LINE):
        for offset in range(0, int(w)+1, step):
            self.line([(x+offset,y),(x+offset,y+h)], color, 1)
        for offset in range(0, int(h)+1, step):
            self.line([(x,y+offset),(x+w,y+offset)], color, 1)

    def save(self, path, vector=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        if vector:
            path.with_suffix(".svg").write_text("\n".join(self.svg+["</svg>"])+"\n", encoding="utf-8")
        if path.suffix == ".svg":
            return
        raster = self.im.resize((self.w,self.h), Image.Resampling.LANCZOS)
        if path.suffix == ".webp":
            raster.save(path, quality=92, method=6)
        elif path.suffix == ".jpg":
            raster.save(path, quality=94, subsampling=0, optimize=True)
        else:
            raster.save(path, optimize=True)


def research_sheet(s, x, y, w, h):
    s.box(x+16,y+18,w,h,PALE,22)
    s.box(x,y,w,h,WHITE,22,LINE,2)
    s.circle(x+35,y+38,5,CORAL)
    s.text(x+53,y+44,"LMQR / PROPOSED TOKEN",17,GREEN,"mono")
    s.line([(x+26,y+70),(x+w-26,y+70)],LINE,1)
    s.text(x+30,y+126,"See the move.",39,GREEN,"serif")
    s.text(x+30,y+173,"Test your assumptions.",29,GREEN,"serif")
    s.grid(x+30,y+210,w-60,h-310,50)
    pts=[(0,.66),(.1,.58),(.18,.67),(.3,.44),(.4,.50),(.5,.24),(.62,.35),(.74,.49),(.87,.25),(1,.30)]
    s.line([(x+38+a*(w-76),y+226+b*(h-335)) for a,b in pts],GREEN,5)
    s.circle(x+w-38,y+226+.30*(h-335),6,CORAL)
    s.text(x+30,y+h-47,"QUOTE FEED / MINT / STATUS",14,MUTED,"mono")
    s.text(x+30,y+h-23,"Illustrative chart. No forecast.",13,MUTED)


def hero():
    s=Scene(2000,1119,"Lumquira market terminal","Original coin pulse mark and Solana research notebook. Illustrative chart with no market forecast.")
    s.circle(1528,528,403,BLUE)
    s.circle(1528,528,354,None,GREEN,1.5)
    s.mark(1535,527,560,GREEN,CORAL)
    s.box(89,89,655,941,GREEN,38)
    s.text(140,154,"L U M Q U I R A",25,PAPER,"mono")
    s.text(138,270,"A clear",84,PAPER,"serif")
    s.text(138,371,"market desk",84,PAPER,"serif")
    s.text(138,472,"for a noisy chain.",66,PAPER,"serif")
    s.line([(143,550),(216,550),(250,498),(297,600),(337,530),(365,550),(436,550)],CORAL,8)
    s.text(140,844,"Observe. Question. Record.",27,PAPER)
    s.text(140,933,"SOLANA / TESTNET MINT",19,BLUE,"mono")
    research_sheet(s,810,577,578,448)
    s.box(1640,924,218,63,CORAL,32)
    s.text(1749,963,"YOUR ASSUMPTIONS",16,GREEN,"mono","center")
    return s


def token():
    s=Scene(1800,1209,"Lumquira LMQR snapshot","Original mark in a research field. A visual identity asset, not a coin or contract.")
    s.grid(100,105,1600,1000,100)
    s.circle(900,553,364,BLUE)
    s.circle(900,553,312,GREEN)
    s.mark(900,553,580,PAPER,CORAL)
    s.box(603,942,594,116,PAPER,58,GREEN,2)
    s.text(900,1014,"SOLANA / IN CONTEXT",34,GREEN,"mono","center")
    s.text(135,166,"01 / OBSERVE",23,GREEN,"mono")
    s.circle(1614,1001,38,CORAL)
    return s


def stack():
    s=Scene(1200,1200,"Lumquira research journal","Three offset notebook sheets for observation, assumptions and review.",BLUE)
    s.box(130,160,840,864,GREEN,26)
    s.box(164,125,840,864,CORAL,26)
    s.box(203,89,840,864,PAPER,26,GREEN,2)
    s.text(263,180,"RESEARCH JOURNAL",20,GREEN,"mono")
    s.mark(947,165,60)
    s.line([(263,224),(983,224)],LINE,2)
    s.text(263,328,"Write the reason.",57,GREEN,"serif")
    rows=[("01","What changed?"),("02","What am I assuming?"),("03","What would change my view?")]
    for i,(number,label) in enumerate(rows):
        y=432+i*155
        s.box(263,y-28,38,38,None,5,GREEN,2)
        s.text(328,y+1,label,25,GREEN)
        s.line([(328,y+49),(973,y+49)],LINE,2)
        s.text(976,y-29,number,15,MUTED,"mono","right")
    s.text(263,894,"LOCAL NOTES. CLEAR ASSUMPTIONS.",17,MUTED,"mono")
    return s


def network():
    s=Scene(1200,1200,"Lumquira scenario sandbox","User price assumptions and a local journal, with no live market feed.",PAPER)
    s.circle(980,162,152,BLUE)
    s.text(93,140,"THE RESEARCH LOOP",22,GREEN,"mono")
    s.text(89,229,"Test your",70,GREEN,"serif")
    s.text(89,311,"assumptions.",70,GREEN,"serif")
    cards=[(385,"01","Snapshot","Observe the source.",GREEN,PAPER),(628,"02","Scenario","Choose your assumptions.",BLUE,GREEN),(871,"03","Journal","Save what you learned.",CORAL,GREEN)]
    for y,no,title,body,fill,text in cards:
        s.box(93,y,1014,179,fill,22)
        s.circle(165,y+89,30,None,text,2)
        s.text(165,y+96,no,20,text,"mono","center")
        s.text(230,y+73,title,42,text,"serif")
        s.text(230,y+120,body,24,text)
        if y<871:
            s.line([(1037,y+191),(1037,y+221),(1027,y+211),(1037,y+221),(1047,y+211)],GREEN,3)
    s.text(94,1122,"A SCENARIO IS NOT A PREDICTION.",18,MUTED,"mono")
    return s


def social_frame(title, description, index):
    s=Scene(1600,900,title,description)
    s.mark(97,70,68)
    s.text(154,82,"Lumquira",37,GREEN,"bold")
    s.text(1531,79,index,15,MUTED,"mono","right")
    s.line([(65,132),(1535,132)],LINE,1.5)
    s.line([(65,803),(1535,803)],LINE,1.5)
    s.text(65,851,"INDEPENDENT SOLANA RESEARCH / LOCAL PREVIEW",15,MUTED,"mono")
    s.text(1535,851,"See the move. Test your assumptions.",19,GREEN,"serif","right")
    return s


def social_assets():
    logo=Scene(400,400,"Lumquira profile mark","Original coin pulse mark in a Solana lime field.",GREEN)
    logo.mark(200,200,302,PAPER,CORAL)
    banner=Scene(1500,500,"Lumquira research banner","See the move. Test your assumptions. Independent Solana research.",PAPER)
    banner.circle(1310,235,280,BLUE)
    banner.mark(1284,247,300,GREEN,CORAL)
    banner.mark(91,85,65)
    banner.text(147,101,"Lumquira",39,GREEN,"bold")
    banner.text(63,228,"See the move.",75,GREEN,"serif")
    banner.text(63,318,"Test your assumptions.",70,GREEN,"serif")
    banner.text(65,405,"Read the signal, keep the proof.",25,MUTED)
    banner.text(65,462,"INDEPENDENT SOLANA RESEARCH",15,GREEN,"mono")

    one=social_frame("Lumquira: Testnet mint, no live quote","The LMQR testnet mint is deployed; no verified market feed is connected.","01 / SNAPSHOT")
    one.text(63,266,"See the move.",85,GREEN,"serif")
    one.text(67,333,"Testnet mint deployed; quote feed offline.",29,MUTED)
    one.box(65,413,1470,310,GREEN,24)
    one.text(106,468,"LMQR / NO LIVE QUOTE",21,PAPER,"mono")
    for x,head,body in [(106,"Mint","Testnet verified"),(584,"Feed","Not wired"),(1062,"Scenario","User priced")]:
        one.text(x,561,head,49,PAPER,"serif")
        one.text(x,619,body,26,BLUE)
        if x>106: one.line([(x-32,505),(x-32,657)],"#547362",1.5)
    one.text(108,688,"CONTEXT BEFORE CONCLUSIONS",15,BLUE,"mono")

    two=social_frame("Lumquira: Test your assumptions","Scenario sandbox inputs are user assumptions, not forecasts or executable orders.","02 / SCENARIO")
    two.text(63,267,"Test your assumptions.",82,GREEN,"serif")
    two.text(67,334,"Your price, amount and move are assumptions only.",29,MUTED)
    two.box(65,412,945,308,BLUE,24)
    two.text(104,468,"SCENARIO SANDBOX",18,GREEN,"mono")
    for x,label,value in [(105,"REFERENCE PRICE","USD"),(556,"AMOUNT + MOVE","LMQR / %")]:
        two.text(x,526,label,16,GREEN,"mono")
        two.box(x,554,410,98,PAPER,12)
        two.line([(x+28,610),(x+190,610)],LINE,2)
        two.text(x+378,616,value,35,GREEN,"mono","right")
    two.box(1040,412,495,308,CORAL,24)
    two.text(1077,471,"KEEP THE BOUNDARY CLEAR",15,GREEN,"mono")
    two.text(1075,553,"A scenario.",49,GREEN,"serif")
    two.text(1075,612,"Not a prediction.",45,GREEN,"serif")
    two.text(1079,677,"No orders. No promised outcome.",20,GREEN)

    three=social_frame("Lumquira: Write the reason","A local research journal with the user's observation, assumptions and review checklist.","03 / JOURNAL")
    three.text(63,267,"Write the reason.",85,GREEN,"serif")
    three.text(67,334,"Keep a record of what you saw and assumed.",29,MUTED)
    three.box(65,411,1470,310,WHITE,24,LINE,1.5)
    three.text(109,470,"RESEARCH JOURNAL / YOUR NOTE",18,GREEN,"mono")
    three.text(105,538,"What would change my view?",44,GREEN,"serif")
    for i,label in enumerate(["Source checked","Assumptions recorded","Context reviewed"]):
        x=109+i*471
        three.box(x,602,30,30,None,5,GREEN,2)
        three.text(x+47,625,label,24,GREEN)
    three.line([(109,668),(1478,668)],LINE,2)

    four=social_frame("Lumquira: Context, assumptions, notes","The workflow separates public observations, user scenarios and local journal notes.","04 / METHOD")
    four.text(63,258,"Clear inputs.",81,GREEN,"serif")
    four.text(63,355,"Useful questions.",81,GREEN,"serif")
    data=[(65,GREEN,PAPER,"01","WATCHLIST","Market symbols","No quote feed."),(567,BLUE,GREEN,"02","ASSUMED","Your scenario","Quantity and price change."),(1069,CORAL,GREEN,"03","RECORDED","Your journal","Notes and review checklist.")]
    for x,fill,ink,no,label,heading,body in data:
        four.box(x,421,466,300,fill,24)
        four.text(x+31,466,no,20,ink,"mono")
        four.text(x+31,522,label,16,ink,"mono")
        four.text(x+29,584,heading,36,ink,"serif")
        four.text(x+31,644,body,22,ink)
    return {"twitter-logo":logo,"twitter-banner":banner,"post-01-signal":one,"post-02-risk":two,"post-03-journal":three,"post-04-research-preview":four}


def generate():
    script=Path(__file__).resolve()
    website=script.parents[1]
    if website.name=="a705" and (website.parent/"src"/"App.vue").exists():
        website=website.parent
    public=website/"public"
    twitter=website.parent/"twitter"
    public.mkdir(exist_ok=True)
    twitter.mkdir(exist_ok=True)

    favicon=Scene(64,64,"Lumquira","Original coin pulse mark.",GREEN)
    favicon.mark(32,32,47,PAPER,CORAL)
    favicon.save(public/"icon.svg",vector=True)
    apple=Scene(180,180,"Lumquira touch icon","Original coin pulse mark.",GREEN)
    apple.mark(90,90,132,PAPER,CORAL)
    apple.save(public/"apple-icon.png")
    for name,scene in [("hero",hero()),("token",token()),("stack",stack()),("network",network())]:
        scene.save(public/f"{name}.webp")
    for name,scene in social_assets().items():
        scene.save(twitter/f"{name}.jpg",vector=True)

    mirror=website/"a705"
    if mirror.is_dir():
        (mirror/"public").mkdir(exist_ok=True)
        (mirror/"scripts").mkdir(exist_ok=True)
        for name in ["icon.svg","apple-icon.png","hero.webp","token.webp","stack.webp","network.webp"]:
            shutil.copy2(public/name,mirror/"public"/name)
        destination=mirror/"scripts"/script.name
        if destination.resolve()!=script:
            shutil.copy2(script,destination)
        elif (website/"scripts"/script.name).resolve()!=script:
            shutil.copy2(script,website/"scripts"/script.name)

    print("Lumquira assets regenerated from deterministic SVG/Pillow scenes.")
    for directory in [public,twitter]:
        for path in sorted(directory.iterdir()):
            if path.suffix in [".jpg",".png",".webp"]:
                with Image.open(path) as im:
                    print(f"{path.relative_to(website.parent)}: {im.width}x{im.height} {im.mode} {path.stat().st_size:,} bytes")
    if mirror.is_dir():
        for name in ["icon.svg","apple-icon.png","hero.webp","token.webp","stack.webp","network.webp"]:
            assert hashlib.sha256((public/name).read_bytes()).digest()==hashlib.sha256((mirror/"public"/name).read_bytes()).digest(),name
        print("Mirror verification: all 6 public assets are byte-identical.")


if __name__=="__main__":
    generate()
