"""生成「岗位小镇」看板：读取 data/ 下的岗位数据，输出两份同内容的文件。

- dashboard/dashboard.html：双击即可打开的离线单页（自带 dashboard/runtime.js 渲染器）。
- dashboard/canvas.dc.html：Claude Design 画布用的同一界面，便于继续在画布里改设计。

不联网，不读取邮箱、CV 或账号；勾选与经验只保存在使用者自己的浏览器。
"""
from pathlib import Path
import argparse
import hashlib
import json
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'dashboard'
sys.path.insert(0, str(DASH))
from sprites import ICONS, CROPS, LOGO, MOON  # noqa: E402

FALLBACK_COLORS = ['#BE185D', '#0E7490', '#6D28D9', '#9A3412', '#4D7C0F', '#334155', '#C2410C', '#2F5BEA', '#0F766E', '#1D4ED8', '#57534E', '#1E3A8A', '#9D174D', '#155E75']
FX_COLORS = ['#6CB4FF', '#F07AA0', '#7BD389', '#F2C14E', '#B59CFF', '#F59E5B']


def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def card_data(warnings):
    cards = load('data/cards.json')
    evidence = {e['page_id']: e for e in load('data/evidence.json')}
    looks = load('data/dashboard.json').get('cards', {})
    data = []
    for c in cards:
        e = evidence[c['page_id']]
        look = looks.get(c['filename'])
        if not look:
            warnings.append(c['filename'] + '：data/dashboard.json 未设置图标，暂用 building 与自动配色')
            look = {}
        icon = look.get('icon', 'building')
        if icon not in ICONS:
            warnings.append(c['filename'] + '：未知图标 ' + icon + '，暂用 building')
            icon = 'building'
        color = look.get('color') or FALLBACK_COLORS[int(hashlib.sha256(c['filename'].encode()).hexdigest(), 16) % len(FALLBACK_COLORS)]
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', color):
            raise ValueError(c['filename'] + ': color must look like #1A2B3C')
        seen, sources = set(), []
        for s in e['sources']:
            url = s['url']
            if not url.startswith('http') or url in seen:
                continue
            seen.add(url)
            sources.append({'label': s['label'], 'url': url, 'kind': s['kind'] + ' · ' + s['date']})
        data.append({
            'fid': c['filename'], 'co': c['company'], 'role': c['role'], 'cat': c['category'], 'status': c['status_label'],
            'pill': c['pill'], 'emp': c['employment'], 'sid': c['short_id'], 'hero': c['hero'],
            'loc': e.get('location') or '地点待核', 'color': color,
            'pxA': ICONS[icon]['a'], 'pxB': ICONS[icon]['b'],
            'kpis': [{'en': k['label'].split(' · ')[0], 'zh': (k['label'].split(' · ') + [''])[1], 'v': k['value'], 'n': k['note']} for k in c['kpis']],
            'eligTitle': c.get('eligibility_title', '招聘与申请资格'),
            'employer': [{'l': r['label'], 'v': r['value']} for r in c['employer']],
            'enote': c.get('employer_note', ''),
            'personal': [{'l': r['label'], 'v': r['value']} for r in c['personal']],
            'pnote': c.get('personal_note', ''),
            'dims': [{'name': d['name'], 'status': d['status'], 'note': d['note'], 'ok': bool(d.get('has_evidence'))} for d in c['dimensions']],
            'matrix': [{'need': m['need'], 'ev': m['evidence'], 'verdict': m['verdict']} for m in c.get('matrix', [])],
            'steps': [{'t': s['title'], 'x': s['text']} for s in c['steps']],
            'appnote': c.get('application_note', ''),
            'qkind': c.get('question_kind', ''), 'qnote': c.get('question_note', ''),
            'qs': [{'zh': q['zh'], 'en': q['en']} for q in c['questions']],
            'projects': [{'name': p['name'], 'sub': p['subtitle'], 'intro': p['intro'], 'bullets': p['bullets'], 'boundary': p['boundary']} for p in c['projects']],
            'gaps': e.get('gaps', []), 'sources': sources,
        })
    return data


