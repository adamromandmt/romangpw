"""Statyczna kontrola wygenerowanej strony (bez sieci): id, SEO, hreflang, OG, linki wewnętrzne, kotwice, sitemap.

Użycie: python3 tools/check_site.py   (kod wyjścia 1, gdy są problemy; uruchamiane w CI po `python3 build.py`)
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://' + (ROOT / 'CNAME').read_text().strip()
print('SITE', SITE)


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []      # (rel, href, hreflang, extra)
        self.metas = {}      # name/property -> content
        self.hrefs = []
        self.srcs = []
        self.title = ''
        self._t = False
        self.h = []          # heading levels in order
        self.in_title = False
        self.h1 = 0
        self.lang = None
        self.cur_h = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'head':
            self.in_head = True
        if tag == 'body':
            self.in_head = False
        if tag == 'title' and getattr(self, 'in_head', False):
            self.in_title = True
        if tag == 'link':
            self.links.append((a.get('rel'), a.get('href'), a.get('hreflang'), a))
        if tag == 'meta':
            k = a.get('name') or a.get('property')
            if k:
                self.metas[k] = a.get('content')
        if tag == 'a' and a.get('href') is not None:
            self.hrefs.append(a['href'])
        if tag in ('img', 'script', 'source') and a.get('src'):
            self.srcs.append(a['src'])
        if re.fullmatch(r'h[1-6]', tag):
            self.h.append(int(tag[1]))

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def url_to_file(url):
    u = urlparse(url)
    p = unquote(u.path)
    if p.endswith('/'):
        p += 'index.html'
    return ROOT / p.lstrip('/')


pages = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts and '__pycache__' not in p.parts)
problems = []
ids_by_page = {}
parsed = {}
for f in pages:
    rel = f.relative_to(ROOT).as_posix()
    pr = P()
    pr.feed(f.read_text(encoding='utf-8'))
    parsed[rel] = pr
    ids_by_page[rel] = set(pr.ids)

for rel, pr in parsed.items():
    f = ROOT / rel
    is404 = rel == '404.html'
    # duplicate ids
    dup = {i for i in pr.ids if pr.ids.count(i) > 1}
    if dup:
        problems.append(f'{rel}: duplicate ids {sorted(dup)}')
    # lang
    if pr.lang not in ('pl', 'en'):
        problems.append(f'{rel}: <html lang> = {pr.lang}')
    exp_lang = 'en' if rel.startswith('en/') else 'pl'
    if not is404 and pr.lang != exp_lang:
        problems.append(f'{rel}: lang {pr.lang} != {exp_lang}')
    # title / description
    t = pr.title.strip()
    if 'GPW Radar' not in t:
        problems.append(f'{rel}: title without brand: {t!r}')
    if len(t) > 75:
        problems.append(f'{rel}: title too long ({len(t)}): {t!r}')
    d = pr.metas.get('description') or ''
    if not is404 and not (40 <= len(d) <= 300):
        problems.append(f'{rel}: description length {len(d)}')
    # headings: exactly one h1, no skipped levels
    if pr.h.count(1) != 1:
        problems.append(f'{rel}: h1 count {pr.h.count(1)}')
    prev = 0
    for lv in pr.h:
        if prev and lv > prev + 1:
            problems.append(f'{rel}: heading jump h{prev}->h{lv}')
            break
        prev = lv
    canon = [l for l in pr.links if l[0] == 'canonical']
    if is404:
        if 'noindex' not in (pr.metas.get('robots') or ''):
            problems.append(f'{rel}: 404 without noindex')
        continue
    if len(canon) != 1:
        problems.append(f'{rel}: canonical count {len(canon)}')
        continue
    c = canon[0][1]
    if not c.startswith(SITE + '/'):
        problems.append(f'{rel}: canonical not absolute {c}')
    else:
        # canonical must point to existing file
        cf = url_to_file(c)
        if not cf.exists():
            problems.append(f'{rel}: canonical target missing {c}')
        elif cf.resolve() != f.resolve():
            problems.append(f'{rel}: canonical points to different file {c}')
    # hreflang
    alts = {l[2]: l[1] for l in pr.links if l[0] == 'alternate' and l[2]}
    for k in ('pl', 'en', 'x-default'):
        if k not in alts:
            problems.append(f'{rel}: missing hreflang {k}')
        elif not alts[k].startswith(SITE + '/'):
            problems.append(f'{rel}: hreflang {k} not absolute {alts[k]}')
        elif not url_to_file(alts[k]).exists():
            problems.append(f'{rel}: hreflang {k} target missing {alts[k]}')
    if alts.get(exp_lang) and alts.get(exp_lang) != c:
        problems.append(f'{rel}: hreflang self != canonical ({alts.get(exp_lang)} vs {c})')
    # OG / twitter
    for k in ('og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'og:site_name', 'og:locale',
              'twitter:card', 'twitter:image'):
        if not pr.metas.get(k):
            problems.append(f'{rel}: missing {k}')
    if pr.metas.get('og:url') and pr.metas['og:url'] != c:
        problems.append(f'{rel}: og:url != canonical')
    img = pr.metas.get('og:image') or ''
    if not img.startswith(SITE + '/') or not url_to_file(img).exists():
        problems.append(f'{rel}: og:image bad {img}')
    if img and f'og-{exp_lang}.png' not in img:
        problems.append(f'{rel}: og:image not language specific {img}')

# link check (internal)
bad_links = 0
for rel, pr in parsed.items():
    base = (ROOT / rel).parent
    for h in pr.hrefs + pr.srcs:
        if re.match(r'^(https?:|mailto:|tel:|data:|javascript:)', h):
            if h.startswith(SITE + '/'):
                tf = url_to_file(h.split('#')[0])
                if not tf.exists():
                    problems.append(f'{rel}: absolute internal link broken {h}')
            continue
        if h.startswith('#'):
            if len(h) > 1 and h[1:] not in ids_by_page[rel]:
                problems.append(f'{rel}: anchor {h} missing')
            continue
        pth, _, frag = h.partition('#')
        pth = pth.split('?')[0]
        if rel == '404.html' and pth.startswith('/'):
            tf = ROOT / pth.lstrip('/')
        elif pth.startswith('/'):
            tf = ROOT / pth.lstrip('/')
        else:
            tf = (base / pth).resolve()
        if tf.is_dir():
            tf = tf / 'index.html'
        if not tf.exists():
            problems.append(f'{rel}: broken link {h}')
            bad_links += 1
        elif frag and tf.suffix == '.html':
            trel = tf.resolve().relative_to(ROOT.resolve()).as_posix()
            if trel in ids_by_page and frag not in ids_by_page[trel]:
                problems.append(f'{rel}: link {h} -> missing anchor in {trel}')

# sitemap
sm = ET.parse(ROOT / 'sitemap.xml')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
locs = [u.find('s:loc', ns).text for u in sm.getroot().findall('s:url', ns)]
print('sitemap urls:', len(locs))
for u in locs:
    if not u.startswith(SITE + '/'):
        problems.append(f'sitemap: not absolute {u}')
    elif not url_to_file(u).exists():
        problems.append(f'sitemap: missing file {u}')
# every canonical must be in sitemap
canon_set = set()
for rel, pr in parsed.items():
    for l in pr.links:
        if l[0] == 'canonical' and rel != '404.html':
            canon_set.add(l[1])
missing = canon_set - set(locs)
extra = set(locs) - canon_set
for m in sorted(missing):
    problems.append(f'sitemap: canonical not in sitemap {m}')
for m in sorted(extra):
    problems.append(f'sitemap: url without matching canonical page {m}')
print('robots:', (ROOT / 'robots.txt').read_text().strip().replace('\n', ' | '))
print('pages checked:', len(parsed))
print('PROBLEMS:', len(problems))
for p in problems:
    print(' -', p)
sys.exit(1 if problems else 0)
