"""Generate the current decision-workspace identity and social kit.

Run: python website/scripts/generate-assets.py
Identity comes from src/brand.js. Rendering uses local Chromium without network.
Requires: pip install -r website/scripts/requirements-assets.txt
"""
import json
import os
from pathlib import Path
import re
import shutil
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

WEBSITE = Path(__file__).resolve().parents[1]
ROOT = next((path for path in WEBSITE.parents if (path / 'BRAND_SELECTION.md').is_file()), WEBSITE)
PUBLIC, TWITTER = WEBSITE / 'public', ROOT / 'twitter'
SOCIAL = PUBLIC / 'social'
identity_source = (WEBSITE / 'src' / 'brand.js').read_text(encoding='utf-8')


def identity_value(key):
    match = re.search(rf'\b{key}:\s*[\"\']([^\"\']+)[\"\']', identity_source)
    if not match:
        raise ValueError(f'Missing identity value in src/brand.js: {key}')
    return match.group(1)


BRAND, SLUG, DOMAIN, HANDLE, TAGLINE = map(identity_value, ('name', 'slug', 'domain', 'handle', 'tagline'))
INK, LIME, WHITE, STEEL = '#111923', '#D5FA5B', '#F4F6F8', '#647381'
PANEL, RULE, PALE, AMBER = '#1D2935', '#344452', '#B5C0CA', '#F6BA74'


def text(x, y, value, size=24, fill=WHITE, weight=400, spacing=0):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}">{escape(value)}</text>'


def rect(x, y, width, height, fill, radius=0, stroke=None):
    border = f' stroke="{stroke}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"{border}/>'


def line(x1, y1, x2, y2, color=RULE, width=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def path(points, color=LIME, width=4):
    return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="miter"/>'


def node(x, y, radius=9, fill=LIME, stroke=None):
    border = f' stroke="{stroke}" stroke-width="3"' if stroke else ''
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}"{border}/>'


def mark(x=0, y=0, size=256, tile=True, inverse=False):
    """A cut-corner routing node: one incoming route, two examined outcomes."""
    color = INK if tile else (LIME if inverse else INK)
    body = '<path d="M0 0H218L256 38V256H38L0 218Z" fill="' + LIME + '"/>' if tile else ''
    body += f'<path d="M49 195L110 134V75H143V120L181 82H164V49H220V105H187V128L142 173L117 148L74 220Z" fill="{color}"/>'
    body += f'<path d="M149 151H216V184H182V218H149Z" fill="{color}"/>'
    return f'<g transform="translate({x} {y}) scale({size / 256})">{body}</g>'


def svg(width, height, title, body):
    description = f'Original {BRAND} decision-workspace artwork. Sample equity research, illustrative scenarios, and a browser-local decision journal.'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>{body}</svg>\n'


def lockup(x, y, size=52, inverse=True):
    return mark(x, y, size, False, inverse) + text(x + size + 14, y + size * .76, BRAND, size * .7, WHITE if inverse else INK, 700, -1.8)


def pill(x, y, label, width=205, fill=PANEL, foreground=LIME):
    return rect(x, y, width, 34, fill, 17) + node(x + 17, y + 17, 4, foreground) + text(x + 31, y + 23, label, 12, foreground, 700, .7)


def topbar(index, label):
    return lockup(57, 33, 60) + pill(1121, 48, label.upper(), 344) + text(1502, 73, f'{index:02d}', 17, PALE, 700) + line(65, 122, 1535, 122)


def footer():
    return line(65, 807, 1535, 807) + text(65, 852, 'RESEARCH PREVIEW / YOUR JUDGMENT', 13, PALE, 700, 1.3) + text(1120, 852, f'{DOMAIN}  /  {HANDLE}', 16, LIME, 700)


def scale(x, y, width, count=24, color=RULE):
    body = line(x, y, x + width, y, color)
    for i in range(count + 1):
        xx = x + width * i / count
        body += line(xx, y, xx, y + (16 if i % 4 == 0 else 7), color)
    return body


