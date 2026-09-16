"""Render the Folivect identity and social kit as editable SVG and exact-size JPEG.

Run: python website/scripts/generate-assets.py
Requires: pip install -r website/scripts/requirements-assets.txt
Uses local Chrome/Edge, FOLIVECT_BROWSER_PATH, or Playwright's Chromium.
"""
import os
from pathlib import Path
import shutil
from xml.sax.saxutils import escape
from playwright.sync_api import sync_playwright

WEBSITE = Path(__file__).resolve().parents[1]
ROOT = next((path for path in WEBSITE.parents if (path / 'BRAND_SELECTION.md').is_file()), WEBSITE)
PUBLIC, TWITTER = WEBSITE / 'public', ROOT / 'twitter'
SOCIAL = PUBLIC / 'social'
BRAND, DOMAIN, HANDLE = 'Folivect', 'folivect.xyz', '@folivect'
TAGLINE = 'See the case. Own the decision.'
BG, CARD, WHITE = '#101315', '#191E22', '#EEF2ED'
MUTED, LINE, GREEN, VIOLET = '#A7B2AB', '#344039', '#CEF576', '#C4B5FD'


def text(x, y, value, size=24, fill=WHITE, weight=400, spacing=0, mono=False):
    family = 'Consolas, monospace' if mono else 'Arial, Helvetica, sans-serif'
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}">{escape(value)}</text>'


def rect(x, y, width, height, fill, radius=0, stroke=None):
    border = f' stroke="{stroke}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"{border}/>'


