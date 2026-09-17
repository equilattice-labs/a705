"""Generate the editorial research-folio identity and social kit.

Run: python website/scripts/generate-assets.py
Identity comes from src/brand.js. Local Chromium renders without network access.
Requires: pip install -r website/scripts/requirements-assets.txt
"""
import base64
import json
import os
from pathlib import Path
import re
import shutil
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

WEBSITE = Path(__file__).resolve().parents[1]
ROOT = next((p for p in WEBSITE.parents if (p / 'BRAND_SELECTION.md').is_file()), WEBSITE)
PUBLIC, TWITTER = WEBSITE / 'public', ROOT / 'twitter'
SOCIAL = PUBLIC / 'social'
identity_source = (WEBSITE / 'src' / 'brand.js').read_text(encoding='utf-8')


def identity_value(key):
    match = re.search(rf'\b{key}:\s*[\"\']([^\"\']+)[\"\']', identity_source)
    if not match:
        raise ValueError(f'Missing identity value in src/brand.js: {key}')
    return match.group(1)


BRAND, SLUG, DOMAIN, HANDLE, TAGLINE = map(identity_value, ('name', 'slug', 'domain', 'handle', 'tagline'))
PAPER, WINE, CLAY, PEACH, SAGE = '#f8f3e9', '#462c34', '#b5412c', '#eedacc', '#dfe9e5'
MUTED, RULE, WHITE = '#715e60', '#cdbdb4', '#fffdf8'


def text(x, y, value, size=24, fill=WINE, weight=400, spacing=0, serif=False, italic=False):
    font = 'Georgia, Times New Roman, serif' if serif else 'Arial, Helvetica, sans-serif'
    style = ' font-style="italic"' if italic else ''
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}"{style}>{escape(value)}</text>'


def title(x, y, value, size=88, fill=WINE, italic=False):
    return text(x, y, value, size, fill, spacing=-2.8, serif=True, italic=italic)


def rect(x, y, width, height, fill, radius=0, stroke=None, stroke_width=1):
    border = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"{border}/>'


def line(x1, y1, x2, y2, color=RULE, width=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def circle(x, y, radius, fill='none', stroke=None, width=1):
    border = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ''
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}"{border}/>'


def mark(x=0, y=0, size=256, tile=True):
    """Three offset folio leaves and an eccentric reading lens, original SVG geometry."""
    body = rect(0, 0, 256, 256, PAPER, 48) if tile else ''
    body += rect(36, 79, 131, 143, CLAY, 7)
    body += rect(64, 53, 131, 143, PEACH, 7)
    body += rect(92, 27, 131, 143, WINE, 7)
    body += circle(157.5, 95, 40, SAGE)
    body += circle(168.5, 84, 26, WINE)
    body += line(112, 148, 185, 148, PAPER, 5)
    return f'<g transform="translate({x} {y}) scale({size / 256})">{body}</g>'


def svg(width, height, label, body):
    description = f'Original {BRAND} editorial research-folio artwork. Sample equity research, hypothetical scenarios, and a browser-local decision journal.'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(label)}</title><desc id="desc">{escape(description)}</desc>{body}</svg>\n'


def lockup(x, y, size=52, light=False):
    return mark(x, y, size, False) + text(x + size + 13, y + size * .74, BRAND, size * .62, PAPER if light else WINE, spacing=-1.6, serif=True)


def label(x, y, value, fill=MUTED, size=13):
    return text(x, y, value.upper(), size, fill, 700, 2)


def header(index, section):
    return lockup(56, 28, 64) + label(1000, 68, 'Research notes / ' + section) + line(64, 116, 1536, 116) + label(1490, 69, f'{index:02d}', CLAY)


def footer(disclosure='RESEARCH PREVIEW / SAMPLE DATA'):
    return line(64, 812, 1536, 812) + label(64, 855, disclosure, size=11) + text(1080, 854, f'{DOMAIN}  /  {HANDLE}', 17, WINE)


def reading_lens(x, y, radius=90):
    body = circle(x, y, radius, SAGE)
    body += circle(x, y, radius * .7, 'none', WINE, 1.5)
    body += circle(x - radius * .18, y + radius * .03, radius * .41, CLAY)
    body += circle(x + radius * .07, y - radius * .2, radius * .41, SAGE)
    body += line(x - radius * 1.18, y, x + radius * 1.18, y, WINE)
    body += line(x, y - radius * 1.18, x, y + radius * 1.18, WINE)
    return body


