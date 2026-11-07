#!/usr/bin/env python3
"""Dependency-free source checks; use check-browser.cjs for rendered behavior."""
import ast
import json
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.elements, self.text = [], [], []
        self.open_elements, self.parents, self.content = [], {}, {}
    def handle_starttag(self, tag, attrs):
        index = len(self.elements)
        self.parents[index] = self.open_elements[-1] if self.open_elements else None
        self.content[index] = []
        self.elements.append((tag, dict(attrs)))
        if tag not in VOID:
            self.stack.append(tag)
            self.open_elements.append(index)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f'Unbalanced tag: {tag}, stack: {self.stack}'
        self.stack.pop()
        self.open_elements.pop()
    def handle_data(self, data):
        if not {'script', 'style'} & set(self.stack):
            self.text.append(data)
        for index in self.open_elements:
            self.content[index].append(data)
    def text_at(self, index):
        return normalized(''.join(self.content[index]))
    def descendants(self, index):
        return [i for i in self.parents if self.is_descendant(i, index)]
    def is_descendant(self, child, ancestor):
        while self.parents[child] is not None:
            child = self.parents[child]
            if child == ancestor:
                return True
        return False

def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()

PAGES = {'en': ROOT / 'index.html', 'nl': ROOT / 'nl' / 'index.html'}
BASE = 'https://acsedasec.com/'
URLS = {'en': BASE, 'nl': BASE + 'nl/'}
ALTERNATES = {**URLS, 'x-default': BASE}