def route_graph(x=0, y=0, width=460, height=420):
    body = ''
    for xx in range(0, int(width) + 1, 40):
        for yy in range(0, int(height) + 1, 40):
            body += node(xx, yy, 1.5, RULE)
    cy = height * .55
    body += path(f'22,{cy} {width * .4},{cy} {width * .72},{height * .18} {width},{height * .18}', LIME, 7)
    body += path(f'{width * .4},{cy} {width * .74},{cy} {width},{cy}', STEEL, 3)
    body += path(f'{width * .4},{cy} {width * .72},{height * .88} {width},{height * .88}', STEEL, 3)
    for nx, ny, nr, color in [(22, cy, 10, WHITE), (width * .4, cy, 18, LIME), (width, height * .18, 12, LIME), (width, cy, 8, STEEL), (width, height * .88, 8, STEEL)]:
        body += node(nx, ny, nr, INK, color)
    body += rect(width * .4 - 7, cy - 7, 14, 14, LIME)
    return f'<g transform="translate({x} {y})">{body}</g>'


def post_signal():
    body = rect(0, 0, 1600, 900, INK) + topbar(1, 'Inspect the case')
    body += text(65, 204, '01 / EVIDENCE BEFORE CONVICTION', 14, LIME, 700, 1.6)
    body += text(58, 314, 'See the case.', 91, WHITE, 700, -4) + text(58, 417, 'Find the gaps.', 91, LIME, 700, -4)
    body += text(65, 491, 'A useful view can explain its own limits.', 27, PALE)
    body += route_graph(80, 547, 610, 176)
    entries = [('01', 'Evidence', 'What can you inspect?'), ('02', 'Interpretation', 'What does it suggest?'), ('03', 'Counter-case', 'What could change the view?')]
    for i, (index, label, question) in enumerate(entries):
        yy = 184 + i * 190
        body += rect(889, yy, 646, 162, PANEL)
        body += text(921, yy + 42, index, 16, LIME, 700) + text(982, yy + 65, label, 37, WHITE, 700, -1)
        body += text(983, yy + 113, question, 23, PALE) + line(890, yy, 890, yy + 162, LIME if i == 0 else RULE, 3)
    return svg(1600, 900, f'{BRAND}: See the case. Find the gaps.', body + footer())


def post_risk():
    body = rect(0, 0, 1600, 900, INK) + topbar(2, 'Stress the scenario')
    body += text(65, 201, '02 / CHANGE THE ASSUMPTIONS', 14, LIME, 700, 1.6)
    body += text(59, 298, 'Move one input.', 85, WHITE, 700, -3.5) + text(59, 396, 'Read every outcome.', 85, WHITE, 700, -3.5)
    body += text(1100, 241, 'ILLUSTRATIVE', 13, PALE, 700, 1.5) + text(1100, 271, '30-DAY PRICE MOVES', 13, PALE, 700, 1.5)
    body += scale(1100, 311, 430, 24) + text(1100, 371, 'Assumptions, not forecasts.', 21, LIME)
    cases = [('BEAR', '-12%', 'Where does the case weaken?', AMBER), ('BASE', '+6%', 'What needs to remain true?', LIME), ('BULL', '+18%', 'What does optimism leave out?', WHITE)]
    for i, (label, value, detail, color) in enumerate(cases):
        xx = 65 + i * 503
        body += rect(xx, 471, 464, 270, PANEL)
        body += line(xx, 471, xx + 464, 471, color, 4) + text(xx + 26, 514, f'PATH {i + 1:02d} / {label}', 14, color, 700, 1)
        body += text(xx + 22, 628, value, 87, color, 700, -3) + text(xx + 26, 697, detail, 20, PALE)
    body += text(65, 782, 'SCENARIO MOVES ARE HYPOTHETICAL. THEY ARE NOT PROBABILITIES OR EXPECTED RETURNS.', 12, PALE, 700, 1)
    return svg(1600, 900, f'{BRAND}: Move one input. Read every outcome.', body + footer())