def folio(x, y, width=445, height=470):
    body = rect(x + 24, y + 22, width, height, PEACH)
    body += rect(x + 12, y + 11, width, height, PAPER, stroke=RULE)
    body += rect(x, y, width, height, WHITE, stroke=WINE)
    body += label(x + 32, y + 41, 'A working thesis', CLAY)
    body += line(x + 32, y + 63, x + width - 32, y + 63)
    body += title(x + 31, y + 119, 'Read closely.', 43)
    body += text(x + 33, y + 155, 'Leave room for another view.', 18, MUTED)
    body += reading_lens(x + width / 2, y + 282, 87)
    body += line(x + 32, y + height - 72, x + width - 32, y + height - 72)
    body += label(x + 33, y + height - 37, 'Evidence / assumptions / judgment', size=9)
    return body


def post_signal():
    body = rect(0, 0, 1600, 900, PAPER) + header(1, 'The evidence')
    body += label(66, 186, '01 / Start with a better question', CLAY)
    body += title(59, 291, 'Read the case.', 91)
    body += title(59, 396, 'Find the gaps.', 91, CLAY, True)
    body += text(66, 467, 'A considered view makes room for doubt.', 26, MUTED)
    rows = [('Evidence', 'What can you inspect?'), ('Interpretation', 'What does it suggest?'), ('Counter-case', 'What would change your view?')]
    for i, (name, detail) in enumerate(rows):
        yy = 558 + i * 75
        body += text(66, yy, f'0{i + 1}', 16, CLAY, serif=True)
        body += text(112, yy, name, 24, WINE, serif=True)
        body += text(349, yy, detail, 20, MUTED)
        body += line(65, yy + 23, 739, yy + 23)
    body += rect(847, 148, 689, 627, SAGE)
    body += folio(950, 203, 465, 494)
    body += circle(1456, 712, 45, CLAY) + text(1434, 722, '01', 28, PAPER, serif=True)
    return svg(1600, 900, f'{BRAND}: Read the case. Find the gaps.', body + footer())


def post_risk():
    body = rect(0, 0, 1600, 900, PAPER) + header(2, 'The assumptions')
    body += label(66, 186, '02 / Give uncertainty a little space', CLAY)
    body += title(60, 288, 'One case.', 87) + title(492, 288, 'Three possibilities.', 87, CLAY, True)
    body += text(66, 353, 'Change the assumptions. Consider what each outcome would mean.', 27, MUTED)
    cases = [('BEAR CASE', '-12%', 'Where does it weaken?', PEACH), ('BASE CASE', '+6%', 'What must remain true?', SAGE), ('BULL CASE', '+18%', 'What might optimism miss?', WHITE)]
    for i, (name, value, question, fill) in enumerate(cases):
        xx = 64 + i * 496
        body += rect(xx, 417, 464, 303, fill)
        body += label(xx + 27, 459, name, WINE)
        body += text(xx + 24, 580, value, 94, WINE, spacing=-4, serif=True)
        body += line(xx + 28, 614, xx + 436, 614, WINE)
        body += text(xx + 28, 664, question, 24, WINE, serif=True)
    body += label(64, 768, 'Illustrative 30-day price moves. Not forecasts, probabilities, or expected returns.', size=11)
    return svg(1600, 900, f'{BRAND}: One case. Three possibilities.', body + footer())


def post_journal():
    body = rect(0, 0, 1600, 900, PAPER) + header(3, 'The record')
    body += label(66, 186, '03 / A note for your future self', CLAY)
    body += title(59, 294, 'Keep the why.', 90)
    body += title(59, 398, 'Return to it.', 90, CLAY, True)
    body += text(66, 473, 'A decision is more useful when', 27, MUTED)
    body += text(66, 515, 'you can revisit the thinking behind it.', 27, MUTED)
    body += mark(61, 584, 137, False)
    body += label(220, 638, 'Your own research journal', WINE, 12)
    body += text(220, 680, 'Stored in this browser.', 22, MUTED, serif=True, italic=True)
    body += rect(873, 194, 636, 573, PEACH)
    body += rect(848, 171, 636, 573, WHITE, stroke=WINE)
    body += label(882, 219, 'Decision record / 001', CLAY)
    body += line(882, 241, 1450, 241)
    entries = [('THE CONTEXT', 'Asset. Scenario. Source.'), ('THE THESIS', 'A view and its conditions.'), ('THE NEXT REVIEW', 'What would change my mind?')]
    for i, (name, value) in enumerate(entries):
        yy = 294 + i * 144
        body += label(883, yy, name, size=11)
        body += text(883, yy + 51, value, 31, WINE, serif=True)
        body += line(883, yy + 86, 1450, yy + 86)
    return svg(1600, 900, f'{BRAND}: Keep the why. Return to it.', body + footer('RESEARCH PREVIEW / BROWSER-LOCAL JOURNAL'))


