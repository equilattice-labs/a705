"""Generate Scenarill's original branch identity and dark research-lab social kit.
Identity comes from src/brand.js; Chromium renders locally with network blocked.
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
        raise ValueError(f'Missing identity: {key}')
    return match.group(1)

BRAND, SLUG, DOMAIN, HANDLE, TAGLINE = map(identity_value, ('name', 'slug', 'domain', 'handle', 'tagline'))
PAPER, WINE, CLAY, PEACH, SAGE = '#0b111b', '#edf3f8', '#c4f06a', '#121c2b', '#8fb9ff'
MUTED, RULE, WHITE = '#a5b1c2', '#263247', '#192638'

def text(x, y, value, size=24, fill=WINE, weight=400, spacing=0, mono=False):
    font = 'Consolas, monospace' if mono else 'Segoe UI, Arial, sans-serif'
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}">{escape(value)}</text>'

def title(x, y, value, size=88, fill=WINE):
    return text(x, y, value, size, fill, 650, -3)

def rect(x, y, w, h, fill, radius=0, stroke=None):
    border = f' stroke="{stroke}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"{border}/>'

def line(x1, y1, x2, y2, color=RULE, width=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'

def circle(x, y, radius, fill):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}"/>'

def mark(x=0, y=0, size=256, tile=True):
    body = rect(0, 0, 256, 256, PAPER, 58) if tile else ''
    body += '<g fill="none" stroke="#c4f06a" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"><path d="M54 195V160Q54 128 91 128H165Q202 128 202 91V59"/><path d="M54 195V160Q54 128 91 128H165Q202 128 202 165V195"/><path d="M54 59V91Q54 128 91 128H202"/></g>'
    for cx, cy in [(54,59),(202,59),(202,195)]:
        body += circle(cx, cy, 12, SAGE)
    return f'<g transform="translate({x} {y}) scale({size/256})">{body}</g>'

def svg(w, h, label, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(label)}</title><desc id="desc">Original {escape(BRAND)} branching research diagram. Sample data, hypothetical scenarios, browser-local journal.</desc>{body}</svg>\n'

def lockup(x, y, size=52):
    return mark(x,y,size,False) + text(x+size+15,y+size*.73,BRAND,size*.62,WINE,650,-1.5)

def label(x,y,value,fill=MUTED,size=13):
    return text(x,y,value.upper(),size,fill,600,1.5,True)

def grid(w,h):
    return ''.join(line(x,0,x,h,'#182231') for x in range(0,w,80)) + ''.join(line(0,y,w,y,'#182231') for y in range(0,h,80))

def branches(x,y,w=500,h=360):
    body = ''
    for end, color, value in [(0.1,CLAY,'BULL'),(.5,SAGE,'BASE'),(.9,'#f2a5a7','BEAR')]:
        yy=y+h*end
        body += f'<path d="M{x} {y+h*.5}C{x+w*.44} {y+h*.5} {x+w*.44} {yy} {x+w} {yy}" fill="none" stroke="{color}" stroke-width="3"/>'
        body += circle(x+w,yy,6,color) + label(x+w-60,yy-20,value,color,10)
    body += circle(x,y+h*.5,8,WINE)
    return body

def header(index,section):
    return lockup(54,28,64)+label(1040,68,section)+label(1482,68,f'{index:02d}',CLAY)+line(64,118,1536,118)

def footer(disclosure='RESEARCH PREVIEW / SAMPLE DATA'):
    return line(64,812,1536,812)+label(64,854,disclosure,size=11)+text(1090,854,f'{DOMAIN} / {HANDLE}',17,MUTED)

def post_signal():
    body=rect(0,0,1600,900,PAPER)+header(1,'The research')
    body+=label(64,194,'01 / Establish the case',CLAY)
    body+=title(58,304,'A view is only',83)+title(58,402,'the beginning.',83,CLAY)
    body+=text(65,476,'Make space for the evidence that challenges it.',24,MUTED)
    for i,(a,b) in enumerate([('THESIS','What supports your view?'),('EVIDENCE','What can you verify?'),('COUNTER-CASE','What would change your mind?')]):
        yy=557+i*76
        body+=label(65,yy,a,SAGE,12)+text(267,yy,b,21)+line(65,yy+24,754,yy+24)
    body+=rect(848,160,688,600,PEACH,24,RULE)
    body+=label(884,207,'Research topology / conceptual',SAGE,11)
    body+=branches(904,284,558,298)
    body+=text(885,688,'One question. Multiple perspectives.',23,MUTED)
    return svg(1600,900,f'{BRAND}: A view is only the beginning.',body+footer())

def post_risk():
    body=rect(0,0,1600,900,PAPER)+header(2,'The scenario')
    body+=label(64,194,'02 / Change the assumptions',CLAY)
    body+=title(58,305,'Think in branches.',92)
    body+=text(65,371,'Compare what could happen before you record what you think.',28,MUTED)
    cases=[('BEAR','-12%','Expectations reset.','#f2a5a7'),('BASE','+6%','The thesis develops.',SAGE),('BULL','+18%','Growth surprises.',CLAY)]
    for i,(name,value,note,color) in enumerate(cases):
        xx=64+i*496
        body+=rect(xx,435,464,279,PEACH,20,RULE)+label(xx+29,481,name,color)
        body+=text(xx+24,596,value,86,color,600,-5,True)+text(xx+29,665,note,23,MUTED)
    body+=label(65,767,'Hypothetical 30-day moves. Not forecasts or probabilities.',size=12)
    return svg(1600,900,f'{BRAND}: Think in branches.',body+footer())

def post_journal():
    body=rect(0,0,1600,900,PAPER)+header(3,'The decision')
    body+=label(64,194,'03 / Build a record',CLAY)
    body+=title(58,308,'Keep your',91)+title(58,416,'reasoning.',91,CLAY)
    body+=text(65,496,'The assumptions. The context. The why.',26,MUTED)
    body+=mark(57,558,133,False)+text(211,633,'Ready to revisit.',28)+text(211,679,'Stored in this browser.',22,MUTED)
    body+=rect(843,177,691,579,PEACH,24,RULE)
    body+=label(877,227,'Decision snapshot / example',SAGE,12)
    for i,(k,v) in enumerate([('ASSET / SCENARIO','AAPL / Base case'),('YOUR REASONING','What must remain true?'),('REVIEW','Revisit. Revise. Keep the original.')]):
        yy=296+i*140
        body+=line(877,yy-27,1500,yy-27)+label(877,yy,k,size=11)+text(877,yy+50,v,28)
    return svg(1600,900,f'{BRAND}: Keep your reasoning.',body+footer('RESEARCH PREVIEW / BROWSER-LOCAL JOURNAL'))

def tagline_lines():
    return 'Explore the branches.', 'Keep the reasoning.'

def post_preview():
    body=rect(0,0,1600,900,PAPER)+grid(1600,900)
    body+=lockup(55,27,70)+label(1150,77,'Research starts here',CLAY,11)
    body+=label(65,215,'The independent research lab',SAGE)
    body+=title(58,333,'Explore the branches.',83)+title(58,435,'Keep the reasoning.',83,CLAY)
    body+=text(65,520,'Equity research, scenarios, and a decision journal.',28,MUTED)
    for i,word in enumerate(['CHOOSE','INSPECT','TEST','RECORD']):
        xx=64+i*264
        body+=rect(xx,615,240,93,PEACH,14,RULE)+label(xx+22,648,f'0{i+1}',SAGE,10)+text(xx+22,684,word,20,WINE,600)
    body+=mark(1215,290,303,False)
    return svg(1600,900,f'{BRAND}: {TAGLINE}',body+footer('SAMPLE DATA / LOCAL JOURNAL / OPTIONAL WALLET / NO TRADES'))

def banner():
    body=rect(0,0,1500,500,PAPER)+grid(1500,500)
    body+=mark(62,75,280,False)+lockup(450,24,53)
    body+=title(449,194,'Explore the branches.',66)+title(449,280,'Keep the reasoning.',66,CLAY)
    body+=text(455,351,'An independent lab for your next decision.',25,MUTED)
    body+=line(455,411,1440,411)+label(455,459,'RESEARCH / SCENARIOS / JOURNAL',size=11)+text(1210,459,DOMAIN,18,SAGE)
    return svg(1500,500,f'{BRAND}: {TAGLINE}',body)

def og_card():
    body=rect(0,0,1200,630,PAPER)+grid(1200,630)+lockup(40,24,61)
    body+=label(903,68,'Research preview',CLAY,11)
    body+=title(40,235,'Explore the',77)+title(40,327,'branches.',77,CLAY)
    body+=text(45,406,'Keep the reasoning.',34)+text(45,457,'Equity research. Scenarios. A local journal.',24,MUTED)
    body+=branches(720,196,384,226)
    body+=line(45,537,1155,537)+label(45,583,'Sample data / independent judgment',size=11)+text(939,583,DOMAIN,18,SAGE)
    return svg(1200,630,f'{BRAND} research preview',body)

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
        contact_page.set_content(f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;padding:24px;background:{PEACH};font:16px Arial;color:{WINE}}}h1{{font:600 36px Arial;margin:0 0 24px}}main{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0;background:{PAPER};padding:14px}}img{{width:100%;height:386px;object-fit:contain;background:{PAPER}}}figcaption{{padding:12px 0 0}}</style><h1>{escape(BRAND)} — research lab asset review</h1><main>{"".join(contact_images)}</main>')
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
