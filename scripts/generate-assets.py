"""Generate editable Decisift SVGs and exact-size JPEGs without network requests.

Run: python website/scripts/generate-assets.py
Requires: pip install -r website/scripts/requirements-assets.txt
Uses local Chrome/Edge, DECISIFT_BROWSER_PATH, or Playwright's Chromium.
"""
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC, TWITTER = ROOT / 'website/public', ROOT / 'twitter'
SOCIAL = PUBLIC / 'social'
PAPER, FOREST, ORANGE = '#F6F5F0', '#183B35', '#ED7147'
SAGE, INK, MUTED, LINE = '#E7EDE6', '#20332E', '#60716A', '#CED7CE'

def text(x, y, value, size=24, fill=INK, weight=400, spacing=0):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}">{value}</text>'

def rect(x, y, w, h, fill, r=0, stroke=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"' + (f' stroke="{stroke}"' if stroke else '') + '/>'

def line(x, y, x2, y2, color=LINE, width=1):
    return f'<path d="M{x} {y}L{x2} {y2}" stroke="{color}" stroke-width="{width}"/>'

def mark(x=0, y=0, size=256, tile=True):
    # Original geometric D with three progressively sifted evidence lines.
    p = PAPER if tile else FOREST
    body = rect(0, 0, 256, 256, FOREST, 58) if tile else ''
    body += f'<path fill="{p}" fill-rule="evenodd" d="M67 43H126C180 43 215 77 215 128S180 213 126 213H67V43ZM101 77V179H126C160 179 181 160 181 128S160 77 126 77H101Z"/>'
    body += f'<path d="M39 97H128M39 159H108" stroke="{p}" stroke-width="12" stroke-linecap="round"/>'
    body += f'<path d="M39 128H145" stroke="{ORANGE}" stroke-width="13" stroke-linecap="round"/>'
    return f'<g transform="translate({x} {y}) scale({size / 256})">{body}</g>'

def svg(w, h, title, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">Original Decisift artwork. Research preview with illustrative data; no live trading.</desc>{body}</svg>\n'

def lockup(x, y, size=48):
    return mark(x, y, size, False) + text(x + size + 12, y + size * .77, 'Decisift', size * .76, FOREST, 700, -.8)

def base(n, label):
    return rect(0, 0, 1600, 900, PAPER) + lockup(72, 57, 53) + text(1488, 94, f'0{n}', 24, MUTED) + line(76, 147, 1524, 147) + text(80, 210, label.upper(), 17, MUTED, 700, 2.5)

def footer():
    return line(76, 790, 1524, 790) + text(80, 844, 'Sift the noise. Decide with clarity.', 22, FOREST) + text(1080, 844, 'decisift.xyz  /  @decisift', 20, MUTED)

def evidence(x=882, y=219, scale=1):
    b = rect(0, 0, 638, 505, SAGE, 18) + text(34, 47, 'FROM SOURCES TO A CLEARER VIEW', 15, MUTED, 700, 1.4)
    for i, label in enumerate(['Source', 'Context', 'Counter-case']):
        cy = 94 + i * 96
        b += rect(32, cy, 270, 70, PAPER, 8, LINE) + text(52, cy + 29, f'0{i+1}', 13, MUTED, 700, 1.3) + text(88, cy + 44, label, 23, FOREST, 600) + line(302, cy + 35, 364, cy + 35, '#A9BAB0', 2)
    b += line(364, 129, 364, 321, '#A9BAB0', 2) + line(364, 225, 430, 225, FOREST, 2)
    b += f'<path d="M422 218L430 225L422 232" fill="none" stroke="{FOREST}" stroke-width="2"/>'
    b += mark(449, 175, 104) + text(425, 322, 'A working thesis', 18, FOREST, 600)
    b += line(34, 394, 604, 394) + text(34, 438, 'Inspect the evidence.', 22, FOREST, 600) + text(34, 471, 'Keep the uncertainty visible.', 19, MUTED)
    return f'<g transform="translate({x} {y}) scale({scale})">{b}</g>'

def post_signal():
    b = base(1, 'The research principle') + text(76, 330, 'Follow the', 82, FOREST, 700, -3) + text(76, 424, 'evidence.', 82, FOREST, 700, -3)
    b += text(81, 496, 'A signal needs a source.', 28) + text(81, 539, 'A thesis needs a counter-case.', 28) + text(81, 679, '01  READ     02  QUESTION     03  DECIDE', 16, MUTED, 700, 1)
    return svg(1600, 900, 'Decisift — Follow the evidence', b + evidence() + footer())

def post_risk():
    b = base(2, 'Make uncertainty useful') + text(76, 330, 'A clear thesis', 77, FOREST, 700, -3) + text(76, 423, 'has limits.', 82, FOREST, 700, -3)
    b += text(81, 500, 'Test the downside before', 28) + text(81, 542, 'taking a position.', 28) + text(81, 679, 'SET LIMITS. REVISIT YOUR ASSUMPTIONS.', 16, MUTED, 700, 1)
    b += rect(882, 219, 638, 505, SAGE, 18) + text(916, 267, 'THREE WAYS THE THESIS COULD MOVE', 15, MUTED, 700, 1.3)
    for cy, label, endpoint, color in [(338, 'Upside case', 1400, FOREST), (434, 'Base case', 1280, FOREST), (530, 'Downside case', 1120, '#B24829')]:
        b += text(916, cy, label, 20, FOREST, 600) + line(916, cy+28, 1483, cy+28, '#BCCABD', 4) + line(1062, cy+28, endpoint, cy+28, color, 8)
        b += f'<circle cx="{endpoint}" cy="{cy+28}" r="8" fill="{color}"/>'
    b += line(916, 615, 1485, 615) + text(916, 658, 'Know what would change your mind.', 22, FOREST, 600) + text(916, 691, 'Illustrative scenarios · No performance forecast', 16, MUTED)
    return svg(1600, 900, 'Decisift — A clear thesis has limits', b + footer())

def post_journal():
    b = base(3, 'Build a decision practice') + text(76, 330, 'Keep', 82, FOREST, 700, -3) + text(76, 424, 'the why.', 82, FOREST, 700, -3)
    b += text(81, 500, 'Write the thesis. Log the evidence.', 27) + text(81, 542, 'Return with a clearer perspective.', 27) + text(81, 679, 'GOOD RESEARCH LEAVES A USEFUL TRAIL.', 16, MUTED, 700, 1)
    b += rect(882, 219, 638, 505, SAGE, 18) + rect(922, 249, 558, 443, PAPER, 7, LINE) + text(954, 294, 'RESEARCH NOTE', 14, MUTED, 700, 2) + text(1396, 294, '01', 16, MUTED)
    for cy, label, copy in [(353, 'Thesis', 'What do I believe?'), (459, 'Evidence', 'Which sources support it?'), (565, 'Counter-case', 'What would prove me wrong?')]:
        b += line(954, cy-27, 1446, cy-27) + rect(954, cy-6, 6, 39, ORANGE, 2) + text(977, cy+7, label, 18, FOREST, 700) + text(977, cy+41, copy, 21, MUTED)
    b += text(954, 662, 'A record to revisit, not a promise of returns.', 17, MUTED)
    return svg(1600, 900, 'Decisift — Keep the why', b + footer())

def post_preview():
    b = base(4, 'The research preview') + text(76, 330, 'Read.', 88, FOREST, 700, -3) + text(76, 430, 'Test. Decide.', 88, FOREST, 700, -3)
    b += text(81, 511, 'The Decisift research preview is open.', 26) + text(81, 553, 'Explore the workflow. Examine the assumptions.', 22, MUTED)
    b += rect(80, 628, 360, 66, FOREST, 8) + text(104, 670, 'Explore the research preview', 21, PAPER, 600) + rect(882, 219, 638, 505, FOREST, 18)
    for i, (label, detail) in enumerate([('Read', 'Gather context and source evidence'), ('Test', 'Challenge the thesis and its limits'), ('Decide', 'Record the reasoning behind a choice')]):
        cy = 313 + i * 127
        b += text(920, cy, f'0{i+1}', 19, '#A9BEB4') + text(984, cy, label, 39, PAPER, 600, -1) + text(984, cy+39, detail, 19, '#CBD8CF')
        if i < 2: b += line(920, cy+69, 1480, cy+69, '#416056')
    b += text(920, 689, 'ILLUSTRATIVE DATA · NO LIVE TRADING', 15, '#CBD8CF', 700, 1)
    return svg(1600, 900, 'Decisift — Read. Test. Decide.', b + footer())

def banner():
    b = rect(0, 0, 1500, 500, PAPER) + lockup(76, 48, 52) + text(77, 202, 'Sift the noise.', 72, FOREST, 700, -3) + text(77, 287, 'Decide with clarity.', 72, FOREST, 700, -3)
    b += text(82, 353, 'A more considered view of the market.', 24, MUTED) + line(76, 405, 852, 405) + text(440, 453, 'RESEARCH PREVIEW  /  decisift.xyz', 16, MUTED, 700, 1)
    return svg(1500, 500, 'Decisift — Sift the noise. Decide with clarity.', b + rect(917, 0, 583, 500, SAGE) + evidence(955, 43, .78))

def og_card():
    b = rect(0, 0, 1200, 630, PAPER) + lockup(58, 48, 52) + text(57, 236, 'Sift the noise.', 65, FOREST, 700, -2.5) + text(57, 314, 'Decide with', 65, FOREST, 700, -2.5) + text(57, 392, 'clarity.', 65, FOREST, 700, -2.5)
    b += text(62, 459, 'Research. Risk. Reasoning.', 23, MUTED) + evidence(643, 144, .78) + line(60, 550, 1140, 550) + text(62, 592, 'DECISIFT / RESEARCH PREVIEW', 15, MUTED, 700, 1.5) + text(998, 592, 'decisift.xyz', 19, FOREST)
    return svg(1200, 630, 'Decisift research preview', b)

def find_browser():
    configured = os.environ.get('DECISIFT_BROWSER_PATH')
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_file(): raise FileNotFoundError(f'DECISIFT_BROWSER_PATH does not exist: {path}')
        return str(path)
    for path in [shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser'), r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if path and Path(path).is_file(): return path
    return None

def main():
    for directory in (PUBLIC, SOCIAL, TWITTER): directory.mkdir(parents=True, exist_ok=True)
    (PUBLIC / 'logo-mark.svg').write_text(svg(256, 256, 'Decisift', mark()), encoding='utf-8')
    (PUBLIC / 'logo-lockup.svg').write_text(svg(550, 128, 'Decisift', lockup(2, 8, 112)), encoding='utf-8')
    avatar = svg(400, 400, 'Decisift profile image', rect(0, 0, 400, 400, FOREST) + mark(56, 56, 288))
    assets = {'twitter-logo': (avatar, 400, 400), 'twitter-banner': (banner(), 1500, 500), 'post-01-signal': (post_signal(), 1600, 900), 'post-02-risk': (post_risk(), 1600, 900), 'post-03-journal': (post_journal(), 1600, 900), 'post-04-research-preview': (post_preview(), 1600, 900), 'og-card': (og_card(), 1200, 630)}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=find_browser())
        for name, (source, width, height) in assets.items():
            path = (SOCIAL if name == 'og-card' else TWITTER) / f'{name}.svg'
            path.write_text(source, encoding='utf-8')
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            page.set_content(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden}}svg{{display:block}}</style></head><body>{source}</body></html>')
            page.evaluate('document.fonts.ready')
            page.screenshot(path=str(path.with_suffix('.jpg')), type='jpeg', quality=95)
            page.close()
            if name != 'og-card':
                for ext in ('svg', 'jpg'): shutil.copyfile(path.with_suffix(f'.{ext}'), SOCIAL / f'{name}.{ext}')
            print(f'Generated {name}: {width} x {height}')
        browser.close()
    # Preserve inbound links while replacing the obsolete launch assertion.
    for directory in (TWITTER, SOCIAL):
        for ext in ('svg', 'jpg'): shutil.copyfile(directory / f'post-04-research-preview.{ext}', directory / f'post-04-contracts-open-tonight.{ext}')
    shutil.copyfile(TWITTER / 'twitter-logo.svg', PUBLIC / 'twitter-logo.svg')

if __name__ == '__main__': main()