def tagline_lines():
    words = TAGLINE.split()
    if len(words) < 2:
        return TAGLINE, ''
    split = min(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))
    return ' '.join(words[:split]), ' '.join(words[split:])


def post_preview():
    body = rect(0, 0, 1600, 900, WINE)
    body += rect(0, 0, 1000, 900, PAPER)
    body += lockup(55, 28, 64) + label(1090, 69, 'An invitation to think', PAPER)
    body += line(64, 116, 936, 116)
    body += label(66, 195, 'The research folio', CLAY)
    first, second = tagline_lines()
    size = min(101, 845 / max(len(first), len(second), 1) * 1.95)
    body += title(59, 315, first, size)
    body += title(59, 429, second, size, CLAY, True)
    body += text(65, 510, 'Equity research. Considered from every side.', 27, MUTED)
    steps = ['Choose an asset', 'Read the case', 'Test a scenario', 'Keep the record']
    for i, value in enumerate(steps):
        yy = 588 + i * 48
        body += text(65, yy, f'0{i + 1}', 17, CLAY, serif=True) + text(114, yy, value, 25, WINE, serif=True)
    body += mark(1111, 222, 376, False)
    body += text(1081, 680, 'A place for evidence.', 26, PAPER, serif=True)
    body += text(1081, 723, 'And your own judgment.', 26, PAPER, serif=True, italic=True)
    body += line(65, 812, 937, 812)
    body += label(65, 855, 'Sample data / local journal / optional wallet / no trades', size=10)
    body += text(1115, 854, DOMAIN, 21, PAPER)
    return svg(1600, 900, f'{BRAND}: {TAGLINE}', body)


def banner():
    body = rect(0, 0, 1500, 500, PAPER)
    body += rect(0, 0, 412, 500, PEACH)
    body += reading_lens(206, 194, 139)
    body += lockup(481, 25, 54)
    body += label(1163, 63, 'Research preview', CLAY, 11)
    body += line(487, 109, 1438, 109)
    first, second = tagline_lines()
    size = min(77, 932 / max(len(first), len(second), 1) * 1.88)
    body += title(479, 214, first, size)
    body += title(479, 302, second, size, CLAY, True)
    body += text(486, 366, 'Evidence. Assumptions. Your judgment.', 25, MUTED)
    # X overlays the profile avatar at the lower left; all essential text is right of it.
    body += line(487, 420, 1438, 420)
    body += label(487, 462, 'Read / test / record / revisit', size=11)
    body += text(1210, 462, DOMAIN, 18, WINE)
    return svg(1500, 500, f'{BRAND}: {TAGLINE}', body)