def post_journal():
    body = rect(0, 0, 1600, 900, INK) + topbar(3, 'Record the reasoning')
    body += text(65, 201, '03 / KEEP THE DECISION CONTEXT', 14, LIME, 700, 1.6)
    body += text(58, 303, 'Save the why.', 88, WHITE, 700, -4) + text(58, 405, 'Revisit the call.', 88, LIME, 700, -4)
    body += text(65, 485, 'The next review starts with', 27, PALE) + text(65, 526, 'the thinking you kept.', 27, PALE)
    body += pill(65, 639, 'STORED IN THIS BROWSER', 270)
    body += scale(65, 715, 605, 28)
    body += rect(823, 178, 711, 565, WHITE)
    body += rect(823, 178, 711, 65, LIME) + text(853, 220, 'DECISION RECORD / 001', 17, INK, 700, 1)
    body += mark(1437, 184, 49, False)
    entries = [('CONTEXT', 'Asset. Scenario. Source.'), ('THESIS', 'A view and its conditions.'), ('NEXT REVIEW', 'What would change your mind?')]
    for i, (label, detail) in enumerate(entries):
        yy = 304 + i * 145
        body += node(858, yy - 6, 6, INK) + text(882, yy, label, 12, STEEL, 700, 1.4)
        body += text(882, yy + 47, detail, 29, INK, 700, -1)
        if i < 2: body += line(853, yy + 88, 1500, yy + 88, '#CDD5DB')
    return svg(1600, 900, f'{BRAND}: Save the why. Revisit the call.', body + footer())


def tagline_lines():
    words = TAGLINE.split()
    if len(TAGLINE) <= 24:
        split = max(1, len(words) // 2)
    else:
        split = min(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))
    return ' '.join(words[:split]), ' '.join(words[split:])


def post_preview():
    body = rect(0, 0, 1600, 900, LIME)
    body += lockup(57, 33, 60, False) + text(1194, 74, 'THE RESEARCH PREVIEW', 15, INK, 700, 1)
    body += line(65, 122, 1535, 122, INK)
    first, second = tagline_lines()
    size = min(113, 1320 / max(len(first), len(second), 1) * 1.72)
    body += text(57, 279, first, size, INK, 700, -5) + text(57, 411, second, size, INK, 700, -5)
    body += mark(1282, 192, 222, False)
    body += text(65, 484, 'Equity research. Scenario testing. A record of your own reasoning.', 27, INK)
    steps = [('01', 'Choose an asset'), ('02', 'Inspect the case'), ('03', 'Test a scenario'), ('04', 'Keep the record')]
    for i, (index, label) in enumerate(steps):
        xx = 65 + i * 380
        body += line(xx, 586, xx + 321, 586, INK, 2) + node(xx + 10, 586, 10, INK)
        body += text(xx, 644, index, 18, INK, 700) + text(xx, 697, label, 30, INK, 700, -1)
    body += line(65, 780, 1535, 780, INK) + text(65, 833, 'SAMPLE DATA / LOCAL JOURNAL / OPTIONAL WALLET / NO TRADE EXECUTION', 13, INK, 700, 1)
    body += text(1230, 833, DOMAIN, 19, INK, 700)
    return svg(1600, 900, f'{BRAND}: {TAGLINE}', body)


def banner():
    body = rect(0, 0, 1500, 500, INK)
    body += lockup(43, 29, 55) + pill(1189, 45, 'RESEARCH PREVIEW', 246)
    first, second = tagline_lines()
    size = min(82, 875 / max(len(first), len(second), 1) * 1.75)
    body += text(48, 200, first, size, WHITE, 700, -3) + text(48, 294, second, size, LIME, 700, -3)
    body += text(54, 350, 'Evidence. Assumptions. Your judgment.', 24, PALE)
    body += route_graph(1020, 134, 420, 256)
    # X overlays the profile avatar in the lower-left corner.
    body += line(390, 419, 1440, 419) + text(392, 463, 'INSPECT / TEST / RECORD / REVISIT', 13, PALE, 700, 1)
    body += text(1215, 463, DOMAIN, 19, LIME, 700)
    return svg(1500, 500, f'{BRAND}: {TAGLINE}', body)


def og_card():
    body = rect(0, 0, 1200, 630, INK)
    body += lockup(37, 27, 59) + line(45, 120, 1155, 120)
    first, second = tagline_lines()
    size = min(80, 755 / max(len(first), len(second), 1) * 1.75)
    body += text(39, 242, first, size, WHITE, 700, -3) + text(39, 336, second, size, LIME, 700, -3)
    body += text(47, 416, 'Equity research. Scenario testing.', 25, PALE) + text(47, 459, 'A record of your own reasoning.', 25, PALE)
    body += mark(857, 176, 285, True)
    body += line(45, 530, 1155, 530) + text(47, 577, 'RESEARCH PREVIEW / SAMPLE DATA', 13, PALE, 700, 1.1)
    body += text(925, 578, DOMAIN, 19, LIME, 700)
    return svg(1200, 630, f'{BRAND} research preview', body)


