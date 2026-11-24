"""Prepare attachment files and a change list; never upload or edit a Page."""
from pathlib import Path
import hashlib
import html
import json

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    config = json.loads((ROOT / 'data/project.json').read_text(encoding='utf-8'))
    cards = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
    records = []
    receipt_name = config.get('sync_receipt', 'sync/2026-11-25-pages-receipt.json')
    if not isinstance(receipt_name, str) or Path(receipt_name).is_absolute():
        raise ValueError('sync_receipt must be a relative path inside this repository')
    receipt_path = (ROOT / receipt_name).resolve()
    if not receipt_path.is_relative_to(ROOT) or not receipt_path.is_file():
        raise ValueError('sync_receipt must point to an existing file inside this repository')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    previous = {c['page_id']: c for c in receipt['cards']}
    if len(previous) != len(receipt['cards']):
        raise ValueError('Duplicate page_id values in the synchronization receipt')
    dest = ROOT / 'dist/pages'
    dest.mkdir(parents=True, exist_ok=True)
    expected = {c['filename'] for c in cards} | {'index.html'}
    for old in dest.glob('*.html'):
        if old.name not in expected:
            old.unlink()
    hub = html.escape(config['hub_url'], quote=True)
    for card in cards:
        text = (ROOT / 'site' / card['filename']).read_text(encoding='utf-8')
        text = text.replace('href="index.html"', f'href="{hub}" target="_blank" rel="noopener"')
        (dest / card['filename']).write_text(text, encoding='utf-8')
        digest = hashlib.sha256(text.encode()).hexdigest()
        old = previous.get(card['page_id'], {})
        records.append({'page_id': card['page_id'], 'filename': card['filename'], 'company': card['company'], 'role': card['role'], 'category': card['category'], 'sha256': digest, 'previous_sha256': old.get('sha256'), 'change': 'unchanged' if old.get('sha256') == digest else ('updated' if old else 'new'), 'uploaded_by_this_build': False})
    index = (ROOT / 'site/index.html').read_text(encoding='utf-8')
    for card in cards:
        index = index.replace('href="' + card['filename'] + '"', f'href="https://chatgpt.com/space/{card["page_id"]}" target="_blank" rel="noopener"')
    index = index.replace('href="index.html"', f'href="{hub}" target="_blank" rel="noopener"')
    index = index.replace('打开 HTML ↗', '打开岗位卡 ↗').replace('每岗独立 HTML', '每岗对应原始卡片').replace('可离线阅读', '在线目录').replace('解压后打开本目录；每张卡也可单独打开。', '点击岗位进入原卡，再打开页尾的简洁版 HTML。离线使用请下载完整压缩包。').replace('选一个岗位，查看资格、经历、准备清单与原始记录。', '选一个岗位进入原卡，再打开对应的简洁版 HTML。')
    (dest / 'index.html').write_text(index, encoding='utf-8')
    result = {'snapshot_date': config['snapshot_date'], 'mode': 'prepare-only', 'historical_receipt': receipt_path.relative_to(ROOT).as_posix(), 'cards': records}
    (ROOT / 'dist/sync-plan.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Prepared {len(cards)} attachment candidates; no remote changes.')


if __name__ == '__main__':
    prepare()