def og_card():
    body = rect(0, 0, 1200, 630, PAPER)
    body += lockup(37, 23, 61) + label(914, 65, 'Research preview', CLAY, 11)
    body += line(45, 111, 1155, 111)
    first, second = tagline_lines()
    size = min(75, 746 / max(len(first), len(second), 1) * 1.95)
    body += title(39, 234, first, size)
    body += title(39, 324, second, size, CLAY, True)
    body += text(47, 404, 'Equity research. Scenario testing.', 25, MUTED)
    body += text(47, 446, 'A record of your own reasoning.', 25, MUTED)
    body += rect(857, 162, 298, 329, PEACH)
    body += mark(872, 196, 266, False)
    body += line(45, 537, 1155, 537)
    body += label(47, 583, 'A research folio / sample data', size=11)
    body += text(925, 583, DOMAIN, 18, WINE)
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
    evidence = ROOT / 'output' / f'{SLUG}-assets'
    evidence.mkdir(parents=True, exist_ok=True)
    identity = {'logo-mark': svg(256, 256, BRAND, mark()), 'logo-lockup': svg(650, 128, BRAND, lockup(0, 4, 118))}
    for name, source in identity.items():
        ET.fromstring(source)
        (PUBLIC / f'{name}.svg').write_text(source, encoding='utf-8')
    shutil.copyfile(PUBLIC / 'logo-mark.svg', PUBLIC / f'{SLUG}-mark.svg')
    avatar = svg(400, 400, f'{BRAND} profile image', rect(0, 0, 400, 400, PAPER) + mark(31, 31, 338, False))
    assets = {'twitter-logo': (avatar, 400, 400), 'twitter-banner': (banner(), 1500, 500), 'post-01-signal': (post_signal(), 1600, 900), 'post-02-risk': (post_risk(), 1600, 900), 'post-03-journal': (post_journal(), 1600, 900), 'post-04-research-preview': (post_preview(), 1600, 900), 'og-card': (og_card(), 1200, 630)}
    validation = {'brand': BRAND, 'dimensions': {}, 'out_of_bounds_text': [], 'social_copies_match': True, 'decoded_jpg_dimensions_match': True, 'network_requests_allowed': False}
    contact_images = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=find_browser())
        for name, (source, width, height) in assets.items():
            ET.fromstring(source)
            output = (SOCIAL if name == 'og-card' else TWITTER) / f'{name}.svg'
            output.write_text(source, encoding='utf-8')
            page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
            page.route('**/*', lambda route: route.abort())
            page.set_content(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{PAPER}}}svg{{display:block}}</style></head><body>{source}</body></html>')
            page.evaluate('document.fonts.ready')
            overflow = page.locator('svg text').evaluate_all('(nodes) => nodes.filter(n => {const b=n.getBoundingClientRect(); return b.left < -1 || b.top < -1 || b.right > innerWidth+1 || b.bottom > innerHeight+1;}).map(n=>n.textContent)')
            validation['out_of_bounds_text'].extend({'asset': name, 'text': value} for value in overflow)
            page.screenshot(path=str(output.with_suffix('.jpg')), type='jpeg', quality=95)
            image_url = 'data:image/jpeg;base64,' + base64.b64encode(output.with_suffix('.jpg').read_bytes()).decode('ascii')
            decoded = page.evaluate('(src) => new Promise((resolve, reject) => {const img = new Image(); img.onload = () => resolve([img.naturalWidth, img.naturalHeight]); img.onerror = reject; img.src = src;})', image_url)
            validation['decoded_jpg_dimensions_match'] &= decoded == [width, height]
            validation['dimensions'][name] = decoded
            contact_images.append(f'<figure><img src="{image_url}"><figcaption>{name} · {width} × {height}</figcaption></figure>')
            page.close()
            if name != 'og-card':
                for ext in ('svg', 'jpg'):
                    destination = SOCIAL / f'{name}.{ext}'
                    shutil.copyfile(output.with_suffix(f'.{ext}'), destination)
                    validation['social_copies_match'] &= output.with_suffix(f'.{ext}').read_bytes() == destination.read_bytes()
            print(f'Generated {name}: {width} x {height}')
        lockup_page = browser.new_page(viewport={'width': 650, 'height': 128})
        lockup_page.route('**/*', lambda route: route.abort())
        lockup_page.set_content(f'<style>body{{margin:0}}</style>{identity["logo-lockup"]}')
        lockup_page.evaluate('document.fonts.ready')
        bounds = lockup_page.locator('svg text').evaluate_all('(nodes) => nodes.filter(n => n.getBoundingClientRect().right > 650).map(n=>n.textContent)')
        validation['out_of_bounds_text'].extend({'asset': 'logo-lockup', 'text': value} for value in bounds)
        lockup_page.close()
        contact_page = browser.new_page(viewport={'width': 1640, 'height': 1500}, device_scale_factor=1)
        contact_page.route('**/*', lambda route: route.abort())
        contact_page.set_content(f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;padding:24px;background:{PEACH};font:16px Arial;color:{WINE}}}h1{{font:36px Georgia;margin:0 0 24px}}main{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0;background:{PAPER};padding:14px}}img{{width:100%;height:386px;object-fit:contain;background:{PAPER}}}figcaption{{padding:12px 0 0}}</style><h1>{escape(BRAND)} — research folio asset review</h1><main>{"".join(contact_images)}</main>')
        contact_page.locator('img').evaluate_all('(nodes) => Promise.all(nodes.map(n => n.decode()))')
        contact_page.screenshot(path=str(evidence / 'contact-sheet.jpg'), type='jpeg', quality=90, full_page=True)
        contact_page.close()
        browser.close()
    shutil.copyfile(TWITTER / 'twitter-logo.svg', PUBLIC / 'twitter-logo.svg')
    for source in (PUBLIC / 'logo-mark.svg', PUBLIC / 'logo-lockup.svg', PUBLIC / f'{SLUG}-mark.svg', PUBLIC / 'twitter-logo.svg'):
        ET.parse(source)
    (evidence / 'asset-validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    if validation['out_of_bounds_text'] or not validation['social_copies_match'] or not validation['decoded_jpg_dimensions_match']:
        raise RuntimeError('Generated assets failed validation; see asset-validation.json')
    print(f'Validated {len(assets)} social compositions and current identity assets.')
    print(f'Contact sheet: {evidence / "contact-sheet.jpg"}')


if __name__ == '__main__':
    main()