def check_page(lang, path):
    """Structural checks; links resolve relative to the page's own folder."""
    doc = Document()
    doc.feed(path.read_text())
    assert not doc.stack, f'{lang}: unclosed tags: {doc.stack}'
    ids = [attrs['id'] for _, attrs in doc.elements if 'id' in attrs]
    assert len(ids) == len(set(ids)), f'{lang}: duplicate IDs'
    assert sum(tag == 'h1' for tag, _ in doc.elements) == 1
    h1_index = next(i for i, (tag, _) in enumerate(doc.elements) if tag == 'h1')
    expected_h1 = {
        'en': 'Managed cybersecurity for businesses in Aruba, the Caribbean and the Netherlands',
        'nl': 'Managed cybersecurity voor het mkb in Nederland en op Aruba',
    }
    assert doc.text_at(h1_index) == expected_h1[lang]
    assert doc.elements[h1_index][1]['class'] == 'hero-pill entrance'
    assert sum(tag == 'main' for tag, _ in doc.elements) == 1
    assert 'contact' in ids
    html = next(attrs for tag, attrs in doc.elements if tag == 'html')
    assert html.get('lang') == lang, f'{path}: <html lang> should be {lang}'
    for tag, attrs in doc.elements:
        for attr in ('href', 'src', *(('content',) if tag == 'meta' and attrs.get('property') == 'og:image' else ())):
            target = attrs.get(attr, '')
            if target.startswith('#'):
                assert target[1:] in ids, f'{lang}: missing anchor: {target}'
            elif target and not re.match(r'\w+:', target):
                resolved = (path.parent / target).resolve()
                # Directory links ("./", "nl/", "../") rely on the server's index.html.
                if target.endswith('/'):
                    resolved = resolved / 'index.html'
                assert resolved.is_file() and ROOT in resolved.parents, f'{lang}: missing file: {target}'
        if tag == 'img':
            assert all(attrs.get(k) for k in ('alt', 'width', 'height')), 'Image missing accessibility/dimension attributes'
            if 'fetchpriority' not in attrs:
                assert attrs.get('loading') == 'lazy', 'Below-fold image must be lazy-loaded'
        if tag in ('input', 'select'):
            assert attrs.get('id'), 'Form control needs an ID'
        for attr in ('aria-controls', 'aria-describedby'):
            for target in attrs.get(attr, '').split():
                assert target in ids, f'{lang}: broken {attr}: {target}'
    # Language switch: one link per language, the page's own marked current, plus hreflang alternates.
    switch = [attrs for tag, attrs in doc.elements if tag == 'a' and attrs.get('hreflang')]
    assert sorted(a['hreflang'] for a in switch) == ['en', 'nl'], f'{lang}: language links'
    assert [a['hreflang'] for a in switch if a.get('aria-current') == 'true'] == [lang], f'{lang}: aria-current language'
    alternates = {a['hreflang']: a['href'] for tag, a in doc.elements if tag == 'link' and a.get('rel') == 'alternate'}
    assert set(alternates) == {'en', 'nl', 'x-default'}, f'{lang}: hreflang alternates'
    assert alternates['x-default'] == alternates['en']
    assert alternates == ALTERNATES, f'{lang}: absolute hreflang URLs'
    for a in switch:
        assert alternates[a['hreflang']] == urljoin(URLS[lang], a['href']), f'{lang}: switch and hreflang disagree for {a["hreflang"]}'

    canonicals = [a['href'] for tag, a in doc.elements if tag == 'link' and a.get('rel') == 'canonical']
    assert canonicals == [URLS[lang]], f'{lang}: canonical URL'
    meta = {a.get('property', a.get('name')): a['content'] for tag, a in doc.elements if tag == 'meta' and 'content' in a}
    assert meta['og:url'] == URLS[lang]
    assert meta['og:image'] == BASE + 'assets/photos/server.jpg'
    assert (meta['og:image:width'], meta['og:image:height']) == ('1024', '576')
    assert meta['twitter:card'] == 'summary_large_image'
    assert meta['description'] == meta['og:description']
    assert meta['og:title'] == doc.text_at(next(i for i, (tag, _) in enumerate(doc.elements) if tag == 'title'))

    faq_index = next(i for i, (_, a) in enumerate(doc.elements) if a.get('id') == 'faq')
    contact_index = next(i for i, (_, a) in enumerate(doc.elements) if a.get('id') == 'contact')
    assert doc.elements[faq_index][0] == 'section' and faq_index < contact_index
    faq_elements = doc.descendants(faq_index)
    headings = [tag for i in faq_elements for tag, _ in [doc.elements[i]] if re.fullmatch(r'h[1-6]', tag)]
    assert headings == ['h2'], f'{lang}: FAQ heading order'
    visible_faq = []
    for i in faq_elements:
        if doc.elements[i][0] != 'details':
            continue
        children = [j for j, parent in doc.parents.items() if parent == i]
        assert [doc.elements[j][0] for j in children] == ['summary', 'p'], f'{lang}: FAQ disclosure structure'
        visible_faq.append(tuple(doc.text_at(j) for j in children))
    assert len(visible_faq) == 6, f'{lang}: six visible FAQs'

    entities = []
    for i, (tag, attrs) in enumerate(doc.elements):
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            data = json.loads(''.join(doc.content[i]))
            assert data['@context'] == 'https://schema.org'
            entities.extend(data.get('@graph', [data]))
    faq_schemas = [e for e in entities if e.get('@type') == 'FAQPage']
    assert len(faq_schemas) == 1, f'{lang}: one FAQPage schema'
    faq_schema = faq_schemas[0]
    assert faq_schema['inLanguage'] == lang
    assert len(faq_schema['mainEntity']) == len(visible_faq)
    schema_faq = []
    for entry in faq_schema['mainEntity']:
        assert entry['@type'] == 'Question' and entry['acceptedAnswer']['@type'] == 'Answer'
        schema_faq.append((entry['name'], entry['acceptedAnswer']['text']))
    assert schema_faq == visible_faq, f'{lang}: schema FAQ text must match visible text exactly'
    services = [e for e in entities if 'ProfessionalService' in e.get('@type', [])]
    assert len(services) == 1, f'{lang}: ProfessionalService schema'
    service = services[0]
    assert 'Organization' in service['@type']
    assert service['name'] == 'Acseda Cybersecurity' and service['url'] == URLS[lang]
    assert service['description'] == meta['description'] and service['slogan']
    assert service['email'] == 'hello@acsedasec.com' and service['knowsLanguage'] == ['en', 'nl']
    assert service['areaServed'] == (['Aruba', 'Caribbean', 'Netherlands'] if lang == 'en' else ['Nederland', 'Aruba', 'Caribisch gebied'])
    assert not {'address', 'telephone'} & service.keys(), 'No office address or placeholder phone in schema'
    for key in ('logo', 'image'):
        assert service[key].startswith(BASE)
        assert (ROOT / urlparse(service[key]).path.lstrip('/')).is_file()
    return doc, ids