def canvas_html(data, snapshot):
    rnd = random.Random(7)
    stars = []
    for _ in range(110):
        x, y = rnd.randrange(0, 1440, 2), rnd.randrange(0, 900, 2)
        size = 2 if rnd.random() < 0.8 else 4
        opacity = rnd.choice([0.25, 0.4, 0.6, 0.85])
        twinkle = rnd.random() < 0.22
        extra = ' class="tw" style="animation-delay: %.1fs"' % (rnd.random() * 4) if twinkle else ''
        stars.append('<rect%s x="%d" y="%d" width="%d" height="%d" fill="#EDE9F7" opacity="%s"></rect>' % (extra, x, y, size, size, opacity))
    # 视图切换：一层星空渐变遮罩，加一群泡泡与星屑（位置、大小、延迟固定，生成结果可重复）
    bubbles = ['<div class="veil"></div>']
    for _ in range(42):
        star = rnd.random() < 0.35
        size = rnd.choice([4, 6]) if star else rnd.randrange(10, 34, 2)
        bubbles.append('<span class="bub%s" data-d="%d" data-r="%d" data-x="%d" style="left: %dpx; top: %dpx; width: %dpx; height: %dpx"></span>' % (
            ' star' if star else '', rnd.randrange(0, 260, 10), rnd.randrange(60, 170, 10), rnd.randrange(-40, 41, 5),
            rnd.randrange(60, 1380, 4), rnd.randrange(90, 800, 4), size, size))
    bars = ''.join(bubbles)
    pool = '<div class="fxp">' + ''.join('<span class="fxs" style="background: %s"></span>' % c for c in FX_COLORS * 2) + '<span class="fxr" style="{{ringStyle}}"></span></div>'
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    if '</script' in js.lower():
        raise ValueError('Card text must not contain </script')
    html = (DASH / 'template.dc.html').read_text(encoding='utf-8')
    for key, value in [('__DATA__', js), ('__CROPS__', json.dumps(CROPS, separators=(',', ':'))),
                       ('__LOGO_A__', LOGO['a']), ('__LOGO_B__', LOGO['b']), ('__MOON__', MOON),
                       ('__STARS__', ''.join(stars)), ('__SWEEP__', bars), ('__FX__', pool * 3),
                       ('__SNAPSHOT__', snapshot), ('__LOGIC__', (DASH / 'logic.js').read_text(encoding='utf-8'))]:
        html = html.replace(key, value)
    left = re.findall(r'__[A-Z]+(?:_[A-Z]+)*__', html)
    if left:
        raise ValueError('Unfilled placeholders: ' + ', '.join(sorted(set(left))))
    return html


def standalone_html(canvas):
    helmet = re.search(r'<helmet>(.*?)</helmet>', canvas, re.S).group(1)
    body = re.search(r'</helmet>(.*?)</x-dc>', canvas, re.S).group(1)
    code = re.search(r'<script type="text/x-dc" data-dc-script[^>]*>(.*?)</script>', canvas, re.S).group(1)
    title = re.search(r'<title>(.*?)</title>', canvas).group(1)
    runtime = (DASH / 'runtime.js').read_text(encoding='utf-8')
    return ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>' + title + '</title>\n' + helmet.strip() + '\n'
            '<style>html,body{height:100%;margin:0;background:#0F0E17;overflow:hidden}'
            '#stage{position:absolute;left:50%;top:50%;width:1440px;height:900px;transform-origin:50% 50%;transform:translate(-50%,-50%)}</style>\n'
            '</head>\n<body>\n<div id="stage"></div>\n<template id="dc-template">' + body + '</template>\n'
            '<script>\n' + runtime + '</script>\n<script>\n' + code + '\n'
            '(function () {\n'
            '  var stage = document.getElementById("stage");\n'
            '  // 当桌面壁纸（Plash 等）时，上方让出菜单栏、下方让出程序坞；也可在地址后加 #desktop&top=38&bottom=92 手动指定\n'
            '  function insets() {\n'
            '    var q = new URLSearchParams(location.hash.slice(1)), ua = navigator.userAgent, cls = document.documentElement.classList;\n'
            '    var desk = q.has("desktop") || cls.contains("is-plash-app") || cls.contains("plash-is-browsing-mode") || (/AppleWebKit/.test(ua) && !/Safari\\//.test(ua) && !/Chrome|Firefox/.test(ua));\n'
            '    if (q.get("desktop") === "0") desk = false;\n'
            '    return desk ? { t: Number(q.get("top") || 38), b: Number(q.get("bottom") || 92) } : { t: 0, b: 0 };\n'
            '  }\n'
            '  function fit() {\n'
            '    var i = insets(), h = Math.max(200, window.innerHeight - i.t - i.b);\n'
            '    var s = Math.min(window.innerWidth / 1440, h / 900);\n'
            '    stage.style.top = (i.t + h / 2) + "px";\n'
            '    stage.style.transform = "translate(-50%, -50%) scale(" + s + ")";\n'
            '  }\n'
            '  window.addEventListener("resize", fit); window.addEventListener("hashchange", fit); fit();\n'
            '  setTimeout(fit, 600); setTimeout(fit, 2000);\n'
            '  DCMount(Component, stage, document.getElementById("dc-template"), {});\n'
            '})();\n</script>\n</body>\n</html>\n')


def build(canvas_out=None, page_out=None):
    warnings = []
    data = card_data(warnings)
    snapshot = load('data/project.json')['snapshot_date']
    canvas = canvas_html(data, snapshot)
    canvas_out = Path(canvas_out or DASH / 'canvas.dc.html')
    page_out = Path(page_out or DASH / 'dashboard.html')
    canvas_out.write_text(canvas, encoding='utf-8')
    page_out.write_text(standalone_html(canvas), encoding='utf-8')
    return {'dashboard_cards': len(data), 'dashboard_warnings': warnings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canvas', type=Path, help='画布文件输出路径（默认 dashboard/canvas.dc.html）')
    parser.add_argument('--page', type=Path, help='离线单页输出路径（默认 dashboard/dashboard.html）')
    args = parser.parse_args()
    result = build(args.canvas, args.page)
    for w in result['dashboard_warnings']:
        print('提示：' + w, file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False))
