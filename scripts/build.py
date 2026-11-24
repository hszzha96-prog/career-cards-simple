"""Build and verify HTML, ZIP and Pages upload candidates. No network calls."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile

from validate import validate_data, validate_site
import dashboard

ROOT = Path(__file__).resolve().parents[1]


def build():
    config = json.loads((ROOT / 'data/project.json').read_text(encoding='utf-8'))
    cards = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
    evidence = json.loads((ROOT / 'data/evidence.json').read_text(encoding='utf-8'))
    validate_data(cards, evidence)
    with tempfile.TemporaryDirectory(prefix='career-cards-') as folder:
        staged = Path(folder) / 'site'
        subprocess.run([sys.executable, str(ROOT / 'scripts/renderer.py'), '--output', str(staged)], check=True)
        report = validate_site(staged, cards, evidence)
        generated_names = sorted(source.name for source in staged.iterdir() if source.is_file())
        site = ROOT / 'site'
        site.mkdir(exist_ok=True)
        # Only generated top-level bundle files are replaced; source data is untouched.
        for previous in site.iterdir():
            if previous.is_file() and (previous.suffix == '.html' or previous.name == '使用说明.txt'):
                previous.unlink()
        for source in staged.iterdir():
            shutil.copyfile(source, site / source.name)
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / 'career-cards-simple.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name in generated_names:
            source = site / name
            info = zipfile.ZipInfo('career-cards-simple/' + source.name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, source.read_bytes())
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        if zipped.namelist() != ['career-cards-simple/' + name for name in generated_names]:
            raise ValueError('ZIP file list differs from the validated bundle')
        for name in generated_names:
            source = site / name
            if zipped.read('career-cards-simple/' + name) != source.read_bytes():
                raise ValueError('ZIP readback mismatch: ' + source.name)
    report.update(version=config['version'], snapshot_date=config['snapshot_date'], zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), zip_bytes=archive.stat().st_size)
    (dist / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/prepare_sync.py')], check=True)
    # 岗位小镇看板：读取同一份 data/，单独输出到 dashboard/，不进入 site/ 与 ZIP 的校验范围。
    board = dashboard.build()
    for warning in board['dashboard_warnings']:
        print('提示：' + warning, file=sys.stderr)
    summary = {k: v for k, v in report.items() if k != 'records'}
    summary['dashboard_cards'] = board['dashboard_cards']
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    build()