docs = {lang: check_page(lang, path) for lang, path in PAGES.items()}
doc, ids = docs['en']

# Both languages must share one structure; count-up amounts may differ by currency.
def skeleton(document):
    body = document.elements[[tag for tag, _ in document.elements].index('body'):]
    keep = lambda k, v: k in ('id', 'class', 'type', 'for', 'name', 'role') or k.startswith('data-') or (k == 'href' and v.startswith('#'))
    return [(tag, sorted((k, '<localized count>' if k == 'data-count' else v) for k, v in attrs.items() if keep(k, v))) for tag, attrs in body]
en_skeleton, nl_skeleton = skeleton(docs['en'][0]), skeleton(docs['nl'][0])
assert len(en_skeleton) == len(nl_skeleton), f'EN/NL element count differs: {len(en_skeleton)} vs {len(nl_skeleton)}'
for index, (a, b) in enumerate(zip(en_skeleton, nl_skeleton)):
    assert a == b, f'EN/NL structure differs at element {index}: {a} vs {b}'

# Verify literal copy from the local reference generator without executing it.
reference = ast.parse((ROOT / 'reference/build_landing.py').read_text())
page_text = normalized(' '.join(doc.text))
expected = []
for node in reference.body:
    # Skip implementation helpers and post-render equalisation code.
    if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
        continue
    for call in ast.walk(node):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            continue
        if call.func.id in ('text', 'h2', 'body', 'eyebrow') and len(call.args) > 1:
            value = call.args[1]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                expected.append(value.value)
for value in expected:
    assert normalized(value) in page_text, f'Reference copy missing: {value}'
for name in ('services', 'events', 'SECTORS'):
    assignment = next(n for n in reference.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    for entry in assignment.value.elts:
        # Service title, subtitle, description and list; event time/title/description; industry title/description.
        positions = {'services': (1, 2, 3, 4), 'events': (0, 2, 3), 'SECTORS': (1, 2)}[name]
        for position in positions:
            value = ast.literal_eval(entry.elts[position])
            for text in value if isinstance(value, list) else [value]:
                assert normalized(text) in page_text, f'Missing {name} copy: {text}'
css = (ROOT / 'css/styles.css').read_text()
for token, value in {'royal':'#1C4FB8','signal':'#2F6EE0','navy':'#0D1F45','navy-2':'#16306A','deep':'#081430','sun':'#F4B63F','bg':'#F3F6FB','ink':'#0F1A30','muted':'#566583','line':'#D8DFEC','soft':'#E6EDF8'}.items():
    assert re.search(rf'--{token}\s*:\s*{value}', css)
assert 'prefers-reduced-motion:reduce' in css

robots = (ROOT / 'robots.txt').read_text().splitlines()
assert [line.strip() for line in robots if line.strip()] == ['User-agent: *', 'Allow: /', 'Sitemap: ' + BASE + 'sitemap.xml']
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
assert sitemap.tag == '{' + ns['s'] + '}urlset'
entries = sitemap.findall('s:url', ns)
assert sorted(entry.findtext('s:loc', namespaces=ns) for entry in entries) == sorted(URLS.values())
for entry in entries:
    links = entry.findall('x:link', ns)
    assert len(links) == 3 and all(link.get('rel') == 'alternate' for link in links)
    assert {link.get('hreflang'): link.get('href') for link in links} == ALTERNATES
print(f'PASS: en + nl valid tag nesting, {len(ids)} unique IDs each, local assets and anchors, image attributes, ARIA references, language switch and absolute hreflang, canonical and social metadata, valid JSON-LD with 6 matching FAQs per page, robots.txt and sitemap.xml, EN/NL structural parity ({len(en_skeleton)} elements), approved EN copy and colour tokens.')