def find_browser():
    configured = os.environ.get('ASSET_BROWSER_PATH') or os.environ.get(f'{SLUG.upper()}_BROWSER_PATH')
    if configured:
        browser_path = Path(configured).expanduser().resolve()
        if not browser_path.is_file():
            raise FileNotFoundError(f'Configured browser path does not exist: {browser_path}')
        return str(browser_path)
    for candidate in [shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser'), r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def main():
    for directory in (PUBLIC, SOCIAL, TWITTER):
        directory.mkdir(parents=True, exist_ok=True)
    identity = {'logo-mark': svg(256, 256, BRAND, mark()), 'logo-lockup': svg(650, 128, BRAND, lockup(4, 8, 112, False))}
    for name, source in identity.items():
        (PUBLIC / f'{name}.svg').write_text(source, encoding='utf-8')
    shutil.copyfile(PUBLIC / 'logo-mark.svg', PUBLIC / f'{SLUG}-mark.svg')
    avatar = svg(400, 400, f'{BRAND} profile image', rect(0, 0, 400, 400, INK) + mark(48, 48, 304, False, True))
    assets = {'twitter-logo': (avatar, 400, 400), 'twitter-banner': (banner(), 1500, 500), 'post-01-signal': (post_signal(), 1600, 900), 'post-02-risk': (post_risk(), 1600, 900), 'post-03-journal': (post_journal(), 1600, 900), 'post-04-research-preview': (post_preview(), 1600, 900), 'og-card': (og_card(), 1200, 630)}
    validation = {'brand': BRAND, 'dimensions': {}, 'out_of_bounds_text': [], 'social_copies_match': True}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=find_browser())
        for name, (source, width, height) in assets.items():
            ET.fromstring(source)
            output = (SOCIAL if name == 'og-card' else TWITTER) / f'{name}.svg'
            output.write_text(source, encoding='utf-8')
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            page.route('**/*', lambda route: route.abort())
            page.set_content(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{INK}}}svg{{display:block}}</style></head><body>{source}</body></html>')
            page.evaluate('document.fonts.ready')
            overflow = page.locator('svg text').evaluate_all('(nodes) => nodes.filter(n => {const b=n.getBoundingClientRect(); return b.left < -1 || b.top < -1 || b.right > innerWidth+1 || b.bottom > innerHeight+1;}).map(n=>n.textContent)')
            validation['out_of_bounds_text'].extend({'asset': name, 'text': value} for value in overflow)
            page.screenshot(path=str(output.with_suffix('.jpg')), type='jpeg', quality=95)
            validation['dimensions'][name] = [width, height]
            page.close()
            if name != 'og-card':
                for ext in ('svg', 'jpg'):
                    destination = SOCIAL / f'{name}.{ext}'
                    shutil.copyfile(output.with_suffix(f'.{ext}'), destination)
                    validation['social_copies_match'] &= output.with_suffix(f'.{ext}').read_bytes() == destination.read_bytes()
            print(f'Generated {name}: {width} x {height}')
        lockup_page = browser.new_page(viewport={'width': 650, 'height': 128})
        lockup_page.set_content(f'<style>body{{margin:0}}</style>{identity["logo-lockup"]}')
        lockup_page.evaluate('document.fonts.ready')
        bounds = lockup_page.locator('svg text').evaluate_all('(nodes) => nodes.filter(n => n.getBoundingClientRect().right > 650).map(n=>n.textContent)')
        validation['out_of_bounds_text'].extend({'asset': 'logo-lockup', 'text': value} for value in bounds)
        lockup_page.close()
        browser.close()
    shutil.copyfile(TWITTER / 'twitter-logo.svg', PUBLIC / 'twitter-logo.svg')
    for source in (PUBLIC / 'logo-mark.svg', PUBLIC / 'logo-lockup.svg', PUBLIC / f'{SLUG}-mark.svg', PUBLIC / 'twitter-logo.svg'):
        ET.parse(source)
    evidence = ROOT / 'output' / f'{SLUG}-assets'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'asset-validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    if validation['out_of_bounds_text'] or not validation['social_copies_match']:
        raise RuntimeError('Generated assets failed validation; see asset-validation.json')
    print(f'Validated {len(assets)} social compositions and current identity assets.')


if __name__ == '__main__':
    main()