def line(x1, y1, x2, y2, color=LINE, width=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="{width}"/>'


def arrow(x, y, size=32, color=GREEN, width=3):
    return f'<path d="M{x} {y + size}L{x + size} {y}M{x} {y}H{x + size}V{y + size}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def mark(x=0, y=0, size=256, tile=True, light=False):
    # A continuous F and an angular V form a compact directional monogram.
    first, second = (BG, BG) if light else (GREEN, VIOLET)
    body = rect(0, 0, 256, 256, GREEN if light else BG, 36) if tile else ''
    body += f'<path d="M29 49H127V80H61V112H114V143H61V207H29Z" fill="{first}"/>'
    body += f'<path d="M114 49H145L171 157L197 49H228L187 207H155Z" fill="{second}"/>'
    return f'<g transform="translate({x} {y}) scale({size / 256})">{body}</g>'


def svg(width, height, title, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">Original Folivect artwork. A research preview with sample data, local decision records, and no trade execution.</desc>{body}</svg>\n'


def lockup(x, y, size=52, light=False):
    return mark(x, y, size, False, light) + text(x + size + 13, y + size * .79, BRAND, size * .8, BG if light else WHITE, 700, -1.2)


def topbar(index, label, light=False):
    ink, rule = (BG, '#718647') if light else (MUTED, LINE)
    return lockup(66, 46, 56, light) + text(1090, 82, label.upper(), 16, ink, 400, 1, True) + text(1482, 84, f'0{index}', 21, ink, 500, 0, True) + line(70, 126, 1530, 126, rule)


def footer(light=False):
    ink, rule = (BG, '#718647') if light else (MUTED, LINE)
    return line(70, 804, 1530, 804, rule) + text(72, 853, 'RESEARCH TOOLS / YOUR JUDGMENT', 16, ink, 400, 1, True) + text(1130, 853, f'{DOMAIN}  /  {HANDLE}', 19, ink)


def vector_field(x=0, y=0, width=510, height=500):
    body = ''
    for gx in range(0, width + 1, 34):
        for gy in range(0, height + 1, 34):
            body += f'<circle cx="{gx}" cy="{gy}" r="1" fill="{LINE}"/>'
    body += f'<path d="M38 {height - 75}L{width - 65} 70M{width - 203} 70H{width - 65}V208" fill="none" stroke="{GREEN}" stroke-width="38"/>'
    body += f'<path d="M20 {height - 13}L{width - 150} 170" fill="none" stroke="{VIOLET}" stroke-width="2"/>'
    body += f'<circle cx="38" cy="{height - 75}" r="10" fill="{BG}" stroke="{GREEN}" stroke-width="3"/>'
    return f'<g transform="translate({x} {y})">{body}</g>'


def post_signal():
    body = rect(0, 0, 1600, 900, BG) + topbar(1, 'Build the case')
    body += text(68, 257, 'A thesis is a starting point.', 82, WHITE, 700, -3)
    body += text(71, 322, 'Give every observation a source. Give every case a challenge.', 28, MUTED)
    cells = [('01', 'Evidence', 'What can you inspect?', 'Start with the source.', GREEN), ('02', 'Interpretation', 'What does it suggest?', 'Separate the fact from the view.', WHITE), ('03', 'Counter-case', 'What could change it?', 'Make the uncertainty visible.', VIOLET)]
    for i, (n, label, question, detail, accent) in enumerate(cells):
        x = 70 + i * 491
        body += rect(x, 410, 478, 327, CARD, 8) + text(x+26, 456, n, 18, accent, 400, 0, True) + arrow(x+414, 432, 25, accent, 2)
        body += text(x+26, 540, label, 33, WHITE, 700, -1) + line(x+26, 568, x+449, 568)
        body += text(x+26, 626, question, 25, WHITE) + text(x+26, 681, detail, 21, MUTED)
    return svg(1600, 900, 'Folivect — Build the case', body + footer())


def post_risk():
    body = rect(0, 0, 1600, 900, BG) + topbar(2, 'Test the assumptions')
    body += text(68, 246, 'Change the input.', 83, WHITE, 700, -3) + text(68, 340, 'Inspect the consequence.', 83, GREEN, 700, -3)
    body += text(74, 406, 'One position. Three hypothetical paths. A clearer sense of the downside.', 27, MUTED)
    for i, (name, value, detail, color) in enumerate([('BEAR', '-12%', 'Challenge the thesis', VIOLET), ('BASE', '+6%', 'State the assumptions', GREEN), ('BULL', '+18%', 'Question the upside', WHITE)]):
        x = 70 + i * 491
        body += rect(x, 479, 478, 229, CARD, 8, LINE) + text(x+25, 518, name, 16, MUTED, 400, 2, True)
        body += text(x+25, 603, value, 67, color, 500, -2, True) + text(x+25, 670, detail, 23, WHITE)
    body += text(74, 761, 'ILLUSTRATIVE 30-DAY PRICE MOVES / NOT FORECASTS OR PROBABILITIES', 17, MUTED, 400, .5, True)
    return svg(1600, 900, 'Folivect — Test the assumptions', body + footer())


def post_journal():
    body = rect(0, 0, 1600, 900, BG) + topbar(3, 'Keep the record')
    body += text(68, 252, 'Keep your reasoning.', 90, WHITE, 700, -3) + text(72, 323, 'The decision matters. So does the thinking that led to it.', 29, MUTED)
    body += rect(70, 384, 1460, 356, CARD, 8) + rect(70, 384, 8, 356, GREEN)
    body += text(107, 432, 'DECISION RECORD / 001', 17, GREEN, 400, 1, True) + text(1190, 432, 'SAVED ON THIS DEVICE', 16, MUTED, 400, 0, True)
    entries = [('CONTEXT', 'The asset, the scenario, and the source.'), ('THESIS', 'What I believe — and what would change my mind.'), ('NEXT REVIEW', 'A question to return to, with fresh evidence.')]
    for i, (label, detail) in enumerate(entries):
        cy = 494 + i * 87
        body += line(106, cy-27, 1490, cy-27) + text(109, cy+14, label, 16, MUTED, 400, .7, True) + text(408, cy+17, detail, 27, WHITE)
    return svg(1600, 900, 'Folivect — Keep your reasoning', body + footer())


def post_preview():
    body = rect(0, 0, 1600, 900, GREEN) + topbar(4, 'The research preview', True)
    body += text(65, 284, 'See the case.', 124, BG, 700, -5) + text(65, 423, 'Own the decision.', 124, BG, 700, -5)
    body += text(73, 495, 'Explore the Folivect research workspace.', 30, BG)
    steps = [('01', 'Pick an asset'), ('02', 'Inspect the case'), ('03', 'Test the risk'), ('04', 'Save the context')]
    for i, (index, label) in enumerate(steps):
        x=70+i*369
        body += rect(x, 565, 353, 151, BG, 8) + text(x+22, 605, index, 17, MUTED, 400, 0, True) + arrow(x+302, 588, 22, GREEN, 2) + text(x+22, 669, label, 26, WHITE, 600, -.5)
    body += text(75, 760, 'SAMPLE DATA / LOCAL JOURNAL / OPTIONAL WALLET / NO TRADE EXECUTION', 17, BG, 400, .4, True)
    return svg(1600, 900, 'Folivect — See the case. Own the decision.', body + footer(True))


def banner():
    body = rect(0, 0, 1500, 500, BG) + rect(995, 0, 505, 500, CARD)
    body += vector_field(1042, 23, 410, 435) + lockup(66, 44, 56)
    body += text(69, 225, 'See the case.', 79, WHITE, 700, -3) + text(69, 321, 'Own the decision.', 79, GREEN, 700, -3)
    body += text(75, 391, 'Equity research. Scenario thinking. A record to revisit.', 24, MUTED)
    # Keep the lower-left area clear for the social profile avatar overlay.
    body += text(433, 466, f'RESEARCH PREVIEW / {DOMAIN}', 16, MUTED, 400, .3, True)
    return svg(1500, 500, 'Folivect — See the case. Own the decision.', body)


def og_card():
    body = rect(0, 0, 1200, 630, BG) + lockup(48, 35, 57)
    body += rect(810, 0, 390, 630, CARD) + vector_field(835, 108, 333, 395)
    body += text(49, 231, 'See the case.', 80, WHITE, 700, -3) + text(49, 331, 'Own the', 80, GREEN, 700, -3) + text(49, 427, 'decision.', 80, GREEN, 700, -3)
    body += text(53, 494, 'A workspace for equity research and risk.', 24, MUTED)
    body += line(52, 550, 758, 550) + text(54, 593, 'RESEARCH PREVIEW', 16, MUTED, 400, 1, True) + text(604, 593, DOMAIN, 21, WHITE)
    return svg(1200, 630, 'Folivect equity research preview', body)


def find_browser():
    configured = os.environ.get('FOLIVECT_BROWSER_PATH')
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_file(): raise FileNotFoundError(f'FOLIVECT_BROWSER_PATH does not exist: {path}')
        return str(path)
    for path in [shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser'), r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if path and Path(path).is_file(): return path
    return None


def main():
    for directory in (PUBLIC, SOCIAL, TWITTER): directory.mkdir(parents=True, exist_ok=True)
    (PUBLIC / 'logo-mark.svg').write_text(svg(256, 256, BRAND, mark()), encoding='utf-8')
    shutil.copyfile(PUBLIC / 'logo-mark.svg', PUBLIC / 'folivect-mark.svg')
    (PUBLIC / 'logo-lockup.svg').write_text(svg(550, 128, BRAND, lockup(2, 8, 112)), encoding='utf-8')
    avatar = svg(400, 400, 'Folivect profile image', rect(0, 0, 400, 400, BG) + mark(41, 41, 318, False))
    assets = {'twitter-logo': (avatar, 400, 400), 'twitter-banner': (banner(), 1500, 500), 'post-01-signal': (post_signal(), 1600, 900), 'post-02-risk': (post_risk(), 1600, 900), 'post-03-journal': (post_journal(), 1600, 900), 'post-04-research-preview': (post_preview(), 1600, 900), 'og-card': (og_card(), 1200, 630)}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=find_browser())
        for name, (source, width, height) in assets.items():
            path = (SOCIAL if name == 'og-card' else TWITTER) / f'{name}.svg'
            path.write_text(source, encoding='utf-8')
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            page.set_content(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{BG}}}svg{{display:block}}</style></head><body>{source}</body></html>')
            page.evaluate('document.fonts.ready')
            page.screenshot(path=str(path.with_suffix('.jpg')), type='jpeg', quality=95)
            page.close()
            if name != 'og-card':
                for ext in ('svg', 'jpg'): shutil.copyfile(path.with_suffix(f'.{ext}'), SOCIAL / f'{name}.{ext}')
            print(f'Generated {name}: {width} x {height}')
        browser.close()
    shutil.copyfile(TWITTER / 'twitter-logo.svg', PUBLIC / 'twitter-logo.svg')


if __name__ == '__main__': main()
