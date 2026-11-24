"""Validate a complete offline bundle without contacting any external service."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import argparse
import hashlib
import json
import re
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.questions, self.sections = [], [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if 'data-q' in attrs:
            self.questions.append(attrs['data-q'])
        if tag == 'section' and 'id' in attrs:
            self.sections.append(attrs['id'])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_data(cards, evidence):
    require(isinstance(cards, list) and isinstance(evidence, list), 'Cards and evidence must be JSON arrays')
    require(bool(cards), 'No cards supplied')
    require(all(isinstance(c, dict) for c in cards + evidence), 'Every card/evidence entry must be an object')
    for key in ('page_id', 'filename'):
        values = [c[key] for c in cards]
        require(all(isinstance(value, str) for value in values), f'{key} must be a string')
        require(len(values) == len(set(values)), f'Duplicate {key}')
    require({c['page_id'] for c in cards} == {x['page_id'] for x in evidence}, 'Card/evidence IDs differ')
    require(len(evidence) == len(cards), 'Duplicate evidence IDs')
    byid = {x['page_id']: x for x in evidence}
    keys = [c.get('storage_key', 'career-simple-' + c['page_id'] + '-prep-v1') for c in cards]
    require(all(isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9_.:-]+', key) for key in keys), 'Unsafe progress storage_key')
    require(len(keys) == len(set(keys)), 'Duplicate progress storage_key')
    for c in cards:
        require(re.fullmatch(r'[a-z0-9-]+\.html', c['filename']) is not None, f'Unsafe filename: {c["filename"]}')
        require(c['filename'] != 'index.html', 'index.html is reserved for the directory')
        require(re.fullmatch(r'page_[a-zA-Z0-9]+', c['page_id']) is not None, 'Invalid page ID')
        require(c['category'] in {'candidate', 'applied', 'incomplete', 'closed', 'trash'}, 'Invalid category')
        source = byid[c['page_id']]
        require(c['filename'] == source['filename'] and c['category'] == source['category'], f'Card/evidence identity mismatch: {c["page_id"]}')
        for field, count in [('kpis', 4), ('employer', 5), ('personal', 5), ('dimensions', 5), ('projects', 2), ('steps', 4), ('questions', 5)]:
            require(isinstance(c[field], list), f'{c["filename"]}: {field} must be an array')
            require(len(c[field]) == count, f'{c["filename"]}: {field} needs {count} entries')


def validate_site(site, cards=None, evidence=None):
    site = Path(site).resolve()
    cards = cards if cards is not None else json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
    evidence = evidence if evidence is not None else json.loads((ROOT / 'data/evidence.json').read_text(encoding='utf-8'))
    validate_data(cards, evidence)
    css = (ROOT / 'templates/simple.css').read_text(encoding='utf-8')
    records, all_keys, count_links = [], [], 0
    expected = {c['filename'] for c in cards} | {'index.html', '使用说明.txt'}
    actual = {p.name for p in site.iterdir() if p.is_file()}
    require(actual == expected, f'Unexpected/missing bundle files: {actual ^ expected}')
    for filename in sorted(expected - {'使用说明.txt'}):
        text = (site / filename).read_text(encoding='utf-8')
        page = Page()
        page.feed(text)
        require(len(page.ids) == len(set(page.ids)), f'Duplicate anchors: {filename}')
        require(re.search(r'<style>(.*?)</style>', text, re.S).group(1) == css, f'Template mismatch: {filename}')
        for link in page.links:
            url = urlsplit(link)
            if url.scheme in ('http', 'https'):
                continue
            require(not url.scheme and not url.netloc, f'Unexpected link scheme: {link}')
            target = (site / unquote(url.path)).resolve() if url.path else site / filename
            require(target.is_relative_to(site) and target.is_file(), f'Broken local link: {filename}: {link}')
            if url.fragment:
                target_page = page
                if target != site / filename:
                    target_page = Page()
                    target_page.feed(target.read_text(encoding='utf-8'))
                require(url.fragment in target_page.ids, f'Broken anchor: {filename}: {link}')
            count_links += 1
        if filename == 'index.html':
            for card in cards:
                require(page.links.count(card['filename']) == 1, f'Directory mapping mismatch: {card["filename"]}')
        else:
            card = next(c for c in cards if c['filename'] == filename)
            require(card['page_id'] in text, f'Missing original card: {filename}')
            require(page.questions == list(map(str, range(5))), f'Checklist mismatch: {filename}')
            require(page.sections == ['eligibility', 'match', 'evidence', 'prep', 'sources'], f'Section mismatch: {filename}')
            keys = re.findall(r"const key='([^']+)'", text)
            require(len(keys) == 1, f'Progress key mismatch: {filename}')
            require(keys[0] == card.get('storage_key', 'career-simple-' + card['page_id'] + '-prep-v1'), f'Changed progress key: {filename}')
            all_keys += keys
            records.append({'filename': filename, 'page_id': card['page_id'], 'category': card['category'], 'progress_key': keys[0], 'sha256': hashlib.sha256(text.encode()).hexdigest()})
    require(len(all_keys) == len(set(all_keys)), 'Progress keys are shared between jobs')
    return {'cards': len(cards), 'categories': dict(Counter(c['category'] for c in cards)), 'local_links_checked': count_links, 'unique_progress_keys': len(all_keys), 'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, default=ROOT / 'site')
    args = parser.parse_args()
    result = validate_site(args.site)
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, ensure_ascii=False))
