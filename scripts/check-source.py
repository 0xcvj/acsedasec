#!/usr/bin/env python3
"""Dependency-free source checks; use check-browser.cjs for rendered behavior."""
import ast
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.elements, self.text = [], [], []
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag not in VOID:
            self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f'Unbalanced tag: {tag}, stack: {self.stack}'
        self.stack.pop()
    def handle_data(self, data):
        self.text.append(data)

def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()

PAGES = {'en': ROOT / 'index.html', 'nl': ROOT / 'nl' / 'index.html'}

def check_page(lang, path):
    """Structural checks; links resolve relative to the page's own folder."""
    doc = Document()
    doc.feed(path.read_text())
    assert not doc.stack, f'{lang}: unclosed tags: {doc.stack}'
    ids = [attrs['id'] for _, attrs in doc.elements if 'id' in attrs]
    assert len(ids) == len(set(ids)), f'{lang}: duplicate IDs'
    assert sum(tag == 'h1' for tag, _ in doc.elements) == 1
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
    for a in switch:
        assert alternates[a['hreflang']] == a['href'], f'{lang}: switch and hreflang disagree for {a["hreflang"]}'
    return doc, ids

docs = {lang: check_page(lang, path) for lang, path in PAGES.items()}
doc, ids = docs['en']

# Both languages must share one structure: same elements, IDs, classes, data attributes and in-page links.
def skeleton(document):
    body = document.elements[[tag for tag, _ in document.elements].index('body'):]
    keep = lambda k, v: k in ('id', 'class', 'type', 'for', 'name', 'role') or k.startswith('data-') or (k == 'href' and v.startswith('#'))
    return [(tag, sorted((k, v) for k, v in attrs.items() if keep(k, v))) for tag, attrs in body]
en_skeleton, nl_skeleton = skeleton(docs['en'][0]), skeleton(docs['nl'][0])
assert len(en_skeleton) == len(nl_skeleton), f'EN/NL element count differs: {len(en_skeleton)} vs {len(nl_skeleton)}'
for index, (a, b) in enumerate(zip(en_skeleton, nl_skeleton)):
    assert a == b, f'EN/NL structure differs at element {index}: {a} vs {b}'

# Verify literal copy from the generator without executing or modifying it.
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
print(f'PASS: en + nl valid tag nesting, {len(ids)} unique IDs each, local assets and anchors, image attributes, ARIA references, language switch and hreflang, EN/NL structural parity ({len(en_skeleton)} elements), approved EN copy and colour tokens.')
